---
title: 【教程】JobSystem详解
tags: [Unity, DOTS, DOTS技术栈, JobSystem, 教程]
category: DOTS技术栈
created: 2026-03-05 09:21
updated: 2026-03-05 09:21
description: Unity JobSystem详解教程
unity_version: 2021.3+
---
# Job System 详解

> 第1课 | DOTS 技术栈模块

## 文档定位

本文档从**使用角度**讲解JobSystem详解。

**相关文档**：[[【教程】JobSystem详解]]

---

## 1. 什么是 Job System？

**Job System** 是 Unity 的多线程任务系统，用于：

- 安全地编写多线程代码
- 自动管理依赖关系
- 与主线程协同工作
- 避免 GC 分配

---

## 2. 基础 Job 类型

### 2.1 IJob - 单线程任务

```csharp
using Unity.Collections;
using Unity.Jobs;
using UnityEngine;

public struct SimpleJob : IJob
{
    public NativeArray<float> input;
    public NativeArray<float> output;
    public float multiplier;

    public void Execute()
    {
        for (int i = 0; i < input.Length; i++)
        {
            output[i] = input[i] * multiplier;
        }
    }
}

// 使用
public class JobExample : MonoBehaviour
{
    void Start()
    {
        var input = new NativeArray<float>(1000, Allocator.TempJob);
        var output = new NativeArray<float>(1000, Allocator.TempJob);

        // 初始化输入
        for (int i = 0; i < input.Length; i++)
            input[i] = i;

        // 创建 Job
        var job = new SimpleJob
        {
            input = input,
            output = output,
            multiplier = 2.0f
        };

        // 调度 Job
        JobHandle handle = job.Schedule();

        // 等待完成
        handle.Complete();

        // 使用结果
        Debug.Log($"Result[0] = {output[0]}, Result[500] = {output[500]}");

        // 释放内存
        input.Dispose();
        output.Dispose();
    }
}
```

### 2.2 IJobParallelFor - 并行任务

```csharp
public struct ParallelJob : IJobParallelFor
{
    [ReadOnly] public NativeArray<Vector3> positions;
    public NativeArray<Vector3> velocities;
    public float deltaTime;

    public void Execute(int index)
    {
        // 每个索引独立执行，可并行
        velocities[index] += positions[index] * deltaTime;
    }
}

// 使用
var job = new ParallelJob
{
    positions = positions,
    velocities = velocities,
    deltaTime = Time.deltaTime
};

// batchCount = 每批次处理数量（自动优化传 64）
// innerloopBatchCount 越小，负载均衡越好，但调度开销越大
JobHandle handle = job.Schedule(positions.Length, 64);
```

### 2.3 IJobParallelForTransform

```csharp
using Unity.Collections.LowLevel.Unsafe;
using Unity.Jobs;
using UnityEngine;

public struct TransformJob : IJobParallelForTransform
{
    public NativeArray<Vector3> positions;
    public float deltaTime;

    public void Execute(int index, TransformAccess transform)
    {
        transform.position = positions[index];
        // 注意：只能访问 position 和 rotation
    }
}

// 需要使用 TransformAccessArray
public class TransformJobExample : MonoBehaviour
{
    public Transform[] transforms;
    private TransformAccessArray transformAccessArray;

    void Start()
    {
        transformAccessArray = new TransformAccessArray(transforms);
    }

    void Update()
    {
        var positions = new NativeArray<Vector3>(transforms.Length, Allocator.TempJob);
        // ... 初始化 positions

        var job = new TransformJob
        {
            positions = positions,
            deltaTime = Time.deltaTime
        };

        JobHandle handle = job.Schedule(transformAccessArray);
        handle.Complete();

        positions.Dispose();
    }

    void OnDestroy()
    {
        transformAccessArray.Dispose();
    }
}
```

---

## 3. NativeContainer 容器

### 3.1 NativeArray

```csharp
// 创建
var array = new NativeArray<int>(1000, Allocator.TempJob);

// 访问
array[0] = 42;
int value = array[0];

// 批量操作
array.CopyTo(anotherArray);

// 释放
array.Dispose();
```

### 3.2 NativeList

```csharp
var list = new NativeList<int>(Allocator.TempJob);

list.Add(1);
list.Add(2);
list.RemoveAt(0);

int length = list.Length;
int capacity = list.Capacity;

list.Dispose();
```

### 3.3 NativeHashMap

```csharp
var map = new NativeHashMap<int, string>(100, Allocator.TempJob);

map.TryAdd(1, "One");
map.TryAdd(2, "Two");

if (map.TryGetValue(1, out var value))
{
    Debug.Log(value);  // "One"
}

map.Dispose();
```

### 3.4 NativeQueue

```csharp
var queue = new NativeQueue<int>(Allocator.TempJob);

queue.Enqueue(1);
queue.Enqueue(2);

if (queue.TryDequeue(out var item))
{
    Debug.Log(item);  // 1
}

queue.Dispose();
```

### 3.5 Allocator 类型

| 类型 | 生命周期 | 用途 |
|------|----------|------|
| Temp | 最短，一帧内 | 临时数据，需手动 Dispose |
| TempJob | Job 完成前 | Job 间传递数据 |
| Persistent | 最长 | 跨帧使用，性能敏感场景 |
| Invalid | - | 仅用于初始化 |

---

## 4. Job 依赖与调度

### 4.1 依赖链

```csharp
// Job A
var jobA = new JobA { data = dataA };
JobHandle handleA = jobA.Schedule();

// Job B 依赖 Job A
var jobB = new JobB { data = dataB };
JobHandle handleB = jobB.Schedule(handleA);  // 等 A 完成后执行

// Job C 依赖 Job A 和 Job B
var jobC = new JobC { data = dataC };
JobHandle handleC = jobC.Schedule(JobHandle.CombineDependencies(handleA, handleB));

// 等待所有完成
handleC.Complete();
```

### 4.2 批量调度

```csharp
public class BatchScheduler : MonoBehaviour
{
    private NativeArray<JobHandle> handles;

    void Update()
    {
        handles = new NativeArray<JobHandle>(10, Allocator.TempJob);

        for (int i = 0; i < 10; i++)
        {
            var job = new ProcessJob { index = i };
            handles[i] = job.Schedule();
        }

        // 合并所有依赖
        JobHandle combined = JobHandle.CombineDependencies(handles);
        combined.Complete();

        handles.Dispose();
    }
}
```

### 4.3 Early Job Schedule

```csharp
public class EarlySchedule : MonoBehaviour
{
    private JobHandle lastFrameJob;

    void Update()
    {
        // 等待上一帧的 Job
        lastFrameJob.Complete();

        // 使用上一帧的结果
        ProcessResults();

        // 启动这一帧的 Job（下一帧使用）
        var job = new ComputeJob { /* ... */ };
        lastFrameJob = job.Schedule();

        // 不在这里 Complete，让 Job 在帧间运行
    }
}
```

---

## 5. 安全性检查

### 5.1 Job Debugger

```csharp
// 启用安全检查（开发时开启）
JobsUtility.JobDebuggerEnabled = true;

// 安全检查会捕获：
// - 多个 Job 同时写入同一数据
// - 在 Job 运行时修改 NativeContainer
// - 使用未初始化的数据
```

### 5.2 常见错误

```csharp
// ❌ 错误：竞态条件
public struct BadJob : IJobParallelFor
{
    public NativeArray<int> data;
    public NativeReference<int> counter;  // 多线程写入！

    public void Execute(int index)
    {
        data[index] = index;
        counter.Value++;  // 错误！非原子操作
    }
}

// ✅ 正确：使用原子计数或单独统计
public struct GoodJob : IJobParallelFor
{
    public NativeArray<int> data;

    public void Execute(int index)
    {
        data[index] = index;
        // 统计在外部进行
    }
}
```

---

## 6. 性能最佳实践

### 6.1 批量大小选择

```csharp
// CPU 密集型任务：较大的批次
JobHandle handle = job.Schedule(count, 128);

// I/O 密集型或负载不均：较小的批次
JobHandle handle = job.Schedule(count, 16);

// 让 Unity 自动选择
JobHandle handle = job.Schedule(count, 64);
```

### 6.2 减少 Complete 调用

```csharp
// ❌ 多次 Complete
handle1.Complete();
handle2.Complete();
handle3.Complete();

// ✅ 合并后一次 Complete
var combined = JobHandle.CombineDependencies(handle1, handle2, handle3);
combined.Complete();
```

### 6.3 Cache Friendly 数据布局

```csharp
// ❌ AoS (Array of Structures)
struct ParticleAoS
{
    Vector3 position;
    Vector3 velocity;
    Color color;
}
ParticleAoS[] particles;  // 访问 position 时会加载整个 struct

// ✅ SoA (Structure of Arrays)
struct ParticleSoA
{
    NativeArray<Vector3> positions;
    NativeArray<Vector3> velocities;
    NativeArray<Color> colors;
}
// 只加载需要的数据
```

---

## 本课小结

### Job 类型对比

| 类型 | 并行度 | 用途 |
|------|--------|------|
| IJob | 单线程 | 顺序任务 |
| IJobParallelFor | 多线程 | 数据并行 |
| IJobParallelForTransform | 多线程 | Transform 操作 |

### NativeContainer 对比

| 容器 | 特点 | 时间复杂度 |
|------|------|-----------|
| NativeArray | 固定大小，最快 | O(1) |
| NativeList | 动态大小 | O(1) 均摊 |
| NativeHashMap | 键值对 | O(1) |
| NativeQueue | FIFO | O(1) |

### 性能提升

| 场景 | 主线程 | Job System |
|------|--------|------------|
| 10万粒子更新 | ~10ms | ~1ms |
| 碰撞检测 | ~20ms | ~2ms |
| 路径寻路 | ~50ms | ~5ms |

---

## 相关链接

- [Unity Job System 官方文档](https://docs.unity3d.com/Manual/JobSystem.html)
- [Unity C# Job System Cookbook](https://github.com/stella3d/job-system-cookbook)
