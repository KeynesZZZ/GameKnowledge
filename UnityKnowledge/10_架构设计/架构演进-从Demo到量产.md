# 架构演进 - 从Demo到量产

> 游戏项目架构的阶段性演进与重构策略 `#架构演进` `#重构` `#项目经验`

## 一、项目生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    项目演进阶段                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阶段1: 原型期 (Prototype)                                  │
│  ├─ 目标：验证核心玩法                                     │
│  ├─ 特点：快速迭代、代码混乱                               │
│  └─ 架构：几乎无架构                                       │
│                                                             │
│  阶段2: Demo期 (Demo)                                       │
│  ├─ 目标：可展示的版本                                     │
│  ├─ 特点：功能基本完整、开始暴露问题                       │
│  └─ 架构：简单单例、直接引用                               │
│                                                             │
│  阶段3: 量产期 (Production)                                 │
│  ├─ 目标：完整可发布版本                                   │
│  ├─ 特点：团队协作、长期维护                               │
│  └─架构：模块化、设计模式、测试覆盖                        │
│                                                             │
│  阶段4: 运营期 (LiveOps)                                    │
│  ├─ 目标：持续更新、长期运营                               │
│  ├─ 特点：频繁更新、AB测试                                 │
│  └─ 架构：热更新、配置驱动                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、各阶段架构特征

### 2.1 原型期：快速验证

```csharp
// 原型期代码特征：直接、简单、混乱

public class GamePrototype : MonoBehaviour
{
    // 所有东西都在一个类里
    public GameObject player;
    public GameObject enemy;
    public Text scoreText;

    private int score;
    private bool isGameOver;

    void Update()
    {
        // 玩家移动
        player.transform.position += new Vector3(
            Input.GetAxis("Horizontal"),
            0,
            Input.GetAxis("Vertical")
        ) * 5f * Time.deltaTime;

        // 敌人追踪
        enemy.transform.position = Vector3.MoveTowards(
            enemy.transform.position,
            player.transform.position,
            3f * Time.deltaTime
        );

        // 碰撞检测
        if (Vector3.Distance(player.transform.position, enemy.transform.position) < 1f)
        {
            isGameOver = true;
        }

        // 分数
        scoreText.text = "Score: " + score;
    }
}

// 原型期策略：
// ✅ 快速实现，验证想法
// ✅ 不用考虑架构
// ❌ 不要在这个阶段过度设计
```

### 2.2 Demo期：开始解耦

```csharp
// Demo期代码特征：简单分离、单例模式

// 分离出的玩家控制器
public class PlayerController : MonoBehaviour
{
    public static PlayerController Instance;

    public float moveSpeed = 5f;

    private void Awake()
    {
        Instance = this;
    }

    void Update()
    {
        Move();
    }

    void Move()
    {
        var input = new Vector3(
            Input.GetAxis("Horizontal"),
            0,
            Input.GetAxis("Vertical")
        );
        transform.position += input * moveSpeed * Time.deltaTime;
    }
}

// 分离出的敌人控制器
public class EnemyController : MonoBehaviour
{
    public float chaseSpeed = 3f;

    void Update()
    {
        // 直接引用玩家单例
        transform.position = Vector3.MoveTowards(
            transform.position,
            PlayerController.Instance.transform.position,
            chaseSpeed * Time.deltaTime
        );
    }
}

// 分离出的游戏管理器
public class GameManager : MonoBehaviour
{
    public static GameManager Instance;

    public int Score { get; private set; }
    public bool IsGameOver { get; private set; }

    public void AddScore(int amount)
    {
        Score += amount;
        UIManager.Instance.UpdateScore(Score);
    }

    public void GameOver()
    {
        IsGameOver = true;
        UIManager.Instance.ShowGameOver();
    }
}

// Demo期策略：
// ✅ 基本的职责分离
// ✅ 简单的单例模式
// ❌ 仍然有很多直接引用
// ❌ 难以测试
```

### 2.3 量产期：模块化设计

```csharp
// 量产期代码特征：接口、依赖注入、事件驱动

// 定义接口
public interface IPlayerService
{
    Vector3 Position { get; }
    void Move(Vector3 direction);
}

public interface IEnemyService
{
    void Chase(Vector3 target);
}

public interface IGameService
{
    int Score { get; }
    void AddScore(int amount);
    event Action<int> OnScoreChanged;
}

// 实现类
public class PlayerService : IPlayerService
{
    private readonly Transform transform;

    public Vector3 Position => transform.position;

    public PlayerService(Transform playerTransform)
    {
        transform = playerTransform;
    }

    public void Move(Vector3 direction)
    {
        transform.position += direction * 5f * Time.deltaTime;
    }
}

// 使用事件通信
public class GameService : IGameService
{
    public int Score { get; private set; }
    public event Action<int> OnScoreChanged;

    public void AddScore(int amount)
    {
        Score += amount;
        OnScoreChanged?.Invoke(Score);
    }
}

// 依赖注入容器
public class GameContainer : MonoBehaviour
{
    private void Awake()
    {
        // 注册服务
        ServiceLocator.Register<IPlayerService>(new PlayerService(player.transform));
        ServiceLocator.Register<IGameService>(new GameService());

        // 订阅事件
        ServiceLocator.Get<IGameService>().OnScoreChanged += OnScoreChanged;
    }

    private void OnScoreChanged(int score)
    {
        // 更新UI
    }
}

// 量产期策略：
// ✅ 接口定义清晰
// ✅ 依赖注入/服务定位器
// ✅ 事件驱动通信
// ✅ 可测试
```

---

## 三、重构策略

### 3.1 识别重构时机

```
┌─────────────────────────────────────────────────────────────┐
│                    重构信号                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  代码异味：                                                 │
│  ├─ 一个类超过500行                                        │
│  ├─ 方法超过50行                                           │
│  ├─ 嵌套超过3层                                            │
│  ├─ 同样的代码复制粘贴多处                                 │
│  ├─ 修改一个功能要改多个文件                               │
│  └─ 不敢修改代码，怕破坏其他功能                           │
│                                                             │
│  团队信号：                                                 │
│  ├─ 新人看不懂代码                                         │
│  ├─ 经常出现"我这里没问题"                                 │
│  ├─ 功能开发越来越慢                                       │
│  └─ Bug越来越多                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 重构步骤

```
┌─────────────────────────────────────────────────────────────┐
│                    安全重构流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 建立测试                                                │
│     └─ 重构前先写测试，确保行为不变                        │
│                                                             │
│  2. 小步重构                                                │
│     └─ 每次只改一小部分                                    │
│     └─ 改完立即测试                                        │
│                                                             │
│  3. 保持功能不变                                            │
│     └─ 重构不改变外部行为                                  │
│     └─ 只是改变内部结构                                    │
│                                                             │
│  4. 持续集成                                                │
│     └─ 频繁提交                                            │
│     └─ 确保每次提交都可运行                                │
│                                                             │
│  5. 代码审查                                                │
│     └─ 重构后必须代码审查                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 常见重构模式

```csharp
// 重构1: 提取方法
// Before
public void Update()
{
    // 移动逻辑...
    float h = Input.GetAxis("Horizontal");
    float v = Input.GetAxis("Vertical");
    transform.position += new Vector3(h, 0, v) * speed * Time.deltaTime;

    // 攻击逻辑...
    if (Input.GetMouseButtonDown(0))
    {
        // ...
    }
}

// After
public void Update()
{
    HandleMovement();
    HandleAttack();
}

private void HandleMovement()
{
    float h = Input.GetAxis("Horizontal");
    float v = Input.GetAxis("Vertical");
    transform.position += new Vector3(h, 0, v) * speed * Time.deltaTime;
}

private void HandleAttack()
{
    if (Input.GetMouseButtonDown(0))
    {
        // ...
    }
}

// 重构2: 提取类
// Before
public class Player : MonoBehaviour
{
    public void Move() { /* 移动逻辑 */ }
    public void Attack() { /* 攻击逻辑 */ }
    public void TakeDamage() { /* 受伤逻辑 */ }
    public void UpdateUI() { /* UI逻辑 */ }
    public void PlaySound() { /* 音效逻辑 */ }
}

// After
public class Player : MonoBehaviour
{
    private PlayerMovement movement;
    private PlayerCombat combat;
    private PlayerHealth health;

    // 只负责协调
}

public class PlayerMovement { /* 移动逻辑 */ }
public class PlayerCombat { /* 攻击逻辑 */ }
public class PlayerHealth { /* 血量逻辑 */ }

// 重构3: 引入接口
// Before
public class Enemy
{
    public void Chase(Player player) { /* 依赖具体类 */ }
}

// After
public interface ITarget
{
    Vector3 Position { get; }
}

public class Enemy
{
    public void Chase(ITarget target) { /* 依赖接口 */ }
}

public class Player : ITarget
{
    public Vector3 Position => transform.position;
}
```

---

## 四、架构演进案例

### 4.1 从单例到依赖注入

```
阶段1：单例
┌─────────────────────────────────────────┐
│  GameManager.Instance.DoSomething()     │
│  AudioManager.Instance.Play()           │
│  SaveManager.Instance.Save()            │
└─────────────────────────────────────────┘
问题：全局状态、难以测试、隐藏依赖

阶段2：服务定位器
┌─────────────────────────────────────────┐
│  Services.Get<IGameManager>().DoXXX()   │
│  Services.Get<IAudioManager>().Play()   │
└─────────────────────────────────────────┘
改进：接口化、可替换

阶段3：依赖注入
┌─────────────────────────────────────────┐
│  public class Player                    │
│  {                                      │
│      private readonly IGameManager gm;  │
│      public Player(IGameManager gm)     │
│      {                                  │
│          this.gm = gm;                  │
│      }                                  │
│  }                                      │
└─────────────────────────────────────────┘
改进：显式依赖、易于测试
```

### 4.2 从直接引用到事件驱动

```
阶段1：直接引用
┌─────────────────────────────────────────┐
│  Player                                 │
│    ├─ healthBar.UpdateHealth()          │
│    ├─ scoreManager.AddScore()           │
│    ├─ audioManager.PlaySound()          │
│    └─ achievementManager.Check()        │
└─────────────────────────────────────────┘
问题：Player依赖太多类

阶段2：事件驱动
┌─────────────────────────────────────────┐
│  Player                                 │
│    └─ EventBus.Publish(OnPlayerDeath)   │
│                                         │
│  HealthBar : IEventHandler              │
│  ScoreManager : IEventHandler           │
│  AudioManager : IEventHandler           │
└─────────────────────────────────────────┘
改进：解耦、易扩展
```

---

## 五、总结

```
┌─────────────────────────────────────────────────────────────┐
│                    架构演进原则                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 适当时机                                                │
│     └─ 原型期不过度设计                                    │
│     └─ Demo期开始规划                                      │
│     └─ 量产期严格执行                                      │
│                                                             │
│  2. 渐进式重构                                              │
│     └─ 不要一次性大重构                                    │
│     └─ 小步快跑，持续改进                                  │
│                                                             │
│  3. 测试保障                                                │
│     └─ 重构前确保有测试                                    │
│     └─ 重构后验证测试通过                                  │
│                                                             │
│  4. 价值导向                                                │
│     └─ 架构服务于功能                                      │
│     └─ 不为架构而架构                                      │
│                                                             │
│  5. 团队共识                                                │
│     └─ 架构规范要团队认可                                  │
│     └─ 代码审查保证执行                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 相关链接

- [设计原理-为什么要用设计模式](设计原理-为什么要用设计模式.md)
- [反模式-常见架构陷阱](反模式-常见架构陷阱.md)
- [实战案例-三消游戏架构](实战案例-三消游戏架构.md)
