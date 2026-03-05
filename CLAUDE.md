# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Unity game development learning documentation repository** in Chinese. It is not a code repository - it stores learning notes, code examples, design documents, and project retrospectives. The repository contains **182+ markdown documents** organized by technical domain.

## Content Structure

### `UnityKnowledge/` - Primary Knowledge Base

The main documentation area, organized by technical domain with numbered prefixes:

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

## Tools

### 1. `tools/knowledge_base/` - Semantic Search & RAG

ChromaDB + Claude powered knowledge management system.

**Features**:
- Intelligent document chunking by Markdown structure
- Vector-based semantic search
- RAG (Retrieval-Augmented Generation) Q&A with Claude
- Knowledge relationship discovery

**Prerequisites**:
```bash
pip install chromadb anthropic
```

**Common Commands**:
```bash
cd tools/knowledge_base

# Import documents
python knowledge_base.py import ../../UnityKnowledge

# Semantic search
python knowledge_base.py search "如何优化UGUI的DrawCall?"

# AI Q&A with RAG
python knowledge_base.py ask "UGUI中如何减少GC分配?"

# Find related topics
python knowledge_base.py related "内存管理"

# Check status
python knowledge_base.py status
```

**Configuration**: Edit `config.json` to set Claude API key and adjust parameters.

### 2. `unity-rules-checker/` - Unity Code Quality Checker

A standalone tool for checking Unity C# code against 60 development rules. Integrates with Claude Code via SKILL and Git hooks.

**Features**:
- 60 rules covering GC, memory, UI, architecture, physics, etc.
- AI-powered checking using Claude Code
- Git hook integration for pre-commit checks
- Cross-platform support (Windows, macOS, Linux)

**Installation**:
```bash
cd unity-rules-checker
./install.sh          # Linux/Mac
# or
powershell -File install.ps1    # Windows
```

**Usage in Claude Code**:
```bash
# Check single file
/check-rules Assets/Scripts/PlayerController.cs

# Check directory
/check-rules Assets/Scripts

# Check specific rule categories
/check-rules Assets/Scripts --rules=GC,MEMORY

# Check specific severity
/check-rules Assets/Scripts --severity=CRITICAL
```

**Rule Categories**: GC, MEMORY, POOL, ARCH, ASYNC, REFACTOR, UI, PHYSICS, RES, PERF, SAFE

See [unity-rules-checker/README.md](unity-rules-checker/README.md) for complete documentation.

### 3. `.claude/` - Claude Code Configuration

- **hooks/** - Git hook specifications (e.g., pre-commit.md)
- **skills/** - Reusable skills (e.g., check-rules.md for Unity code validation)
- **settings.json** - Permission and directory configurations

## Document Conventions

### Document Types (Filename Prefix)

- `代码片段-*` - Reusable code snippets
- `最佳实践-*` - Recommended practices
- `踩坑记录-*` - Common pitfalls and solutions
- `性能数据-*` - Performance benchmarks
- `设计原理-*` - Design rationale ("why" not just "how")
- `架构决策-*` - Architecture decision records
- `系统架构-*` - System architecture overviews
- `实战案例-*` - Real-world case studies
- `教程-*` - Tutorial content
- `反模式-*` - Common anti-patterns

### YAML Frontmatter (Required for New Docs)

All documents should include YAML frontmatter:

```yaml
---
title: 【代码片段】对象池通用实现
tags: [C#, Unity, 架构, 性能优化, 代码片段]
category: 架构设计/代码片段
created: 2024-01-15 10:30
updated: 2024-03-04 15:20
description: C#泛型对象池的基础实现，减少GC分配
unity_version: 2021.3+
---
```

See [元数据规范.md](UnityKnowledge/00_元数据与模板/元数据规范.md) for complete standards.

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

1. **Choose directory** based on technical domain (use numbering system)
2. **Use template** from `UnityKnowledge/00_元数据与模板/模板-*.md`
3. **Add YAML frontmatter** with title, tags, category, dates
4. **Include code examples** following Unity conventions
5. **Add minimum 2 tags** from tag system
6. **Use internal links** with `[[文档名]]` format for related docs
7. **Update README** in parent directory if needed

## Quick Reference

| Task | Command/Location |
|------|------------------|
| **Search knowledge base** | `cd tools/knowledge_base && python knowledge_base.py search "<query>"` |
| **Ask AI question** | `cd tools/knowledge_base && python knowledge_base.py ask "<question>"` |
| **Import new docs** | `cd tools/knowledge_base && python knowledge_base.py import <path>` |
| **Check knowledge status** | `cd tools/knowledge_base && python knowledge_base.py status` |
| **Check Unity code** | `/check-rules <path>` (in Claude Code) |
| **Setup rules checker** | `cd unity-rules-checker && ./install.sh` |
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
    └── [技术领域]/
        └── README.md → Domain-specific navigation

tools/knowledge_base/
    ├── knowledge_base.py → Semantic search & RAG implementation
    ├── README.md → Tool documentation
    └── config.json → Configuration

unity-rules-checker/
    ├── README.md → Tool documentation
    ├── docs/开发规则清单.md → Complete 60 rules reference
    └── .claude/skills/check-rules.md → Claude Code integration

.claude/
    ├── hooks/pre-commit.md → Git hook specification
    └── skills/ → Reusable Claude Code skills
```

## Statistics

- **Total documents**: 182+ Markdown files
- **Primary domains**: 12 technical areas
- **Tools**: 2 (knowledge base, rules checker)
- **Languages**: Chinese (content), English (code/tooling)
