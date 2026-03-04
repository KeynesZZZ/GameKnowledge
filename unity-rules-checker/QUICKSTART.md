# 快速安装指南

## 30秒快速开始

```bash
# 1. 复制工具包到Unity项目根目录
cp -r unity-rules-checker /path/to/YourUnityProject/

# 2. 进入工具包目录
cd unity-rules-checker

# 3. 运行安装脚本
./install.sh          # Mac/Linux
# 或
powershell -File install.ps1    # Windows

# 4. 开始使用
# 在Claude Code中：
/check-rules Assets/Scripts/PlayerController.cs
```

---

## 安装前检查清单

- [ ] 已安装Claude Code CLI
- [ ] 在Unity项目根目录（能看到Assets文件夹）
- [ ] 有写权限（可创建.claude和docs目录）

---

## 安装后验证

```bash
# 检查文件是否正确安装
ls .claude/skills/check-rules.md
ls docs/开发规则清单.md

# 如果Git Hook已安装
ls .git/hooks/pre-commit
```

---

## 常见问题

### Q: 安装脚本无法运行？

**A**: 检查脚本权限：

```bash
chmod +x install.sh
```

Windows用户确保PowerShell版本≥5.1：

```powershell
$PSVersionTable.PSVersion
```

### Q: 找不到规则清单？

**A**: 检查以下路径：

```bash
./docs/开发规则清单.md
unity-rules-checker/docs/开发规则清单.md
```

### Q: Git Hook不工作？

**A**: 检查Git仓库是否存在：

```bash
git status
```

如果提示"not a git repository"，说明项目没有初始化Git。

### Q: 如何跳过Hook检查？

**A**:

```bash
git commit --no-verify -m "message"
```

---

## 需要帮助？

- 查看完整文档：[README.md](README.md)
- 提交Issue：[GitHub Issues](https://github.com/your-username/unity-rules-checker/issues)
