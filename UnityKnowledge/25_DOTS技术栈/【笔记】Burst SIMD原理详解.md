---
title: 【笔记】Burst SIMD原理详解
tags: ["Unity", "DOTS", "Burst", "SIMD", "深度解析", "笔记"]
category: DOTS技术栈
created: "2026-07-01"
description: 从CPU向量寄存器、LLVM编译流水线到内存布局，深入理解Burst SIMD自动向量化的底层原理与实战要点。
unity_version: 2021.3+
status: 待验证
validation: Demo验证
related: ["[[【教程】Burst编译器]]", "[[【教程】JobSystem详解]]", "[[【设计原理】ECS为什么快]]", "[[DOTS专题索引]]"]
author: llm
sources:
  - "[[【教程】Burst编译器]]"
  - "[[【设计原理】ECS为什么快]]"
---

# Burst SIMD 原理详解

> DOTS 技术栈 · 深度笔记 | 从硬件到编译器，理解 Burst 性能提升的核心来源。

## 文档定位

Burst 编译器的 [[【教程】Burst编译器|基础教程]] 覆盖了 API 用法，本文深入 SIMD（Single Instruction, Multiple Data）的底层原理：CPU 向量寄存器、Burst → LLVM 编译流水线、内存布局对向量化的影响，以及实战中的无分支编程技巧。

---

## 1. SIMD 是什么？

**SIMD**（Single Instruction, Multiple Data）是一种 CPU 并行计算模型——一条指令同时处理多个数据元素。

### SISD vs SIMD 对比

```
┌─────────────────────────────────────────────┐
│           SISD（传统标量运算）                 │
│  指令: ADD                                   │
│  A[0] + B[0] → C[0]   1条指令算1个数据        │
│  A[1] + B[1] → C[1]   再1条指令               │
│  A[2] + B[2] → C[2]   再1条指令               │
│  A[3] + B[3] → C[3]   再1条指令               │
├─────────────────────────────────────────────┤
│           SIMD（向量运算）                    │
│  指令: ADDPS (一条打包加法指令)                │
│  [A[0],A[1],A[2],A[3]]                      │
│  + [B[0],B[1],B[2],B[3]]                    │
│  = [C[0],C[1],C[2],C[3]]  1条指令算4个        │
└─────────────────────────────────────────────┘
```

**核心思想**：将多个数据"打包"进一个宽寄存器，用一条 CPU 指令同时运算。

---

## 2. CPU 硬件基础：向量寄存器

现代 CPU 有专门的**宽寄存器**，这是 SIMD 的物理基础：

| 指令集 | 寄存器宽度 | float 能装几个 | 典型平台 |
|--------|-----------|---------------|---------|
| SSE (128-bit) | 16 字节 | 4 个 float | PC (x86-64) |
| AVX (256-bit) | 32 字节 | 8 个 float | 现代 PC/服务器 |
| AVX-512 (512-bit) | 64 字节 | 16 个 float | 高端服务器 |
| NEON (128-bit) | 16 字节 | 4 个 float | 移动端 ARM |

### 128-bit SSE 寄存器结构

```
       128-bit SSE 寄存器 (XMM0)
┌──────┬──────┬──────┬──────┐
│float │float │float │float │   ← 4个32位浮点数打包在一起
│ 32bit│ 32bit│ 32bit│ 32bit│
└──────┴──────┴──────┴──────┘
```

对应的 CPU 指令（以 x86 为例）：

- `ADDPS` — 打包单精度加法（4 个 float 同时加）
- `MULPS` — 打包乘法
- `SQRTPS` — 打包开方
- `CMPLTPS` — 打包比较（生成掩码）

Burst 根据目标平台自动选择最优指令集：PC 上用 SSE/AVX，移动端用 NEON。

---

## 3. Burst SIMD 的两个层面

### 3.1 自动向量化（Auto-Vectorization）

Burst 编译器分析你的循环，**自动**将标量运算重写为向量运算——你不需要写任何特殊代码。

```csharp
[BurstCompile]
public struct VectorAddJob : IJobParallelFor
{
    [ReadOnly] public NativeArray<float> a;
    [ReadOnly] public NativeArray<float> b;
    public NativeArray<float> result;

    public void Execute(int i)
    {
        result[i] = a[i] + b[i];  // 你写的是标量代码
    }
}
```

**Burst 编译器内部做了什么**：

```
你的 C# 代码              Burst 中间表示(LLVM IR)         最终机器码(SSE)
────────────              ──────────────────           ────────────────
for (i=0..N)              vector.body:                 movaps xmm0, [a+i*4]
  result[i] =             %wide = load <4 x float>      addps  xmm0, [b+i*4]
    a[i] + b[i]           %sum = fadd <4 x float>       movaps [result+i*4], xmm0
                          store <4 x float> %sum        ;; 一条指令处理了4个元素！
```

**自动向量化的触发条件**：

1. **循环体无分支依赖**（或分支可用掩码处理）
2. **数据连续内存布局**（`NativeArray<float>`，而非 `List<float>`）
3. **无数据依赖冲突**（每个迭代独立，`result[i]` 不依赖 `result[i-1]`）
4. **循环次数可推断**（有明确的上界）

### 3.2 显式向量类型（手动 SIMD）

使用 `Unity.Mathematics` 的向量类型，直接告诉编译器用 SIMD：

```csharp
using Unity.Mathematics;

// float4 本质上就是占满一个 128-bit SSE 寄存器
float4 a = new float4(1, 2, 3, 4);
float4 b = new float4(5, 6, 7, 8);
float4 c = a + b;  // 一条 ADDPS 指令完成 4 个加法
// c = (6, 8, 10, 12)
```

常用 SIMD 类型：

| 类型 | 大小 | 对应寄存器 | 用途 |
|------|------|-----------|------|
| `float4` | 16 字节 | 1×XMM | 位置、颜色 RGBA |
| `float3` | 12 字节 | 1×XMM（尾数浪费） | 3D 坐标 |
| `float4x4` | 64 字节 | 4×XMM | 变换矩阵 |
| `int4` | 16 字节 | 1×XMM | 整数向量 |
| `bool4` | 16 字节 | 1×XMM | 掩码运算 |

---

## 4. 内存布局对 SIMD 的关键影响

SIMD 要求数据**连续对齐**，否则性能大打折扣。

### SoA vs AoS

```
✅ 理想布局 — Structure of Arrays (SoA)
position_x: [x0, x1, x2, x3, x4, x5, x6, x7, ...]
position_y: [y0, y1, y2, y3, y4, y5, y6, y7, ...]
position_z: [z0, z1, z2, z3, z4, z5, z6, z7, ...]
             ←—— 一条指令加载 4 个连续 x ——→

❌ 糟糕布局 — Array of Structures (AoS)
entities: [{x0,y0,z0}, {x1,y1,z1}, {x2,y2,z2}, ...]
          // 加载 4 个 x 需要跨 stride 跳跃，无法用一条指令
```

**ECS 的 Chunk 架构天然适配 SIMD**——ECS 将同一组件的相同字段连续存储（SoA），Burst 可以完美进行向量化加载。这也是 [[【设计原理】ECS为什么快|ECS 为什么快]] 的核心原因之一。

---

## 5. Burst 完整编译流水线

```
你的 C# Job 代码
      │
      ▼
┌──────────────┐
│  C# → IL     │  Roslyn 编译器（标准 C# 编译）
└──────┬───────┘
       │ IL 字节码
       ▼
┌──────────────┐
│  IL → LLVM IR │  Burst 前端翻译
│  （此处进行    │  · 类型检查（只允许 blittable）
│   循环分析）   │  · 依赖分析
└──────┬───────┘  · 向量化可行性判断
       │ LLVM IR
       ▼
┌──────────────┐
│  LLVM 优化    │  ← 核心阶段
│  · 循环展开   │  · auto-vectorization pass
│  · 自动向量化 │  · 内联 Unity.Mathematics 函数
│  · 指令合并   │  · 常量折叠
└──────┬───────┘
       │ 优化后 LLVM IR
       ▼
┌──────────────┐
│  后端代码生成  │  目标平台不同，指令集不同
│  x86: SSE/AVX│  ARM: NEON
│  生成机器码   │
└──────┬───────┘
       │
       ▼
   原生机器码（无需 JIT，直接执行）
```

关键点：Burst 使用 **LLVM** 后端，这意味着它拥有工业级编译器的全部优化能力，包括循环展开、指令调度、寄存器分配等，不仅仅是"把 C# 编译成机器码"。

---

## 6. 实战要点

### 6.1 用 `Unity.Mathematics` 替代 `UnityEngine.Mathf`

```csharp
// ❌ Mathf 无法被 Burst 向量化
result[i] = Mathf.Sqrt(data[i]);

// ✅ math 库内联后可以被向量化
result[i] = math.sqrt(data[i]);
```

`Unity.Mathematics` 的函数被标记为 `[MethodImpl(AggressiveInlining)]`，Burst 内联后可直接映射到一条 SIMD 指令（如 `SQRTPS`）。

### 6.2 `FloatMode.Fast` 允许更激进的向量化

```csharp
// IEEE 754 严格模式：加法顺序不能变（阻止向量化）
//   因为浮点加法不满足结合律：(a+b)+c ≠ a+(b+c)

// Fast 模式：允许重排 → 循环可以被向量化
[BurstCompile(FloatMode = FloatMode.Fast)]
public struct FastSimdJob : IJobParallelFor { ... }
```

### 6.3 避免分支（if/else）破坏向量化

```csharp
// ❌ 分支导致向量化失败（需要 mask 处理）
if (value > threshold)
    result[i] = a[i];
else
    result[i] = b[i];

// ✅ 用 math.select 替代分支 → 无分支 SIMD
result[i] = math.select(b[i], a[i], value > threshold);
// CPU 的 SIMD 比较生成掩码，select 用掩码混合两个向量
```

更多无分支技巧：

```csharp
// math.max / math.min — 无分支的极值
result[i] = math.max(a[i], b[i]);

// math.step — 阶跃函数（x < edge ? 0 : 1）
result[i] = math.step(threshold, value);

// math.lerp — 线性插值（可被向量化）
result[i] = math.lerp(a[i], b[i], t[i]);
```

### 6.4 内存对齐访问

```csharp
// NativeArray 默认 16 字节对齐 → SSE 完美命中
// 如果用 unsafe 指针，确保起始地址对齐
float* ptr = (float*)UnsafeUtility.Malloc(size, 16, Allocator.Persistent);
//                                          ^^ 对齐到 16 字节
```

未对齐的内存访问在 x86 上会触发性能惩罚（或 AVX 下的 `#GP` 异常）。

### 6.5 用 Burst Inspector 验证 SIMD 生效

```
菜单: Jobs > Burst > Open Inspector
```

在 Inspector 中找到对应 Job，查看生成的汇编代码：

- 出现 `addps` / `mulps` / `sqrtps` → SSE 向量化成功
- 出现 `vaddps` / `vmulps` (VEX 前缀) → AVX 向量化成功
- 只看到标量指令 `addss` / `mulss` → 向量化失败，检查上述条件

---

## 7. 总结

| 层面 | 你做什么 | Burst 做什么 |
|------|---------|-------------|
| **自动向量化** | 写普通的标量循环 | 分析循环 → 自动打包成 SIMD |
| **显式 SIMD** | 用 `float4`/`math` 类型 | 直接映射到 SIMD 指令 |
| **内存布局** | 用 ECS / SoA 布局 | 连续加载，一条指令处理多数据 |
| **无分支编程** | 用 `math.select` 替代 if | 生成掩码运算，保持向量化 |

**一句话总结**：Burst SIMD = 利用 CPU 宽寄存器 + 连续内存布局 + LLVM 自动向量化，让一条 CPU 指令同时处理 4~16 个数据，这是 DOTS 性能提升的核心来源之一。

---

## 相关链接

- [[【教程】Burst编译器]] — Burst API 用法教程（属性、类型、SharedStatic、FunctionPointer）
- [[【教程】JobSystem详解]] — 多线程 Job 调度
- [[【设计原理】ECS为什么快]] — ECS 内存布局与缓存命中原理
- [Burst 官方文档](https://docs.unity3d.com/Packages/com.unity.burst@latest)
- [LLVM Auto-Vectorization 文档](https://llvm.org/docs/Vectorizers.html)
