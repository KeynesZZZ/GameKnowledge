# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **personal technical knowledge base** in Chinese. It is not primarily a code repository - it stores learning notes, code examples, design documents, AI coding workflows, automation practices, and project retrospectives.

The repository has two major knowledge areas:
- `UnityKnowledge/` - Unity game development, technical architecture, performance, tooling, and project practice
- `AIKnowledge/` - AI/LLM principles, Karpathy-style learning, AI coding workflows, prompt patterns, automation, experiments, and retrospectives

**Repository**: https://github.com/KeynesZZZ/Doc

## LLM-Wiki 维护模式（核心）

本仓库按 Karpathy LLM-Wiki 模式运作：LLM 持续编译并维护一个会复利的 Markdown wiki，人负责 sourcing / 提问 / 验证。

### 三层模型
- **原始层 (raw)**：外部文章/论文，落 `_sources/`，不可变。捕获进 `01_Inbox/` 后提升。
- **笔记层 (wiki)**：现有笔记 + LLM 生成的 `【综述】` 页。`author: llm` 的综合页必须带 `sources:`。
- **schema 层**：本文件（CLAUDE.md）。

### 三个操作
- **ingest**：读源 → 讨论 → 写综述/更新页（碰到的真相层页加 `updated`）→ 更新 `index.md` → 追加 `log.md`。
- **query**：先读 `index.md` 下钻 → 读相关页 → 带引用作答 → 好答案回填为新页（`author: llm` + `sources:`）。
- **lint**：`python3 scripts/lint.py`。ERROR（断链 / 综述缺 sources）阻断；WARN（孤儿页 / 声明无据 / stale）报告。推翻既有结论进 review，不静默改。

### 关键字段
- `author: human|llm`：`human` 是真相源，不可被 LLM 静默改写。
- `sources: [...]`：综述页必填，引用即契约。
- `status`：复用现有 `草稿/待验证/已验证/已过时/已归档`。
- 详细 lint 规则与设计见 `docs/superpowers/specs/2026-06-18-llm-wiki-knowledge-base-design.md`。

## Content Structure

### `UnityKnowledge/` - Unity Technical Architecture Knowledge Base

The Unity documentation area, organized by technical domain with numbered prefixes:

```
UnityKnowledge/
├── 00_元数据与模板/    # Templates, metadata standards, tag system
├── 10_架构设计/        # Design patterns, architecture decisions (36 docs)
├── 20_核心系统/        # Unity core systems (30+ docs)
│   ├── 21_动画系统/   # Animation, State Machine
│   ├── 22_渲染系统/   # Rendering, Shaders, URP
│   ├── 23_物理系统/   # Physics engine
│   ├── 24_输入系统/   # Input management
│   ├── 25_音频系统/   # Audio system
│   └── 游戏系统/      # Game systems
├── 25_DOTS技术栈/     # ECS, Job System, Burst (4 docs)
├── 30_性能优化/        # Performance optimization
│   ├── 31_代码优化/   # Code optimization
│   ├── 32_内存管理/   # Memory management
│   ├── 33_渲染优化/   # Rendering optimization
│   └── 34_启动时间优化/ # Startup time optimization
├── 35_高级主题/        # Advanced topics (4 docs)
├── 36_高级编程/        # Advanced programming (4 docs)
├── 40_工具链/          # Editor extensions, tooling (3 docs)
├── 50_平台适配/        # Platform adaptation (iOS, Android, WebGL)
├── 60_第三方库/        # Third-party libraries (DOTween, UniTask, etc.)
├── 90_项目复盘/        # Project retrospectives
└── 100_项目实战/       # Real-world implementations
    ├── 01_休闲游戏云存档系统/  # Cloud save system
    └── 02_休闲游戏框架/        # Casual game framework
```

**Numbering System**:
- `00` - Metadata & templates
- `10` - Architecture & design
- `20` - Core Unity systems
- `25` - DOTS technology stack
- `30` - Performance optimization
- `35-36` - Advanced topics
- `40` - Tooling
- `50-60` - Platform & libraries
- `90-100` - Real-world experience

See [UnityKnowledge/README.md](UnityKnowledge/README.md) for detailed index.

### `AIKnowledge/` - AI Learning & Workflow Knowledge Base

The AI documentation area, organized around lightweight learning, experiments, and repeatable personal development systems:

```
AIKnowledge/
├── 00_元数据与模板/    # Metadata standards and lightweight templates
├── 01_Inbox/           # Daily capture; classify later
├── 10_Karpathy路线/    # Karpathy-style learning route and reproduction notes
├── 20_LLM基础/         # Tokenizer, Bigram, Transformer, GPT, Agent/RAG
├── 30_工作流/          # Prompt, AI coding workflow, automation, knowledge operations
├── 40_实验复现/        # Local experiments, training logs, failed attempts
└── 90_复盘案例/        # Learning retrospectives, task reviews, project cases
```

**Numbering System**:
- `00` - Metadata & templates
- `01` - Inbox
- `10` - Karpathy-style learning
- `20` - LLM foundations and Agent/RAG concepts
- `30` - AI workflows and automation
- `40` - Experiments and reproduction
- `90` - Retrospectives and cases

See [AIKnowledge/README.md](AIKnowledge/README.md) for detailed index.

## Tools

### 1. `scripts/` - LLM-Wiki 操作脚本

- `lint.py` - 统一 lint：断链 / 综述缺 sources（ERROR 阻断）、孤儿页 / 声明无据 / stale（WARN）。
- `generate_llm_index.py` - 生成各知识库的 `index.md`。
- `migrate_add_author.py` - 批量回填 `author: human` 字段。
- `_frontmatter.py` - 前置元数据解析共享模块。

### 2. `UnityKnowledge/scripts/check_links.py` - Link Validation Tool

Python 脚本校验 Obsidian 风格的 `[[WikiLinks]]`。

```bash
# From repository root
python UnityKnowledge/scripts/check_links.py
```

确保重组或删除后内部链接仍有效。

### 3. `.claude/` - Claude Code 配置

- **skills/** - 可复用 skill：`check-rules.md`（Unity 代码校验）、`create-doc.md`（新建文档）。
- **settings.json** - 权限与目录配置。

## Document Conventions

### Document Types (Filename Prefix)

For new documents, prefer the lightweight V2 type set:

- `【笔记】` - Learning, concepts, explanations
- `【踩坑】` - Problems, causes, fixes
- `【复盘】` - Project, stage, or experiment retrospectives
- `【片段】` - Reusable prompts, commands, code, checklists

Older Unity documents may still use legacy types such as `【教程】`, `【最佳实践】`, `【设计原理】`, `【架构决策】`, `【系统架构】`, `【实战案例】`, and `【代码片段】`. Do not rename old files just for consistency.

### YAML Frontmatter (Required for New Docs)

New documents should include minimal YAML frontmatter:

```yaml
---
title: 【笔记】Self-Attention本质
tags: [AI, LLM, 笔记]
created: 2026-06-17
description: 用最小例子解释 Self-Attention 解决的问题
---
```

Optional fields such as `updated`, `category`, `status`, `tools`, or `unity_version` can be added only when useful. See [AIKnowledge/00_元数据与模板/元数据规范.md](AIKnowledge/00_元数据与模板/元数据规范.md) and [UnityKnowledge/00_元数据与模板/元数据规范.md](UnityKnowledge/00_元数据与模板/元数据规范.md) for domain-specific details.

### Tag System

Documents use tags (defined in [标签体系.md](UnityKnowledge/00_元数据与模板/标签体系.md)):
- **Technical domain**: `#架构`, `#渲染`, `#UI`, `#网络`, `#DOTS`, etc.
- **Quality**: `#最佳实践`, `#反模式`, `#踩坑记录`
- **Document type**: `#教程`, `#深度解析`, `#代码片段`
- **Platform**: `#iOS`, `#Android`, `#WebGL`
- **Status**: `#草稿`, `#待验证`, `#已归档`

Minimum 2 tags per document.

### Code Examples

All code examples follow Unity conventions:
- Use `[SerializeField]` for Inspector-exposed fields
- Include `/// <summary>` XML documentation comments
- Follow Unity naming conventions (PascalCase for public methods)
- Comments in Chinese for consistency
- Specify minimum Unity version if using version-specific features

**Primary coverage**: Unity 2021.3 LTS, Unity 2022.3 LTS, Unity 6

### Obsidian Integration

- Uses Obsidian双向链接 format: `[[文档名]]`
- `.obsidian/` directory contains workspace configuration
- Supports Smart Connections plugin for local AI Q&A

## When Creating New Documents

1. **Capture first** in the nearest `01_Inbox/` when the category is unclear.
2. **Choose directory** based on use case, not taxonomy purity.
3. **Use the minimal template** from `AIKnowledge/00_元数据与模板/【模板】最小知识笔记.md` for AI docs, or existing Unity templates for Unity docs.
4. **Add minimal YAML frontmatter** with `title`, `tags`, `created`, and `description`.
5. **Use internal links** with `[[文档名]]` format for related docs.
6. **Update README** only for high-value, stable entry points.

## Quick Reference

| Task | Command/Location |
|------|------------------|
| **Create new document** | `/create-doc "主题"` (in Claude Code) |
| **Check Unity code** | `/check-rules <path>` (in Claude Code) |
| **统一 lint** | `python3 scripts/lint.py` |
| **生成目录** | `python3 scripts/generate_llm_index.py` |
| **回填 author** | `python3 scripts/migrate_add_author.py` |
| **Validate doc links** | `python UnityKnowledge/scripts/check_links.py` |
| **Find document template** | `UnityKnowledge/00_元数据与模板/模板-*.md` |
| **Read tag system** | `UnityKnowledge/00_元数据与模板/标签体系.md` |
| **View main index** | `UnityKnowledge/README.md` |
| **View projects** | `UnityKnowledge/100_项目实战/README.md` |

## Language

All documents are written in **Chinese (Simplified)**. When editing or creating documents, maintain Chinese language consistency.

## File Relationships

```
CLAUDE.md (this file)
    ├── Repository overview and workflow guidance
    └── Quick reference for common tasks

UnityKnowledge/
    ├── README.md → Complete document index
    ├── 00_元数据与模板/
    │   ├── 元数据规范.md → YAML frontmatter standards
    │   ├── 标签体系.md → Tag taxonomy
    │   └── 模板-*.md → Document templates
    ├── scripts/check_links.py → Validate Obsidian [[WikiLinks]]
    └── [技术领域]/
        └── README.md → Domain-specific navigation

scripts/
    ├── lint.py → 统一 lint（断链 / sources / 孤儿页）
    ├── generate_llm_index.py → 生成 index.md
    ├── migrate_add_author.py → 批量回填 author 字段
    └── _frontmatter.py → 前置元数据解析共享模块

.claude/
    └── skills/ → Reusable Claude Code skills (check-rules, create-doc)
```

## Statistics

- **Total documents**: 182+ Markdown files
- **Primary domains**: 12 technical areas
- **Languages**: Chinese (content), English (code/tooling)
