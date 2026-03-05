---
title: 【教程】C#高级特性
tags: [C#, Unity, 高级编程, C#特性, 教程]
category: 高级编程
created: 2026-03-05 08:41
updated: 2026-03-05 08:41
description: C#语言高级特性详解
unity_version: 2021.3+
---
# C# 高级特性

> 第1课 | 高级编程模块

## 1. async/await 异步编程

### 1.1 基础概念

```csharp
// 同步方法
public int GetData()
{
    Thread.Sleep(1000);  // 阻塞线程
    return 42;
}

// 异步方法
public async Task<int> GetDataAsync()
{
    await Task.Delay(1000);  // 不阻塞线程
    return 42;
}
```

### 1.2 状态机原理

编译器将 async 方法转换为状态机：

```csharp
// 原始代码
public async Task<int> GetValueAsync()
{
    int a = await GetValueA();
    int b = await GetValueB();
    return a + b;
}

// 编译器生成的状态机（简化）
private struct GetValueAsyncStateMachine : IAsyncStateMachine
{
    public int a;
    public int b;
    public int result;
    public int state;

    public void MoveNext()
    {
        switch (state)
        {
            case 0:
                state = 1;
                // await GetValueA()
                return;
            case 1:
                a = /* GetValueA 的结果 */;
                state = 2;
                // await GetValueB()
                return;
            case 2:
                b = /* GetValueB 的结果 */;
                result = a + b;
                // 完成
                break;
        }
    }
}
```

### 1.3 Task 与 ValueTask

```csharp
// Task - 引用类型，有分配开销
public async Task<int> ComputeAsync()
{
    await Task.Delay(100);
    return 42;
}

// ValueTask - 值类型，避免分配（适用于同步路径）
public ValueTask<int> ComputeValueAsync()
{
    if (cachedResult.HasValue)
        return new ValueTask<int>(cachedResult.Value);  // 同步返回，无分配

    return new ValueTask<int>(ComputeInternalAsync());
}
```

### 1.4 CancellationToken

```csharp
public async Task LoadDataAsync(CancellationToken ct)
{
    for (int i = 0; i < 100; i++)
    {
        ct.ThrowIfCancellationRequested();  // 检查取消
        await ProcessItemAsync(i, ct);
    }
}

// 使用
using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
try
{
    await LoadDataAsync(cts.Token);
}
catch (OperationCanceledException)
{
    Debug.Log("操作超时取消");
}
```

### 1.5 ConfigureAwait

```csharp
// Unity 中通常不需要 ConfigureAwait(false)
// 因为 Unity 的同步上下文会自动处理

// 在库代码中
public async Task<string> FetchDataAsync()
{
    // 不需要回到原上下文，提高性能
    var data = await httpClient.GetStringAsync(url).ConfigureAwait(false);
    return ProcessData(data);
}
```

### 1.6 Unity 中的异步最佳实践

```csharp
// ❌ 错误：async void
public async void LoadScene()  // 异常无法捕获
{
    await SceneManager.LoadSceneAsync("Game");
}

// ✅ 正确：async Task
public async Task LoadSceneAsync()
{
    await SceneManager.LoadSceneAsync("Game");
}

// ✅ 使用 UniTask（推荐）
public async UniTask LoadSceneUniTask()
{
    await SceneManager.LoadSceneAsync("Game").ToUniTask();
}
```

---

## 2. 反射与元数据

### 2.1 Type 类

```csharp
// 获取 Type
Type type1 = typeof(MyClass);
Type type2 = myObject.GetType();
Type type3 = Type.GetType("MyNamespace.MyClass");

// 类型信息
Debug.Log(type.Name);           // "MyClass"
Debug.Log(type.Namespace);      // "MyNamespace"
Debug.Log(type.Assembly);       // 所在程序集
Debug.Log(type.BaseType);       // 基类
Debug.Log(type.IsClass);        // 是否是类
Debug.Log(type.IsValueType);    // 是否是值类型
Debug.Log(type.IsAbstract);     // 是否是抽象类
```

### 2.2 获取成员信息

```csharp
Type type = typeof(MyClass);

// 字段
FieldInfo[] fields = type.GetFields(BindingFlags.Public | BindingFlags.Instance);
FieldInfo privateField = type.GetField("privateField", BindingFlags.NonPublic | BindingFlags.Instance);

// 属性
PropertyInfo[] properties = type.GetProperties();
PropertyInfo nameProp = type.GetProperty("Name");

// 方法
MethodInfo[] methods = type.GetMethods();
MethodInfo doSomething = type.GetMethod("DoSomething");

// 构造函数
ConstructorInfo[] constructors = type.GetConstructors();
ConstructorInfo ctor = type.GetConstructor(new[] { typeof(int), typeof(string) });
```

### 2.3 动态调用

```csharp
// 创建实例
Type type = typeof(MyClass);
object instance = Activator.CreateInstance(type);
object instanceWithArgs = Activator.CreateInstance(type, 42, "test");

// 调用方法
MethodInfo method = type.GetMethod("DoSomething");
method.Invoke(instance, new object[] { "parameter" });

// 获取/设置属性
PropertyInfo prop = type.GetProperty("Name");
object value = prop.GetValue(instance);
prop.SetValue(instance, "New Name");

// 获取/设置字段
FieldInfo field = type.GetField("privateField", BindingFlags.NonPublic | BindingFlags.Instance);
field.SetValue(instance, 123);
```

### 2.4 特性（Attribute）

```csharp
// 定义特性
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public class MyAttribute : Attribute
{
    public string Name { get; }
    public int Priority { get; set; }

    public MyAttribute(string name)
    {
        Name = name;
    }
}

// 使用特性
[My("Test", Priority = 10)]
public class TestClass
{
    [My("Method")]
    public void DoSomething() { }
}

// 读取特性
Type type = typeof(TestClass);
var attr = type.GetCustomAttribute<MyAttribute>();
Debug.Log($"{attr.Name}, Priority: {attr.Priority}");
```

### 2.5 性能优化：缓存反射结果

```csharp
// ❌ 每次都反射
public void ProcessBad(object obj)
{
    var type = obj.GetType();
    var method = type.GetMethod("Process");  // 每次都查找
    method.Invoke(obj, null);
}

// ✅ 缓存反射结果
private static readonly Dictionary<Type, MethodInfo> _methodCache = new();

public void ProcessGood(object obj)
{
    var type = obj.GetType();

    if (!_methodCache.TryGetValue(type, out var method))
    {
        method = type.GetMethod("Process");
        _methodCache[type] = method;
    }

    method.Invoke(obj, null);
}
```

---

## 3. Expression 表达式树

### 3.1 基础概念

```csharp
// 简单表达式
Expression<Func<int, int>> expr = x => x * 2;

// 手动构建表达式
ParameterExpression param = Expression.Parameter(typeof(int), "x");
BinaryExpression multiply = Expression.Multiply(param, Expression.Constant(2));
Expression<Func<int, int>> expr2 = Expression.Lambda<Func<int, int>>(multiply, param);

// 编译执行
Func<int, int> func = expr.Compile();
int result = func(5);  // 10
```

### 3.2 高性能属性访问

```csharp
public static class PropertyAccessorFactory
{
    // 缓存编译后的访问器
    private static readonly Dictionary<Type, Dictionary<string, Delegate>> _cache = new();

    public static Func<T, TValue> CreateGetter<T, TValue>(string propertyName)
    {
        var type = typeof(T);

        if (_cache.TryGetValue(type, out var typeCache) &&
            typeCache.TryGetValue(propertyName, out var cached))
        {
            return (Func<T, TValue>)cached;
        }

        // 构建表达式：obj => (TValue)obj.PropertyName
        var param = Expression.Parameter(typeof(T), "obj");
        var property = Expression.Property(param, propertyName);
        var convert = Expression.Convert(property, typeof(TValue));
        var lambda = Expression.Lambda<Func<T, TValue>>(convert, param);

        var getter = lambda.Compile();

        // 缓存
        if (!_cache.ContainsKey(type))
            _cache[type] = new Dictionary<string, Delegate>();
        _cache[type][propertyName] = getter;

        return getter;
    }
}

// 使用：比反射快 10-100 倍
var getter = PropertyAccessorFactory.CreateGetter<MyClass, string>("Name");
string name = getter(myObject);
```

### 3.3 对象映射器实现

```csharp
public static class Mapper
{
    public static Func<TSource, TDest> CreateMapFunc<TSource, TDest>()
        where TDest : new()
    {
        var sourceParam = Expression.Parameter(typeof(TSource), "src");
        var destVar = Expression.Variable(typeof(TDest), "dest");

        var statements = new List<Expression>
        {
            Expression.Assign(destVar, Expression.New(typeof(TDest)))
        };

        // 匹配同名属性
        var sourceProps = typeof(TSource).GetProperties();
        var destProps = typeof(TDest).GetProperties();

        foreach (var sp in sourceProps)
        {
            var dp = Array.Find(destProps, p => p.Name == sp.Name && p.PropertyType == sp.PropertyType);
            if (dp != null && dp.CanWrite)
            {
                var sourceAccess = Expression.Property(sourceParam, sp);
                var destAccess = Expression.Property(destVar, dp);
                statements.Add(Expression.Assign(destAccess, sourceAccess));
            }
        }

        statements.Add(destVar);

        var body = Expression.Block(new[] { destVar }, statements);
        return Expression.Lambda<Func<TSource, TDest>>(body, sourceParam).Compile();
    }
}

// 使用
var mapFunc = Mapper.CreateMapFunc<UserDTO, UserEntity>();
UserEntity entity = mapFunc(dto);  // 高性能映射
```

---

## 4. Span 与 Memory

### 4.1 Span<T> 基础

```csharp
// 从数组创建
int[] array = { 1, 2, 3, 4, 5 };
Span<int> span = array.AsSpan();
Span<int> slice = array.AsSpan(1, 3);  // [2, 3, 4]

// 栈上分配
Span<int> stackSpan = stackalloc int[100];  // 无堆分配

// 修改数据
span[0] = 10;  // 原数组也会被修改

// 遍历
foreach (var item in span)
{
    Console.WriteLine(item);
}
```

### 4.2 高性能字符串处理

```csharp
// ❌ 传统方式：产生大量字符串
public static int SumNumbersBad(string input)
{
    var parts = input.Split(',');  // 分配字符串数组
    int sum = 0;
    foreach (var part in parts)
    {
        sum += int.Parse(part);  // 每个部分分配新字符串
    }
    return sum;
}

// ✅ 使用 Span：零分配
public static int SumNumbersGood(ReadOnlySpan<char> input)
{
    int sum = 0;
    while (input.Length > 0)
    {
        int commaIndex = input.IndexOf(',');
        if (commaIndex == -1)
        {
            sum += int.Parse(input);
            break;
        }

        sum += int.Parse(input.Slice(0, commaIndex));
        input = input.Slice(commaIndex + 1);
    }
    return sum;
}
```

### 4.3 ArrayPool<T>

```csharp
using System.Buffers;

// ❌ 每次分配新数组
public void ProcessBad(int size)
{
    var buffer = new byte[size];  // 堆分配
    Process(buffer);
    // buffer 被 GC 回收
}

// ✅ 使用数组池
public void ProcessGood(int size)
{
    var buffer = ArrayPool<byte>.Shared.Rent(size);  // 从池中租用
    try
    {
        Process(buffer.AsSpan(0, size));  // 注意：实际大小可能大于 size
    }
    finally
    {
        ArrayPool<byte>.Shared.Return(buffer);  // 归还到池
    }
}
```

### 4.4 Memory<T> 与 IMemoryOwner

```csharp
// Memory<T> 可以存储在堆上（异步场景）
public async Task ProcessAsync(Memory<byte> buffer)
{
    await SomeAsyncOperation(buffer);  // 可以跨 await
}

// IMemoryOwner 管理内存生命周期
public IMemoryOwner<byte> AllocateBuffer(int size)
{
    return MemoryPool<byte>.Shared.Rent(size);
}

// 使用
using var owner = AllocateBuffer(1024);
Memory<byte> buffer = owner.Memory;
await ProcessAsync(buffer);
// 自动释放
```

---

## 本课小结

### 核心知识点

| 知识点 | 用途 | 性能影响 |
|--------|------|----------|
| async/await | 异步编程 | 状态机开销 |
| Task vs ValueTask | 任务表示 | ValueTask 减少分配 |
| 反射 | 运行时类型检查 | 较慢，需缓存 |
| Expression | 编译时生成代码 | 编译慢，执行快 |
| Span<T> | 零分配内存操作 | 极快 |
| ArrayPool | 数组复用 | 减少 GC |

### 性能对比

| 操作 | 传统方式 | 优化后 | 提升 |
|------|----------|--------|------|
| 属性访问 | 反射: ~1000ns | Expression: ~10ns | 100x |
| 字符串解析 | Split: ~500ns | Span: ~50ns | 10x |
| 临时数组 | new: GC压力 | ArrayPool: 无GC | ∞ |

---

## 延伸阅读

- [C# in Depth](https://csharpindepth.com/)
- [Span<T> 性能指南](https://docs.microsoft.com/en-us/dotnet/standard/memory-and-spans/)
- [Expression Trees](https://docs.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/expression-trees/)
