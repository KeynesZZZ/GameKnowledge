---
title: 【架构决策】单例 vs 依赖注入
tags: [C#, Unity, 架构决策, 单例模式, 依赖注入, VContainer, Zenject]
category: 架构设计/架构决策
created: 2024-01-10 11:00
updated: 2026-03-04 21:36
description: 深度对比单例模式与依赖注入两种管理依赖的方式，分析各自的优缺点、适用场景和选择指南
unity_version: 2021.3+
---

# 【架构决策】单例 vs 依赖注入

> 核心问题：如何管理全局访问？选择单例还是依赖注入？

## 一、问题背景：如何管理全局访问？

### 1.1 常见需求

```
游戏开发中常见的全局访问需求：
├─ GameManager - 游戏状态
├─ AudioManager - 音频控制
├─ SaveSystem - 存档管理
├─ ConfigManager - 配置管理
└─ EventManager - 事件系统

问题：如何让需要的地方能够访问这些服务？
```

### 1.2 两种解决方案

```
方案A：单例模式
└─ 全局静态访问点
└─ 任何地方都可以调用

方案B：依赖注入
└─ 通过构造函数/属性注入
└─ 显式声明依赖
```

---

## 二、单例模式

### 2.1 实现方式

```csharp
// 经典单例
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void PauseGame() => Time.timeScale = 0;
    public void ResumeGame() => Time.timeScale = 1;
}

// 使用
public class Player : MonoBehaviour
{
    private void Die()
    {
        GameManager.Instance.PauseGame();  // 直接访问
    }
}
```

### 2.2 单例的优势

```
┌─────────────────────────────────────────────────────────────┐
│                    单例的优势                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 简单易用                                                │
│     └─ GameManager.Instance.Method()                       │
│     └─ 不需要额外的配置                                     │
│                                                             │
│  ✅ 快速开发                                                │
│     └─ 适合原型和Demo                                       │
│     └─ 适合小型项目                                         │
│                                                             │
│  ✅ 全局可用                                                │
│     └─ 任何地方都能访问                                     │
│     └─ 不需要传递引用                                       │
│                                                             │
│  ✅ 易于理解                                                │
│     └─ 概念简单                                             │
│     └─ 新手友好                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 单例的问题

```
┌─────────────────────────────────────────────────────────────┐
│                    单例的问题                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ❌ 隐式依赖                                                │
│     └─ 类内部隐藏了对单例的依赖                             │
│     └─ 看接口不知道需要什么                                 │
│                                                             │
│      public class Player                                    │
│      {                                                      │
│          public void Die()                                  │
│          {                                                  │
│              // 隐藏依赖：看不出需要GameManager             │
│              GameManager.Instance.PauseGame();              │
│          }                                                  │
│      }                                                      │
│                                                             │
│  ❌ 难以测试                                                │
│     └─ 测试时需要mock单例                                   │
│     └─ 单例状态影响其他测试                                 │
│                                                             │
│      [Test]                                                 │
│      public void TestPlayerDeath()                          │
│      {                                                      │
│          // 问题：GameManager.Instance 是真实的单例         │
│          // 无法替换为 mock                                 │
│          var player = new Player();                         │
│          player.Die();  // 会调用真实的 GameManager         │
│      }                                                      │
│                                                             │
│  ❌ 全局状态                                                │
│     └─ 任何地方都能修改                                     │
│     └─ 难以追踪状态变化                                     │
│                                                             │
│  ❌ 生命周期问题                                            │
│     └─ 初始化顺序不确定                                     │
│     └─ 场景切换时可能出问题                                 │
│                                                             │
│  ❌ 违反依赖倒置                                            │
│     └─ 依赖具体实现，不是接口                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、依赖注入

### 3.1 核心思想

```
┌─────────────────────────────────────────────────────────────┐
│                    依赖注入本质                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  不是"我自己去获取依赖"，而是"依赖被注入给我"               │
│                                                             │
│  单例方式：                                                 │
│  public class Player                                        │
│  {                                                          │
│      public void Die()                                      │
│      {                                                      │
│          GameManager.Instance.PauseGame();  // 我去获取     │
│      }                                                      │
│  }                                                          │
│                                                             │
│  依赖注入方式：                                             │
│  public class Player                                        │
│  {                                                          │
│      private readonly IGameManager gameManager;             │
│                                                             │
│      // 依赖通过构造函数注入                                │
│      public Player(IGameManager gameManager)                │
│      {                                                      │
│          this.gameManager = gameManager;                    │
│      }                                                      │
│                                                             │
│      public void Die()                                      │
│      {                                                      │
│          gameManager.PauseGame();  // 使用注入的依赖        │
│      }                                                      │
│  }                                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Unity中的依赖注入 (VContainer示例)

```csharp
// 1. 定义接口
public interface IGameManager
{
    void PauseGame();
    void ResumeGame();
}

// 2. 实现类
public class GameManager : MonoBehaviour, IGameManager
{
    public void PauseGame() => Time.timeScale = 0;
    public void ResumeGame() => Time.timeScale = 1;
}

// 3. 配置注入
public class GameInstaller : MonoInstaller
{
    public override void Configure(IContainerBuilder builder)
    {
        // 注册服务
        builder.Register<IGameManager, GameManager>(Lifetime.Singleton);
    }
}

// 4. 使用注入
public class Player : MonoBehaviour
{
    [Inject]  // VContainer 注入标记
    private IGameManager gameManager;

    private void Die()
    {
        gameManager.PauseGame();
    }
}
```

### 3.3 依赖注入的优势

```
┌─────────────────────────────────────────────────────────────┐
│                  依赖注入的优势                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 显式依赖                                                │
│     └─ 构造函数明确声明需要什么                             │
│     └─ 一眼看出类的依赖                                     │
│                                                             │
│      public class Player                                    │
│      {                                                      │
│          private readonly IGameManager gameManager;         │
│          private readonly IAudioManager audioManager;       │
│                                                             │
│          // 依赖清晰可见                                    │
│          public Player(                                     │
│              IGameManager gameManager,                      │
│              IAudioManager audioManager)                    │
│          { ... }                                            │
│      }                                                      │
│                                                             │
│  ✅ 易于测试                                                │
│     └─ 可以注入 mock 对象                                   │
│     └─ 测试隔离性好                                         │
│                                                             │
│      [Test]                                                 │
│      public void TestPlayerDeath()                          │
│      {                                                      │
│          var mockGame = new Mock<IGameManager>();           │
│          var mockAudio = new Mock<IAudioManager>();         │
│                                                             │
│          var player = new Player(mockGame.Object, mockAudio.Object);
│          player.Die();                                      │
│                                                             │
│          mockGame.Verify(g => g.PauseGame(), Times.Once);   │
│      }                                                      │
│                                                             │
│  ✅ 依赖接口，不是实现                                      │
│     └─ 符合依赖倒置原则                                     │
│     └─ 实现可以随时替换                                     │
│                                                             │
│  ✅ 生命周期管理                                            │
│     └─ 由容器管理对象生命周期                               │
│     └─ 单例、瞬态、作用域等                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 依赖注入的代价

```
代价：
├─ 学习曲线（需要理解DI框架）
├─ 初期配置成本
├─ 调试复杂（注入链难以追踪）
├─ 小项目可能过度设计
└─ 运行时错误（注入失败）
```

---

## 四、对比总结

### 4.1 特性对比

| 特性 | 单例 | 依赖注入 |
|------|------|----------|
| **学习成本** | 低 | 中高 |
| **代码量** | 少 | 多（需要接口+注册） |
| **依赖可见性** | 隐藏 | 显式 |
| **可测试性** | 差 | 好 |
| **灵活性** | 低 | 高 |
| **调试难度** | 低 | 中 |
| **适合项目规模** | 小型 | 中大型 |

### 4.2 选择指南

```
┌─────────────────────────────────────────────────────────────┐
│                     选择指南                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  选择单例：                                                 │
│  ├─ 项目规模小（< 1万行）                                   │
│  ├─ 原型/Demo                                               │
│  ├─ 快速开发优先                                            │
│  ├─ 团队成员经验较少                                        │
│  └─ 不需要单元测试                                          │
│                                                             │
│  选择依赖注入：                                             │
│  ├─ 项目规模中大型（> 5万行）                               │
│  ├─ 需要单元测试                                            │
│  ├─ 团队有DI经验                                            │
│  ├─ 长期维护的项目                                          │
│  └─ 需要灵活替换实现                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 混合方案

```csharp
// 实际项目中可以混合使用

// 服务定位器模式：介于单例和DI之间
public static class Services
{
    private static IGameManager gameManager;
    public static IGameManager GameManager => gameManager;

    public static void Initialize(IGameManager manager)
    {
        gameManager = manager;
    }
}

// 使用
public class Player : MonoBehaviour
{
    private void Die()
    {
        Services.GameManager.PauseGame();
    }
}

// 测试时可以替换
[Test]
public void TestPlayerDeath()
{
    Services.Initialize(new MockGameManager());
    // ...
}
```

---

## 五、常见误区

### 5.1 单例滥用

```csharp
// ❌ 什么都做成单例
public class PlayerSingleton : MonoBehaviour { ... }
public class EnemySingleton : MonoBehaviour { ... }
public class BulletSingleton : MonoBehaviour { ... }
// 单例不是用来解决"需要多个对象"的问题的！
```

### 5.2 过度注入

```csharp
// ❌ 构造函数参数过多
public class Player
{
    public Player(
        IGameManager game,
        IAudioManager audio,
        IInputManager input,
        IInventoryManager inventory,
        IQuestManager quest,
        IAchievementManager achievement,
        ISaveManager save,
        IConfigManager config)
    {
        // 依赖太多，可能违反单一职责原则
    }
}
```

---

## 六、总结

```
┌─────────────────────────────────────────────────────────────┐
│                    决策总结                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  单例：简单、快速、但不利于测试和维护                        │
│  依赖注入：复杂、但更专业、更易测试                          │
│                                                             │
│  关键不是哪个更好，而是哪个更适合你的项目：                  │
│                                                             │
│  • 小项目/原型 → 单例                                       │
│  • 大项目/长期维护 → 依赖注入                               │
│  • 需要测试 → 依赖注入                                      │
│  • 快速迭代 → 单例                                          │
│                                                             │
│  最重要：根据实际情况选择，不要过度设计                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 相关链接

> 本文档是单例模式系列的一部分，建议配合阅读：

- [[最佳实践-单例模式]] - 单例的多种实现方式
- [[最佳实践-依赖注入使用指南]] - VContainer完整使用指南
- [[反模式-常见架构陷阱]] - 单例滥用的危害分析
- [[设计原理-为什么要用设计模式]] - 设计模式的本质思考
