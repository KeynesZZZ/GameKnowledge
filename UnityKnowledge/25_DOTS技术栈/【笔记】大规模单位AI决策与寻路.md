---
title: 【笔记】大规模单位 AI 决策与寻路
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "寻路", "AI", "Flow Field", "JobSystem", "性能优化", "笔记"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-06-30"
description: 10w 单位的 AI 决策与寻路——为什么 NavMesh 撑不住、Flow Field 流场寻路（同目标 O(1) 查询）、DOTS Job 化、空间分区、局部避障与分帧决策。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【笔记】同屏大规模单位渲染方案]]"
  - "[[【笔记】大规模单位动画方案]]"
  - "[[【教程】JobSystem详解]]"
  - "[[【教程】ECS架构入门]]"
related: ["[[【笔记】同屏大规模单位渲染方案]]", "[[【笔记】大规模单位动画方案]]", "[[【片段】UniformGrid空间分区Job实现]]", "[[【片段】FlowField流场Job实现]]", "[[【片段】RVO2局部避障ECS移植]]", "[[【笔记】大规模单位战斗结算]]", "[[【实战案例】10w单位渲染与动画最小Demo]]", "[[【教程】JobSystem详解]]", "[[【教程】Burst编译器]]", "[[DOTS专题索引]]"]
---

# 【笔记】大规模单位 AI 决策与寻路

> 承 [[【笔记】同屏大规模单位渲染方案]]。10w 单位「会动」之后，下一个硬问题是「往哪动、打谁」。本文讲为什么传统 NavMesh 撑不住，以及大规模寻路/决策的 DOTS 方案。

## 一、为什么 NavMesh / A* 撑不住 10w

| 方案 | 问题 |
|------|------|
| `NavMeshAgent`（GameObject） | 每单位一个 agent，主线程开销；10w 个直接卡死 |
| 每单位独立 A*（哪怕 Job 化） | 10w 条独立路径，O(N × 路径长)，再快也扛不住 |
| `com.unity.ai.navigation` | 是 GameObject 体系，非 DOTS 原生 |

> ⚠️ Unity 在 1.4 期**没有稳定的 DOTS 原生 NavMesh 包**。10w 同目标场景的工业标准答案是 **Flow Field（流场寻路）**：把「从任意格到目标的最佳方向」**预计算**成一张方向场，每个单位 O(1) 采样自己格子的方向。

## 二、Flow Field 流场寻路（核心）

### 原理：把寻路从「每单位算路径」变成「目标算一次场，单位查表」

```
网格化地图 → 3 张场：
1. Cost Field   每格通行代价（障碍=∞，空地=1，泥地=2…）
2. Integration Field  从目标格做 Dijkstra 扩散，每格存「到目标的累计代价」
3. Vector Field  对 Integration Field 取梯度（向代价下降最快的方向），每格存最佳移动方向

运行时：单位查自己所在格的 Vector Field → 得方向 → O(1)
```

**关键优势**：10w 个单位**朝同一目标**时，Integration/Vector Field 只算**一次**（O(格子数)），之后所有单位 O(1) 查询。目标变了才重算。这是 RTS 大军、塔防、群妖的标准做法。

### DOTS 实现要点

- 地图数据用 `NativeArray`：`CostField`(int/byte)、`IntegrationField`(float)、`VectorField`(float3)，按 `int3(cellX,cellY,0)` 或 1D index 索引。
- **Integration Field 计算**：纯 A* 的优先队列在 Burst/HPC# 里不好写，工程上常用 **分层 BFS / Dijkstra with buckets**（按 cost 分桶用 `NativeQueue`/多 NativeList 模拟）。障碍小图可直接 BFS（cost=1）。
- **VectorField 计算**：Burst Job 并行每格，取相邻 Integration 最小差方向。
- **单位移动**：`IJobEntity` 查 `VectorField[cellOf(unit)]` 得方向，写入 `Velocity`，交给移动系统。

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;

public struct FlowFieldData : IComponentData {
    public int Width, Height;
    public float CellSize;
    public float3 Origin;       // 网格世界原点
    // 实际场数组用 DynamicBuffer 或 Entity 上的 NativeArray（managed）托管；
    // 推荐把三张场放在 singleton 的 unmanaged 资源里，job 里 [ReadOnly] 读 VectorField
}

[BurstCompile]
public partial struct SteeringSystem : ISystem
{
    private NativeArray<float3> m_VectorField;   // 方向场（外部构建）

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // 读 VectorField 查方向，写 Velocity（移动由 UnitMovementSystem 执行）
        float cell = 1f; // cellSize，实际从 singleton 取
        new SteerJob { Field = m_VectorField, CellSize = cell }.ScheduleParallel();
    }

    [BurstCompile]
    partial struct SteerJob : IJobEntity
    {
        [ReadOnly] public NativeArray<float3> Field;
        public float CellSize;
        void Execute(ref Velocity vel, in LocalTransform t)
        {
            // 世界坐标 → 格子索引（简化，忽略边界）
            int gx = (int)(t.Position.x / CellSize);
            int gz = (int)(t.Position.z / CellSize);
            // Field[gx + gz*width] 即最佳方向（实际需校验边界、width 从 singleton 取）
            // vel.Value = lerp(vel.Value, dir * speed, 0.1f);
        }
    }
}
```

> ⚠️ 骨架仅示意查表逻辑；工程上 VectorField 用持久 `NativeArray`（在系统 `OnCreate` 分配，`OnDestroy` 释放），width/height/cellSize 从 singleton 读，注意边界与 NaN。

---

## 三、空间分区：10w 单位找「最近敌人」

逐对比较 O(N²) 必死（10w² = 一百亿次）。需空间索引加速邻域查询：

| 方案 | 适用 | 复杂度 |
|------|------|--------|
| **Uniform Grid**（`NativeMultiHashMap<int3, Entity>`） | 单位密度均匀，实现简单，Flow Field 同款网格复用 | 构建 O(N)，查询 O(邻居数) |
| **Unity.Physics broadphase** | 已用 Unity Physics 时，复用其碰撞树 | 引擎托管 |
| **NativeQuadTree / KD-Tree**（社区实现） | 单位分布稀疏不均 | 构建 O(N log N)，查询 O(log N + k) |

**工业首选 Uniform Grid**——实现简单、Burst 友好、可复用 Flow Field 网格。核心流程：

```
每帧：
  1. BuildGrid（并行）：所有敌方单位 → WorldToCell → HashMap.Add(cell, entity)
  2. QueryTarget（并行）：己方单位 → 查自己格 + 邻接 8 格 → 逐个比距离 → 取最近
```

> **完整 Burst Job 实现**（构建、查询、多阵营、分帧优化、性能分析 12500x 加速比）见 [[【片段】UniformGrid空间分区Job实现]]。

关键参数：`CellSize ≈ 查询半径`（近战 CellSize=4, QueryRadius=1 → 3×3 邻域覆盖 12m）。网格构建一次可多系统共享（Targeting / Avoidance / Combat / AOE），呼应 [[【笔记】大规模单位战斗结算]] 的碰撞检测路线 B。

```csharp
// 每帧（或分帧）：把所有 Enemy 位置写入 UniformGrid
// 用 NativeMultiHashMap<int3, Entity>，key=格子坐标
// 查询单位扫自己 3×3 邻域，取最近者写 Target 组件
```

---

## 四、局部避障（RVO / boids）

Flow Field 只给方向，单位会叠在一起/穿模。大规模避障常用：

- **RVO2/ORCA**：速度障碍法，社区有 Job 移植版；适合人形单位互不穿透。
- **Boids 简化**：分离力（离最近邻居太近就推开）+ 对齐 + 凝聚，`IJobEntity` 里算，轻量。
- **Flow Field + 轻量分离力**：实战最常见组合——主方向来自 Flow Field，叠加邻居分离力。

---

## 五、分帧决策：别每帧跑 10w 个 AI

决策（选目标、切状态）不必每帧跑全量：

- **轮询分桶**：按 `entity.Index % N` 把单位分 N 桶，每帧只决策一桶（60 桶 = 每单位 ~1 秒决策一次）。
- **事件驱动**：进入攻击范围才触发攻击决策（用 trigger/空间分区通知），而非每帧扫。
- **LOD AI**：远处单位用更便宜的决策（只跟 Flow Field 走），近处才精细决策。

---

## 六、整合到现有单位系统

| 系统 | 职责 | 频率 |
|------|------|------|
| `FlowFieldBuildSystem` | 目标变化时重建 VectorField | 按需（目标变/障碍变） |
| `TargetingSystem` | UniformGrid 查最近敌，写 `Target` | 分帧轮询 |
| `SteeringSystem` | 查 VectorField 写 `Velocity` | 每帧（Burst 并行） |
| `AvoidanceSystem` | RVO/boids 避障修正 `Velocity` | 每帧 |
| `DecisionSystem` | 选目标/切 `AnimState`/放技能 | 分帧轮询 |
| `UnitMovementSystem` | `Position += Vel*dt` | 每帧（见 [[【笔记】同屏大规模单位渲染方案]]） |
| `UnitAnimSystem` | 据 velocity/health/target 切动画 | 每帧（见 [[【笔记】大规模单位动画方案]]） |

---

## 七、避坑

- **别每单位独立 A***：10w 路径必死，用 Flow Field 同目标共享。
- **多目标**：单位朝不同目标时，按目标分组各建一个 Flow Field，或退化为少量 DOTS A*（只给精英/Boss）。
- **VectorField 内存**：大地图格子多，注意 `NativeArray` 生命周期（系统 OnCreate/OnDestroy 管理，禁用 managed 泄漏）。
- **优先队列在 Burst**：HPC# 无堆，用桶式 BFS 替代 Dijkstra 优先队列。
- **决策别每帧扫全场**：分帧 + 事件驱动，否则 CPU 被吃光。
- **Flow Field 重算节流**：目标频繁抖动会频繁重算，加最小重算间隔/距离阈值。

## 速查清单

- [ ] 同目标寻路用 Flow Field（预计算方向场，单位 O(1) 查表）
- [ ] VectorField 用持久 NativeArray，Burst Job 算 Integration（桶式 BFS）+ 梯度
- [ ] 邻域查询用 UniformGrid（NativeMultiHashMap<int3, Entity>）
- [ ] 避障用 RVO/boids，Flow Field + 分离力组合
- [ ] 决策分帧轮询（分桶/事件驱动），别每帧跑 10w
- [ ] AI LOD：远处便宜决策，近处精细决策
- [ ] VectorField 重算节流（最小间隔/距离阈值）

## 相关链接

- [[【笔记】同屏大规模单位渲染方案]] · [[【笔记】大规模单位动画方案]] · [[【片段】UniformGrid空间分区Job实现]] · [[【片段】FlowField流场Job实现]] · [[【片段】RVO2局部避障ECS移植]] · [[【笔记】大规模单位战斗结算]] · [[【实战案例】10w单位渲染与动画最小Demo]] · [[【教程】JobSystem详解]] · [[【教程】Burst编译器]] · [[【教程】ECS架构入门]]
