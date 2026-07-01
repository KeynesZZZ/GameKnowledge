---
title: 【笔记】ECS与GameObject通信
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "GameObject", "MonoBehaviour", "混合架构", "Baking", "Companion", "笔记"]
category: DOTS技术栈
created: "2026-07-01"
updated: "2026-07-01"
description: ECS ↔ 非ECS 混合开发中的六种通信模式——EntityManager 直操作、托管 Singleton 桥接、ECS 数据读取、事件队列通知、Companion Components 与分层策略。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档]]"
  - "[[【教程】ECS架构入门]]"
  - "[[【设计原理】ECS为什么快]]"
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/index.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/companion-components.html
related: ["[[【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档]]", "[[【教程】ECS架构入门]]", "[[【设计原理】ECS为什么快]]", "[[【实战案例】10w单位渲染与动画最小Demo]]", "[[DOTS专题索引]]"]
---

# 【笔记】ECS 与 GameObject 通信

> 实际项目中，纯 ECS 只是战斗/模拟层，UI/输入/相机/过场仍是 GameObject 体系。本文系统梳理两者之间的六种通信模式与选型。

## 核心问题

ECS 的数据在 **Chunk 连续内存**里（见 [[【设计原理】ECS为什么快]]），由 **Burst Job** 并行处理；GameObject 的数据在 **托管堆**上，由 **MonoBehaviour.Update** 主线程驱动。两个世界的数据访问模型完全不同：

| 维度 | ECS (ISystem) | 非ECS (MonoBehaviour) |
|------|--------------|----------------------|
| 数据存储 | Chunk 连续内存 | 托管堆（分散） |
| 执行 | Burst Job 多核并行 | Update() 主线程串行 |
| 线程限制 | Job 内不能访问托管对象 | 主线程可直接操作 EntityManager |
| GC | 无（unmanaged） | 有（managed） |

**通信原则：桥接层尽可能窄——最少的跨边界操作，最窄的数据接口。**

---

## 通信方向总览

```
GameObject 侧 (MonoBehaviour)              ECS 侧 (Entity/System)
    │                                            │
    │  ① EntityManager 直接操作                   │
    │  ② 托管 Singleton → ECS 读取                │
    │ ──────────────────────────────────────────→│
    │                                            │
    │  ③ 从 ECS 读取组件数据                      │
    │  ④ ECS 写事件 → MonoBehaviour 消费          │
    │←──────────────────────────────────────────  │
    │                                            │
    │  ⑤ Companion Components（共存）             │
    │←──────────────────────────────────────────→│
    │                                            │
    │  ⑥ Baking 管线（编辑期转换）                 │
    │──────────────────────────────────────────→ │（运行时只有 Entity）
```

---

## ① GameObject → ECS：EntityManager 直接操作

最常见的场景——UI 按钮点击、玩家输入触发 ECS 逻辑。

```csharp
using Unity.Entities;
using Unity.Mathematics;

public class SpawnButton : MonoBehaviour
{
    private EntityManager m_EM;
    public Entity Prefab;  // 由 Baking 或代码赋值

    void Start()
    {
        m_EM = World.DefaultGameObjectInjectionWorld.EntityManager;
    }

    public void OnClick()
    {
        // 方式 A：克隆 Prefab Entity（推荐）
        Entity e = m_EM.Instantiate(Prefab);
        m_EM.SetComponentData(e, LocalTransform.FromPosition(spawnPos));

        // 方式 B：从头创建
        Entity e2 = m_EM.CreateEntity();
        m_EM.AddComponentData(e2, new Health { Current = 100, Max = 100 });

        // 方式 C：修改已有 Entity
        m_EM.SetComponentData(targetEntity, new Health { Current = 50 });
    }
}
```

> ⚠️ **限制**：`EntityManager` 的结构性变更 API（CreateEntity / AddComponent / DestroyEntity）必须在**主线程**调用，且不能在 Job 运行期间操作同一批 Entity。大量结构性变更应改用 `EntityCommandBuffer`。

### 批量操作：EntityCommandBuffer

```csharp
public class WaveSpawner : MonoBehaviour
{
    void SpawnWave(int count)
    {
        var world = World.DefaultGameObjectInjectionWorld;
        var ecb = new EntityCommandBuffer(Allocator.Temp);

        for (int i = 0; i < count; i++)
        {
            Entity e = ecb.Instantiate(Prefab);
            ecb.SetComponent(e, LocalTransform.FromPosition(RandomPos()));
        }

        // 一次性回放（比逐条 EntityManager 调用快）
        ecb.Playback(world.EntityManager);
        ecb.Dispose();
    }
}
```

---

## ② GameObject → ECS：托管 Singleton 桥接

当 MonoBehaviour 需要持续向 ECS 推送数据（如输入、配置），用 **unmanaged Singleton** 做桥接：

```csharp
using Unity.Entities;
using Unity.Mathematics;

/// <summary>全局输入状态——unmanaged struct，可 Burst / 进 Job。</summary>
public struct InputState : IComponentData
{
    public float2 MoveDir;
    public bool FirePressed;
    public float3 MouseWorldPos;
}

/// <summary>MonoBehaviour 端：每帧写入 Singleton。</summary>
public class PlayerInputBridge : MonoBehaviour
{
    private EntityManager m_EM;
    private Entity m_InputEntity;

    void Start()
    {
        var world = World.DefaultGameObjectInjectionWorld;
        m_EM = world.EntityManager;
        // 创建一个只携带 InputState 的 Entity（Singleton）
        m_InputEntity = m_EM.CreateEntity(typeof(InputState));
    }

    void Update()
    {
        var input = m_EM.GetComponentData<InputState>(m_InputEntity);
        input.MoveDir = new float2(
            Input.GetAxisRaw("Horizontal"),
            Input.GetAxisRaw("Vertical"));
        input.FirePressed = Input.GetButtonDown("Fire");
        m_EM.SetComponentData(m_InputEntity, input);
    }
}

/// <summary>ECS 端：Burst Job 读取 Singleton。</summary>
[BurstCompile]
public partial struct PlayerMoveSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        var input = SystemAPI.GetSingleton<InputState>();
        new MoveJob { Dir = input.MoveDir, Dt = SystemAPI.Time.DeltaTime }
            .ScheduleParallel();
    }

    [BurstCompile]
    partial struct MoveJob : IJobEntity
    {
        public float2 Dir;
        public float Dt;
        void Execute(ref LocalTransform t, in Speed speed)
        {
            t.Position += new float3(Dir.x, 0, Dir.y) * speed.Value * Dt;
        }
    }
}
```

> 关键：`InputState` 是 **unmanaged struct**，存在 Chunk 中，ECS 系统 Burst 读取零开销。MonoBehaviour 在主线程 `SetComponentData` 写入（非结构性变更，只改值，安全）。

### SystemAPI.GetSingleton vs SetSingleton

```csharp
// ECS 系统中读写 Singleton
var input = SystemAPI.GetSingleton<InputState>();           // 读
SystemAPI.SetSingleton(new InputState { FirePressed = false }); // 写
```

> 仅当该组件类型在 World 中**只有一个 Entity** 拥有时可用 `GetSingleton`，否则报错。

---

## ③ ECS → GameObject：MonoBehaviour 读 ECS 数据

UI 血条、调试面板等需要从 MonoBehaviour 侧读取 ECS 数据：

### 单体查询

```csharp
public class HealthBarUI : MonoBehaviour
{
    public Entity Target;  // 由 Baking 或代码指定
    private EntityManager m_EM;

    void Start() => m_EM = World.DefaultGameObjectInjectionWorld.EntityManager;

    void Update()
    {
        if (Target == Entity.Null || !m_EM.HasComponent<Health>(Target))
        {
            gameObject.SetActive(false);
            return;
        }

        var hp = m_EM.GetComponentData<Health>(Target);
        healthSlider.value = hp.Current / hp.Max;
    }
}
```

### 批量查询

```csharp
public class LeaderboardUI : MonoBehaviour
{
    private EntityQuery m_Query;

    void Start()
    {
        var world = World.DefaultGameObjectInjectionWorld;
        m_Query = world.EntityManager.CreateEntityQuery(
            typeof(Score), typeof(PlayerName));
    }

    void Refresh()
    {
        var scores = m_Query.ToComponentDataArray<Score>(Allocator.TempJob);
        var names  = m_Query.ToComponentDataArray<PlayerName>(Allocator.TempJob);
        try
        {
            // 排序 + 更新 UI
            for (int i = 0; i < scores.Length; i++)
                Debug.Log($"{names[i].Name}: {scores[i].Value}");
        }
        finally
        {
            scores.Dispose();
            names.Dispose();
        }
    }
}
```

> `ToComponentDataArray` 做了一次数据拷贝（ECS Chunk → 托管数组），适合低频 UI 刷新。别在每帧 `Update` 里调用。

---

## ④ ECS → GameObject：事件队列通知

ECS 系统产生事件（击杀、升级、伤害），MonoBehaviour 消费（显示通知、播音效）。由于 Job 内不能访问托管对象，需要 **两段式传递**：

```
ECS Job (Burst)          ECS 主线程回放         MonoBehaviour
    │                        │                      │
    │ 1. NativeQueue 写入     │                      │
    ▼                        │                      │
  [NativeQueue] ──── 2. Complete + 逐条转 ──→ [ConcurrentQueue] ──→ 3. 轮询消费
                             │                      │
                           (Job→托管转换)           (UI/音频)
```

### 完整实现

```csharp
using System.Collections.Concurrent;
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;

// ─── 事件定义 ───
public struct KillEvent : IBufferElementData
{
    public Entity Killer;
    public Entity Victim;
    public float Damage;
}

// ─── MonoBehaviour 端：全局事件桥 ───
public class GameEventBridge : MonoBehaviour
{
    public static GameEventBridge Instance { get; private set; }

    // 线程安全的托管队列（ECS 主线程写，MonoBehaviour 读）
    public readonly ConcurrentQueue<KillEvent> PendingKills = new();

    void Awake() => Instance = this;
}

// ─── ECS 端：Burst Job 收集 + 主线程回放 ───
[BurstCompile]
[UpdateInGroup(typeof(SimulationSystemGroup))]
[UpdateAfter(typeof(CombatResolveSystem))]
public partial struct KillEventSystem : ISystem
{
    private NativeQueue<KillEvent> m_Queue;

    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        m_Queue = new NativeQueue<KillEvent>(Allocator.Persistent);
    }

    [BurstCompile]
    public void OnDestroy(ref SystemState state) => m_Queue.Dispose();

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        m_Queue.Clear();

        // Job 内收集事件（Burst 并行写 NativeQueue）
        new CollectKillsJob { Queue = m_Queue.AsParallelWriter() }
            .ScheduleParallel();

        // 主线程回放：NativeQueue → 托管 ConcurrentQueue
        state.Dependency.Complete();
        var bridge = GameEventBridge.Instance;
        if (bridge == null) return;

        while (m_Queue.TryDequeue(out var ev))
            bridge.PendingKills.Enqueue(ev);
    }

    [BurstCompile]
    partial struct CollectKillsJob : IJobEntity
    {
        public NativeQueue<KillEvent>.ParallelWriter Queue;
        void Execute(Entity e, in Health hp, in LastDamage dmg)
        {
            if (hp.Current <= 0 && dmg.Amount > 0)
                Queue.Enqueue(new KillEvent { Victim = e, Killer = dmg.Source, Damage = dmg.Amount });
        }
    }
}

// ─── MonoBehaviour 消费 ───
public class KillFeedUI : MonoBehaviour
{
    void Update()
    {
        while (GameEventBridge.Instance.PendingKills.TryDequeue(out var ev))
        {
            ShowKillNotification(ev.Killer, ev.Victim, ev.Damage);
            PlayKillSound();
        }
    }
}
```

> 关键：Burst Job 内**只能写 unmanaged 结构**（`NativeQueue<T>` where T is unmanaged）。托管 `ConcurrentQueue<T>` 只能在主线程操作。`NativeQueue` 是两者之间的桥。

---

## ⑤ Companion Components：GameObject 与 Entity 共存

Unity 1.4 Baking 管线支持把**不适合纯数据化的组件**保留为 Companion。详见 [[【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档]] 的 Companion Components 章节。

### 适用场景

| 组件类型 | 能否纯 ECS？ | Companion 原因 |
|---------|-------------|---------------|
| `Light` | ❌ | URP/HDRP 光照是 GameObject 管线 |
| `ParticleSystem` | ❌ | CPU 粒子模拟是托管 |
| `VisualEffect` (VFX Graph) | ❌ | 托管组件（见 [[【笔记】大规模技能特效方案]]） |
| `AudioSource` | ❌ | 音频引擎绑定 GameObject |
| `Camera` | ⚠️ | 默认禁用转换，主相机不应是 Companion |
| `SkinnedMeshRenderer` | ⚠️ | Unity 6+ 可用 Mesh Deformations 替代 |

### 代码示例

```csharp
// SubScene 中放一个带 Light 的 GameObject
// Baking 自动保留为 Companion（只要 Light 在支持列表中）

// ECS 系统中操作 Companion（必须主线程，不能 Burst）
public partial class DayNightSystem : SystemBase
{
    protected override void OnUpdate()
    {
        float intensity = ComputeIntensity(SystemAPI.Time.ElapsedTime);

        // Companion 查询：Entities.Graphics 提供 CompanionComponent<T>
        // 不能 Burst，不能进 Job
        foreach (var light in SystemAPI.Query<RefRW<Unity.Rendering.CompanionLight>>())
        {
            light.ValueRW.Light.intensity = intensity;
        }
    }
}
```

> ⚠️ Companion 的代价：不走 Chunk 内存布局，**不享 ECS 性能**，不能 Burst / 不能进 Job。仅用于必须保留 GameObject 的情况。大规模特效应用 VFX Graph GPU 事件（见 [[【笔记】大规模技能特效方案]]），而非逐单位 Companion。

---

## ⑥ Baking 管线：编辑期 GameObject → Entity

Baking 是 GameObject → Entity 的**一次性桥梁**——在编辑器/SubScene 加载时完成转换，运行时零开销。详见 [[【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档]] 的 Baking 章节。

```csharp
using Unity.Entities;
using UnityEngine;

// ─── Authoring（SubScene 中的 MonoBehaviour，给人配）───
public class EnemyAuthoring : MonoBehaviour
{
    public float MaxHealth = 100f;
    public float Speed = 5f;
    public GameObject Prefab;
}

// ─── Baker（编辑器烘焙时调用）───
public class EnemyBaker : Baker<EnemyAuthoring>
{
    public override void Bake(EnemyAuthoring src)
    {
        var e = GetEntity(TransformUsageFlags.Dynamic);
        AddComponent(e, new Health { Current = src.MaxHealth, Max = src.MaxHealth });
        AddComponent(e, new Speed { Value = src.Speed });

        // 引用 Prefab → Entity Prefab
        if (src.Prefab != null)
            AddComponent(e, new PrefabRef { Value = GetEntity(src.Prefab, TransformUsageFlags.Dynamic) });
    }
}
```

> Baking 是 **SubScene 模式**的核心——创作期用 GameObject，运行期自动变成 Entity。不需要手写 GameObject→Entity 运行时转换代码。

---

## 选型决策树

```
需要在运行时通信吗？
│
├─ 否，只是编辑期创作 ──→ ⑥ Baking 管线
│
└─ 是，运行时需要通信
    │
    ├─ 谁发起？
    │   │
    │   ├─ GameObject → ECS
    │   │   │
    │   │   ├─ 少量操作（创建/修改）──→ ① EntityManager 直操作
    │   │   │
    │   │   └─ 持续推送（输入/配置）──→ ② 托管 Singleton
    │   │
    │   └─ ECS → GameObject
    │       │
    │       ├─ MonoBehaviour 读 ECS 数据 ──→ ③ GetComponentData / Query
    │       │
    │       ├─ ECS 主动通知 MonoBehaviour ──→ ④ 事件队列
    │       │
    │       └─ 必须保留 GameObject 组件 ──→ ⑤ Companion
    │
    └─ 通信频率高？
        │
        ├─ 每帧 ──→ 用 unmanaged struct Singleton（②），避免每帧结构性变更
        │
        └─ 偶发 ──→ EntityManager（①）或事件队列（④）
```

---

## 实际项目分层策略

```
┌──────────────────────────────────────────────────────┐
│  GameObject 层（少量、交互密集）                       │
│                                                       │
│  · 玩家角色（Animator / Rigidbody / Input）           │
│  · UI 系统（UGUI / DOTS UI Hybrid）                   │
│  · Camera（Cinemachine）                              │
│  · 音频管理（AudioSource）                            │
│  · 游戏流程管理（协程 / 状态机）                       │
│  · 过场动画（Timeline）                                │
│                                                       │
│       ↕  桥接层（窄接口）                              │
│       · EntityManager（创建/销毁/修改 Entity）         │
│       · 托管 Singleton（输入/配置/全局状态）            │
│       · 事件队列（击杀/成就/通知）                     │
│       · Companion（Light/VFX/Audio 共存）             │
│                                                       │
│  ECS 层（海量、数据并行）                              │
│                                                       │
│  · 10w 小怪/投射物/粒子                               │
│  · 寻路 / 战斗结算 / AOE                              │
│  · 大规模渲染（Entities Graphics）                    │
│  · AI 决策 / 避障 / 空间分区                           │
│                                                       │
└──────────────────────────────────────────────────────┘
```

呼应 [[【设计原理】ECS为什么快]] 的混合架构建议：**GameObject 做少量复杂交互，ECS 做海量数据并行。**

---

## 速查清单

- [ ] 单次创建/修改：`EntityManager` API（主线程，大量用 ECB 批量）
- [ ] 持续输入/配置推送：unmanaged struct Singleton（MonoBehaviour 写，ISystem Burst 读）
- [ ] MonoBehaviour 读 ECS：`GetComponentData<T>` 单体 / `ToComponentDataArray<T>` 批量
- [ ] ECS 通知 MonoBehaviour：`NativeQueue`（Burst Job）→ 主线程回放 → `ConcurrentQueue`（托管消费）
- [ ] 必须保留的 GameObject 组件：Companion Components（主线程，不享 ECS 性能）
- [ ] 编辑期创作：Baking 管线（Authoring + Baker → 运行时零开销 Entity）
- [ ] 桥接层尽量窄——最少的跨边界操作，最窄的数据接口
- [ ] 托管组件（`class` IComponentData）是逃生舱，不是默认选项

---

## 相关链接

- [[【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档]] — Baking 管线 / Companion Components / 托管组件
- [[【教程】ECS架构入门]] — Entity / Component / System 基础
- [[【设计原理】ECS为什么快]] — Chunk 内存模型 / 混合架构建议
- [[【笔记】大规模技能特效方案]] — VFX Graph（托管组件）与 ECS 桥接示例
- [[【实战案例】10w单位渲染与动画最小Demo]] — 混合架构的工程实践
- [Entities 官方手册](https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/index.html)
- [Companion Components](https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/companion-components.html)
