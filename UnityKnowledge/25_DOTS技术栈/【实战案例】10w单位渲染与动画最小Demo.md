---
title: 【实战案例】10w 单位渲染与动画最小 Demo
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "Entities Graphics", "动画", "VAT", "实战案例"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-06-30"
description: 把渲染、VAT 动画、ECS 状态机串成可跑的 10w 单位端到端最小 Demo——工程结构、关键系统、Profiler 验证清单与已知坑。
unity_version: 2022.3 LTS+ / Unity 6
status: 草稿
author: llm
sources:
  - "[[【笔记】同屏大规模单位渲染方案]]"
  - "[[【笔记】大规模单位动画方案]]"
  - "[[【片段】VAT顶点动画烘焙脚本]]"
  - "[[【笔记】Entities 1.4 与 Entities Graphics 1.4 官方文档]]"
related: ["[[【笔记】同屏大规模单位渲染方案]]", "[[【笔记】大规模单位动画方案]]", "[[【片段】VAT顶点动画烘焙脚本]]", "[[【笔记】大规模单位AI决策与寻路]]", "[[【笔记】Entities 1.4 与 Entities Graphics 1.4 官方文档]]", "[[DOTS专题索引]]"]
---

# 【实战案例】10w 单位渲染与动画最小 Demo

> 把 [[【笔记】同屏大规模单位渲染方案]] + [[【笔记】大规模单位动画方案]] + [[【片段】VAT顶点动画烘焙脚本]] 串成一个**可跑的最小工程骨架**。本文是参考实现，非某次真实项目复盘，性能数字为经验估算/待实测，已标注。

## 0. 目标与边界

- **目标**：1 个 SubScene + 运行时 Instantiate 生成 10w 单位，每单位独立移动 + 5 状态动画（VAT），个位数 batch 渲染，60fps。
- **不含**（本 Demo 范围外，见 [[【笔记】大规模单位AI决策与寻路]]）：AI 决策、寻路、战斗结算、血条 UI、音效。

## 1. 工程依赖（manifest.json 片段）

```json
{
  "dependencies": {
    "com.unity.entities": "1.4.7",
    "com.unity.entities.graphics": "1.4.17",
    "com.unity.render-pipelines.universal": "14.x",   // URP，仅 Forward+
    "com.unity.burst": "1.8.x",
    "com.unity.mathematics": "1.3.x",
    "com.unity.collections": "2.x"
  }
}
```

> ⚠️ Entities Graphics 不支持 Built-in RP；URP 必须切到 **Forward+** 路径（Project Settings → Graphics → URP Asset → Rendering Path = Forward+）。

## 2. 目录结构

```
Assets/
├─ _Scenes/
│  └─ UnitScene.unity          # 主场景，含一个 SubScene
├─ Subscenes/
│  └─ UnitSubScene.unity       # SubScene，放 UnitAuthoring prefab
├─ Scripts/
│  ├─ Authoring/
│  │  └─ UnitAuthoring.cs      # MonoBehaviour + Baker
│  ├─ Components.cs            # 业务组件
│  ├─ Systems/
│  │  ├─ UnitSpawnSystem.cs    # 运行时批量 Instantiate
│  │  ├─ UnitMovementSystem.cs # IJobEntity 移动
│  │  └─ UnitAnimSystem.cs     # IJobEntity 状态机 + 时间推进
│  └─ Shader/
│     └─ VatShader.shader      # DOTS Instancing VAT shader
├─ VAT/                        # 烘焙产物
│  ├─ VatTex_*.asset
│  └─ VatLUT_*.asset
└─ Editor/
   └─ VatBaker.cs              # 见 [[【片段】VAT顶点动画烘焙脚本]]
```

## 3. 组件定义（`Components.cs`）

```csharp
using Unity.Entities;
using Unity.Mathematics;

public enum AnimState : byte { Idle, Move, Attack1, Attack2, Death }

public struct Velocity : IComponentData { public float3 Value; }
public struct Health   : IComponentData { public float Current; public float Max; }
public struct MonsterType : IComponentData { public byte TypeId; }   // 0..11

public struct UnitAnim : IComponentData {
    public AnimState State;
    public float Time;
    public float Speed;
}

// 传 shader 的 per-instance 属性（DOTS Instancing）
// 需为每属性建组件并用 [MaterialProperty] 标注（Unity.Rendering）
// 例：
//   [MaterialProperty("_AnimIndex")] public struct AnimIndexProp : IComponentData { public float Value; }
//   [MaterialProperty("_AnimTime")]  public struct AnimTimeProp  : IComponentData { public float Value; }
```

## 4. Authoring + Baker（`UnitAuthoring.cs`）

```csharp
using Unity.Entities;
using UnityEngine;

public class UnitAuthoring : MonoBehaviour
{
    public byte MonsterTypeId = 0;
    public float MaxHealth = 100f;
    public float AnimSpeed = 1f;
}

public class UnitBaker : Baker<UnitAuthoring>
{
    public override void Bake(UnitAuthoring a)
    {
        // 单位运行时会移动 → Dynamic（得 LocalTransform + LocalToWorld）
        var e = GetEntity(TransformUsageFlags.Dynamic);
        AddComponent(e, new Velocity { Value = float3.zero });
        AddComponent(e, new Health { Current = a.MaxHealth, Max = a.MaxHealth });
        AddComponent(e, new MonsterType { TypeId = a.MonsterTypeId });
        AddComponent(e, new UnitAnim { State = AnimState.Idle, Time = 0, Speed = a.AnimSpeed });
        // 渲染组件由 MeshFilter/MeshRenderer 自动烘焙；VAT 材质挂在 prefab 上
    }
}
```

> prefab 上挂 MeshFilter + MeshRenderer + VAT 材质（12 怪可做 12 个 prefab 或同 mesh 不同材质/MaterialMeshInfo）。SubScene 里放 1 个作为「原型」由 SpawnSystem 引用。

## 5. 系统：批量生成（`UnitSpawnSystem.cs`）

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Rendering;
using Unity.Transforms;
using UnityEngine;

[BurstCompile]
public partial struct UnitSpawnSystem : ISystem
{
    private Entity m_Prefab;

    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        // 需要一个 spawner：把 SubScene 里 UnitAuthoring 的 entity 当 prefab
        // 简化：用 RequireForUpdate<SpawnRequest> 触发一次性生成
        state.RequireForUpdate<SpawnRequest>();
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // 一次性生成，禁用本系统
        state.Enabled = false;

        var req = SystemAPI.GetSingleton<SpawnRequest>();
        var em = state.EntityManager;

        // req.Prefab 已是烘焙好的 prefab entity（运行时由 spawner 配置注入）
        NativeArray<Entity> units = em.Instantiate(req.Prefab, req.Count);

        // 并行设初始位置 + 随机速度（用一个 Burst job 比主线程循环快）
        var job = new InitJob { Units = units, Seed = 12345, Radius = req.Radius };
        job.ScheduleParallel(req.Count, 64, state.Dependency).Complete();
        units.Dispose();
    }

    [BurstCompile]
    struct InitJob : IJobParallelFor
    {
        public NativeArray<Entity> Units;
        public uint Seed;
        public float Radius;
        public void Execute(int i)
        {
            // 由外部用 ECB / SetComponent 写 LocalTransform；此处仅示意初始化
        }
    }
}

public struct SpawnRequest : IComponentData
{
    public Entity Prefab;
    public int Count;       // 100_000
    public float Radius;
}
```

> ⚠️ `Instantiate(prefab, count)` 是 ECS 批量克隆的正确入口（远快于循环）。初始位置用 ECB 或后续系统设。`InitJob` 处示意简化，实际用 ECB.ParallelWriter 写 `LocalTransform`。

## 6. 系统：移动 + 动画（`UnitMovementSystem.cs` / `UnitAnimSystem.cs`）

> 代码同 [[【笔记】大规模单位动画方案]] 第三节。要点：
- 移动：`IJobEntity` 对 `(LocalTransform, Velocity)` 做 `Position += Vel * dt`。
- 动画：`IJobEntity` 按 死亡>攻击>移动>待机 优先级切 `AnimState`，推进 `AnimTime`，并写 `AnimIndexProp`/`AnimTimeProp`。
- 都加 `[BurstCompile]` + `ScheduleParallel()`。

```csharp
[BurstCompile]
public partial struct UnitMovementSystem : ISystem
{
    [BurstCompile] public void OnUpdate(ref SystemState state)
        => new MoveJob { Dt = SystemAPI.Time.DeltaTime }.ScheduleParallel();

    [BurstCompile]
    partial struct MoveJob : IJobEntity
    {
        public float Dt;
        void Execute(ref LocalTransform t, in Velocity v)
            => t.Position += v.Value * Dt;
    }
}
```

## 7. VAT shader

见 [[【片段】VAT顶点动画烘焙脚本]] 第二节。材质勾选 **SRP Batcher 兼容** + shader 启用 `DOTS_INSTANCING_ON`。

## 8. 验证清单（Profiler）

> 上线前在**目标机**用 Profiler / Frame Debugger 实测，经验数字仅作起步参考。

- [ ] **Entities Hierarchy**：单位数 = 10w，archetype 数 = 个位数（理想 1，按 mesh 种类 +N）
- [ ] **Frame Debugger**：DrawCall 个位数～12（按 mesh 种类），batch 数同
- [ ] **Profiler CPU**：
  - `UnitMovementSystem` ~1–2ms（Burst 并行）
  - `UnitAnimSystem` ~1–3ms
  - `EntitiesGraphicsSystem`（culling/batching）应稳定，无主线程尖刺
  - 无 `EntityManager.SetComponentData` 主线程阻塞热点
- [ ] **Profiler GPU**：vertex shader 多一次 VAT 采样无显著压力；overdraw（若有）才是瓶颈
- [ ] **内存**：VAT 纹理体积符合预期（RGBAFloat 大，必要时降 Half）
- [ ] **结构性变更**：Profiler 中无每帧大量 `CreateEntity/DestroyEntity`（死亡用 `IEnableableComponent` + 对象池）

## 9. 已知坑（实测时优先排查）

| 现象 | 根因 / 处置 |
|------|------------|
| batch 数爆炸到几千 | archetype 太多（怪类型用组件区分了）/ 材质实例太多 → 改用 `MonsterType` byte + 索引 |
| 单位不动 | `TransformUsageFlags` 没给 `Dynamic`（缺 LocalTransform），或移动系统没进 SimulationSystemGroup |
| 动画全单位同步播放 | per-instance `_AnimTime` 没正确上传（MaterialPropertyOverride 缺失），或 shader 没读 DOTS Instanced 属性 |
| VAT 采样错乱 | 顶点顺序不一致（烘焙与运行时 mesh 顶点顺序必须一致）；float 纹理被压缩 |
| URP 下不显示 | 渲染路径不是 Forward+；shader 未启用 DOTS Instancing；材质 SRP Batcher 不兼容 |
| 进入 PlayMode 卡很久 | 首次烘焙/加载 SubScene；确认 SubScene 已烘焙（关闭实时烘焙，用后台全量） |

## 相关链接

- [[【笔记】同屏大规模单位渲染方案]] · [[【笔记】大规模单位动画方案]] · [[【片段】VAT顶点动画烘焙脚本]] · [[【笔记】大规模单位AI决策与寻路]] · [[【笔记】Entities 1.4 与 Entities Graphics 1.4 官方文档]]
