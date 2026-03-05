---
title: 【教程】CPU优化技术
tags: [Unity, 性能优化, CPU, 教程]
category: 性能优化
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: Unity CPU优化技术详解
unity_version: 2021.3+
---
# CPU优化技术

> 第2课 | 性能优化与发布模块

## 1. GC（垃圾回收）优化

### 1.1 GC基础原理

```
┌─────────────────────────────────────────────────────────────┐
│                    Unity GC 工作原理                         │
│                                                             │
│  托管堆（Managed Heap）                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [对象A] [对象B] [空位] [对象C] [空位] [对象D]        │   │
│  └─────────────────────────────────────────────────────┘   │
│           ↓ GC触发                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [对象A] [对象B] [对象C] [对象D]                      │   │
│  └─────────────────────────────────────────────────────┘   │
│           ↑ 压缩后                                         │
│                                                             │
│  GC触发条件：                                               │
│  1. 堆内存不足时自动触发                                    │
│  2. 手动调用 GC.Collect()                                  │
│  3. 场景加载时                                              │
│                                                             │
│  GC影响：                                                   │
│  ├── 暂停所有线程                                          │
│  ├── 检查所有存活对象                                      │
│  └── 移动对象引用                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 常见GC分配陷阱

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// GC陷阱示例与优化
/// </summary>
public class GCTrapsExample : MonoBehaviour
{
    // ❌ 陷阱1：字符串拼接
    public void BadStringConcat()
    {
        string result = "";
        for (int i = 0; i < 100; i++)
        {
            result += i.ToString(); // 每次拼接都产生新字符串
        }
    }

    // ✅ 优化：使用StringBuilder
    public void GoodStringConcat()
    {
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < 100; i++)
        {
            sb.Append(i);
        }
        string result = sb.ToString();
    }

    // ❌ 陷阱2：装箱
    public void BadBoxing()
    {
        int value = 42;
        object boxed = value; // 装箱产生GC
        int unboxed = (int)boxed; // 拆箱
    }

    // ✅ 优化：使用泛型
    public void GoodGeneric<T>(T value) where T : struct
    {
        // 无装箱
    }

    // ❌ 陷阱3：foreach对数组（Unity旧版本）
    public void BadForeach()
    {
        int[] array = new int[100];
        foreach (var item in array) // 旧版本Unity会产生GC
        {
            // ...
        }
    }

    // ✅ 优化：使用for循环
    public void GoodFor()
    {
        int[] array = new int[100];
        for (int i = 0; i < array.Length; i++)
        {
            var item = array[i];
            // ...
        }
    }

    // ❌ 陷阱4：返回数组
    public int[] BadReturnArray()
    {
        return new int[] { 1, 2, 3 }; // 每次调用都分配
    }

    // ✅ 优化：使用预分配数组
    private int[] cachedArray = new int[3];
    public int[] GoodReturnArray()
    {
        cachedArray[0] = 1;
        cachedArray[1] = 2;
        cachedArray[2] = 3;
        return cachedArray;
    }
}
```

### 1.3 零GC模式

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 零GC游戏管理器示例
/// </summary>
public class ZeroGCManager : MonoBehaviour
{
    // 预分配集合
    private List<Gem> activeGems;
    private List<Gem> matchedGems;
    private Queue<Gem> gemPool;

    // 预分配事件参数
    private MatchEventArgs matchArgs;

    // 缓存常用字符串
    private static readonly string[] GEM_TYPE_NAMES = { "Fire", "Water", "Earth", "Wind" };

    // 对象池引用缓存
    private Dictionary<int, Gem> gemCache;

    private void Awake()
    {
        // 初始化时预分配
        activeGems = new List<Gem>(64);    // 预设容量
        matchedGems = new List<Gem>(32);
        gemPool = new Queue<Gem>(64);
        gemCache = new Dictionary<int, Gem>(64);
        matchArgs = new MatchEventArgs();
    }

    // ✅ 无GC的匹配检测
    public void CheckMatches()
    {
        matchedGems.Clear(); // 清空复用，不重新分配

        for (int i = 0; i < activeGems.Count; i++)
        {
            var gem = activeGems[i];
            if (IsMatched(gem))
            {
                matchedGems.Add(gem);
            }
        }
    }

    // ✅ 使用struct避免堆分配
    public struct MatchEventArgs
    {
        public int X;
        public int Y;
        public int MatchCount;
        public GemType Type;
    }

    // ✅ 使用枚举代替字符串
    public enum GemType
    {
        Fire,
        Water,
        Earth,
        Wind
    }

    private bool IsMatched(Gem gem)
    {
        // 匹配逻辑
        return false;
    }
}
```

### 1.4 使用Span和Memory

```csharp
using UnityEngine;
using System;

/// <summary>
/// Span<T> 高性能内存操作示例
/// </summary>
public class SpanExample : MonoBehaviour
{
    // ✅ 使用Span处理数组切片（无分配）
    public void ProcessBoardData()
    {
        int[] boardData = new int[64]; // 8x8棋盘

        // 获取第一行（不产生新数组）
        Span<int> firstRow = boardData.AsSpan(0, 8);

        // 处理第一行
        for (int i = 0; i < firstRow.Length; i++)
        {
            firstRow[i] *= 2;
        }

        // 获取特定区域
        Span<int> region = boardData.AsSpan(9, 6); // 第2行中间6个
    }

    // ✅ 使用stackalloc避免堆分配（小数组）
    public unsafe void ProcessSmallArray()
    {
        // 在栈上分配（仅适用于小数组）
        Span<int> buffer = stackalloc int[16];

        for (int i = 0; i < buffer.Length; i++)
        {
            buffer[i] = i;
        }
        // 函数结束时自动释放，无GC
    }

    // ✅ 使用Memory<T>进行异步操作
    public async void ProcessAsync()
    {
        int[] data = new int[100];
        Memory<int> memory = data;

        // 可以跨异步边界传递
        await ProcessMemoryAsync(memory);
    }

    private System.Threading.Tasks.Task ProcessMemoryAsync(Memory<int> memory)
    {
        // 处理数据
        return System.Threading.Tasks.Task.CompletedTask;
    }
}
```

---

## 2. Job System + Burst Compiler

### 2.1 Job System基础

```
┌─────────────────────────────────────────────────────────────┐
│                    Unity Job System                          │
│                                                             │
│  主线程                          工作线程                    │
│  ┌─────────┐                    ┌─────────────────────┐    │
│  │ 游戏逻辑 │                    │ Worker Thread 1     │    │
│  │         │   Schedule Job     │ ├── Job A          │    │
│  │ Job创建 │ ─────────────────> │ └── Job B          │    │
│  │         │                    ├─────────────────────┤    │
│  │ 等待完成 │ <───────────────── │ Worker Thread 2     │    │
│  │         │   Complete         │ ├── Job C          │    │
│  └─────────┘                    │ └── Job D          │    │
│                                 └─────────────────────┘    │
│                                                             │
│  优势：                                                     │
│  ├── 自动管理线程池                                         │
│  ├── 安全的多线程访问（NativeContainer）                    │
│  ├── 与主线程无竞争                                         │
│  └── 配合Burst编译器极大提升性能                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Job类型

```csharp
using Unity.Collections;
using Unity.Jobs;
using Unity.Burst;
using UnityEngine;

/// <summary>
/// Job System 示例
/// </summary>
public class JobSystemExample : MonoBehaviour
{
    // ========== IJob: 单个任务 ==========

    [BurstCompile]
    private struct SquareRootJob : IJob
    {
        public NativeArray<float> input;
        public NativeArray<float> output;

        public void Execute()
        {
            for (int i = 0; i < input.Length; i++)
            {
                output[i] = Mathf.Sqrt(input[i]);
            }
        }
    }

    // ========== IJobParallelFor: 并行任务 ==========

    [BurstCompile]
    private struct ParallelMatchJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<int> boardData;
        public NativeArray<bool> matchResults;
        public int boardWidth;

        public void Execute(int index)
        {
            int x = index % boardWidth;
            int y = index / boardWidth;

            // 简单的匹配检测逻辑
            if (x > 0 && x < boardWidth - 1)
            {
                int current = boardData[index];
                int left = boardData[index - 1];
                int right = boardData[index + 1];

                matchResults[index] = (current == left && current == right);
            }
            else
            {
                matchResults[index] = false;
            }
        }
    }

    // ========== IJobParallelForBatch: 批处理任务 ==========

    [BurstCompile]
    private struct BatchProcessJob : IJobParallelForBatch
    {
        public NativeArray<float> data;

        public void Execute(int startIndex, int count)
        {
            for (int i = startIndex; i < startIndex + count; i++)
            {
                data[i] = data[i] * 2f + 1f;
            }
        }
    }

    // ========== 使用示例 ==========

    public void RunJobs()
    {
        // 创建数据
        var input = new NativeArray<float>(1000, Allocator.TempJob);
        var output = new NativeArray<float>(1000, Allocator.TempJob);

        // 初始化输入
        for (int i = 0; i < input.Length; i++)
        {
            input[i] = i;
        }

        // 创建并调度Job
        var job = new SquareRootJob
        {
            input = input,
            output = output
        };

        JobHandle handle = job.Schedule();
        handle.Complete(); // 等待完成

        // 使用结果...

        // 释放内存
        input.Dispose();
        output.Dispose();
    }
}
```

### 2.3 三消匹配算法并行化

```csharp
using Unity.Collections;
using Unity.Jobs;
using Unity.Burst;
using UnityEngine;

/// <summary>
/// 并行化三消匹配检测
/// </summary>
public class ParallelMatchDetector : MonoBehaviour
{
    private const int BOARD_SIZE = 8;

    private NativeArray<int> boardData;
    private NativeArray<bool> horizontalMatches;
    private NativeArray<bool> verticalMatches;
    private NativeArray<bool> allMatches;

    private void Start()
    {
        // 初始化NativeArray
        boardData = new NativeArray<int>(BOARD_SIZE * BOARD_SIZE, Allocator.Persistent);
        horizontalMatches = new NativeArray<bool>(BOARD_SIZE * BOARD_SIZE, Allocator.Persistent);
        verticalMatches = new NativeArray<bool>(BOARD_SIZE * BOARD_SIZE, Allocator.Persistent);
        allMatches = new NativeArray<bool>(BOARD_SIZE * BOARD_SIZE, Allocator.Persistent);
    }

    private void OnDestroy()
    {
        // 释放内存
        if (boardData.IsCreated) boardData.Dispose();
        if (horizontalMatches.IsCreated) horizontalMatches.Dispose();
        if (verticalMatches.IsCreated) verticalMatches.Dispose();
        if (allMatches.IsCreated) allMatches.Dispose();
    }

    /// <summary>
    /// 检测所有匹配（并行）
    /// </summary>
    public JobHandle DetectMatches()
    {
        // 水平匹配检测Job
        var horizontalJob = new HorizontalMatchJob
        {
            boardData = boardData,
            matches = horizontalMatches,
            boardWidth = BOARD_SIZE
        };

        // 垂直匹配检测Job
        var verticalJob = new VerticalMatchJob
        {
            boardData = boardData,
            matches = verticalMatches,
            boardWidth = BOARD_SIZE
        };

        // 合并结果Job
        var combineJob = new CombineMatchesJob
        {
            horizontal = horizontalMatches,
            vertical = verticalMatches,
            result = allMatches
        };

        // 调度Job链
        var hHandle = horizontalJob.Schedule(boardData.Length, 64);
        var vHandle = verticalJob.Schedule(boardData.Length, 64);
        var combined = JobHandle.CombineDependencies(hHandle, vHandle);
        var finalHandle = combineJob.Schedule(boardData.Length, 64, combined);

        return finalHandle;
    }

    // ========== Job定义 ==========

    [BurstCompile]
    private struct HorizontalMatchJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<int> boardData;
        public NativeArray<bool> matches;
        public int boardWidth;

        public void Execute(int index)
        {
            int x = index % boardWidth;
            int y = index / boardWidth;
            int gemType = boardData[index];

            // 检查左边两个
            if (x >= 2)
            {
                int left1 = boardData[index - 1];
                int left2 = boardData[index - 2];
                if (gemType == left1 && gemType == left2)
                {
                    matches[index] = true;
                    return;
                }
            }

            // 检查右边两个
            if (x <= boardWidth - 3)
            {
                int right1 = boardData[index + 1];
                int right2 = boardData[index + 2];
                if (gemType == right1 && gemType == right2)
                {
                    matches[index] = true;
                    return;
                }
            }

            matches[index] = false;
        }
    }

    [BurstCompile]
    private struct VerticalMatchJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<int> boardData;
        public NativeArray<bool> matches;
        public int boardWidth;

        public void Execute(int index)
        {
            int y = index / boardWidth;
            int gemType = boardData[index];

            // 检查下面两个
            if (y >= 2)
            {
                int down1 = boardData[index - boardWidth];
                int down2 = boardData[index - boardWidth * 2];
                if (gemType == down1 && gemType == down2)
                {
                    matches[index] = true;
                    return;
                }
            }

            // 检查上面两个
            if (y <= boardWidth - 3)
            {
                int up1 = boardData[index + boardWidth];
                int up2 = boardData[index + boardWidth * 2];
                if (gemType == up1 && gemType == up2)
                {
                    matches[index] = true;
                    return;
                }
            }

            matches[index] = false;
        }
    }

    [BurstCompile]
    private struct CombineMatchesJob : IJobParallelFor
    {
        [ReadOnly] public NativeArray<bool> horizontal;
        [ReadOnly] public NativeArray<bool> vertical;
        public NativeArray<bool> result;

        public void Execute(int index)
        {
            result[index] = horizontal[index] || vertical[index];
        }
    }
}
```

### 2.4 Burst Compiler最佳实践

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using UnityEngine;

/// <summary>
/// Burst编译器最佳实践
/// </summary>
public class BurstBestPractices : MonoBehaviour
{
    // ✅ 使用BurstCompile属性
    [BurstCompile]
    private struct OptimizedJob : IJob
    {
        public NativeArray<float> data;

        public void Execute()
        {
            for (int i = 0; i < data.Length; i++)
            {
                data[i] = math.sqrt(data[i]); // 使用Unity.Mathematics
            }
        }
    }

    // ✅ 使用float3/int3等Unity.Mathematics类型
    [BurstCompile]
    private struct VectorJob : IJobParallelFor
    {
        public NativeArray<float3> positions;
        public float3 offset;

        public void Execute(int index)
        {
            positions[index] += offset;
        }
    }

    // ✅ 指定编译选项
    [BurstCompile(
        CompileSynchronously = true,  // 同步编译（开发时）
        FloatMode = FloatMode.Fast,   // 快速浮点（牺牲精度）
        FloatPrecision = FloatMode.Medium
    )]
    private struct FastMathJob : IJob
    {
        public NativeArray<float> values;

        public void Execute()
        {
            for (int i = 0; i < values.Length; i++)
            {
                // 快速数学运算
                values[i] = math.abs(values[i]);
            }
        }
    }

    // ❌ 避免在Job中使用托管对象
    // 以下代码会导致Burst编译失败：
    /*
    [BurstCompile]
    private struct BadJob : IJob
    {
        public string name;           // ❌ 托管类型
        public int[] array;           // ❌ 托管数组
        public List<int> list;        // ❌ 托管列表

        public void Execute() { }
    }
    */

    // ✅ 正确做法：使用NativeContainer
    [BurstCompile]
    private struct GoodJob : IJob
    {
        public FixedString64 name;    // ✅ 固定大小字符串
        public NativeArray<int> array; // ✅ NativeArray

        public void Execute() { }
    }
}
```

---

## 3. 批处理与GPU Instancing

### 3.1 静态批处理

```csharp
using UnityEngine;

/// <summary>
/// 静态批处理设置
/// </summary>
public class StaticBatchingSetup : MonoBehaviour
{
    [Header("棋盘格子")]
    [SerializeField] private GameObject tilePrefab;
    [SerializeField] private int boardSize = 8;

    private void Start()
    {
        CreateBoard();
    }

    private void CreateBoard()
    {
        // 标记为静态以启用静态批处理
        // 在Inspector中也可以勾选 Static 标志

        for (int x = 0; x < boardSize; x++)
        {
            for (int y = 0; y < boardSize; y++)
            {
                var tile = Instantiate(tilePrefab, new Vector3(x, y, 0), Quaternion.identity);
                tile.transform.parent = transform;

                // 运行时标记为静态（需要配合StaticBatchingUtility）
                tile.isStatic = true;
            }
        }

        // 合并静态批次
        StaticBatchingUtility.Combine(gameObject);
    }
}
```

### 3.2 动态批处理

```
┌─────────────────────────────────────────────────────────────┐
│                    动态批处理条件                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✓ 使用相同材质实例                                         │
│  ✓ 顶点数 ≤ 900（Mobile）或 ≤ 300（Desktop）               │
│  ✓ 缩放为 (1,1,1) 或统一缩放                               │
│  ✓ 材质Shader使用相同关键字                                 │
│  ✓ 不使用光照贴图或使用相同光照贴图                         │
│  ✓ 多 Pass Shader 会打断批处理                              │
│                                                             │
│  设置位置：                                                  │
│  Player Settings > Other Settings > Dynamic Batching        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 GPU Instancing

```csharp
using UnityEngine;

/// <summary>
/// GPU Instancing 渲染棋子
/// </summary>
public class GPUInstancingRenderer : MonoBehaviour
{
    [Header("Instancing Settings")]
    [SerializeField] private Mesh gemMesh;
    [SerializeField] private Material instancingMaterial;
    [SerializeField] private int boardSize = 8;

    // 每个实例的属性
    private Matrix4x4[] matrices;
    private MaterialPropertyBlock propertyBlock;
    private Vector4[] colors;
    private int instanceCount;

    // GPU Instancing 支持的最大实例数
    private const int MAX_INSTANCES_PER_BATCH = 1023;

    private void Start()
    {
        instanceCount = boardSize * boardSize;
        matrices = new Matrix4x4[instanceCount];
        colors = new Vector4[instanceCount];
        propertyBlock = new MaterialPropertyBlock();

        // 确保材质开启GPU Instancing
        if (!instancingMaterial.enableInstancing)
        {
            instancingMaterial.enableInstancing = true;
        }

        InitializeInstances();
    }

    private void InitializeInstances()
    {
        int index = 0;
        for (int x = 0; x < boardSize; x++)
        {
            for (int y = 0; y < boardSize; y++)
            {
                matrices[index] = Matrix4x4.TRS(
                    new Vector3(x, y, 0),
                    Quaternion.identity,
                    Vector3.one * 0.9f
                );

                // 随机颜色
                colors[index] = new Vector4(
                    Random.Range(0.5f, 1f),
                    Random.Range(0.5f, 1f),
                    Random.Range(0.5f, 1f),
                    1f
                );

                index++;
            }
        }
    }

    private void Update()
    {
        // 更新属性块
        propertyBlock.SetVectorArray("_Color", colors);

        // 绘制所有实例（一次DrawCall）
        Graphics.DrawMeshInstanced(
            gemMesh,
            0,  // submesh index
            instancingMaterial,
            matrices,
            instanceCount,
            propertyBlock,
            UnityEngine.Rendering.ShadowCastingMode.Off,
            false,  // receive shadows
            0,      // layer
            null,   // camera
            UnityEngine.Rendering.LightProbeUsage.Off
        );
    }

    /// <summary>
    /// 更新单个实例的颜色
    /// </summary>
    public void UpdateGemColor(int index, Color color)
    {
        if (index >= 0 && index < instanceCount)
        {
            colors[index] = new Vector4(color.r, color.g, color.b, color.a);
        }
    }

    /// <summary>
    /// 更新单个实例的位置
    /// </summary>
    public void UpdateGemPosition(int index, Vector3 position)
    {
        if (index >= 0 && index < instanceCount)
        {
            matrices[index] = Matrix4x4.TRS(position, Quaternion.identity, Vector3.one * 0.9f);
        }
    }
}
```

### 3.4 大量实例的分批渲染

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 大量实例的分批渲染管理器
/// </summary>
public class BatchedInstancingRenderer : MonoBehaviour
{
    private const int BATCH_SIZE = 1023; // GPU Instancing单批上限

    private List<Matrix4x4[]> matrixBatches = new List<Matrix4x4[]>();
    private Mesh mesh;
    private Material material;

    public void Initialize(Mesh mesh, Material material, int totalInstances)
    {
        this.mesh = mesh;
        this.material = material;

        // 计算需要多少批次
        int batchCount = (totalInstances + BATCH_SIZE - 1) / BATCH_SIZE;

        matrixBatches.Clear();
        for (int i = 0; i < batchCount; i++)
        {
            int thisBatchSize = Mathf.Min(BATCH_SIZE, totalInstances - i * BATCH_SIZE);
            matrixBatches.Add(new Matrix4x4[thisBatchSize]);
        }
    }

    public void SetMatrix(int globalIndex, Matrix4x4 matrix)
    {
        int batchIndex = globalIndex / BATCH_SIZE;
        int localIndex = globalIndex % BATCH_SIZE;

        if (batchIndex < matrixBatches.Count && localIndex < matrixBatches[batchIndex].Length)
        {
            matrixBatches[batchIndex][localIndex] = matrix;
        }
    }

    public void Render()
    {
        for (int i = 0; i < matrixBatches.Count; i++)
        {
            Graphics.DrawMeshInstanced(
                mesh,
                0,
                material,
                matrixBatches[i],
                matrixBatches[i].Length
            );
        }
    }
}
```

---

## 4. 协程优化

### 4.1 协程最佳实践

```csharp
using UnityEngine;
using System.Collections;

/// <summary>
/// 协程优化示例
/// </summary>
public class CoroutineOptimization : MonoBehaviour
{
    // ❌ 不好：每帧都new WaitForSeconds
    public IEnumerator BadWait()
    {
        while (true)
        {
            yield return new WaitForSeconds(1f); // 每次产生GC
        }
    }

    // ✅ 好：缓存WaitForSeconds
    private WaitForSeconds waitOneSecond = new WaitForSeconds(1f);

    public IEnumerator GoodWait()
    {
        while (true)
        {
            yield return waitOneSecond; // 无GC
        }
    }

    // ✅ 缓存常用等待指令
    private static readonly WaitForEndOfFrame waitForEndOfFrame = new WaitForEndOfFrame();
    private static readonly WaitForFixedUpdate waitForFixedUpdate = new WaitForFixedUpdate();

    // ✅ 使用WaitUntil/WaitWhile代替轮询
    public IEnumerator WaitForCondition()
    {
        // ❌ 轮询方式
        /*
        while (!IsReady)
        {
            yield return null;
        }
        */

        // ✅ 条件等待
        yield return new WaitUntil(() => IsReady);
    }

    private bool IsReady => true;

    // ✅ 使用CustomYieldInstruction实现自定义等待
    public class WaitForAnimation : CustomYieldInstruction
    {
        private Animator animator;
        private int layerIndex;
        private string stateName;

        public WaitForAnimation(Animator animator, string stateName, int layerIndex = 0)
        {
            this.animator = animator;
            this.stateName = stateName;
            this.layerIndex = layerIndex;
        }

        public override bool keepWaiting
        {
            get
            {
                return animator.GetCurrentAnimatorStateInfo(layerIndex).IsName(stateName) &&
                       animator.GetCurrentAnimatorStateInfo(layerIndex).normalizedTime < 1f;
            }
        }
    }
}
```

### 4.2 消除动画协程示例

```csharp
using UnityEngine;
using System.Collections;
using System.Collections.Generic;

/// <summary>
/// 棋子消除动画管理器
/// </summary>
public class MatchAnimationManager : MonoBehaviour
{
    [Header("Animation Settings")]
    [SerializeField] private float matchAnimDuration = 0.3f;
    [SerializeField] private float fallAnimDuration = 0.2f;
    [SerializeField] private AnimationCurve scaleCurve;
    [SerializeField] private AnimationCurve fallCurve;

    // 缓存WaitForSeconds
    private WaitForSeconds waitMatchAnim;

    // 活跃的协程
    private Dictionary<int, Coroutine> activeAnimations = new Dictionary<int, Coroutine>();

    private void Awake()
    {
        waitMatchAnim = new WaitForSeconds(matchAnimDuration);
    }

    /// <summary>
    /// 播放消除动画
    /// </summary>
    public void PlayMatchAnimation(List<Gem> matchedGems, System.Action onComplete)
    {
        StartCoroutine(MatchAnimationCoroutine(matchedGems, onComplete));
    }

    private IEnumerator MatchAnimationCoroutine(List<Gem> gems, System.Action onComplete)
    {
        float elapsed = 0f;

        while (elapsed < matchAnimDuration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / matchAnimDuration;
            float scale = scaleCurve.Evaluate(t);

            foreach (var gem in gems)
            {
                if (gem != null)
                {
                    gem.transform.localScale = Vector3.one * scale;
                }
            }

            yield return null; // 无GC
        }

        // 回收棋子
        foreach (var gem in gems)
        {
            if (gem != null)
            {
                gem.gameObject.SetActive(false);
                gem.transform.localScale = Vector3.one;
            }
        }

        onComplete?.Invoke();
    }

    /// <summary>
    /// 播放下落动画
    /// </summary>
    public void PlayFallAnimation(Gem gem, Vector3 startPos, Vector3 endPos)
    {
        int key = gem.GetInstanceID();

        // 如果已有动画在播放，先停止
        if (activeAnimations.TryGetValue(key, out var existingCoroutine))
        {
            StopCoroutine(existingCoroutine);
        }

        activeAnimations[key] = StartCoroutine(FallAnimationCoroutine(gem, startPos, endPos));
    }

    private IEnumerator FallAnimationCoroutine(Gem gem, Vector3 startPos, Vector3 endPos)
    {
        gem.transform.position = startPos;
        float elapsed = 0f;

        while (elapsed < fallAnimDuration)
        {
            elapsed += Time.deltaTime;
            float t = fallCurve.Evaluate(elapsed / fallAnimDuration);
            gem.transform.position = Vector3.Lerp(startPos, endPos, t);

            yield return null;
        }

        gem.transform.position = endPos;
        activeAnimations.Remove(gem.GetInstanceID());
    }
}

public class Gem : MonoBehaviour
{
    // Gem类定义
}
```

---

## 本课小结

### 核心知识点

| 优化方向 | 关键技术 | 效果 |
|----------|----------|------|
| GC优化 | 预分配、对象池、StringBuilder | 减少GC暂停 |
| Job System | IJob、IJobParallelFor | 多核并行 |
| Burst编译 | [BurstCompile]、Unity.Mathematics | 10-100x性能提升 |
| 批处理 | 静态/动态批处理、GPU Instancing | 减少DrawCall |
| 协程优化 | 缓存WaitForSeconds、条件等待 | 减少GC |

### 性能优化检查清单

```markdown
## CPU优化检查清单

### GC
- [ ] 无每帧字符串拼接
- [ ] 无频繁装箱操作
- [ ] 集合预设容量
- [ ] 使用对象池

### Job System
- [ ] 耗时计算已并行化
- [ ] 使用[BurstCompile]
- [ ] 正确使用NativeContainer
- [ ] 及时Dispose

### 批处理
- [ ] 静态物体标记Static
- [ ] 使用相同材质
- [ ] 考虑GPU Instancing
- [ ] 检查DrawCall数量

### 协程
- [ ] 缓存WaitForSeconds
- [ ] 避免协程内new对象
- [ ] 合理使用WaitUntil
```

---

## 延伸阅读

- [Unity Job System](https://docs.unity3d.com/Manual/JobSystem.html)
- [Burst Compiler](https://docs.unity3d.com/Packages/com.unity.burst@latest)
- [GPU Instancing](https://docs.unity3d.com/Manual/GPUInstancing.html)
- [Unity Performance Best Practices](https://docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity.html)
