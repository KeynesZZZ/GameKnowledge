---
title: 【教程】ECS架构入门
tags: [Unity, DOTS技术栈, ECS, 教程]
category: DOTS技术栈
created: 2026-03-05 09:21
updated: 2026-03-05 09:21
description: Unity ECS架构入门教程
unity_version: 2021.3+
---
# ECS 架构入门

> 第3课 | DOTS 技术栈模块

## 1. ECS 核心概念

### 1.1 什么是 ECS？

**Entity-Component-System** 是一种数据导向的架构模式：

```
传统 OOP:
GameObject → 包含所有数据的对象

ECS:
Entity   → 只是 ID（轻量）
Component → 纯数据（无逻辑）
System    → 纯逻辑（处理数据）
```

### 1.2 核心优势

| 特性 | OOP | ECS |
|------|-----|-----|
| 内存布局 | 分散 | 连续（Cache友好） |
| 数据耦合 | 高 | 低 |
| 并行性 | 差 | 优秀 |
| 扩展性 | 继承 | 组合 |

---

## 2. Entity（实体）

### 2.1 创建实体

```csharp
using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;

public class EntityCreator : MonoBehaviour
{
    private EntityManager entityManager;

    private void Start()
    {
        entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;

        // 方式1：使用 EntityArchetype
        EntityArchetype archetype = entityManager.CreateArchetype(
            typeof(Position),
            typeof(Velocity),
            typeof(RenderMesh)
        );
        Entity entity1 = entityManager.CreateEntity(archetype);

        // 方式2：创建空实体后添加组件
        Entity entity2 = entityManager.CreateEntity();
        entityManager.AddComponentData(entity2, new Position { Value = float3.zero });
        entityManager.AddComponentData(entity2, new Velocity { Value = new float3(1, 0, 0) });

        // 方式3：批量创建
        NativeArray<Entity> entities = new NativeArray<Entity>(100, Allocator.Temp);
        entityManager.CreateEntity(archetype, entities);
        entities.Dispose();
    }
}
```

### 2.2 销毁实体

```csharp
// 销毁单个实体
entityManager.DestroyEntity(entity);

// 销毁所有匹配的实体
EntityQuery query = entityManager.CreateEntityQuery(typeof(EnemyTag));
entityManager.DestroyEntity(query);
```

---

## 3. Component（组件）

### 3.1 IComponentData

```csharp
using Unity.Entities;
using Unity.Mathematics;

// 数据组件 - 必须是 struct
public struct Position : IComponentData
{
    public float3 Value;
}

public struct Velocity : IComponentData
{
    public float3 Value;
}

public struct Health : IComponentData
{
    public int Current;
    public int Max;
}

// 标签组件 - 无数据，用于标记
public struct EnemyTag : IComponentData { }
public struct PlayerTag : IComponentData { }
```

### 3.2 IBufferElementData（动态缓冲）

```csharp
// 动态数组组件
public struct PathPoint : IBufferElementData
{
    public float3 Position;
}

// 使用
public class BufferExample : MonoBehaviour
{
    private void Start()
    {
        var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;
        Entity entity = entityManager.CreateEntity();

        // 添加动态缓冲
        entityManager.AddBuffer<PathPoint>(entity);

        // 获取并操作
        DynamicBuffer<PathPoint> buffer = entityManager.GetBuffer<PathPoint>(entity);
        buffer.Add(new PathPoint { Position = new float3(0, 0, 0) });
        buffer.Add(new PathPoint { Position = new float3(1, 0, 0) });

        // 访问
        for (int i = 0; i < buffer.Length; i++)
        {
            Debug.Log(buffer[i].Position);
        }
    }
}
```

### 3.3 ISharedComponentData（共享组件）

```csharp
// 共享组件 - 相同值的实体存储在一起
public struct RenderSettings : ISharedComponentData
{
    public Mesh Mesh;
    public Material Material;
}

// 使用
public class SharedExample : MonoBehaviour
{
    private void Start()
    {
        var entityManager = World.DefaultGameObjectInjectionWorld.EntityManager;

        // 相同 Material 的实体会被分组
        Entity entity1 = entityManager.CreateEntity(typeof(RenderSettings));
        Entity entity2 = entityManager.CreateEntity(typeof(RenderSettings));

        Material mat = Resources.Load<Material>("Material");

        entityManager.SetSharedComponentData(entity1, new RenderSettings { Material = mat });
        entityManager.SetSharedComponentData(entity2, new RenderSettings { Material = mat });

        // entity1 和 entity2 会在同一个 Archetype Chunk 中
    }
}
```

---

## 4. System（系统）

### 4.1 SystemBase

```csharp
using Unity.Entities;
using Unity.Jobs;
using Unity.Burst;
using Unity.Mathematics;
using Unity.Transforms;

// 基础系统
[BurstCompile]
public partial struct MovementSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        // 遍历所有拥有 Position 和 Velocity 的实体
        foreach (var (position, velocity) in
                 SystemAPI.Query<RefRW<Position>, RefRO<Velocity>>())
        {
            position.ValueRW.Value += velocity.ValueRO.Value * deltaTime;
        }
    }
}
```

### 4.2 使用 Job 的系统

```csharp
[BurstCompile]
public partial struct MovementJobSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        MovementJob job = new MovementJob
        {
            deltaTime = SystemAPI.Time.DeltaTime
        };

        state.Dependency = job.ScheduleParallel(state.Dependency);
    }
}

[BurstCompile]
public partial struct MovementJob : IJobEntity
{
    public float deltaTime;

    void Execute(ref Position position, in Velocity velocity)
    {
        position.Value += velocity.Value * deltaTime;
    }
}
```

### 4.3 EntityQuery

```csharp
public partial struct QuerySystem : ISystem
{
    private EntityQuery query;

    public void OnCreate(ref SystemState state)
    {
        // 创建查询
        query = state.GetEntityQuery(
            ComponentType.ReadWrite<Position>(),
            ComponentType.ReadOnly<Velocity>(),
            ComponentType.Exclude<DisabledTag>()
        );
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // 使用查询
        NativeArray<Position> positions = query.ToComponentDataArray<Position>(Allocator.TempJob);

        // 处理...

        positions.Dispose();
    }
}
```

---

## 5. Archetype 与 Chunk

### 5.1 内存布局原理

```
Archetype: 决定实体拥有的组件组合

例如：Archetype A = {Position, Velocity, Health}

┌─────────────────────────────────────────────┐
│                 Chunk 0                      │
├─────────────────────────────────────────────┤
│ Position[0-127] │ Velocity[0-127] │ Health[0-127] │
├─────────────────────────────────────────────┤
│ Entity[0-127]   (实体 ID)                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                 Chunk 1                      │
├─────────────────────────────────────────────┤
│ Position[0-45]  │ Velocity[0-45]  │ Health[0-45]  │
├─────────────────────────────────────────────┤
│ Entity[0-45]    (实体 ID)                    │
└─────────────────────────────────────────────┘
```

### 5.2 ArchetypeChunk

```csharp
[BurstCompile]
public partial struct ChunkIterationSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // 获取所有匹配的 Chunk
        var query = state.GetEntityQuery(
            ComponentType.ReadWrite<Position>(),
            ComponentType.ReadOnly<Velocity>()
        );

        NativeArray<ArchetypeChunk> chunks = query.ToArchetypeChunkArray(Allocator.TempJob);

        var positionType = state.GetComponentTypeHandle<Position>(false);
        var velocityType = state.GetComponentTypeHandle<Velocity>(true);

        foreach (var chunk in chunks)
        {
            NativeArray<Position> positions = chunk.GetNativeArray(positionType);
            NativeArray<Velocity> velocities = chunk.GetNativeArray(velocityType);

            for (int i = 0; i < chunk.Count; i++)
            {
                positions[i] = new Position
                {
                    Value = positions[i].Value + velocities[i].Value
                };
            }
        }

        chunks.Dispose();
    }
}
```

---

## 6. 命令缓冲区

### 6.1 EntityCommandBuffer

```csharp
public partial struct SpawnSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        var ecb = new EntityCommandBuffer(Allocator.TempJob);

        foreach (var (spawner, entity) in
                 SystemAPI.Query<RefRO<Spawner>>().WithEntityAccess())
        {
            // 在主线程外延迟执行创建
            Entity spawned = ecb.Instantiate(spawner.ValueRO.Prefab);
            ecb.SetComponent(spawned, new Position { Value = spawner.ValueRO.SpawnPosition });

            // 销毁生成器
            ecb.DestroyEntity(entity);
        }

        ecb.Playback(state.EntityManager);
        ecb.Dispose();
    }
}
```

### 6.2 EntityCommandBufferSystem

```csharp
// 在特定点执行命令
public partial struct DeferredSpawnSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // 获取 EndSimulationEntityCommandBufferSystem
        var ecbSystem = state.World.GetOrCreateSystemManaged<EndSimulationEntityCommandBufferSystem>();
        EntityCommandBuffer ecb = ecbSystem.CreateCommandBuffer();

        foreach (var (spawner, entity) in
                 SystemAPI.Query<RefRO<Spawner>>().WithEntityAccess())
        {
            Entity spawned = ecb.Instantiate(spawner.ValueRO.Prefab);
            // 命令会在帧末执行
        }

        // 不需要手动 Playback
    }
}
```

---

## 7. 完整示例：移动系统

### 7.1 定义组件

```csharp
// Position.cs
using Unity.Entities;
using Unity.Mathematics;

public struct Position : IComponentData
{
    public float3 Value;
}

// Velocity.cs
public struct Velocity : IComponentData
{
    public float3 Value;
}

// Speed.cs
public struct Speed : IComponentData
{
    public float Value;
}

// MovementTag.cs
public struct MovementTag : IComponentData { }
```

### 7.2 创建系统

```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;

[BurstCompile]
public partial struct MovementSystem : ISystem
{
    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        state.RequireForUpdate<MovementTag>();
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        foreach (var (position, velocity, speed) in
                 SystemAPI.Query<RefRW<Position>, RefRO<Velocity>, RefRO<Speed>>())
        {
            position.ValueRW.Value += velocity.ValueRO.Value * speed.ValueRO.Value * deltaTime;
        }
    }
}

[BurstCompile]
public partial struct BounceSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float3 bounds = new float3(10, 10, 10);

        foreach (var (position, velocity) in
                 SystemAPI.Query<RefRW<Position>, RefRW<Velocity>>())
        {
            float3 pos = position.ValueRO.Value;
            float3 vel = velocity.ValueRO.Value;

            // 边界反弹
            if (pos.x < 0 || pos.x > bounds.x)
            {
                vel.x = -vel.x;
                velocity.ValueRW.Value = vel;
            }
            if (pos.y < 0 || pos.y > bounds.y)
            {
                vel.y = -vel.y;
                velocity.ValueRW.Value = vel;
            }
            if (pos.z < 0 || pos.z > bounds.z)
            {
                vel.z = -vel.z;
                velocity.ValueRW.Value = vel;
            }
        }
    }
}
```

### 7.3 Authoring（MonoBehaviour 转 ECS）

```csharp
using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;

public class MovementAuthoring : MonoBehaviour
{
    public float3 initialVelocity;
    public float speed = 1f;

    class Baker : Baker<MovementAuthoring>
    {
        public override void Bake(MovementAuthoring authoring)
        {
            Entity entity = GetEntity(TransformUsageFlags.Dynamic);

            AddComponent(entity, new Position
            {
                Value = authoring.transform.position
            });

            AddComponent(entity, new Velocity
            {
                Value = authoring.initialVelocity
            });

            AddComponent(entity, new Speed
            {
                Value = authoring.speed
            });

            AddComponent<MovementTag>(entity);
        }
    }
}
```

---

## 8. SystemGroup 与更新顺序

### 8.1 系统组结构

```csharp
// Unity 默认系统组
InitializationSystemGroup    // 初始化
    ├── BeginInitializationSystemGroup
    ├── CopyInitialTransformFromGameObjectSystem
    └── EndInitializationSystemGroup

SimulationSystemGroup        // 逻辑更新
    ├── BeginSimulationSystemGroup
    ├── TransformSystemGroup
    │   ├── EndFrameParentSystem
    │   ├── EndFrameTRSToLocalToWorldSystem
    │   └── EndFrameLocalToParentSystem
    └── EndSimulationSystemGroup

PresentationSystemGroup      // 渲染
    ├── BeginPresentationSystemGroup
    └── EndPresentationSystemGroup
```

### 8.2 自定义系统组

```csharp
[UpdateInGroup(typeof(SimulationSystemGroup))]
[UpdateBefore(typeof(TransformSystemGroup))]
public partial struct MyCustomSystemGroup : ComponentSystemGroup { }

[UpdateInGroup(typeof(MyCustomSystemGroup))]
[UpdateOrder(0)]
public partial struct FirstSystem : ISystem { }

[UpdateInGroup(typeof(MyCustomSystemGroup))]
[UpdateOrder(1)]
public partial struct SecondSystem : ISystem { }
```

---

## 本课小结

### ECS 三要素

| 要素 | 作用 | 特点 |
|------|------|------|
| Entity | 标识符 | 轻量 ID |
| Component | 数据 | 纯数据 struct |
| System | 逻辑 | 处理数据 |

### 组件类型

| 类型 | 用途 | 特点 |
|------|------|------|
| IComponentData | 常规数据 | 每个 Entity 独立 |
| IBufferElementData | 动态数组 | 可变长度数据 |
| ISharedComponentData | 共享数据 | 相同值共享内存 |

### 性能对比

| 场景 | GameObject | ECS |
|------|------------|-----|
| 10000 实体更新 | ~10ms | ~0.5ms |
| 内存占用 | 高（分散） | 低（连续） |
| Cache 命中率 | 低 | 高 |

---

## 延伸阅读

- [ECS 官方文档](https://docs.unity3d.com/Packages/com.unity.entities@latest)
- [ECS FAQ](https://docs.unity3d.com/Packages/com.unity.entities@latest/manual/ecs_faq.html)
- [DOTS 示例项目](https://github.com/Unity-Technologies/EntityComponentSystemSamples)
