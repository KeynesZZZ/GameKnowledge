# 最佳实践 - GC优化清单

> 减少GC触发，提升游戏流畅度 `#性能优化` `#内存管理` `#最佳实践`

## GC基础

### 什么是GC？

垃圾回收（Garbage Collection）自动回收不再使用的内存。Unity使用Boehm GC，非分代、非压缩。

### GC触发时机

1. **显式调用**: `GC.Collect()`
2. **内存不足**: 堆内存达到阈值
3. **分配失败**: 无法找到足够连续内存

### GC影响

| 场景 | GC耗时 | 表现 |
|------|--------|------|
| 小型GC | 1-5ms | 轻微卡顿 |
| 中型GC | 5-20ms | 明显卡顿 |
| 大型GC | 50-200ms | 严重掉帧 |

---

## 优化清单

### 1. 字符串优化

#### ❌ 避免

```csharp
// 每帧拼接字符串 - 产生大量GC
void Update()
{
    string info = "Score: " + score + " Level: " + level;
    text.text = info;
}

// 使用 + 拼接
string result = a + b + c + d;

// 字符串比较
if (tag == "Player") { }
```

#### ✅ 推荐

```csharp
// 使用StringBuilder
private System.Text.StringBuilder sb = new();

void Update()
{
    sb.Clear();
    sb.Append("Score: ").Append(score).Append(" Level: ").Append(level);
    text.text = sb.ToString();
}

// 使用字符串插值（编译时优化）
string result = $"{a}{b}{c}{d}";

// 使用CompareTag
if (CompareTag("Player")) { }

// 缓存字符串
private static readonly string[] NumberStrings = { "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" };
```

### 2. 集合优化

#### ❌ 避免

```csharp
// 每帧new集合
void Update()
{
    var list = new List<int>();  // GC!
    // ...
}

// 频繁Clear和Add
list.Clear();
for (int i = 0; i < 100; i++)
{
    list.Add(i);  // 可能触发扩容
}

// 使用LINQ
var result = list.Where(x => x > 5).ToList();  // GC!
```

#### ✅ 推荐

```csharp
// 缓存集合
private List<int> cachedList = new(100);  // 预设容量

void Update()
{
    cachedList.Clear();  // 不释放内存
    // ...
}

// 预设容量
var list = new List<int>(100);
var dict = new Dictionary<int, string>(50);

// 避免LINQ，使用for循环
for (int i = 0; i < list.Count; i++)
{
    if (list[i] > 5)
    {
        // 处理
    }
}

// 使用ArrayPool
using System.Buffers;
var array = ArrayPool<int>.Shared.Rent(100);
try
{
    // 使用array
}
finally
{
    ArrayPool<int>.Shared.Return(array);
}
```

### 3. 装箱拆箱

#### ❌ 避免

```csharp
// 装箱
object boxed = 123;  // GC!
int value = (int)boxed;  // 拆箱

// 方法参数装箱
void Log(object message) { }
Log(123);  // 装箱!

// 枚举装箱
enum State { A, B }
State s = State.A;
object o = s;  // 装箱!

// ArrayList
var list = new ArrayList();
list.Add(123);  // 装箱!
```

#### ✅ 推荐

```csharp
// 使用泛型
void Log<T>(T message) { }
Log(123);  // 无装箱

// 使用泛型集合
var list = new List<int>();
list.Add(123);  // 无装箱

// 避免object参数
void LogInt(int message) { }
void LogString(string message) { }

// 使用枚举泛型方法
State s = State.A;
int value = (int)s;  // 直接转换，无装箱
```

### 4. 委托与事件

#### ❌ 避免

```csharp
// 每帧new委托
void Update()
{
    button.onClick.AddListener(OnClick);  // GC!
}

// Lambda捕获
int count = 0;
Func<int> getCount = () => count;  // GC! (闭包)

// 匿名方法
list.ForEach(x => Debug.Log(x));  // GC!
```

#### ✅ 推荐

```csharp
// 缓存委托
private Action onClick;

void Awake()
{
    onClick = OnClick;
    button.onClick.AddListener(onClick);
}

// 避免闭包，使用类成员
private int count;
private int GetCount() => count;

// 使用for循环代替ForEach
for (int i = 0; i < list.Count; i++)
{
    Debug.Log(list[i]);
}
```

### 5. 协程优化

#### ❌ 避免

```csharp
// 每次new WaitForSeconds
IEnumerator Loop()
{
    while (true)
    {
        yield return new WaitForSeconds(1f);  // GC!
    }
}

// yield return 字符串
yield return "levelLoaded";  // GC!

// 使用new创建WaitUntil
yield return new WaitUntil(() => ready);  // GC!
```

#### ✅ 推荐

```csharp
// 缓存WaitForSeconds
private WaitForSeconds waitOneSecond = new(1f);

IEnumerator Loop()
{
    while (true)
    {
        yield return waitOneSecond;  // 无GC
    }
}

// 使用WaitForSecondsRealtime（需要new但不受Time.scale影响）
private WaitForSecondsRealtime waitRealtime = new(1f);

// 使用自定义WaitUntil缓存
private WaitUntil waitUntilReady;

void Awake()
{
    waitUntilReady = new WaitUntil(() => ready);
}

IEnumerator MyCoroutine()
{
    yield return waitUntilReady;
}
```

### 6. 资源加载

#### ❌ 避免

```csharp
// 每次加载相同资源
void Spawn()
{
    var prefab = Resources.Load<GameObject>("Enemy");  // 重复加载
    Instantiate(prefab);
}

// 同步加载大资源
var asset = Resources.Load<GameObject>("BigAsset");  // 阻塞主线程
```

#### ✅ 推荐

```csharp
// 缓存加载的资源
private GameObject enemyPrefab;

void Awake()
{
    enemyPrefab = Resources.Load<GameObject>("Enemy");
}

void Spawn()
{
    Instantiate(enemyPrefab);
}

// 使用Addressables异步加载
Addressables.LoadAssetAsync<GameObject>("Enemy").Completed += handle =>
{
    enemyPrefab = handle.Result;
};

// 使用对象池
public class EnemyPool
{
    private Stack<GameObject> pool = new();

    public GameObject Get()
    {
        if (pool.Count > 0)
            return pool.Pop();
        return Instantiate(enemyPrefab);
    }

    public void Return(GameObject go)
    {
        go.SetActive(false);
        pool.Push(go);
    }
}
```

### 7. Unity API优化

#### ❌ 避免

```csharp
// 每帧获取组件
void Update()
{
    var rb = GetComponent<Rigidbody>();  // GC!
    rb.velocity = velocity;
}

// 每帧访问属性
void Update()
{
    var name = gameObject.name;  // GC! (string属性)
    var tag = gameObject.tag;    // GC!
}

// 使用Find
void Start()
{
    var player = GameObject.Find("Player");  // 慢!
}
```

#### ✅ 推荐

```csharp
// 缓存组件
private Rigidbody rb;

void Awake()
{
    rb = GetComponent<Rigidbody>();
}

void Update()
{
    rb.velocity = velocity;
}

// 缓存常用属性
private string cachedName;
private bool isTagCached;

// 使用CompareTag
if (CompareTag("Player")) { }  // 无GC

// 使用FindObjectOfType缓存
private static Player player;

public static Player Player
{
    get
    {
        if (player == null)
            player = FindObjectOfType<Player>();
        return player;
    }
}
```

### 8. 数组优化

#### ❌ 避免

```csharp
// 每帧new数组
void Update()
{
    var array = new int[100];  // GC!
}

// 多维数组访问
int[,] multiArray = new int[10, 10];
int value = multiArray[5, 5];  // 稍慢
```

#### ✅ 推荐

```csharp
// 缓存数组
private int[] cachedArray = new int[100];

// 使用锯齿数组（性能更好）
int[][] jaggedArray = new int[10][];
for (int i = 0; i < 10; i++)
{
    jaggedArray[i] = new int[10];
}
int value = jaggedArray[5][5];  // 更快
```

---

## GC检测工具

### Unity Profiler

```
1. Window > Analysis > Profiler
2. 选择 GC Alloc 列
3. 深色模式查看每帧分配
```

### 代码检测

```csharp
// 运行时检测GC
long before = GC.GetTotalMemory(false);

// 执行代码
DoSomething();

long after = GC.GetTotalMemory(false);
long allocated = after - before;

if (allocated > 0)
{
    Debug.Log($"Allocated: {allocated} bytes");
}
```

### 自动化检测

```csharp
// 编辑器模式下的GC检测
#if UNITY_EDITOR
[UnityEditor.MenuItem("Debug/Check GC Allocations")]
static void CheckGCAllocations()
{
    var go = new GameObject("Test");
    var before = GC.GetTotalMemory(false);

    // 测试代码
    var component = go.AddComponent<TestComponent>();

    var after = GC.GetTotalMemory(false);
    Debug.Log($"GC Allocation: {after - before} bytes");

    DestroyImmediate(go);
}
#endif
```

---

## 优化检查清单

### 每帧执行代码

- [ ] 无字符串拼接
- [ ] 无new对象
- [ ] 无LINQ使用
- [ ] 无GetComponent调用
- [ ] 无Resources.Load
- [ ] 无委托创建
- [ ] 无闭包捕获

### 初始化代码

- [ ] 集合预设容量
- [ ] 组件缓存完成
- [ ] 资源预加载
- [ ] 对象池预热

### 事件处理

- [ ] 使用struct事件数据
- [ ] 及时取消订阅
- [ ] 无循环事件

---

## 相关链接

- 深入学习: [Unity内存管理](../../35_高级主题/教程-Unity内存管理.md)
- 踩坑记录: [内存泄漏模式](踩坑记录-内存泄漏模式.md)
- 性能数据: [字符串拼接方式对比](性能数据-字符串拼接方式对比.md)
