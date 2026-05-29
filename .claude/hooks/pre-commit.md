# Pre-commit Hook: Unity代码规则检查

> 在提交代码前自动检查 Unity C# 规则，阻止低误报、高风险的 CRITICAL 问题。

## 当前结构

| 文件 | 作用 |
|------|------|
| `.claude/hooks/pre-commit.md` | Hook 设计说明和维护说明 |
| `.claude/hooks/config.json` | Hook 配置，决定检查范围、阻塞级别和规则源 |
| `.claude/hooks/pre-commit.py` | 可执行检查脚本，可直接接入 Git pre-commit |
| `.claude/rules/unity-rules.json` | 唯一机器可读规则源 |

## 工作流程

1. 获取暂存的 `.cs` 文件列表
2. 读取 `.claude/hooks/config.json`
3. 从 `.claude/rules/unity-rules.json` 加载规则
4. 对每个暂存文件执行轻量静态检查
5. 发现 CRITICAL 级别问题时阻止提交
6. 输出违规摘要和修复建议

## 安装方式

把仓库脚本链接到 Git hooks：

```bash
ln -sf ../../.claude/hooks/pre-commit.py .git/hooks/pre-commit
chmod +x .claude/hooks/pre-commit.py
chmod +x .git/hooks/pre-commit
```

也可以不安装，手动检查指定文件：

```bash
python3 .claude/hooks/pre-commit.py .claude/skills/test_example.cs
```

## 配置

配置文件：`.claude/hooks/config.json`

```json
{
  "rules_source": "../rules/unity-rules.json",
  "check_patterns": ["*.cs"],
  "exclude_patterns": ["*/Generated/*", "*/Temp/*"],
  "block_on": ["CRITICAL"],
  "warn_on": ["HIGH"],
  "include_review_rules": true,
  "max_files": 50
}
```

## 规则来源

规则只维护在：

```text
.claude/rules/unity-rules.json
```

每条规则包含：

| 字段 | 说明 |
|------|------|
| `id` | 规则 ID |
| `category` | 规则分类 |
| `severity` | 严重性：CRITICAL/HIGH/MEDIUM/LOW |
| `detection` | `automatic` 可自动判断，`review` 需要人工或 AI 复核 |
| `pattern` | 本地脚本使用的检测模式 |
| `message` | 问题说明 |
| `suggestion` | 修复建议 |

## 输出示例

### 通过检查

```text
Unity code rule check
Checked files: 3
Findings: 0

No blocking findings.
```

### 发现违规

```text
Unity code rule check
Checked files: 1
Findings: 3

CRITICAL (1)
  Assets/Scripts/PlayerController.cs:25 [RULE-GC-003] Update中new集合
    code: var items = new List<int>();
    why: Update/FixedUpdate/LateUpdate 中创建 List/Dictionary/HashSet，容易造成每帧 GC。
    fix: 把集合提升为字段并 Clear 复用，或使用对象池。

Commit blocked by CRITICAL findings.
```

## 错误处理

### Hook无法运行

1. 检查 `.git/hooks/pre-commit` 文件权限
2. 确保 Python 3 可用
3. 手动运行 `python3 .claude/hooks/pre-commit.py .claude/skills/test_example.cs`

### 临时跳过

```bash
git commit --no-verify -m "提交信息"
```

只在明确知道风险、且后续会补修时使用。

## 设计边界

本地 hook 只做轻量检查，不伪装成完整 C# 静态分析器。

- `automatic` 规则：可用简单模式相对稳定判断
- `review` 规则：只提示风险，需要人工或 AI 结合上下文复核

## 维护建议

1. 规则只改一处：`.claude/rules/unity-rules.json`
2. 谨慎把规则设为 CRITICAL，避免误报阻塞提交
3. 对架构、生命周期、上下文相关规则使用 `review`
4. 如果检查变慢，优先缩小 `check_patterns` 或 `max_files`
