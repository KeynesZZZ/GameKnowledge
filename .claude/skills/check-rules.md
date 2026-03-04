# Unity开发规则检查

> 检查C#代码是否符合Unity开发最佳实践和规则

## 什么时候使用

当你需要检查Unity C#代码是否符合开发规范时使用此技能：

- 编写新代码后，检查是否违反规则
- Code Review前，自动检查代码质量
- 提交代码前，确保没有严重违规
- 重构代码时，验证重构是否符合规范

## 工作流程

1. **读取规则清单**
   - 从 `UnityKnowledge/00_元数据与模板/开发规则清单.md` 读取所有规则
   - 解析规则ID、严重性、检测模式、修复建议

2. **分析代码文件**
   - 读取用户指定的C#源文件
   - 检查代码中的规则违规

3. **生成检查报告**
   - 按严重性分组显示违规
   - 提供具体的修复建议
   - 引用规则文档中的示例

## 用户指令

### 检查单个文件

```
/check-rules Assets/Scripts/PlayerController.cs
```

### 检查整个目录

```
/check-rules Assets/Scripts
```

### 只检查特定类别规则

```
/check-rules Assets/Scripts --rules=GC,MEMORY
```

可选类别：GC, MEMORY, POOL, ARCH, ASYNC, REFACTOR, UI, PHYSICS, RES, PERF, SAFE

### 只检查特定严重性

```
/check-rules Assets/Scripts --severity=CRITICAL
```

可选严重性：CRITICAL, HIGH, MEDIUM, LOW

## 规则检查清单

### GC优化规则（RULE-GC-xxx）

- [ ] **RULE-GC-001**: 检查 `Update()`, `FixedUpdate()`, `LateUpdate()` 中的字符串拼接
  - 模式：在Update方法中查找 `+` 拼接字符串
  - 例外：字符串插值 `$""` 可接受

- [ ] **RULE-GC-002**: 检查协程中是否有缓存的 `WaitForSeconds`
  - 模式：在协程循环中查找 `new WaitForSeconds()`

- [ ] **RULE-GC-003**: 检查Update中是否有 `new List<>()` 或 `new Dictionary<>()`
  - 模式：在Update方法中查找集合初始化

- [ ] **RULE-GC-004**: 检查Update中是否有 `GetComponent<T>()` 调用
  - 模式：在Update方法中查找GetComponent调用

- [ ] **RULE-GC-005**: 检查Update中是否有LINQ使用
  - 模式：在Update方法中查找 `.Where()`, `.Select()`, `.ToList()` 等

- [ ] **RULE-GC-006**: 检查Update中遍历List是否使用foreach
  - 模式：在Update方法中查找 `foreach (var item in xxxList)`
  - 例外：遍历数组可使用foreach

- [ ] **RULE-GC-007**: 检查是否使用 `gameObject.tag` 而不是 `CompareTag()`
  - 模式：查找 `.tag ==` 或 `.tag !=`

### 内存管理规则（RULE-MEM-xxx）

- [ ] **RULE-MEM-001**: 检查事件订阅是否有配对的取消订阅
  - 模式：查找 `EventBus.Subscribe` 或 `+=` 订阅事件
  - 需要验证：在 `OnDisable` 或 `OnDestroy` 中有对应的 `Unsubscribe` 或 `-=`

- [ ] **RULE-MEM-002**: 检查协程是否保存引用并正确停止
  - 模式：查找 `StartCoroutine()` 调用
  - 需要验证：协程引用保存在字段中，且在 `OnDisable` 中停止

- [ ] **RULE-MEM-003**: 检查静态集合是否有清理机制
  - 模式：查找静态 `List<>`, `Dictionary<>`
  - 需要验证：存在 `Remove()` 或 `Clear()` 方法

- [ ] **RULE-MEM-004**: 检查DOTween动画是否Kill
  - 模式：查找 `.DOScale()`, `.DOMove()` 等 DOTween 调用
  - 需要验证：Tween引用被保存并在 `OnDisable` 中调用 `.Kill()`

### 对象池规则（RULE-POOL-xxx）

- [ ] **RULE-POOL-001**: 检查高频创建的对象是否使用对象池
  - 模式：在Update或高频方法中查找 `Instantiate()`
  - 需要验证：对象创建频率、是否应该池化

- [ ] **RULE-POOL-002**: 检查对象归还时是否重置状态
  - 模式：查找对象池归还逻辑
  - 需要验证：调用 `.Reset()` 或类似重置方法

### 架构规则（RULE-ARCH-xxx）

- [ ] **RULE-ARCH-001**: 检查是否滥用单例模式
  - 模式：查找 `public static xxx Instance` 模式
  - 需要验证：是真正的全局服务还是游戏实体

- [ ] **RULE-ARCH-002**: 检查事件处理中是否触发新事件
  - 模式：在事件处理方法中查找 `EventBus.Publish()` 或类似调用

- [ ] **RULE-ARCH-003**: 检查高频对象是否有独立Update
  - 模式：查找大量相同类型的MonoBehaviour，每个都有Update
  - 建议：使用管理器统一更新

- [ ] **RULE-ARCH-004**: 检查Update中是否有 `GameObject.Find()` 或 `FindObjectOfType()`
  - 模式：在Update方法中查找这些方法

- [ ] **RULE-ARCH-006**: 检查是否使用public字段暴露给Inspector
  - 模式：查找 `public` 字段（非方法）
  - 建议：使用 `[SerializeField] private` 替代

### 异步编程规则（RULE-ASYNC-xxx）

- [ ] **RULE-ASYNC-001**: 检查是否有深层协程嵌套
  - 模式：查找 `yield return StartCoroutine()` 嵌套

- [ ] **RULE-ASYNC-002**: 检查异步操作是否支持取消
  - 模式：查找无限循环的异步操作
  - 需要验证：接受 `CancellationToken` 参数

### 代码安全规则（RULE-SAFE-xxx）

- [ ] **RULE-SAFE-001**: 检查公共方法是否有null检查
  - 模式：公共方法直接使用参数而不检查null

- [ ] **RULE-SAFE-002**: 检查是否使用 `?.` 操作符处理可能为null的对象
  - 模式：冗长的if null检查可以用 `?.` 简化

- [ ] **RULE-SAFE-003**: 检查Update中可能抛异常的代码
  - 模式：Update中访问数组、字典、可能为null的对象

## 报告格式

### 控制台输出

```
🔍 检查文件: Assets/Scripts/PlayerController.cs

✅ 通过规则: 45条
⚠️  发现违规: 3条

🔴 CRITICAL (1):
  [RULE-MEM-001] 事件订阅未配对取消
    位置: Line 25
    代码: EventBus.Subscribe<PlayerEvent>(OnPlayerEvent);

    ❌ 问题: 在OnEnable中订阅事件，但没有在OnDisable中取消订阅

    ✅ 修复:
    private void OnDisable()
    {
        EventBus.Unsubscribe<PlayerEvent>(OnPlayerEvent);
    }

    📚 参考: 开发规则清单 > RULE-MEM-001

🟠 HIGH (2):
  [RULE-GC-004] Update中调用GetComponent
    位置: Line 58
    代码: var rb = GetComponent<Rigidbody>();

    ❌ 问题: 每帧都调用GetComponent有性能开销

    ✅ 修复: 在Awake或Start中缓存组件引用
    private Rigidbody rb;
    private void Awake() => rb = GetComponent<Rigidbody>();

    📚 参考: 开发规则清单 > RULE-GC-004

  [RULE-ARCH-006] 使用public字段暴露给Inspector
    位置: Line 12
    代码: public float maxHealth = 100f;

    ❌ 问题: public字段破坏封装

    ✅ 修复: 使用SerializeField
    [SerializeField] private float maxHealth = 100f;
    public float MaxHealth => maxHealth;

    📚 参考: 开发规则清单 > RULE-ARCH-006

📊 检查摘要:
  - 检查文件: 1个
  - 代码行数: 150行
  - 违规数量: 3个 (CRITICAL: 1, HIGH: 2)
  - 预计修复时间: 10分钟
```

### 修复优先级

1. **立即修复** - CRITICAL级别违规
2. **尽快修复** - HIGH级别违规
3. **计划修复** - MEDIUM级别违规
4. **可选优化** - LOW级别违规

## 特殊处理

### 架构相关规则

架构规则（如单例使用、组件化等）需要上下文理解，AI检查时应该：
- 询问用户设计意图
- 提供替代方案
- 不要过于死板

### 可选规则

某些规则有明确的例外情况，检查时应该：
- 识别例外场景
- 询问用户是否符合例外
- 灵活判断

## 相关文件

- `UnityKnowledge/00_元数据与模板/开发规则清单.md` - 规则来源
- `UnityKnowledge/40_工具链/自动化规则检查工具.md` - 使用文档
