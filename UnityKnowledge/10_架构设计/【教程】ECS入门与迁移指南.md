---
title: 【教程】ECS 入门与迁移指南
tags: [C#, Unity, 架构, 教程, ECS, DOTS, Entities, 数据导向]
category: 架构设计/教程
created: 2024-01-05 09:00
updated: 2026-03-04 22:00
description: Unity DOTS 技术栈中 ECS 架构的入门指南，包含从 OOP 到 ECS 的迁移策略和最佳实践
unity_version: 2021.3+
dependencies: [Unity.Entities, Unity.Burst, Unity.Jobs]
---

# 【教程】ECS 入门与迁移指南

> 核心价值：从传统 OOP 思维平滑过渡到 ECS 数据导向设计

## 文档定位

本文档从**使用角度**讲解ECS 入门与迁移指南。

**相关文档**：[[【教程】ECS入门与迁移指南]]

---

## 概述

ECS (Entity-Component-System) 是一种数据导向的架构模式，Unity DOTS 的核心组件。

## 核心概念

### 传统 OOP vs ECS

```
OOP: 对象 = 数据 + 行为
ECS: 分离 = Entity(容器) + Component(数据) + System(行为)
```

### 三大要素

| 概念 | 说明 | 对应OOP |
|------|------|---------|
| Entity | 轻量ID | GameObject |
| Component | 纯数据 | 数据字段 |
| System | 纯逻辑 | 方法/行为 |

## 基础示例

### 定义Component

```csharp
using Unity.Entities;

// IComponentData - 结构体，无逻辑
public struct Movement : IComponentData
{
    public float Speed;
    public float3 Direction;
}

public struct Position : IComponentData
{
    public float3 Value;
}
```

### 创建Entity

```csharp
// 方式1: 使用EntityManager
var entity = EntityManager.CreateEntity();
EntityManager.AddComponent<Movement>(entity);
EntityManager.AddComponent<Position>(entity);

// 方式2: 使用EntityCommandBuffer
var ecb = new EntityCommandBuffer(Allocator.Temp);
var entity = ecb.CreateEntity();
ecb.AddComponent(new Movement { Speed = 5f });
ecb.Playback(EntityManager);
```

### 编写System

```csharp
[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))]
public partial class MovementSystem : SystemBase
{
    protected override void OnUpdate()
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        Entities
            .WithName("MovementJob")
            .ForEach((ref Position position, in Movement movement) =>
            {
                position.Value += movement.Direction * movement.Speed * deltaTime;
            })
            .ScheduleParallel();
    }
}
```

## 迁移策略

### 阶段1: 评估

- 识别性能瓶颈
- 确定适合ECS的系统（大量相似实体）
- 评估学习成本

### 阶段2: 并行运行

- 保持OOP系统运行
- 新功能使用ECS实现
- 逐步迁移核心系统

### 阶段3: 混合架构

```csharp
// GameObject → Entity 转换
public class UnitAuthoring : MonoBehaviour
{
    public float Speed;

    class Baker : Baker<UnitAuthoring>
    {
        public override void Bake(UnitAuthoring authoring)
        {
            var entity = GetEntity(TransformUsageFlags.Dynamic);
            AddComponent(entity, new Movement
            {
                Speed = authoring.Speed
            });
        }
    }
}
```

### 阶段4: 完全迁移

- 移除旧OOP代码
- 优化数据布局
- 利用Burst编译

## 性能优势

| 优势 | 原因 |
|------|------|
| 缓存友好 | 数据连续存储 |
| 并行处理 | SystemBase + ScheduleParallel |
| 零GC | 结构体 + NativeContainer |
| SIMD优化 | Burst Compiler |

## 常见陷阱

1. **在Component中写逻辑** - Component应只包含数据
2. **频繁的结构修改** - 避免运行时Add/RemoveComponent
3. **忽略Archetype** - 合理设计Chunk布局
4. **过度同步** - 减少主线程等待

## 学习路径

1. 学习 Entities 包基础API
2. 理解 Archetype 和 Chunk
3. 掌握 SystemBase 和 Job
4. 学习 Burst 编译器
5. 实践完整项目

## 相关链接

- [DOTS 学习路径](【教程】DOTS学习路径.md)
- [Job System 详解](【教程】Job System.md)
