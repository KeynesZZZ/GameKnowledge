---
title: 【教程】ComputeShader入门
tags: [Unity, 渲染系统, ComputeShader, 教程]
category: 核心系统/渲染系统
created: 2026-03-05 08:31
updated: 2026-03-05 08:31
description: ComputeShader基础入门教程
unity_version: 2021.3+
---
# Compute Shader 入门

> Unity Compute Shader 基础语法和实战应用 `#渲染与Shader` `#ComputeShader` `#GPU计算`

## 概述

Compute Shader 允许在 GPU 上运行通用计算，利用并行处理能力加速大量数据的处理。适用于粒子系统、物理模拟、图像处理等场景。

## Compute Shader 基础

### 1. Compute Shader 文件结构

```hlsl
#pragma kernel MainKernel

RWStructuredBuffer<float> Result;
StructuredBuffer<float> Input;
uint NumElements;

[numthreads(8,8,1)]
void MainKernel (uint3 id : SV_DispatchThreadID)
{
    if (id.x >= NumElements) return;
    
    Result[id.x] = Input[id.x] * 2.0f;
}
```

### 2. 线程组（Thread Groups）

```hlsl
// 8x8x1 线程组
[numthreads(8,8,1)]
void Kernel (uint3 id : SV_DispatchThreadID)
{
    // id.x, id.y, id.z 是线程 ID
    uint globalIndex = id.x + id.y * 8;
}
```

---

## C# 代码调用

### 1. 基础调用

```csharp
using UnityEngine;
using UnityEngine.Rendering;

public class ComputeShaderController : MonoBehaviour
{
    public ComputeShader computeShader;
    public int size = 1000;
    
    private ComputeBuffer inputBuffer;
    private ComputeBuffer outputBuffer;
    private float[] inputData;
    private float[] outputData;

    void Start()
    {
        // 初始化数据
        inputData = new float[size];
        for (int i = 0; i < size; i++)
        {
            inputData[i] = Random.Range(0f, 100f);
        }
        
        // 创建 Buffer
        inputBuffer = new ComputeBuffer(size, sizeof(float));
        inputBuffer.SetData(inputData);
        
        outputBuffer = new ComputeBuffer(size, sizeof(float));
        
        // 设置 Shader 变量
        computeShader.SetBuffer(0, inputBuffer);
        computeShader.SetBuffer(1, outputBuffer);
        computeShader.SetInt("NumElements", size);
    }

    void Update()
    {
        // Dispatch Shader
        int threadGroups = Mathf.CeilToInt(size / 64.0f);
        computeShader.Dispatch(0, threadGroups, 1, 1);
        
        // 读取结果
        outputData = new float[size];
        outputBuffer.GetData(outputData);
    }

    void OnDestroy()
    {
        // 清理 Buffer
        inputBuffer.Release();
        outputBuffer.Release();
    }
}
```

---

## 实战案例

### 1. 粒子系统加速

```hlsl
#pragma kernel UpdateParticles

RWStructuredBuffer<float3> Positions;
RWStructuredBuffer<float3> Velocities;
float DeltaTime;
float Lifetime;

[numthreads(64,1,1)]
void UpdateParticles (uint3 id : SV_DispatchThreadID)
{
    uint index = id.x;
    
    // 更新位置
    Positions[index] += Velocities[index] * DeltaTime;
    
    // 减少生命周期
    Velocities[index].z -= DeltaTime * 0.1f;
}
```

```csharp
using UnityEngine;

public class ParticleSystemGPU : MonoBehaviour
{
    public ComputeShader computeShader;
    public int particleCount = 10000;

    private ComputeBuffer positionsBuffer;
    private ComputeBuffer velocitiesBuffer;

    void Start()
    {
        Vector3[] positions = new Vector3[particleCount];
        Vector3[] velocities = new Vector3[particleCount];

        // 创建 Buffer
        positionsBuffer = new ComputeBuffer(
            particleCount,
            sizeof(float) * 3
        );
        velocitiesBuffer = new ComputeBuffer(
            particleCount,
            sizeof(float) * 3
        );
    }

    void Update()
    {
        computeShader.SetFloat("DeltaTime", Time.deltaTime);
        computeShader.SetBuffer(0, positionsBuffer);
        computeShader.SetBuffer(1, velocitiesBuffer);
        
        int threadGroups = Mathf.CeilToInt(particleCount / 64.0f);
        computeShader.Dispatch(0, threadGroups, 1, 1);
    }
}
```

### 2. 图像处理

```hlsl
#pragma kernel ImageProcessing

RWTexture2D<float4> Result;
Texture2D<float4> Input;

[numthreads(8,8,1)]
void ImageProcessing (uint3 id : SV_DispatchThreadID)
{
    uint2 pixelID = id.xy;
    
    // 简单的灰度处理
    float4 color = Input[pixelID];
    float gray = dot(color.rgb, float3(0.299, 0.587, 0.114));
    
    Result[pixelID] = float4(gray, gray, gray, 1.0);
}
```

---

## 性能优化

### 1. 合理设置线程组

```csharp
// ✅ 推荐大小：8x8x1, 16x16x1, 32x32x1
int threadGroupsX = Mathf.CeilToInt(width / 8.0f);
int threadGroupsY = Mathf.CeilToInt(height / 8.0f);
computeShader.Dispatch(0, threadGroupsX, threadGroupsY, 1);
```

### 2. 使用共享内存

```hlsl
groupshared float sharedData[256];

[numthreads(16,16,1)]
void Kernel (uint3 id : SV_DispatchThreadID)
{
    // 使用共享内存加速
    sharedData[id.x] = Input[id.x];
    GroupMemoryBarrierWithGroupSync();
}
```

---

## 最佳实践

### DO ✅

- 使用 Compute Shader 处理大量数据
- 合理设置线程组大小
- 使用共享内存优化访问
- 及时释放 ComputeBuffer
- 使用异步加载避免卡顿

### DON'T ❌

- 不要在小数据量上使用 Compute Shader（CPU 更快）
- 不要忘记释放 ComputeBuffer
- 不要使用过大的线程组（性能问题）
- 不要在 Update 中频繁分配内存

---

## 常见问题

### Q: Compute Shader 不工作？
**A**: 
1. 检查是否正确支持 Compute Shader
2. 检查是否正确设置了 Dispatch
3. 检查 Shader 是否正确编译
4. 检查 Buffer 是否正确创建

### Q: 性能不如 CPU？
**A**: 
1. 检查数据量是否足够大
2. 检查线程组设置是否合理
3. 检查是否频繁同步数据（CPU-GPU 传输成本）

---

## 相关链接

- [Shader基础语法](./Shader基础语法.md)
- [性能优化指南](../../30_性能优化/README.md)

---

**适用版本**: Unity 2019.4+
**最后更新**: 2026-03-04
