# Pre-commit Hook: Unity代码规则检查

> 在提交代码前自动检查Unity开发规则

## 触发时机

每次执行 `git commit` 时自动运行

## 工作流程

1. 获取暂存的 `.cs` 文件列表
2. 对每个文件调用 `/check-rules` SKILL
3. 如果发现 CRITICAL 级别违规，阻止提交
4. 显示违规摘要

## 检查规则

只检查 **CRITICAL** 和 **HIGH** 级别的规则，包括：

### CRITICAL 级别（阻止提交）

- RULE-GC-003: Update中new集合
- RULE-GC-005: Update中使用LINQ
- RULE-MEM-001: 事件订阅未配对取消
- RULE-POOL-001: 高频对象未池化
- RULE-POOL-002: 对象归还未重置状态
- RULE-RES-003: Addressables Handle未Release
- RULE-REFACTOR-004: 重构前未建立测试
- RULE-SAFE-003: Update中可能抛异常

### HIGH 级别（警告但不阻止）

- RULE-GC-001: Update中字符串拼接
- RULE-GC-004: Update中GetComponent
- RULE-GC-006: Update中foreach遍历List
- RULE-MEM-002: 协程未正确停止
- RULE-MEM-003: 静态集合无清理机制
- RULE-MEM-004: DOTween动画未Kill
- RULE-POOL-003: 池化长期存活对象
- RULE-ARCH-001: 滥用单例模式
- RULE-RES-001: 使用Resources加载
- RULE-RES-002: 同步加载资源
- RULE-SAFE-001: 公共方法无null检查

## 输出格式

### 通过检查

```
✅ 代码规则检查通过

检查文件: 3个
通过规则: 所有CRITICAL和HIGH级别规则
建议: 可以安全提交
```

### 发现违规

```
⚠️  代码规则检查发现问题

检查文件: 3个
发现问题: 2个文件

🔴 CRITICAL违规 (阻止提交):

  PlayerController.cs:
    [RULE-MEM-001] 事件订阅未配对取消
    位置: OnEnable方法

    💡 修复建议:
    private void OnDisable()
    {
        EventBus.Unsubscribe<PlayerEvent>(OnPlayerEvent);
    }

🟠 HIGH警告 (不阻止):

  Enemy.cs:
    [RULE-GC-004] Update中调用GetComponent
    位置: Line 45
    建议: 在Awake中缓存组件引用

💡 如何修复CRITICAL违规?

方法1: 修复后重新提交
  git add <修复的文件>
  git commit

方法2: 跳过检查（不推荐）
  git commit --no-verify

❌ 提交被阻止
```

## 配置选项

### 跳过检查

如果确实需要跳过检查（不推荐）：

```bash
git commit --no-verify -m "提交信息"
```

### 自定义检查级别

在 `.claude/hooks/config.json` 中配置：

```json
{
  "block_on": "CRITICAL",
  "warn_on": "HIGH",
  "check_patterns": ["Assets/**/*.cs"],
  "exclude_patterns": ["**/Generated/**/*.cs", "**/Temp/**/*.cs"]
}
```

## 错误处理

### Hook无法运行

如果Hook执行失败：

1. 检查 `.git/hooks/pre-commit` 文件权限
2. 确保 Claude Code CLI 可用
3. 查看 Hook 日志：`.git/hooks/pre-commit.log`

### 临时禁用Hook

```bash
# 禁用pre-commit hook
cd .git/hooks
chmod -x pre-commit

# 重新启用
chmod +x pre-commit
```

## 集成说明

此Hook与以下工具配合使用：

1. **Claude Code SKILL** - 执行规则检查
2. **Git Hooks** - 自动触发检查
3. **Python工具** - 生成详细报告（可选）

## 性能说明

- 只检查暂存的文件（staged files）
- 使用增量检查，只分析修改的部分
- 预计每次提交检查时间 < 5秒

## 维护建议

1. **定期更新规则** - 当开发规则清单更新时同步更新
2. **调整检查级别** - 根据团队反馈调整阻塞/警告级别
3. **性能优化** - 如果检查变慢，考虑优化Hook逻辑
