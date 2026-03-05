---
title: 【教程】Unity脚本生命周期
tags: [C#, Unity, 架构, 教程, MonoBehaviour, 生命周期, Unity基础]
category: 架构设计/教程
created: 2024-01-02 09:00
updated: 2026-03-04 23:00
description: 深入理解Unity脚本生命周期，包含Awake、Start、Update等函数的执行顺序和最佳实践
unity_version: 2021.3+
---

# Unity脚本生命周期深度解析

> 第1课 | 脚本与架构模块

## 文档定位

本文档从**使用角度**讲解Unity脚本生命周期。

**相关文档**：[[【教程】Unity脚本生命周期]]、、

---

## 1. Unity底层如何管理脚本执行

Unity的脚本执行是由**Unity Runtime**管理的，它维护了一个**MonoBehaviour列表**，在每帧的特定时机调用相应的方法。

**核心机制：**
```
游戏循环 (Game Loop)
    │
    ├── 初始化阶段
    │   ├── Awake()    ← 首先调用
    │   ├── OnEnable() ← 对象激活时
    │   └── Start()    ← 第一帧Update之前
    │
    ├── 物理阶段 (Fixed Timestep)
    │   └── FixedUpdate()
    │
    ├── 输入/游戏逻辑阶段
    │   ├── Update()
    │   └── 协程执行
    │
    └── 渲染阶段
        ├── LateUpdate()
        └── 渲染回调
```

**底层真相：**
- Unity使用**反射**来检测MonoBehaviour中定义的生命周期方法
- 只有**声明了**的方法才会被加入调用列表
- 空的`Update()`仍然会产生**性能开销**（虽然Unity会缓存跳过）

---

## 2. Awake/Start/OnEnable的真正区别

| 方法 | 调用时机 | 用途 | 注意事项 |
|------|----------|------|----------|
| `Awake()` | 对象实例化时立即调用 | 初始化自身数据、获取组件引用 | 执行顺序不保证 |
| `OnEnable()` | 对象激活时调用 | 订阅事件、重置状态 | 每次激活都会调用 |
| `Start()` | 第一帧Update之前 | 依赖其他对象的初始化 | 保证在所有Awake之后 |

### 关键区别：执行顺序问题

```csharp
// 场景中有两个对象：A 和 B
// A 脚本需要引用 B 脚本的数据

public class A : MonoBehaviour
{
    private B b;

    void Awake()
    {
        b = GetComponent<B>();  // 获取引用
        // ❌ 错误：此时 b.data 可能还未初始化
        // Debug.Log(b.data);
    }

    void Start()
    {
        // ✅ 正确：所有Awake都已执行完毕
        Debug.Log(b.data);
    }
}

public class B : MonoBehaviour
{
    public int data;

    void Awake()
    {
        data = 100;
    }
}
```

**执行顺序不确定性示例：**
```
Frame 0:
  可能顺序1: A.Awake() → B.Awake() → A.Start() → B.Start()
  可能顺序2: B.Awake() → A.Awake() → B.Start() → A.Start()
  关键点: 所有Awake在所有Start之前完成
```

### 控制执行顺序的方法

```csharp
// 方法1：使用特性（推荐）
[DefaultExecutionOrder(-100)]
public class B : MonoBehaviour { }  // B会在A之前执行Awake

// 方法2：Project Settings → Script Execution Order
```

---

## 3. 协程(IEnumerator)的底层实现原理

### 协程是什么？
- 协程是**伪异步**，本质上是在**主线程**上分帧执行的
- 使用C#的`yield return`实现**状态机**

### 底层机制

```csharp
// 你写的代码
IEnumerator MyCoroutine()
{
    Debug.Log("Step 1");
    yield return new WaitForSeconds(1f);
    Debug.Log("Step 2");
    yield return null;  // 等待一帧
    Debug.Log("Step 3");
}

// 编译器实际生成的（简化版状态机）
class MyCoroutineStateMachine : IEnumerator
{
    private int state = 0;

    public bool MoveNext()
    {
        switch (state)
        {
            case 0:
                Debug.Log("Step 1");
                state = 1;
                return true;
            case 1:
                // WaitForSeconds检查是否过了1秒
                if (waitComplete) {
                    Debug.Log("Step 2");
                    state = 2;
                }
                return true;
            case 2:
                Debug.Log("Step 3");
                return false;  // 协程结束
        }
        return false;
    }
}
```

### 常用yield指令

| 指令 | 效果 | 底层实现 |
|------|------|----------|
| `yield return null` | 等待下一帧 | 加入下一帧的协程队列 |
| `yield return new WaitForEndOfFrame()` | 等待帧结束 | 在渲染完成后执行 |
| `yield return new WaitForSeconds(t)` | 等待t秒 | 每帧检查Time.time |
| `yield return new WaitForFixedUpdate()` | 等待下一次物理更新 | 在FixedUpdate后执行 |
| `yield return StartCoroutine(Other())` | 等待另一个协程完成 | 嵌套协程 |
| `yield return new WaitUntil(() => condition)` | 等待条件为true | 每帧检查条件 |
| `yield return new WaitWhile(() => condition)` | 等待条件为false | 每帧检查条件 |

### 性能优化技巧

```csharp
// ❌ 每次都会产生GC Alloc
IEnumerator BadExample()
{
    while (true)
    {
        yield return new WaitForSeconds(1f);  // 每次new产生垃圾
    }
}

// ✅ 缓存yield指令
private WaitForSeconds waitOneSecond = new WaitForSeconds(1f);

IEnumerator GoodExample()
{
    while (true)
    {
        yield return waitOneSecond;  // 无GC
    }
}

// ✅ 更高效的方式（Unity 2020+）
IEnumerator BetterExample()
{
    var wait = WaitForSecondsRealtime.WaitForSeconds(1f);
    while (true)
    {
        yield return wait;
    }
}
```

---

## 4. async/await与Unity主线程的关系

### async/await vs 协程

| 特性 | 协程 | async/await |
|------|------|-------------|
| 返回值 | 无（IEnumerator） | 有（Task<T>） |
| 异常处理 | 需要手动捕获 | try-catch支持 |
| 取消 | StopCoroutine | CancellationToken |
| 线程 | 主线程 | 可配置 |
| Unity版本 | 所有版本 | 2017+（推荐2020+） |

### Unity中的async/await注意事项

```csharp
using UnityEngine;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;  // 推荐使用UniTask

public class AsyncExample : MonoBehaviour
{
    async void Start()
    {
        // ⚠️ async void 的异常会导致崩溃
        // 推荐使用 async Task 或 UniTaskVoid

        await SomeAsyncOperation();
    }

    async Task SomeAsyncOperation()
    {
        // ⚠️ 默认可能不在主线程执行
        // Unity API必须在主线程调用

        await Task.Delay(1000);

        // ❌ 可能崩溃：不在主线程
        // transform.position = Vector3.zero;

        // ✅ 确保回到主线程
        await Task.Yield();  // 或使用UniTask
        transform.position = Vector3.zero;
    }
}

// ✅ 推荐使用UniTask（零GC，主线程安全）
public class UniTaskExample : MonoBehaviour
{
    async UniTaskVoid Start()
    {
        await UniTask.Delay(1000);
        transform.position = Vector3.zero;  // 安全，在主线程
    }
}
```

### UniTask优势
- 零GC分配
- 完全主线程安全
- 支持所有Unity AsyncOperations
- PlayerLoop集成，精确控制执行时机

---

## 5. 实战应用：三消游戏的生命周期管理

```csharp
public class Match3Game : MonoBehaviour
{
    private Board board;
    private MatchDetector matchDetector;
    private CombatSystem combatSystem;

    // 第一阶段：初始化自身
    void Awake()
    {
        // 获取组件引用（不依赖其他脚本）
        board = GetComponent<Board>();
        matchDetector = GetComponent<MatchDetector>();
        combatSystem = GetComponent<CombatSystem>();
    }

    // 第二阶段：初始化依赖
    void Start()
    {
        // 此时所有脚本的Awake都已执行
        board.Initialize(7, 7);  // 初始化7x7棋盘
        matchDetector.Initialize(board);
        combatSystem.Initialize();

        // 开始游戏循环
        StartCoroutine(GameLoop());
    }

    IEnumerator GameLoop()
    {
        while (true)
        {
            // 等待玩家输入
            yield return WaitForPlayerInput();

            // 检测消除
            var matches = matchDetector.DetectMatches();

            if (matches.Count > 0)
            {
                // 执行消除动画
                yield return ProcessMatches(matches);

                // 触发战斗
                combatSystem.ProcessCombat(matches);

                // 填充新棋子
                yield return board.FillBoard();
            }
        }
    }

    void OnEnable()
    {
        // 订阅事件
        InputManager.OnSwipe += HandleSwipe;
    }

    void OnDisable()
    {
        // 取消订阅（防止内存泄漏）
        InputManager.OnSwipe -= HandleSwipe;
    }

    void OnDestroy()
    {
        // 清理资源
        StopAllCoroutines();
    }
}
```

---

## 本课小结

| 知识点 | 核心要点 |
|--------|----------|
| 生命周期管理 | Unity通过反射检测方法，加入对应调用列表 |
| Awake vs Start | Awake用于自身初始化，Start用于依赖初始化 |
| 执行顺序 | 使用`DefaultExecutionOrder`控制，或设计为顺序无关 |
| 协程 | 伪异步，状态机实现，注意缓存yield指令减少GC |
| async/await | 推荐使用UniTask，主线程安全，零GC |

---

## 相关链接

- [Unity Script Lifecycle Flowchart](https://docs.unity3d.com/Manual/ExecutionOrder.html)
- [Unity Coroutine详解](https://docs.unity3d.com/Manual/Coroutines.html)
- [UniTask GitHub](https://github.com/Cysharp/UniTask)
