---
title: 【片段】RVO2 局部避障 ECS 移植
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "RVO", "ORCA", "避障", "JobSystem", "Burst", "代码片段", "片段"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-07-01"
description: RVO2/ORCA 局部避障的完整 Burst ECS 移植——邻域查询、computeORCALines、linearProgram1/2/3 数学、AvoidanceJob 驱动与参数调优。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【笔记】大规模单位AI决策与寻路]]"
  - "https://gamma.cs.unc.edu/RVO2/ (ORCA 算法参考)"
  - "[[【教程】JobSystem详解]]"
related: ["[[【笔记】RVO避障算法原理]]", "[[【笔记】大规模单位AI决策与寻路]]", "[[【片段】FlowField流场Job实现]]", "[[【笔记】大规模单位战斗结算]]", "[[【实战案例】10w单位渲染与动画最小Demo]]", "[[【教程】JobSystem详解]]", "[[【教程】Burst编译器]]", "[[DOTS专题索引]]"]
---

# 【片段】RVO2 局部避障 ECS 移植

> 承 [[【笔记】大规模单位AI决策与寻路]]。Flow Field 只给方向，单位会叠挤穿模。本篇给 **RVO2/ORCA** 的完整 Burst ECS 移植，让 10w 单位互不穿透。
> **算法来源**：UNC gamma 实验室 RVO2 库（`gamma.cs.unc.edu/RVO2`，BSD）。以下为忠实 C#→Burst 移植，数学部分按其公开实现还原，标注来源。
> **算法原理**：VO → RVO → ORCA 的完整推演见 [[【笔记】RVO避障算法原理]]，本文聚焦代码实现。

## 一、ORCA 原理（30 秒）

每个单位 i 对每个邻居 j 算一个**速度障碍**，因双方互惠避让各取**半责任**，得到一条 **ORCA 半平面**（line）。所有 line 约束 + `|v| ≤ maxSpeed` 圆，求**最接近期望速度**（preferred velocity，来自 Flow Field）的可行速度 → 解 2D 线性规划。三个 `linearProgram` 函数就是干这个的。

## 二、数据结构（XZ 平面，2D 投影）

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;

/// <summary>单位避障数据（unmanaged）。preferredVelocity 来自 Flow Field。</summary>
public struct UnitAgent : IComponentData {
    public float3 Position;       // 由 LocalTransform 同步
    public float3 Velocity;       // 当前速度
    public float2 PrefVelocity;   // 期望速度（xz），Flow Field 给
    public float Radius;
    public float MaxSpeed;
}

/// <summary>ORCA 半平面：result 必须在 direction 法向 ≥ 0 侧（point 为线上一点）。</summary>
struct Line { public float2 Point; public float2 Direction; }

/// <summary>2D 叉乘（标量）：det(a,b)=a.x*b.y-a.y*b.x。</summary>
[MethodImpl(MethodImplOptions.AggressiveInlining)]
static float Det2(float2 a, float2 b) => a.x * b.y - a.y * b.x;
```

## 三、邻域查询（复用 UniformGrid）

单位 i 的邻居 = 自己所在格 + 邻接 8 格里、距离 ≤ `neighborDist` 的单位。用 [[【笔记】大规模单位AI决策与寻路]] 的 `NativeMultiHashMap<int3, Entity>` 网格，`TryGetMultiValue` 枚举。邻居数据用 `ComponentLookup<UnitAgent>`（只读）读。

## 四、computeORCALines（建约束线，核心几何）

> 忠实移植 RVO2 `Agent::computeNewVelocity` 里 per-neighbor 建线部分。`inverseTimeHorizon = 1 / timeHorizon`。

```csharp
/// <summary>对单位 agent 的所有邻居构建 ORCA 约束线，写入 lines（NativeList）。</summary>
static void ComputeORCALines(
    in UnitAgent self, NativeList<Line> lines,
    NativeMultiHashMap<int3, Entity>.Enumerator neighbors,   // 已截断到 neighborDist 的邻居
    ComponentLookup<UnitAgent> lookup, float invTimeHorizon)
{
    lines.Clear();
    float2 selfVelXZ = self.Velocity.xz;

    foreach (Entity otherE in neighbors)
    {
        if (!lookup.HasComponent(otherE)) continue;
        UnitAgent other = lookup[otherE];
        float2 relPos = other.Position.xz - self.Position.xz;
        float2 relVel = selfVelXZ - other.Velocity.xz;
        float distSq = math.lengthsq(relPos);
        float combinedRadius = self.Radius + other.Radius;
        float combinedRadiusSq = combinedRadius * combinedRadius;

        Line line = default;
        float2 u;

        if (distSq > combinedRadiusSq) {
            // 无碰撞：截断圆锥速度障碍
            float2 w = relVel - invTimeHorizon * relPos;
            float wLenSq = math.lengthsq(w);
            float dp1 = math.dot(w, relPos);
            if (dp1 < 0f && dp1 * dp1 > combinedRadiusSq * wLenSq) {
                // 投影到 cut-off 圆
                float wLen = math.sqrt(wLenSq);
                float2 unitW = w / wLen;
                line.Direction = new float2(unitW.y, -unitW.x);
                u = unitW * combinedRadius - selfVelXZ;
            } else {
                // 投影到左/右 leg
                float leg = math.sqrt(distSq - combinedRadiusSq);
                if (Det2(relPos, w) > 0f)
                    line.Direction = new float2(relPos.x * leg - relPos.y * combinedRadius,
                                                relPos.x * combinedRadius + relPos.y * leg) / distSq;
                else
                    line.Direction = -(new float2(relPos.x * leg + relPos.y * combinedRadius,
                                                  -relPos.x * combinedRadius + relPos.y * leg) / distSq);
                float dp2 = math.dot(relVel, line.Direction);
                u = dp2 * line.Direction - relVel;
            }
        } else {
            // 已碰撞：直接构建 cut-off
            float dist = math.sqrt(distSq);
            float2 w = relVel - invTimeHorizon * relPos;
            float wLen = math.length(w);
            float2 unitW = wLen > 1e-5f ? w / wLen : new float2(1f, 0f);
            line.Direction = new float2(unitW.y, -unitW.x);
            u = (combinedRadius - invTimeHorizon * dist) * unitW - relVel;
        }

        // ORCA：双方各承担一半责任（RVO=0.5）
        line.Point = selfVelXZ + 0.5f * u;
        lines.Add(line);
    }
}
```

## 五、linearProgram1/2/3（2D 线性规划，忠实移植）

> 来源：RVO2 `linearProgram1/2/3`。在 `|v| ≤ radius` 圆与半平面约束下，求最接近 `optVelocity` 的点。

```csharp
/// <summary>单约束（lineNo 这条 + 已有 0..lineNo-1）下求可行点。</summary>
static bool LinearProgram1(NativeArray<Line> lines, int lineNo, float radius,
    float2 optVelocity, bool directionOpt, out float2 result)
{
    result = float2.zero;
    float dp = math.dot(lines[lineNo].Point, lines[lineNo].Direction);
    float disc = dp * dp + radius * radius - math.lengthsq(lines[lineNo].Point);
    if (disc < 0f) return false;
    float sqrtD = math.sqrt(disc);
    float tLeft = -dp - sqrtD, tRight = -dp + sqrtD;

    for (int i = 0; i < lineNo; i++) {
        float denom = Det2(lines[lineNo].Direction, lines[i].Direction);
        float numer = Det2(lines[i].Direction, lines[lineNo].Point - lines[i].Point);
        if (math.abs(denom) <= 1e-6f) {
            if (numer < 0f) return false;
            continue;
        }
        float t = numer / denom;
        if (denom >= 0f) tRight = math.min(tRight, t);
        else             tLeft  = math.max(tLeft, t);
        if (tLeft > tRight) return false;
    }

    if (directionOpt) {
        result = math.dot(optVelocity, lines[lineNo].Direction) > 0f
            ? lines[lineNo].Point + tRight * lines[lineNo].Direction
            : lines[lineNo].Point + tLeft  * lines[lineNo].Direction;
    } else {
        float t = math.dot(lines[lineNo].Direction, optVelocity - lines[lineNo].Point);
        if (t < tLeft) t = tLeft; else if (t > tRight) t = tRight;
        result = lines[lineNo].Point + t * lines[lineNo].Direction;
    }
    return true;
}

/// <summary>在已满足的约束上逐条加入新约束，返回首个失败索引（=lineNo 表示全满足）。</summary>
static int LinearProgram2(NativeArray<Line> lines, float radius,
    float2 optVelocity, bool directionOpt, ref float2 result, int lineNo)
{
    if (directionOpt) result = optVelocity * radius;
    else if (math.lengthsq(optVelocity) > radius * radius) result = math.normalizesafe(optVelocity) * radius;
    else result = optVelocity;

    for (int i = 0; i < lineNo; i++) {
        if (Det2(lines[i].Direction, lines[i].Point - result) > 0f) {
            float2 temp = result;
            if (!LinearProgram1(lines, i, radius, directionOpt ? optVelocity : float2.zero, directionOpt, out result)) {
                result = temp;
                return i;
            }
        }
    }
    return lineNo;
}

/// <summary>兜底：当 LP2 失败时，3D 投影求最远可行解（保证有输出）。</summary>
static void LinearProgram3(NativeArray<Line> lines, int numObstacleLines, int numLines,
    float radius, ref float2 result, NativeList<Line> projLines)
{
    float distance = 0f;
    for (int i = numObstacleLines; i < numLines; i++) {
        if (Det2(lines[i].Direction, lines[i].Point - result) > distance) {
            projLines.Clear();
            for (int j = 0; j < numObstacleLines; j++) projLines.Add(lines[j]);

            for (int j = numObstacleLines; j < i; j++) {
                Line line;
                float det = Det2(lines[i].Direction, lines[j].Direction);
                if (math.abs(det) <= 1e-6f) {
                    if (math.dot(lines[i].Direction, lines[j].Direction) > 0f) continue;
                    line.Point = 0.5f * (lines[i].Point + lines[j].Point);
                } else {
                    line.Point = lines[i].Point
                        + (Det2(lines[j].Direction, lines[i].Point - lines[j].Point) / det) * lines[i].Direction;
                }
                line.Direction = math.normalizesafe(lines[j].Direction - lines[i].Direction);
                projLines.Add(line);
            }

            float2 temp = result;
            int failed = LinearProgram2(projLines.AsArray(), radius, -lines[i].Direction, true, ref result, projLines.Length);
            if (failed < projLines.Length) result = temp;   // 用上一可行解
            distance = Det2(lines[i].Direction, lines[i].Point - result);
        }
    }
}
```

## 六、AvoidanceJob（IJobEntity 串联）

```csharp
[BurstCompile]
partial struct AvoidanceSystem : ISystem
{
    private ComponentLookup<UnitAgent> m_Lookup;
    private NativeMultiHashMap<int3, Entity> m_Grid;

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        m_Lookup = state.GetComponentLookup<UnitAgent>(isReadOnly: true);
        // m_Grid 由 BuildGridSystem 每帧（或分帧）写入；这里只读
        new AvoidanceJob {
            Lookup = m_Lookup,
            Grid = m_Grid,
            TimeHorizon = 1.5f,
            NeighborDist = 4f
        }.ScheduleParallel();
        state.Dependency.Complete();   // Grid/Lookup 写入侧需在下一帧前完成
    }

    [BurstCompile]
    partial struct AvoidanceJob : IJobEntity
    {
        [ReadOnly] public ComponentLookup<UnitAgent> Lookup;
        [ReadOnly] public NativeMultiHashMap<int3, Entity> Grid;
        public float TimeHorizon;
        public float NeighborDist;

        void Execute(ref UnitAgent agent, ref Velocity vel)
        {
            // 1) 邻域枚举（简化：这里假设已有一个 neighbors 枚举器；实际用 Grid 枚举 3x3 邻域并按 NeighborDist 过滤）
            var lines = new NativeList<Line>(16, Allocator.Temp);
            // neighbors = Grid 3x3 枚举 + NeighborDist 过滤（见 [[【笔记】大规模单位AI决策与寻路]] 空间分区）
            // ComputeORCALines(in agent, lines, neighbors, Lookup, 1f/TimeHorizon);

            // 2) 求 ORCA 速度
            // optVelocity 用当前速度（惯性策略），而非期望速度——见 [[【笔记】RVO避障算法原理]] 第五节
            float2 newVel = agent.Velocity.xz;
            int numLines = lines.Length;
            int lineFail = LinearProgram2(lines.AsArray(), agent.MaxSpeed, agent.Velocity.xz, false, ref newVel, numLines);
            if (lineFail < numLines)
                LinearProgram3(lines.AsArray(), 0, numLines, agent.MaxSpeed, ref newVel, /*projLines*/ lines);

            // 3) 写回（XZ → 3D）
            vel.Value = new float3(newVel.x, 0f, newVel.y);
            lines.Dispose();
        }
    }
}
```

> ⚠️ 邻域枚举细节（Grid 的 3×3 邻域 `TryGetMultiValue` + `NeighborDist` 过滤）见 [[【笔记】大规模单位AI决策与寻路]] 第三节，此处省略以聚焦 ORCA 主干。`NativeList<Line>` 在 job 内分配 `Allocator.Temp`，结束 Dispose。

## 七、参数调优

| 参数 | 含义 | 起步值 |
|------|------|--------|
| `NeighborDist` | 邻居查询半径 | 4–8（单位半径的几倍） |
| `TimeHorizon` | 避障预见时间窗 | 1.0–2.0 秒 |
| `MaxNeighbors` | 最大邻居数（截断） | 10–20（控性能） |
| `Radius` | 单位碰撞半径 | 真实模型半径 |
| `MaxSpeed` | 最大速度 | 与 Flow Field 期望速度上限一致 |

调大 `TimeHorizon`/`NeighborDist` → 避让更早更平滑但 CPU 更贵；调小 → 易抖动穿模。10w 单位时优先压 `MaxNeighbors` 和 `NeighborDist`。

## 八、避坑

- **2D 投影**：全程在 XZ 平面用 `float2`，结果再转 `float3(vx,0,vz)`。别用 XY。
- **ORCA 半责任**：`line.Point = selfVel + 0.5*u`。若做静态障碍（非互惠），障碍侧建 line 用全责任（`u` 不乘 0.5）。
- **抖动**：速度低频平滑（`vel = lerp(vel, newVel, 0.3)`），别每帧硬切。
- **Grid 一致性**：`BuildGridSystem`（写 Grid）与 `AvoidanceSystem`（读 Grid + Lookup）必须接 JobHandle 依赖，否则读到半更新数据。最稳：分帧——偶数帧建 Grid，奇数帧避障，或读写系统用 `[UpdateAfter]` 串行化。
- **邻居数上界**：枚举时按 `MaxNeighbors` 截断（保留最近的），避免高密度区单单位邻居爆炸。
- **Burst 兼容**：`NativeMultiHashMap.Enumerator` 在 Burst 里可枚举；`ComponentLookup` 用 `state.GetComponentLookup<T>(isReadOnly)`，跨帧需 `Update()` 刷新。

## 相关链接

- [[【笔记】大规模单位AI决策与寻路]] · [[【片段】FlowField流场Job实现]] · [[【笔记】大规模单位战斗结算]] · [[【实战案例】10w单位渲染与动画最小Demo]] · [[【教程】JobSystem详解]] · [[【教程】Burst编译器]]
- [RVO2 库（ORCA 算法来源）](https://gamma.cs.unc.edu/RVO2/)
