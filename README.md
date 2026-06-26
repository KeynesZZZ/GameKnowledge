# 个人技术知识库

> 面向 Unity 技术架构、AI/LLM 学习、AI 工作流、项目复盘与个人经验沉淀的长期知识系统。

## 知识库组成

| 知识库 | 定位 | 适合沉淀的内容 |
|--------|------|----------------|
| [[UnityKnowledge/README]] | Unity 技术架构知识库 | Unity 架构设计、核心系统、性能优化、工具链、平台适配、项目实战 |
| [[AIKnowledge/README]] | AI 学习与工作流知识库 | Karpathy 式从零构建路线、LLM/Agent、Prompt、AI 辅助开发、实验复现 |

## 使用方式

### 1. 先分类，再写文档

新知识进入知识库前，先判断它解决的是哪类问题：

| 问题类型 | 推荐位置 |
|----------|----------|
| Unity 系统怎么设计 | `UnityKnowledge/10_架构设计` 或 `UnityKnowledge/20_核心系统` |
| Unity 性能怎么优化 | `UnityKnowledge/30_性能优化` |
| Unity 工具链怎么搭建 | `UnityKnowledge/40_工具链` |
| AI 怎么帮我写代码 | `AIKnowledge/30_工作流` |
| AI/LLM 原理怎么学 | `AIKnowledge/10_Karpathy路线` 或 `AIKnowledge/20_LLM基础` |
| 自动化流程怎么搭 | `AIKnowledge/30_工作流` |
| 知识库怎么维护 | `AIKnowledge/30_工作流` |

### 2. 用固定文档类型沉淀知识

优先使用 4 种轻量文档类型：

| 类型 | 用途 |
|------|------|
| `【笔记】` | 学习、理解、概念沉淀 |
| `【踩坑】` | 问题、原因、解决方案 |
| `【复盘】` | 项目、阶段、实验总结 |
| `【片段】` | Prompt、代码、命令、检查清单 |

### 3. 用同一套工作流维护

```mermaid
flowchart LR
    A["输入：问题、项目、经验"] --> B["捕获到 Inbox"]
    B --> C["选择文档类型"]
    C --> D["写入最小 YAML 元数据"]
    D --> E["补充双向链接"]
    E --> F["定期复盘与更新"]
```

## 每周维护清单

- [ ] 把本周解决过的问题沉淀为 `【踩坑】`、`【复盘】` 或 `【片段】`
- [ ] 把重复使用 3 次以上的 Prompt、命令、代码整理为 `【片段】`
- [ ] 给新增文档补齐最小 YAML frontmatter、标签、内部链接
- [ ] 把零散笔记移动到对应知识库目录
- [ ] 检查是否有过期结论，必要时更新 `updated` 字段

## 推荐入口

- [[UnityKnowledge/00_元数据与模板/学习路径导航]]
- [[UnityKnowledge/00_元数据与模板/文档定位指南]]
- [[AIKnowledge/10_Karpathy路线/【教程】Karpathy式AI学习路径]]
- [[AIKnowledge/20_LLM基础/【教程】LLM从字符模型到GPT]]
- [[AIKnowledge/30_工作流/【教程】AI辅助开发工作流]]
- [[AIKnowledge/30_工作流/【最佳实践】个人知识库维护机制]]
