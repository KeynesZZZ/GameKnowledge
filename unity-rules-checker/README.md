# Unity开发规则检查工具

> 🚀 开箱即用的Unity代码质量检查工具 - 基于Claude Code SKILL

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](VERSION)
[![Rules](https://img.shields.io/badge/rules-60-green.svg)](docs/开发规则清单.md)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## ✨ 特性

- ✅ **60条Unity开发规则** - 覆盖GC、内存、UI、架构、物理等11个领域
- 🤖 **AI智能检查** - 利用Claude Code理解代码上下文
- 🚦 **三级严重性** - CRITICAL/HIGH/MEDIUM，明确修复优先级
- 🔄 **Git Hook集成** - 提交前自动检查，防止违规代码入库
- 📦 **开箱即用** - 一键安装，无需手动配置
- 🌍 **跨平台支持** - Windows、macOS、Linux全平台支持

---

## 📋 规则分类

| 类别 | 规则数 | 检查内容 |
|------|--------|----------|
| GC优化 | 7条 | Update中的字符串拼接、new集合、LINQ等 |
| 内存管理 | 4条 | 事件订阅、协程、静态集合、DOTween |
| 对象池 | 3条 | 高频对象池化、状态重置 |
| 架构设计 | 7条 | 单例使用、事件触发、组件化等 |
| 异步编程 | 2条 | 协程嵌套、取消支持 |
| 重构规则 | 6条 | 类大小、方法长度、嵌套层次等 |
| UI优化 | 5条 | Canvas拆分、Text更新、虚拟列表等 |
| 物理系统 | 4条 | 碰撞体选择、碰撞矩阵、NonAlloc等 |
| 资源管理 | 5条 | Addressables、异步加载、Handle释放 |
| 编译期优化 | 4条 | sealed、struct、泛型等 |
| 代码安全 | 4条 | null检查、异常处理、TryGet模式 |

详见：[开发规则清单.md](docs/开发规则清单.md)

---

## 🚀 快速开始

### 前置要求

1. **Unity项目** - Unity 2019.4或更高版本
2. **Claude Code** - 已安装Claude Code CLI（[安装指南](https://claude.ai/code)）
3. **Git** - 可选，用于Git Hook功能

### 安装步骤

#### 方法1: 克隆仓库（推荐）

```bash
# 在Unity项目根目录执行
cd YourUnityProject/

# 克隆工具包
git clone https://github.com/your-username/unity-rules-checker.git
cd unity-rules-checker

# 运行安装脚本
./install.sh          # Linux/Mac
# 或
powershell -File install.ps1    # Windows
```

#### 方法2: 下载压缩包

1. 从 [Releases](https://github.com/your-username/unity-rules-checker/releases) 下载最新版本
2. 解压到Unity项目根目录
3. 运行安装脚本（同方法1）

#### 方法3: 直接复制文件

```bash
# 复制整个工具包目录到Unity项目
cp -r unity-rules-checker /path/to/YourUnityProject/

# 手动复制文件（如果需要）
mkdir -p .claude/skills .claude/hooks docs
cp unity-rules-checker/.claude/skills/check-rules.md .claude/skills/
cp unity-rules-checker/.claude/hooks/* .claude/hooks/
cp unity-rules-checker/docs/开发规则清单.md docs/
```

### 安装验证

安装成功后，你将看到：

```
✓ Unity开发规则检查工具安装成功！

使用方法：
1. 在Claude Code中运行：
   /check-rules Assets/Scripts/YourScript.cs
```

---

## 📖 使用方法

### 基本用法

在Claude Code中直接调用SKILL：

```bash
# 检查单个文件
/check-rules Assets/Scripts/PlayerController.cs

# 检查整个目录
/check-rules Assets/Scripts

# 检查多个文件
/check-rules Assets/Scripts/*.cs
```

### 高级选项

```bash
# 只检查特定规则类别
/check-rules Assets/Scripts --rules=GC,MEMORY

# 可选类别: GC, MEMORY, POOL, ARCH, ASYNC, REFACTOR, UI, PHYSICS, RES, PERF, SAFE

# 只检查特定严重性
/check-rules Assets/Scripts --severity=CRITICAL

# 可选严重性: CRITICAL, HIGH, MEDIUM, LOW
```

### Git Hook使用

如果安装了Git Hook，每次提交时会自动检查：

```bash
git add .
git commit -m "feat: add player controller"
# → 自动触发规则检查
# → CRITICAL违规会阻止提交
```

### 跳过Hook检查（不推荐）

```bash
git commit --no-verify -m "提交信息"
```

---

## 📊 检查报告示例

```
🔍 检查文件: Assets/Scripts/PlayerController.cs

✅ 通过规则: 53条
⚠️  发现违规: 7条

🔴 CRITICAL (3):
  [RULE-MEM-001] 事件订阅未配对取消
    位置: Line 47
    代码: EventBus.Subscribe<PlayerEvent>(OnPlayerEvent);

    ❌ 问题: 在OnEnable中订阅事件，但没有在OnDisable中取消订阅

    ✅ 修复:
    private void OnDisable()
    {
        EventBus.Unsubscribe<PlayerEvent>(OnPlayerEvent);
    }

🟠 HIGH (4):
  [RULE-GC-001] Update中字符串拼接
  [RULE-GC-004] Update中GetComponent
  [RULE-ARCH-006] public字段暴露
  [RULE-ARCH-004] GameObject.Find使用

📊 检查摘要:
  - 检查文件: 1个
  - 代码行数: 75行
  - 违规数量: 7个 (CRITICAL: 3, HIGH: 4)
  - 预计修复时间: 15分钟
```

---

## 🔧 配置选项

### Git Hook配置

编辑 `.claude/hooks/config.json`:

```json
{
  "block_on": "CRITICAL",           // 阻止提交的最低级别
  "warn_on": "HIGH",                // 警告的最低级别
  "check_patterns": ["Assets/**/*.cs"],
  "exclude_patterns": [
    "**/Generated/**/*.cs",
    "**/Temp/**/*.cs",
    "**/Plugins/**/*.cs"
  ],
  "auto_fix": false,                // 是否自动修复（未来功能）
  "fail_on_violations": true        // 发现违规时是否失败
}
```

### 规则清单位置

工具会自动在以下位置查找规则清单：

1. `./docs/开发规则清单.md` - 项目本地（优先）
2. `unity-rules-checker/docs/开发规则清单.md` - 工具包目录
3. 用户全局Knowledge目录（Claude Code配置）

---

## 🗑️ 卸载

### Windows

```powershell
Remove-Item -Recurse -Force .claude\skills\check-rules.md
Remove-Item -Recurse -Force .claude\hooks
Remove-Item -Recurse -Force docs\开发规则清单.md
Remove-Item -Force .git\hooks\pre-commit
Remove-Item -Recurse -Force unity-rules-checker
```

### Linux/Mac

```bash
rm -rf .claude/skills/check-rules.md
rm -rf .claude/hooks
rm -rf docs/开发规则清单.md
rm -f .git/hooks/pre-commit
rm -rf unity-rules-checker
```

---

## 🔄 更新

```bash
cd unity-rules-checker
git pull origin main

# 重新运行安装脚本
./install.sh          # Linux/Mac
# 或
powershell -File install.ps1    # Windows
```

---

## 📚 文档

- [开发规则清单.md](docs/开发规则清单.md) - 完整的60条规则
- [自动化规则检查工具.md](docs/自动化规则检查工具.md) - 详细使用文档
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Claude Code](https://claude.ai/code) - 强大的AI代码助手
- Unity社区 - 提供了大量性能优化最佳实践

---

## 📮 联系方式

- Issues: [GitHub Issues](https://github.com/your-username/unity-rules-checker/issues)
- Email: your-email@example.com

---

*最后更新: 2026-03-04*
*工具版本: v1.0.0*
