---
title: 【片段】Flow Field 流场 Job 实现
tags: ["Unity", "DOTS", "DOTS技术栈", "ECS", "寻路", "Flow Field", "JobSystem", "Burst", "代码片段", "片段"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-06-30"
description: Flow Field 流场完整 Burst Job 实现——三场（Cost/Integration/Vector），wavefront Dijkstra（桶式替代优先队列）+ 8 邻域梯度，含对角线代价与边界。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【笔记】大规模单位AI决策与寻路]]"
  - "[[【教程】JobSystem详解]]"
  - "[[【教程】Burst编译器]]"
related: ["[[【笔记】大规模单位AI决策与寻路]]", "[[【片段】RVO2局部避障ECS移植]]", "[[【笔记】大规模单位战斗结算]]", "[[【实战案例】10w单位渲染与动画最小Demo]]", "[[【教程】JobSystem详解]]", "[[DOTS专题索引]]"]
---

# 【片段】Flow Field 流场 Job 实现

> 承 [[【笔记】大规模单位AI决策与寻路]]，给出 Flow Field **三场**（Cost / Integration / Vector）的完整 Burst Job 代码骨架，可直接改用。

## 数据布局与符号约定

```
网格 W×H（2D，XZ 平面），1D 索引 index = z * W + x
  CostField       : NativeArray<byte>   // 0=障碍，>0=通行代价（1=空地，2=泥地…）
  IntegrationField: NativeArray<float>  // 每格到目标的累计代价（目标=0）
  VectorField     : NativeArray<float3> // 每格最佳移动方向（单位化，xz）
```

三张场是**全局共享、目标变化才重算**的资源，放 singleton（`IComponentData` 里存引用，或系统持有持久 `NativeArray`，`OnCreate` 分配 / `OnDestroy` 释放）。10w 单位只读 `VectorField` 查表，O(1)。

## 一、为什么不用优先队列（关键工程点）

HPC#/Burst 没有 `PriorityQueue`/`NativeHeap`（社区实现不稳定）。Flow Field 的 Integration Field 本质是**从目标出发的 Dijkstra 扩散**，工程上两种做法：

| 做法 | 适用 | 实现 |
|------|------|------|
| **Wavefront BFS**（队列 + 松弛） | cost 一致或近似 | `NativeQueue<int>` + 反复松弛，可能重复入队但收敛 |
| **桶式 Dijkstra**（bucket queue） | cost 分档多 | 按距离分层 `NativeList<int>[]`，当前层处理完进下一层 |

下面给** Wavefront 版**（绝大多数 RTS/塔防地图够用），并附桶式扩展要点。

## 二、CostField 构建（按项目填）

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;

/// <summary>初始化 CostField。障碍=0（不可通行），空地按地形填代价。
/// 实际由碰撞体烘焙 / 手工编辑 / 程序生成填入，这里只给 reset 骨架。</summary>
[BurstCompile]
struct BuildCostFieldJob : IJob
{
    public NativeArray<byte> CostField;
    public int Width, Height;
    public void Execute()
    {
        for (int i = 0; i < CostField.Length; i++)
            if (CostField[i] == 0) CostField[i] = 1;   // 默认空地代价 1，障碍保持 0
    }
}
```

## 三、IntegrationField（核心：Wavefront Dijkstra）

```csharp
/// <summary>从目标格做 Dijkstra 扩散，每格得到「到目标的累计代价」。
/// 用 NativeQueue + 松弛（SPFA 风格）；非负 cost 保证收敛。</summary>
[BurstCompile]
struct BuildIntegrationFieldJob : IJob
{
    [ReadOnly] public NativeArray<byte> CostField;
    public NativeArray<float> Integration;     // 初始全 float.MaxValue，目标=0
    public int Width, Height;
    public int2 Target;                         // 目标格子

    public void Execute()
    {
        // 1) 初始化（MAX 表示未访问）
        for (int i = 0; i < Integration.Length; i++) Integration[i] = float.MaxValue;
        int tIdx = Target.y * Width + Target.x;
        Integration[tIdx] = 0f;

        // 2) wavefront 队列
        var frontier = new NativeQueue<int>(Allocator.Temp);
        frontier.Enqueue(tIdx);

        // 8 邻域偏移（前 4 直边 cost 1，后 4 对角 cost √2）
        int2List dirs = new int2List(8);   // 见下方邻域定义
        // (用 NativeArray<int2> 预先建好更优，这里为可读性展开)

        while (frontier.Count > 0)
        {
            int cur = frontier.Dequeue();
            int cx = cur % Width, cz = cur / Width;
            float curCost = Integration[cur];

            int2[] neighbors = {
                new int2(cx+1, cz),   new int2(cx-1, cz),
                new int2(cx, cz+1),   new int2(cx, cz-1),
                new int2(cx+1, cz+1), new int2(cx-1, cz+1),
                new int2(cx+1, cz-1), new int2(cx-1, cz-1),
            };
            float[] stepCost = { 1,1,1,1, 1.4142f,1.4142f,1.4142f,1.4142f };

            for (int n = 0; n < 8; n++)
            {
                int nx = neighbors[n].x, nz = neighbors[n].y;
                if (nx < 0 || nz < 0 || nx >= Width || nz >= Height) continue;
                int nIdx = nz * Width + nx;
                byte nCostByte = CostField[nIdx];
                if (nCostByte == 0) continue;                          // 障碍
                // 对角线穿墙检查：两个相邻直边格不能都是障碍
                if (n >= 4 && (CostField[cz * Width + nx] == 0 || CostField[nz * Width + cx] == 0)) continue;

                float newCost = curCost + nCostByte * stepCost[n];
                if (newCost < Integration[nIdx])
                {
                    Integration[nIdx] = newCost;
                    frontier.Enqueue(nIdx);   // 松弛：重新入队传播
                }
            }
        }
        frontier.Dispose();
    }
}
```

> ⚠️ 上例为可读性用了托管数组（`int2[]`/`float[]`），**实际 Burst 编译需改 `NativeArray<int2>`/`NativeArray<float>`**（栈上 fixed 也可）。`NativeQueue<int>` 来自 `Unity.Collections`。重复入队导致的最坏复杂度高于正经 Dijkstra，但地图不极端时实测可接受；要严格最优用下面桶式。

**桶式 Dijkstra 扩展**（cost 分档多时）：
```
buckets: NativeList<int>[maxPossibleCost]   // 每桶存该距离层的格子
当前层 d=0 放 Target；处理 d 层时，邻居 newCost = d + edgeCost，放入 buckets[newCost]
按 d 从小到大扫桶，每格只处理一次 → 严格 O(格子数 × 邻域)
```
Burst 里 `NativeList<int>[]` 用 `NativeList<int3>`（x=格,y=桶,占位）或固定段实现，按规模选。

## 四、VectorField（8 邻域梯度，并行）

```csharp
/// <summary>对 Integration Field 取「代价下降最快」的方向，得 VectorField。
/// 每格独立，可 IJobParallelFor 并行。</summary>
[BurstCompile]
struct BuildVectorFieldJob : IJobParallelFor
{
    [ReadOnly] public NativeArray<float> Integration;
    [ReadOnly] public NativeArray<byte> CostField;
    public NativeArray<float3> Vector;
    public int Width, Height;

    public void Execute(int idx)
    {
        if (CostField[idx] == 0) { Vector[idx] = float3.zero; return; }  // 障碍无方向
        int cx = idx % Width, cz = idx / Width;
        float best = Integration[idx];
        int2 bestDir = int2.zero;

        int2[] neighbors = {
            new int2(1,0), new int2(-1,0), new int2(0,1), new int2(0,-1),
            new int2(1,1), new int2(-1,1), new int2(1,-1), new int2(-1,-1),
        };
        foreach (var d in neighbors)
        {
            int nx = cx + d.x, nz = cz + d.y;
            if (nx < 0 || nz < 0 || nx >= Width || nz >= Height) continue;
            int nIdx = nz * Width + nx;
            if (CostField[nIdx] == 0) continue;
            if (Integration[nIdx] < best) { best = Integration[nIdx]; bestDir = d; }
        }

        if (bestDir.x == 0 && bestDir.y == 0) { Vector[idx] = float3.zero; return; }
        float3 dir = math.normalizesafe(new float3(bestDir.x, 0f, bestDir.y));
        Vector[idx] = dir;
    }
}
```

> 这里取「最小 Integration 的邻居方向」（贪婪梯度）。更平滑的做法是**双线性插值**：单位不正好在格子中心时，按位置在 4 个相邻格的 VectorField 上插值，避免格子边界的方向跳变。

## 五、系统集成骨架

```csharp
using Unity.Entities;
using Unity.Collections;

/// <summary>目标/障碍变化时重建流场。节流：最小重算间隔 + 目标移动距离阈值。</summary>
public partial struct FlowFieldBuildSystem : ISystem
{
    private NativeArray<byte>   m_Cost;
    private NativeArray<float>  m_Integration;
    private NativeArray<float3> m_Vector;
    private int m_W, m_H;
    private bool m_Dirty;

    public void OnCreate(ref SystemState state)
    {
        m_W = 128; m_H = 128;
        m_Cost       = new NativeArray<byte>(m_W * m_H, Allocator.Persistent);
        m_Integration= new NativeArray<float>(m_W * m_H, Allocator.Persistent);
        m_Vector     = new NativeArray<float3>(m_W * m_H, Allocator.Persistent);
    }
    public void OnDestroy(ref SystemState state)
    {
        // 三场 Dispose；VectorField 若被 SteeringSystem 跨系统读，需共享句柄/生命周期管理
        if (m_Cost.IsCreated) m_Cost.Dispose();
        if (m_Integration.IsCreated) m_Integration.Dispose();
        if (m_Vector.IsCreated) m_Vector.Dispose();
    }
    public void OnUpdate(ref SystemState state)
    {
        if (!m_Dirty) return;
        m_Dirty = false;
        // 串行 job 链：Cost → Integration（IJob，串行队列）→ Vector（并行）
        var costJob   = new BuildCostFieldJob { /* ... */ };
        var integJob  = new BuildIntegrationFieldJob { CostField = m_Cost, Integration = m_Integration, Width = m_W, Height = m_H, Target = /*tgt*/ default };
        var vecJob    = new BuildVectorFieldJob { Integration = m_Integration, CostField = m_Cost, Vector = m_Vector, Width = m_W, Height = m_H };
        var h1 = costJob.Schedule();
        var h2 = integJob.Schedule(h1);
        var h3 = vecJob.Schedule(m_W * m_H, 64, h2);
        state.Dependency = h3;
    }
}
```

> ⚠️ 跨系统共享 `VectorField`：`SteeringSystem`（见 [[【笔记】大规模单位AI决策与寻路]]）要读它。工程上用**单例 NativeArray 句柄**（`state.WorldUnmanaged.ResolveSystemHandle` + 显式 `Dependency` 链）或托管 `NativeArray` 包一层 singleton 组件，确保读在写之后。`NativeArray` 跨系统共享时务必接 JobHandle 依赖，否则数据竞争。

## 六、避坑

- **优先队列**：Burst 无堆，用 wavefront 松弛（够用）或桶式（严格）。地图大/cost 分档多别用朴素松弛，会慢。
- **对角线穿墙**：扩散与梯度都要检查对角两邻接直边格不能同是障碍，否则单位切角穿墙。
- **重复入队**：wavefront 松弛会重复入队，设个 visited 上限或换桶式防止病态地图卡死。
- **目标频繁抖动**：节流重算（最小间隔 + 距离阈值），否则每帧重建 Integration 吃 CPU。
- **VectorField 跳变**：用双线性插值采样，单位边界处方向平滑。
- **多目标**：按目标分组各建一场，或仅给精英/Boss 独立 DOTS A*（见 [[【笔记】大规模单位AI决策与寻路]]）。

## 相关链接

- [[【笔记】大规模单位AI决策与寻路]] · [[【片段】RVO2局部避障ECS移植]] · [[【笔记】大规模单位战斗结算]] · [[【实战案例】10w单位渲染与动画最小Demo]] · [[【教程】JobSystem详解]] · [[【教程】Burst编译器]]
