---
title: 【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "Entities", "Entities Graphics", "Baking", "SubScene", "渲染", "综述"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-06-30"
description: 综合 Unity 官方 Entities 1.4 + Entities Graphics 1.4 手册，补全既有 ECS 笔记未覆盖的现代编程模型、Baking 烘焙管线、SubScene/内容管理与 ECS 渲染。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/index.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/index.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/baking-overview.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/baking-baker-overview.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/transforms-usage-flags.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/conversion-subscenes.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/streaming-loading-scenes.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/content-management-introduction.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/systems-comparison.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/components-managed.html
  - https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/aspects-concepts.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/requirements-and-compatibility.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/runtime-entity-creation.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/companion-components.html
  - https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/performance.html
related: ["[[【教程】ECS架构入门]]", "[[【教程】JobSystem详解]]", "[[【教程】Burst编译器]]", "[[【教程】DOTS学习路径]]", "[[DOTS专题索引]]", "[[../10_架构设计/【设计原理】ECS为什么快]]"]
---

# 【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档

> 数据来源：Unity 官方手册 `com.unity.entities@1.4`（1.4.7）+ `com.unity.entities.graphics@1.4`（1.4.17）。本文聚焦**既有 ECS 笔记未覆盖**的 1.4 现代编程模型、Baking、SubScene/内容管理、ECS 渲染。

## 文档定位

[[【教程】ECS架构入门]] 讲清了 Entity/Component/System 三要素、Archetype/Chunk、EntityCommandBuffer 与基础 SystemGroup，是 DOTS 入门骨架。但它停留在「概念演示」层面，示例仍用早期 `RenderMesh` / 自定义 `Position` 组件，**没有覆盖 1.4 量产栈的三个关键拼图**：

1. **Baking 烘焙管线** —— GameObject 创作态如何变成 Entity 运行时数据（取代旧「运行时 Conversion」）。
2. **SubScene / Entity Scene / 内容管理** —— DOTS 场景的加载、流式分片、按需投递。
3. **Entities Graphics** —— 怎么把海量 Entity 渲染出来（不是渲染管线，而是「收集渲染数据 → 喂给 URP/HDRP」）。

本文综合两份官方手册补全这三块，并修正若干 1.4 版本要点（如 **`IAspect` 在 1.4 已废弃**）。ECS 基础概念不重复，需要请回 [[【教程】ECS架构入门]]。

> ⚠️ 来源诚实声明：Baking / SubScene / Content Management / Entities Graphics / `ISystem` 对比 / 托管组件 / Aspects 废弃 等，均据上述官方手册页面编译（见 `sources`）。`SystemAPI` 与「系统更新顺序」两页抓取时官方站点持续 500，相关小节据其它页引用与 ECS 通用机制归纳，已在该小节标注，引用前建议对照原文。

---

## 0. 一张图看懂 1.4 量产栈

```
┌─ 编辑器（Authoring，给人配）──────────────────────────────┐
│  普通 Scene ── SubScene 组件 ──▶ Authoring GameObject       │
│                                   + MonoBehaviour(Authoring) │
│         仅编辑器发生  │  Baking（Baker + TransformUsageFlags）│
└──────────────────────┼───────────────────────────────────┘
                       ▼
┌─ 运行时（Runtime，给机器跑）─────────────────────────────┐
│  Entity Scene（= 二进制 Content Archive）                  │
│   ├ header(section 0) ── Resolve ──▶ 创建 meta entity       │
│   └ sections ── Load ──▶ 流式载入实际 Entity 数据           │
│                                                             │
│  World: Entity + IComponentData  ◀── System(ISystem)处理   │
│                                                             │
│  Entities Graphics: 收集 LocalToWorld+渲染组件 ──▶ BRG      │
│   ──▶ URP/HDRP(SRP Batcher) 绘制                           │
└─────────────────────────────────────────────────────────────┘
```

核心一句话：**SubScene 是创作态工具，Entity Scene 才是运行时真正加载的东西；Baking 把前者烘焙成后者，Entities Graphics 负责把后者画出来。**

---

## 1. Entities 1.4 现代编程模型

### 1.1 相对旧 DOTS（0.x）的范式转移

| 维度 | 旧 DOTS 0.x | Entities 1.x → 1.4 |
|------|-------------|--------------------|
| GameObject→Entity | 运行时 Conversion（`GameObjectConversionSystem`） | **编辑器 Baking**（运行时零转换开销） |
| 默认 System | `ComponentSystem`（托管） | **`ISystem`（非托管，可 Burst）** |
| Transform | `Translation`/`Rotation`/`Scale` 分散组件 | **`LocalTransform` + `LocalToWorld`**，由 `TransformUsageFlags` 决定加哪些 |
| 渲染包 | Hybrid Renderer（`com.unity.entities.hybrid`，已废弃） | **Entities Graphics**（`com.unity.entities.graphics`） |
| 场景加载 | `SceneSystem.LoadSubScene`（1.4 已弃用） | `SceneSystem.LoadSceneAsync` |

> 既有 [[【教程】ECS架构入门]] 的示例（`RenderMesh`、自定义 `Position`/`Velocity`）属于概念演示；1.4 实战以 `LocalTransform`、`MaterialMeshInfo` 为准。

### 1.2 组件类型全表（1.4）

| 类型 | 形态 | 存储与性能 | 用途 |
|------|------|-----------|------|
| `IComponentData`（unmanaged） | `struct`，仅 blittable 值类型 | 直接存于 archetype chunk，cache 友好，可 Burst/进 Job | **绝大多数业务数据** |
| `IManagedComponentData`（managed） | `class`，可持有任意引用类型 | 存于 World 级数组，chunk 只存索引；多一次间接寻址、引发 GC、**不能 Burst/进 Job** | 必须持有托管对象（如 `UnityEngine.Object`）时才用 |
| `IBufferElementData` | `struct` | 动态长度缓冲（chunk 内） | 变长数组（路径点、背包槽） |
| `ISharedComponentData` | `struct`，值 equality | 相同值的实体聚到同一 chunk；改变值触发实体迁移（结构性变更） | 分组（同材质/同网格归簇） |
| `ICleanupComponentData` | `struct` | 实体销毁时**不会被立即移除**，需显式清理后才真正销毁 | 资源回收（先释放 GPU/外部句柄再删实体） |
| `IEnableableComponent` | `struct`（多为 tag） | 每实体 1 bit 的 enabled 状态，**不触发结构性变更**即可「软启停」组件 | 状态开关（冷却中、眩晕），避免增删组件的开销 |
| Tag component | `struct`，无字段 | 0 字节，仅作分组/标记 | 标记（`EnemyTag`） |

> **为何优先 unmanaged**：托管组件不进 chunk，破坏内存局部性，访问慢且产生 GC。ECS 的性能优势建立在 chunk 连续布局上，托管组件是「逃生舱」而非默认选项。

### 1.3 ISystem vs SystemBase

`ISystem`（非托管 struct，默认推荐）vs `SystemBase`（托管 class，仅必要时用）。下表据官方 `systems-comparison.html`：

| 特性 | ISystem | SystemBase |
|------|---------|-----------|
| 托管 | 否 | 是 |
| 可 Burst 编译 | **是** | 否 |
| `OnUpdate` 中引用类型（如 `string`） | 不允许 | 允许 |
| 堆分配 | 零（遵循规则） | 有 |
| 生产推荐 | **是** | 仅在必要时 |

**选型决策树**：① 默认 `ISystem`；② 需要引用类型/.NET/UnityObject API → `SystemBase`；③ 用 `ISystem` 但要引用 `UnityEngine.Object` → 用 `UnityObjectRef`（安全地放进非托管上下文）。

**ISystem 生命周期**（每个回调带 `ref SystemState`）：
`OnCreate → OnStartRunning → OnUpdate（每帧）→ OnStopRunning → OnDestroy`。其中 `OnStartRunning`/`OnStopRunning` 来自可选接口 `ISystemStartStop`（系统首次更新前 / 不再匹配 `RequireForUpdate` 时触发）。`SystemState` 提供 `GetEntityQuery`、`RequireForUpdate`、`EntityManager`、`WorldUnmanaged`、`Enabled` 等。

### 1.4 SystemAPI（据通用机制归纳，原文页 500 未取）

> ⚠️ 本节据其它页引用与 ECS 通用机制归纳，`systemapi.html` 抓取失败，引用前建议对照原文。

`SystemAPI` 是一组**静态方法**，封装「系统 `OnUpdate` 主线程上下文里安全高效访问实体数据」的常见操作。**为什么用 SystemAPI 而非 EntityManager**：EntityManager 的 `GetComponent`/`SetComponent` 做完整安全检查与版本号更新、同步阻塞、破坏 Job 依赖调度；SystemAPI 复用系统持有的 query 缓存与依赖跟踪，更轻量，且能正确登记读写依赖以便多系统并行。常见成员：`SystemAPI.Query<...>()`、`HasComponent<T>`/`GetComponent<T>`/`SetComponent<T>`、`GetBuffer<T>`、`GetSingleton<T>`、`GetComponentLookup<T>(isReadOnly)`、`Time.DeltaTime`。

**现代遍历写法（推荐）**：

```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

[BurstCompile]
public partial struct MovementSystem : ISystem
{
    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        // 没有匹配实体时不跑 OnUpdate（省 CPU）
        state.RequireForUpdate<Velocity>();
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        // 用 Unity.Transforms.LocalTransform（1.4 标准），而非自定义 Position
        foreach (var (transform, velocity) in
                 SystemAPI.Query<RefRW<LocalTransform>, RefRO<Velocity>>())
        {
            transform.ValueRW.Position += velocity.ValueRO.Value * dt;
        }
    }
}

public struct Velocity : IComponentData { public float3 Value; }
```

### 1.5 Aspects（`IAspect`）—— 1.4 已废弃，仅作了解

> ⚠️ **版本要点**：官方 `aspects-concepts.html` 明确 `IAspect` 在 Entities 1.4 已 **deprecated（废弃）**，计划在后续主版本移除，转而直接用 `SystemAPI.Query<RefRW<T>, RefRO<U>>()` 组件访问。

它原本是「把一个实体若干相关组件打包成 `readonly partial struct`」的封装层（字段为 `Entity`/`RefRW<T>`/`RefRO<T>`/`DynamicBuffer<T>` 等），用于简化跨组件只读访问、提升可读性。**新代码不要再引入 Aspects**；维护旧代码时见到 `SystemAPI.Query<MyAspect>()` 知道是其含义即可，逐步迁移回裸组件查询。

### 1.6 系统更新顺序（据通用机制归纳，原文页 500 未取）

> ⚠️ 系统更新顺序页抓取失败，本节据 ECS 通用机制归纳。

`ComponentSystemGroup` 是「本身不干活、只按序驱动子系统」的特殊系统。Unity 默认三大根组：

| 默认组 | 阶段 | 典型用途 |
|--------|------|---------|
| `InitializationSystemGroup` | 帧初 | 初始化、subscene 加载、ECB 回放 |
| `SimulationSystemGroup` | 帧中 | **主要游戏逻辑**（系统默认归这里） |
| `PresentationSystemGroup` | 帧末/渲染前 | 渲染准备（⚠️ 此组后通常不可再做结构性变更） |

排序特性：`[UpdateInGroup(typeof(SimulationSystemGroup))]`（指定所属组）、`[UpdateBefore(typeof(T))]`/`[UpdateAfter(typeof(T))]`（显式先后）、`[RequireMatchingQueriesForUpdate]`（有匹配才更新）。ECS 收集这些约束构建依赖图做拓扑排序；同组无显式约束的系统顺序不保证稳定，**跨系统的数据正确性靠 JobHandle/安全句柄在数据层保证，而非靠系统顺序**。

---

## 2. Baking 烘焙管线（核心增量）

### 2.1 为什么从「运行时 Conversion」迁移到「编辑器 Baking」

旧 DOTS 在进入 PlayMode/构建时才把 GameObject 转成 Entity，问题：① 运行时转换吃 CPU、产生 GC，拖慢启动与帧率；② GameObject 同时背负创作态 + 运行时两套数据模型。

**Baking 的解法**：把「创作态 → 运行时」的昂贵映射**提前到编辑器**（类比资源导入），运行时只读已烘焙的二进制 Entity Scene。收益：运行时零转换开销、启动快；创作态数据不进包体；烘焙可缓存、可增量、可后台异步。

**两种触发模式**：
- **SubScene 打开 → Live Baking（实时烘焙）**：边编辑边烘焙；其中 **Incremental baking（增量）** 只重烘焙被改动的 GameObject，**Full baking（全量）** 处理整个场景。
- **SubScene 关闭 → 后台异步全量烘焙**：由后台导入进程完成，主编辑器保持响应。

> ⚠️ **增量 vs 全量输出不完全一致**（entity 顺序/数量/chunk 布局可能有差异）。写 Baker 要保证两种模式结果一致，避免「编辑器正常、打包异常」。改了烘焙代码后，给程序集加 `[BakingVersion]` 并递增版本号，才能让旧 entity scene 过期重烘焙。

### 2.2 Authoring + Baker 工作流

**Authoring component** = 挂在 SubScene 里 GameObject 上的普通 `MonoBehaviour`（创作态输入）。**`Baker<TAuthoringType>`** = 烘焙时对每个该类型 Authoring 调一次，把数据写成 Entity 上的 component。

**Baker 三条架构约束**（重要）：
1. **无状态**：Baker 实例只构造一次，`Bake` 被多次调用且顺序不定。**禁止缓存字段**，否则增量烘焙错乱。
2. **可撤销**：Authoring 改动时 Unity 先撤销上次烘焙影响再重烘焙，故 Baker 产出全被记录。
3. **声明依赖**：Baker 默认只跟踪自己 Authoring 字段；访问**其它** component/GameObject/资源时必须用 Baker 自身成员方法（`GetComponent<T>(other)`/`DependsOn(obj)`），否则依赖变化不会触发重烘焙。

**完整 Authoring + Baker 示例**：

```csharp
using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;

// 运行时组件
public struct RotationSpeed : IComponentData { public float RadiansPerSecond; }

// 创作组件（普通 MonoBehaviour）
public class RotationSpeedAuthoring : MonoBehaviour
{
    public float DegreesPerSecond = 90f;
}

// Baker
public class RotationSpeedBaker : Baker<RotationSpeedAuthoring>
{
    public override void Bake(RotationSpeedAuthoring authoring)
    {
        // 1) 取主 Entity 并声明 transform 用法：会自转 → 需 LocalTransform → Dynamic
        var entity = GetEntity(TransformUsageFlags.Dynamic);
        // 2) 度数转弧度写入
        AddComponent(entity, new RotationSpeed
        {
            RadiansPerSecond = math.radians(authoring.DegreesPerSecond)
        });
    }
}
```

### 2.3 TransformUsageFlags（关键）

控制烘焙时给 Entity 加哪些 transform 组件，**目的是剔除不必要的 transform 组件**（省内存/带宽）。据官方 `transforms-usage-flags.html`：

| 取值 | 含义 | 运行时通常得到 |
|------|------|---------------|
| `None` | 无特定需求（其他 Baker 仍可叠加 flag） | 仅当被叠加才有 transform 组件 |
| `Renderable` | 只需「能被渲染」，运行时不动 | `LocalToWorld`（世界空间，无层级） |
| `Dynamic` | 运行时会移动 | `LocalToWorld` + `LocalTransform`（+ `Parent` 若有动态父） |
| `WorldSpace` | 必须在世界空间（即便父是动态体） | 强制世界空间 transform |
| `NonUniformScale` | 需要非均匀缩放 | 额外非均匀 scale 组件 |
| `ManualOverride` | 忽略其它 Baker 的 flag，不加任何 transform 组件 | 无 transform 组件 |

**叠加规则**：一个 Entity 上多个 Baker 给的 flag 被 **OR 合并**。**典型优化**：静态楼 + 静态窗户子物体都标 `Renderable` → 不需要层级，transform 烘焙进各自 `LocalToWorld`，省掉 `LocalTransform`/`Parent`。Entity Prefab 默认自动标 `Dynamic`（实例化后能放进世界）。

### 2.4 IBaker vs Baking System

Baking 分两阶段：① 各 **Baker** 把 authoring 转成 component；② 所有 Baker 跑完后，跑一组 `[BakingSystem]` 系统对产出 entity 做批量后处理（执行组：`PreBakingSystemGroup` → `TransformBakingSystemGroup` → `BakingSystemGroup`（默认）→ `PostBakingSystemGroup`）。

| 维度 | `IBaker`（Baker） | Baking System |
|------|------------------|---------------|
| 作用范围 | 单个 Authoring → 自己的 entity | 整个 baking world 所有 Baker 产出后的 entity |
| 能否读/改别的 entity | ❌ | ✅（可查询修改任意 entity） |
| 增量依赖跟踪 | 自动 | 不自动 |
| 访问 authoring/`UnityEngine.Object` | ✅ | ❌（此时 authoring 已不在） |
| 选用原则 | **优先** | 仅当必须**跨 entity** 处理时 |

**结论**：能用 Baker 就用 Baker；只有逻辑依赖「多 entity 间相互作用」才上 baking system。

### 2.5 Prefab 引用

Authoring 里引用 GameObject Prefab，Baker 中 `GetEntity(authoring.Prefab, TransformUsageFlags.Dynamic)` 即得 prefab entity（带 `Prefab` tag，默认被所有 query 排除）。运行时用 `EntityManager.Instantiate(prefab)` 或 `ecb.Instantiate(prefab)` 克隆。

```csharp
public class SpawnerAuthoring : MonoBehaviour
{
    public GameObject Prefab;
    public int Count;
}
public struct Spawner : IComponentData { public Entity Prefab; public int Count; }

public class SpawnerBaker : Baker<SpawnerAuthoring>
{
    public override void Bake(SpawnerAuthoring authoring)
    {
        var entity = GetEntity(TransformUsageFlags.Dynamic);
        AddComponent(entity, new Spawner
        {
            Prefab = GetEntity(authoring.Prefab, TransformUsageFlags.Dynamic),
            Count  = authoring.Count
        });
    }
}
```

---

## 3. SubScene / Entity Scene / 内容管理

### 3.1 SubScene vs Entity Scene

**SubScene** 是挂了 `SubScene` 组件的 GameObject，其子物体就是要烘焙的 Authoring GameObject。
- **编辑器态**：SubScene 是 GameObject，子物体是 authoring。
- **运行时态**：SubScene **不再是 GameObject**，而是带 `Subscene` 组件的 Entity，作为 Entity Scene 的「挂载点」。
- **Entity Scene（= Content Archive）**：烘焙输出的二进制磁盘文件，由 header + 若干 section 组成，运行时真正加载的就是它。

| 维度 | 普通 Scene | SubScene / Entity Scene |
|------|-----------|------------------------|
| 数据形态 | GameObject + MonoBehaviour | Entity + IComponentData |
| 转换 | 运行时即用，无烘焙 | **编辑器烘焙** |
| 流式分片 | 不支持原生 | 支持 **SceneSection** 分片流式 |
| 运行时加载 | `SceneManager.LoadScene` | `SceneSystem.LoadSceneAsync` |

### 3.2 SceneSection 分片 + Resolve→Load 两阶段

Unity 把场景内 entity 分组到 **sections**（section 0 是 header）。每个 entity 带 `SceneSection` shared component 指示所属 section。加载分两步：
1. **Resolve（解析）**：加载 header，为整个 scene 和每个 section 各创建一个 **meta entity**（场景根 meta 带 `SceneRoot` tag，section meta 带 `ResolvedSection` 持有数据 `WeakReference`）。
2. **Load（载入）**：流式载入 section 实际 entity 数据；全部完成后 section meta 上出现 `SectionLoaded` tag。

加载状态由 `SectionLoadingState`/`EntitySceneLoadState` 跟踪：`Unloaded → InProgress → Loaded`。

### 3.3 运行时加载 API

两种方式：① SubScene 勾选 **Auto Load Scene**（默认开），父场景加载时自动流式加载；② 取消勾选，用 `SceneSystem` 手动控制。

| API | 作用 |
|-----|------|
| `SceneSystem.LoadSceneAsync(WorldUnmanaged, SceneGUID, LoadParameters)` | 异步加载，返回代表加载状态的 Entity（**1.4 统一入口**，`LoadSubScene` 已弃用） |
| `SceneSystem.UnloadScene(WorldUnmanaged, sceneEntity)` | 完全卸载（含 section 数据） |
| `SceneSystem.UnloadSceneFragment(WorldUnmanaged, sceneEntity)` | 卸载但**保留 section 数据**，重载更快 |

```csharp
using Unity.Entities;
using Unity.Scenes;

public partial struct SceneLoaderSystem : ISystem
{
    private Entity _sceneEntity;
    private bool _loaded;

    public void OnUpdate(ref SystemState state)
    {
        // 演示：按需加载/卸载
        if (!_loaded)
        {
            _sceneEntity = SceneSystem.LoadSceneAsync(
                state.WorldUnmanaged,
                sceneGUID,                       // SubScene 的 GUID
                new SceneSystem.LoadParameters());
            _loaded = true;
        }
        else
        {
            SceneSystem.UnloadSceneFragment(state.WorldUnmanaged, _sceneEntity);
            _loaded = false;
        }
    }
}
```

### 3.4 Content Management（1.4 重点新方向）

除 SceneSection 流式外，1.4 提供基于 **ContentLoadModule** 的更通用**内容投递系统**：把 scene 或 object 打包成 Content Archive（用 Content Management 窗口创建），用 `WeakReference`/`WeakObjectReference<T>` 持有弱引用，运行时通过 `ContentLoadSystem` **引用计数**地 `Load`/`Release`。它把「加载什么」从「玩家在哪」解耦，支持任意（非 scene）对象按需加载，是 SceneSection 的超集/演进方向。1.4 里 subscene 也被纳入「content set（用 GUID 命名）」统一管理。

> **1.4 升级注意**：Entity Scene 序列化文件格式版本升级，旧 SubScene entity 缓存**需要重建**；`SceneSystem.LoadSubScene` 弃用改 `LoadSceneAsync`；`SceneSystem` 改为 Burst 化的 `ISystem`。

---

## 4. Entities Graphics 渲染

### 4.1 定位：不是渲染管线

> 官方原话：**"Entities Graphics is not a render pipeline: it is a system that collects the data necessary for rendering ECS entities, and sends this data to Unity's existing rendering architecture."**

它是 ECS 与 URP/HDRP 之间的**桥梁**：本身不定义渲染 Pass、不做光照、不输出帧；URP/HDRP 才负责内容创作与渲染 Pass。底层构建于引擎的 **`BatchRendererGroup` (BRG) API**（Unity 2022.1 重写为统一 code path）。普通用户无需直接调 BRG，Entities Graphics 已封装；只在完全自定义渲染数据收集时才直接用 BRG。

| 维度 | Hybrid Renderer（旧，已废弃） | Entities Graphics（1.x） |
|------|------------------------------|--------------------------|
| 包名 | `com.unity.entities.hybrid` | `com.unity.entities.graphics` |
| 状态 | 废弃 | 当前推荐 |
| 底层 | 旧 code path | 统一新 BRG API |

### 4.2 Requirements（硬性）

| 维度 | 要求 |
|------|------|
| 渲染管线 | **不支持 Built-in RP**；HDRP 需 Unity 2022 LTS；URP 需 Unity 2022 LTS 且**仅 Forward+ 路径** |
| 平台 | **不支持 WebGL**；HDRP 不支持 Android/iOS；URP 移动端仅 Vulkan/GLES3.1+/Metal |
| 多 World | 当前**不支持**多 World 同时渲染 |
| Shader | 必须 **DOTS Instancing 兼容**（URP/HDRP 默认 Shader 已兼容；自定义 Shader 需手动实现） |
| 其它 | 需 SRP Batcher |

### 4.3 每帧渲染数据收集管线

| 阶段 | 说明 |
|------|------|
| ① 数据收集 | 收集同时拥有 `LocalToWorld` + 渲染组件 + `RenderBounds` 的实体 |
| ② LOD 计算 | 按屏幕空间百分比选 LOD level（`MeshLODGroupComponent` → 选定 `MeshLODComponent`） |
| ③ 剔除 | 视锥剔除（开箱即用）+ 层级剔除；遮挡剔除视管线有限支持 |
| ④ 排序/合批 | 按材质/网格排序；**每个 archetype 一个 batch**，BRG 过大自动拆分 |
| ⑤ 属性上传 | per-instance 属性上传为 GPU buffer（DOTS Instancing） |
| ⑥ 提交渲染 | 经 BRG 提交 draw commands，URP/HDRP 用 **SRP Batcher** 绘制 |

> ⚠️ **材质上传发生在剔除之前**，因此**纹理流送（Texture streaming）不起作用**。

### 4.4 指定/更换网格与材质：MaterialMeshInfo

实体通过 `MaterialMeshInfo` 组件知道用哪个 mesh+material，两种方式：
1. **引用 `RenderMeshArray` 数组索引**（烘焙期默认）：`MaterialMeshInfo.FromRenderMeshArrayIndices(meshIndex:0, materialIndex:0)`，实体从共享的 `RenderMeshArray` 中按下标选。
2. **直接引用注册 ID**（运行时动态更换）：用 `EntitiesGraphicsSystem.RegisterMesh/ RegisterMaterial` 拿 ID，写回 `MaterialMeshInfo` 即时换（用完需 `Unregister`）。

`RenderMeshArray` 是共享组件，烘焙时 Entities Graphics **尽量把整个 SubScene 的 mesh/material 打包进一个共享 `RenderMeshArray`** 以减少 chunk 碎片化。

**运行时创建可渲染实体**（`RenderMeshUtility`）：

```csharp
using Unity.Entities;
using Unity.Rendering;
using UnityEngine.Rendering;

var em = World.DefaultGameObjectInjectionWorld.EntityManager;

// 1) 描述渲染设置（阴影/层等）
var desc = new RenderMeshDescription(
    shadowCastingMode: ShadowCastingMode.On,
    receiveShadows: true);
// 2) 共享 mesh+material 数组
var rma = new RenderMeshArray(new[] { material }, new[] { mesh });
// 3) 创建 prototype 并填充渲染组件
var proto = em.CreateEntity();
RenderMeshUtility.AddComponents(proto, em, desc, rma,
    MaterialMeshInfo.FromRenderMeshArrayIndices(0, 0));
em.AddComponentData(proto, new LocalToWorld());
// 之后用 Instantiate 在 Burst job 里高效克隆，再 SetComponent 设各自 LocalToWorld
```

> ⚠️ `AddComponents` 是主线程 API，**不适合大批量创建**。正确做法：先建 prototype，再用 `EntityCommandBuffer.ParallelWriter` 在 Burst job 里 `Instantiate` 克隆，最后 `SetComponent` 设各自数据（无结构性变更、可并行）。**不要手动逐个加图形组件**（结构性变更低效且不前向兼容）。

### 4.5 Companion Components（跨界对象）

一些图形组件（`Light`/`ParticleSystem`/`VisualEffect`/`DecalProjector`/`Volume` 等）不适合转成纯 ECS 数据，可**作为托管组件附加到实体**（Companion），在 ECS system 中查询。代价：不走 chunk 内存布局，**不享 ECS 性能**，不能 Burst/进 Job。规则：不在支持列表的 MonoBehaviour 会被剥离；Transform 层级不保留（重建为根 GameObject）；Camera 转换默认禁用。

```csharp
// 查询托管 companion —— 不能 Burst，必须主线程
class AnimateLightSystem : SystemBase
{
    protected override void OnUpdate()
    {
        foreach (var light in SystemAPI.Query<RefRW<Light>>())
            light.ValueRW.intensity = 1.5f;
    }
}
```

### 4.6 Material Overrides 与性能要点

- **Material Overrides**：用标记 `[MaterialProperty]` 的 `IComponentData`（`MaterialPropertyOverride`）逐实体覆盖材质属性，**无需新建材质**，与 SRP Batcher 兼容。⚠️ **每个唯一 per-instance 值会破坏合批**，可能自成一批。
- **性能优化目标**：最大化 chunk occupancy（每 chunk 实体数）+ 最小化 archetype 数量（减 batch 数）。给大量实体加各不相同的独特组件会把它移到新 archetype，严重掉性能。
- **LOD 范围**：设置过宽（如 0%–100%）让 GPU 无法有效剔除；**设准确的 LOD 屏幕空间百分比范围**有助精确剔除。
- **数据布局**：烘焙时图形组件与高频访问组件（`LocalToWorld`）分 chunk，降低缓存压力。
- **Mesh Deformations（蒙皮）**：Unity 6+ 通过 URP/HDRP Deformations 支持线性混合蒙皮（`MeshDeformation` 组件），是纯 ECS 中 `SkinnedMeshRenderer` 无直接对应物的补充方案。

### 4.7 限制速查

| 类别 | 限制 |
|------|------|
| 渲染管线 | 不支持 Built-in RP；URP 仅 Forward+ |
| 平台 | 不支持 WebGL；HDRP 不支持 Android/iOS |
| 多 World | 不支持 |
| Shader | 必须 DOTS Instancing 兼容；ShaderGraph Custom Function 节点不支持 |
| 纹理流送 | 不起作用（材质上传在剔除前） |
| SkinnedMeshRenderer | 须作 Companion（或 Unity 6+ Mesh Deformations） |
| Material Overrides | 每个唯一 per-instance 值破坏合批 |
| Camera | 默认禁用 Camera 转换（主相机不能是 companion） |
| 结构性变更时机 | PresentationGroup 后不可改 ECS data，延迟到下帧开头 |

---

## 5. 完整工作流串联（端到端）

一个最简「旋转的方块」从创作到渲染：

```
1. 创作：SubScene 里放 Cube(GameObject) + 挂 RotationSpeedAuthoring(MonoBehaviour)
2. 烘焙（编辑器，自动）：
   RotationSpeedBaker.Bake →
     GetEntity(TransformUsageFlags.Dynamic)  // 得 Entity + LocalTransform + LocalToWorld
     AddComponent(RotationSpeed)
   MeshFilter/MeshRenderer → 烘焙出 RenderMeshArray + MaterialMeshInfo + RenderBounds
3. 运行时加载：SceneSystem 流式载入 Entity Scene（Resolve → Load）
4. 逻辑：MovementSystem(ISystem, Burst) 用 SystemAPI.Query 改 LocalTransform
5. 渲染：Entities Graphics 收集 LocalToWorld+渲染组件 → 剔除/合批 → BRG → URP/HDRP(SRP Batcher) 绘制
```

---

## 6. 1.4 要点速查 & 避坑

- **默认用 `ISystem` + Burst + `SystemAPI.Query`**；需引用类型才用 `SystemBase`。详见 [[【教程】ECS架构入门]]、[[【教程】Burst编译器]]、[[【教程】JobSystem详解]]。
- **不要再引入 `IAspect`**（1.4 已废弃），新代码用裸组件查询。
- **transform 一律用 `Unity.Transforms.LocalTransform`/`LocalToWorld`**，通过 `TransformUsageFlags` 控制烘焙时加哪些（静态可渲染标 `Renderable` 省 transform 组件）。
- **Baker 必须无状态**，跨 entity 逻辑才用 baking system；改烘焙代码记得递增 `[BakingVersion]`。
- **运行时加载 scene 用 `SceneSystem.LoadSceneAsync`**（`LoadSubScene` 已弃用）；卸载用 `UnloadScene`（彻底）或 `UnloadSceneFragment`（保数据快重载）。
- **运行时创建可渲染实体**：`RenderMeshUtility.AddComponents` 建 prototype，再 `Instantiate` 批量克隆，**勿手动逐个加图形组件**。
- **Entities Graphics 只支持 SRP**（URP 仅 Forward+），不支持 Built-in RP / WebGL；Shader 需 DOTS Instancing 兼容。
- **性能三件事**：① 最大化 chunk occupancy、最小化 archetype 数；② Material Overrides 唯一值会破坏合批；③ 设准确 LOD 范围助 GPU 剔除。

---

## 与既有笔记的关系

- [[【教程】ECS架构入门]]：ECS 三要素/Archetype/Chunk/ECB/SystemGroup 基础（本文不重复，仅修正 1.4 现代 API）。
- [[【教程】JobSystem详解]] / [[【教程】Burst编译器]]：`ISystem` 调度的 `IJobEntity` 与 Burst 编译细节。
- [[【设计原理】ECS为什么快]]：数据导向设计的性能原理（chunk 连续布局、cache 命中），是本文「为何优先 unmanaged/为何托管组件慢」的底层解释。
- [[【教程】DOTS学习路径]]：DOTS 学习顺序，本文是其 1.4 量产栈深化。

## 相关链接

- [Entities 1.4 手册](https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/index.html)
- [Entities Graphics 1.4 手册](https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.4/manual/index.html)
- [ECS Samples（GitHub）](https://github.com/Unity-Technologies/EntityComponentSystemSamples)
- [[【教程】ECS架构入门]] · [[【教程】JobSystem详解]] · [[【教程】Burst编译器]] · [[【教程】DOTS学习路径]] · [[DOTS专题索引]]
