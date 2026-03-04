# 可移植工具包使用示例

本文档展示如何在不同场景中使用Unity规则检查工具包。

---

## 示例1: 新Unity项目

### 场景

刚创建一个新的Unity 2D项目，想要从一开始就确保代码质量。

### 步骤

```bash
# 1. 创建Unity项目（Unity Editor）
# File → New Project → 2D Core

# 2. 复制工具包到项目
cd /path/to/YourNewUnityProject
cp -r /path/to/unity-rules-checker .

# 3. 运行安装
cd unity-rules-checker
./install.sh

# 4. 开始编写代码
mkdir -p Assets/Scripts

# 5. 代码完成后，检查规则
# 在Claude Code中：
/check-rules Assets/Scripts/PlayerController.cs
```

### 结果

```
✓ 检测到Unity项目
✓ 已安装: check-rules.md
✓ 已安装: 开发规则清单.md
✓ Git Hook已配置
```

---

## 示例2: 现有项目集成

### 场景

现有Unity项目，团队规模5人，想要统一代码规范。

### 步骤

```bash
# 1. 团队负责人添加工具包到仓库
cd /path/to/ExistingUnityProject
cp -r /path/to/unity-rules-checker .
git add unity-rules-checker
git commit -m "chore: add code quality checker tool"

# 2. 更新README，添加安装说明
cat >> README.md << 'EOF'

## 代码规范

本项目使用Unity规则检查工具。

首次设置：
```bash
cd unity-rules-checker
./install.sh
```

日常使用：
```bash
# 在Claude Code中
/check-rules Assets/Scripts
```
EOF

# 3. 推送到远程
git push origin main

# 4. 团队成员更新代码
git pull
cd unity-rules-checker
./install.sh
```

### 结果

- 所有团队成员统一使用相同的规则检查
- Git Hook防止违规代码入库
- Code Review更有依据

---

## 示例3: CI/CD集成

### 场景

使用GitHub Actions的Unity项目，想在PR时自动检查代码。

### 步骤

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check

on:
  pull_request:
    paths:
      - 'Assets/**/*.cs'
      - '.claude/**'

jobs:
  rules-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Claude Code
        run: |
          curl -fsSL https://claude.ai/code/install.sh | sh

      - name: Install Rules Checker
        run: |
          cd unity-rules-checker
          bash install.sh --non-interactive

      - name: Run Rules Check
        run: |
          claude-code skill check-rules Assets/Scripts --severity=CRITICAL

      - name: Comment PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ 代码规则检查未通过，请查看CI日志'
            })
```

---

## 示例4: 多项目共享

### 场景

公司有多个Unity项目，想要共享统一的规则检查工具。

### 方案A: Git Submodule

```bash
# 项目A
cd ProjectA
git submodule add https://github.com/company/unity-rules-checker.git unity-rules-checker
git submodule update --init --recursive
cd unity-rules-checker && ./install.sh

# 项目B
cd ProjectB
git submodule add https://github.com/company/unity-rules-checker.git unity-rules-checker
git submodule update --init --recursive
cd unity-rules-checker && ./install.sh

# 更新所有项目的工具
git submodule update --remote --merge
```

### 方案B: 本地共享

```bash
# 创建共享目录
mkdir -p ~/UnityTools/unity-rules-checker
cp -r /path/to/unity-rules-checker/* ~/UnityTools/unity-rules-checker/

# 在每个项目中创建符号链接
cd ProjectA
ln -s ~/UnityTools/unity-rules-checker unity-rules-checker
cd unity-rules-checker && ./install.sh

cd ../ProjectB
ln -s ~/UnityTools/unity-rules-checker unity-rules-checker
cd unity-rules-checker && ./install.sh
```

---

## 示例5: 自定义规则

### 场景

项目有特殊的命名规范，想要添加到检查规则中。

### 步骤

```bash
# 1. 编辑规则清单
vim docs/开发规则清单.md

# 2. 添加自定义规则
cat >> docs/开发规则清单.md << 'EOF'

## 12. 项目特定规则

### RULE-CUSTOM-001 类名必须符合PascalCase

**必须**: 类名使用PascalCase
**禁止**: 使用下划线或小写开头

```csharp
// ❌ 错误
class playerController { }

// ✅ 正确
class PlayerController { }
```

**严重性**: HIGH
EOF

# 3. 重新检查代码
/check-rules Assets/Scripts
```

---

## 示例6: 排除自动生成代码

### 场景

使用代码生成工具（如protobuf），生成的代码不应检查。

### 步骤

```bash
# 1. 编辑Hook配置
vim .claude/hooks/config.json

# 2. 添加排除模式
{
  "exclude_patterns": [
    "**/Generated/**/*.cs",
    "**/ProtoFiles/**/*.cs",
    "**/Temp/**/*.cs"
  ]
}

# 3. Hook会自动跳过这些文件
```

---

## 示例7: 修复历史代码

### 场景

接手一个旧项目，代码质量较差，需要逐步修复。

### 步骤

```bash
# 1. 只检查CRITICAL规则
/check-rules Assets/Scripts --severity=CRITICAL

# 2. 修复CRITICAL违规

# 3. 逐步提高标准
/check-rules Assets/Scripts --severity=HIGH

# 4. 为新代码应用所有规则
# 配置Git Hook只检查新修改的文件
```

---

## 常见使用场景

| 场景 | 命令 |
|------|------|
| 检查单个文件 | `/check-rules Assets/Scripts/Player.cs` |
| 检查整个目录 | `/check-rules Assets/Scripts` |
| 只检查GC规则 | `/check-rules Assets/Scripts --rules=GC` |
| 只检查CRITICAL | `/check-rules Assets/Scripts --severity=CRITICAL` |
| Code Review前检查 | `/check-rules --files=modified` |
| 提交前检查 | Git Hook自动运行 |

---

## 最佳实践

1. **新项目**: 从第一天就使用，建立良好习惯
2. **现有项目**: 先对新代码使用，逐步修复旧代码
3. **团队协作**: 统一工具版本，定期同步规则
4. **CI/CD**: 集成到PR流程，自动检查
5. **规则定制**: 根据项目特点调整规则

---

*更多示例请参考：[README](unity-rules-checker/README.md)*
