# Burst Compiler 详解

> 第2课 | DOTS 技术栈模块

## 1. 什么是 Burst？

**Burst** 是 Unity 的高性能编译器，将 C# 编译为高度优化的原生机器码。

### 优势

- **10-100x 性能提升**
- **自动 SIMD 向量化**
- **零 GC 分配**
- **跨平台优化**

---

## 2. 基础使用

### 2.1 启用 Burst

```csharp
using Unity.Burst;

[BurstCompile]
public struct MyJob : IJob
{
    public NativeArray<float> data;

    public void Execute()
    {
        for (int i = 0; i < data.Length; i++)
        {
            data[i] = data[i] * 2.0f;
        }
    }
}
```

### 2.2 BurstCompile 属性

```csharp
[BurstCompile]
public struct BasicJob : IJob { }

// 带选项
[BurstCompile(FloatMode = FloatMode.Fast, FloatPrecision = FloatPrecision.Standard)]
public struct FastMathJob : IJob { }

// 指定编译目标
[BurstCompile(FloatMode = FloatMode.Fast, CompileSynchronously = true)]
public struct SyncJob : IJob { }
```

### 2.3 FloatMode 选项

| 模式 | 说明 | 性能 |
|------|------|------|
| Default | 标准 IEEE 754 | 标准 |
| Fast | 允许优化（可能损失精度） | 更快 |
| Strict | 严格 IEEE 754 兼容 | 最慢 |

```csharp
[BurstCompile(FloatMode = FloatMode.Fast)]
public struct FastFloatJob : IJobParallelFor
{
    public NativeArray<float> data;

    public void Execute(int index)
    {
        // Fast 模式下可以优化
        data[index] = Mathf.Sqrt(data[index]);
    }
}
```

---

## 3. Burst 支持的类型

### 3.1 支持的类型

```csharp
[BurstCompile]
public struct SupportedTypesJob : IJob
{
    // 基本类型
    public bool b;
    public byte by;
    public sbyte sb;
    public short s;
    public ushort us;
    public int i;
    public uint ui;
    public long l;
    public ulong ul;
    public float f;
    public double d;

    // Unity 类型
    public Vector2 v2;
    public Vector3 v3;
    public Vector4 v4;
    public Quaternion q;
    public Matrix4x4 m;
    public Color c;
    public Bounds bnds;

    // 指针（unsafe）
    public int* ptr;

    // NativeContainer
    public NativeArray<int> array;
    public NativeList<int> list;
    public NativeHashMap<int, int> map;

    public void Execute() { }
}
```

### 3.2 不支持的类型

```csharp
[BurstCompile]
public struct UnsupportedTypesJob : IJob
{
    // ❌ 不支持
    // public string text;           // 引用类型
    // public object obj;            // 装箱
    // public int[] managedArray;    // 托管数组
    // public List<int> list;        // 托管 List
    // public delegate Func<int> f;  // 委托

    public void Execute() { }
}
```

---

## 4. SIMD 向量化

### 4.1 自动向量化

```csharp
[BurstCompile]
public struct AutoVectorizationJob : IJobParallelFor
{
    public NativeArray<float> a;
    public NativeArray<float> b;
    public NativeArray<float> result;

    public void Execute(int index)
    {
        // Burst 自动使用 SIMD 指令
        result[index] = a[index] + b[index];
    }
}
```

### 4.2 手动 SIMD

```csharp
using Unity.Mathematics;
using Unity.Burst;

[BurstCompile]
public struct ManualSimdJob : IJobParallelFor
{
    [ReadOnly] public NativeArray<float4> positions;
    public NativeArray<float4> velocities;

    public void Execute(int index)
    {
        // float4 = 4 个 float 同时处理
        float4 pos = positions[index];
        float4 vel = velocities[index];

        velocities[index] = pos + vel;  // 一条指令处理 4 个值
    }
}
```

### 4.3 math 库

```csharp
using Unity.Mathematics;

[BurstCompile]
public struct MathLibraryJob : IJob
{
    public NativeArray<float3> positions;
    public float3 center;
    public float radius;

    public void Execute()
    {
        for (int i = 0; i < positions.Length; i++)
        {
            float3 pos = positions[i];

            // 使用 math 库（Burst 优化）
            float dist = math.distance(pos, center);
            float3 dir = math.normalize(pos - center);

            if (dist > radius)
            {
                positions[i] = center + dir * radius;
            }
        }
    }
}
```

---

## 5. SharedStatic

### 5.1 静态数据共享

```csharp
using Unity.Burst;
using Unity.Collections;

public class SharedData
{
    // 静态数据，所有 Job 共享
    public static readonly SharedStatic<int> GlobalCounter = SharedStatic<int>.GetOrCreate<SharedData>();

    [BurstCompile]
    public struct IncrementJob : IJob
    {
        public void Execute()
        {
            // 原子递增
            int newValue = SharedData.GlobalCounter.Data + 1;
            SharedData.GlobalCounter.Data = newValue;
        }
    }
}
```

---

## 6. Function Pointers

### 6.1 Burst 函数指针

```csharp
using Unity.Burst;
using Unity.Collections;

public class FunctionPointerExample
{
    // 定义函数指针签名
    public delegate int BinaryOp(int a, int b);

    // Burst 编译的函数
    [BurstCompile]
    public static int Add(int a, int b) => a + b;

    [BurstCompile]
    public static int Multiply(int a, int b) => a * b;

    [BurstCompile]
    public struct UseFunctionPointerJob : IJob
    {
        public FunctionPointer<BinaryOp> operation;
        public NativeArray<int> a;
        public NativeArray<int> b;
        public NativeArray<int> result;

        public void Execute()
        {
            for (int i = 0; i < result.Length; i++)
            {
                result[i] = operation.Invoke(a[i], b[i]);
            }
        }
    }

    public void Run()
    {
        var a = new NativeArray<int>(new[] { 1, 2, 3 }, Allocator.TempJob);
        var b = new NativeArray<int>(new[] { 4, 5, 6 }, Allocator.TempJob);
        var result = new NativeArray<int>(3, Allocator.TempJob);

        // 编译时获取函数指针
        var addPtr = BurstCompiler.CompileFunctionPointer<BinaryOp>(Add);

        var job = new UseFunctionPointerJob
        {
            operation = addPtr,
            a = a,
            b = b,
            result = result
        };

        job.Run();

        Debug.Log($"{result[0]}, {result[1]}, {result[2]}");  // 5, 7, 9

        a.Dispose();
        b.Dispose();
        result.Dispose();
    }
}
```

---

## 7. 调试与分析

### 7.1 Burst Inspector

```
菜单: Jobs > Burst > Open Inspector
```

可以查看：
- 生成的汇编代码
- 编译警告和错误
- 优化信息

### 7.2 编译选项

```csharp
// 强制同步编译（便于调试）
[BurstCompile(CompileSynchronously = true)]
public struct DebugJob : IJob { }

// 禁用优化（调试用）
[BurstCompile(OptimizeFor = OptimizeFor.Debugging)]
public struct DebugOptJob : IJob { }
```

### 7.3 日志输出

```csharp
[BurstCompile]
public struct LoggingJob : IJob
{
    public int value;

    public void Execute()
    {
        // 仅在编辑器和开发构建中输出
        UnityEngine.Debug.Log($"Value: {value}");
    }
}
```

---

## 8. 性能对比

### 8.1 基准测试

```csharp
// 100 万次浮点运算

// 纯 C#（主线程）: ~50ms
// C# + Job System: ~15ms
// C# + Job + Burst: ~1ms
```

### 8.2 实际案例

| 场景 | 无 Burst | 有 Burst | 提升 |
|------|----------|----------|------|
| 粒子更新 (10万) | 8ms | 0.8ms | 10x |
| 碰撞检测 | 12ms | 0.5ms | 24x |
| 矩阵运算 | 20ms | 0.3ms | 66x |
| 路径寻路 | 50ms | 2ms | 25x |

---

## 本课小结

### Burst 属性选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| FloatMode | Default | 浮点优化级别 |
| FloatPrecision | Standard | 浮点精度 |
| CompileSynchronously | false | 同步编译 |
| OptimizeFor | Performance | 优化目标 |

### 最佳实践

1. **始终使用 Burst** - 所有 Job 都加 [BurstCompile]
2. **使用 math 库** - 替代 Mathf
3. **使用 SIMD 类型** - float4, int4 等
4. **避免托管类型** - 只用 blittable 类型
5. **开启 Burst Inspector** - 检查优化效果

---

## 延伸阅读

- [Burst 官方文档](https://docs.unity3d.com/Packages/com.unity.burst@latest)
- [Unity Mathematics](https://docs.unity3d.com/Packages/com.unity.mathematics@latest)
