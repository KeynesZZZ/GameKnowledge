# 更新日志 (Changelog)

本文档记录Unity开发规则检查工具的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2026-03-04

### 新增
- ✨ 首次发布可移植版本
- ✅ 支持60条Unity开发规则检查
  - GC优化规则（7条）
  - 内存管理规则（4条）
  - 对象池规则（3条）
  - 架构规则（7条）
  - 异步编程规则（2条）
  - 重构规则（6条）
  - UI优化规则（5条）
  - 物理系统规则（4条）
  - 资源管理规则（5条）
  - 编译期优化规则（4条）
  - 代码安全规则（4条）
- 🔧 Claude Code SKILL集成
- 🔄 Git Hook自动检查
- 📦 跨平台安装脚本（Windows/Linux/Mac）
- 📚 完整的使用文档

### 功能
- 自动路径检测规则清单
- 三级严重性分类（CRITICAL/HIGH/MEDIUM）
- 详细的修复建议
- Git Hook配置文件支持

### 兼容性
- Unity 2019.4+
- Claude Code CLI（最新版）
- Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)

---

## [未来计划]

### v1.1.0（计划中）
- [ ] Python脚本检查工具（CI/CD集成）
- [ ] HTML/JSON报告生成
- [ ] 自动修复部分违规
- [ ] VS Code扩展

### v1.2.0（计划中）
- [ ] Roslyn Analyzer（IDE实时提示）
- [ ] 规则自定义配置
- [ ] 团队规则共享

---

## 版本说明

- **主版本号（Major）**: 不兼容的API更改
- **次版本号（Minor）**: 向下兼容的功能新增
- **修订号（Patch）**: 向下兼容的问题修复

---

*关于本项目版本发布的更多信息，请查看 [GitHub Releases](https://github.com/your-username/unity-rules-checker/releases)*
