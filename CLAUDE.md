# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Unity game development learning documentation repository** containing systematic study notes in Chinese for a Match-3 + Roguelike game project. It is not a code repository - it stores learning notes, code examples, design documents, and project retrospectives.

## Content Structure

This repository has **three main documentation areas** with different purposes:

### 1. `学习/` - Systematic Learning Path

Tutorial-focused content organized by learning progression:

```
学习/
├── 01-脚本与架构/      # Unity 基础与设计模式
├── 02-渲染与图形/      # Shader、渲染管线、视觉效果
├── 03-游戏系统开发/    # UI、三消、战斗、Roguelike
├── 04-性能优化/        # 分析工具、CPU/渲染优化
├── 05-高级主题/        # 内存、网络、热更新
├── 06-高级编程/        # C#高级特性、并发、高性能编程
├── 07-DOTS技术栈/      # Job System、Burst、ECS
├── 08-编辑器扩展/      # EditorWindow、Inspector、Gizmos
├── 09-动画系统/        # Animator、混合树、IK、Playables
└── 10-网络编程实战/    # Socket、同步模型、服务器架构
```

### 2. `UnityKnowledge/` - Quick Reference Knowledge Base

Structured for rapid lookup, organized by technical domain with numbered prefixes:

```
UnityKnowledge/
├── 00_元数据与模板/    # Templates (代码片段, Bug记录, 性能分析) + 标签体系
├── 10_架构设计/        # Design patterns, architecture decisions
├── 20_核心系统/        # Physics, Animation, Rendering, Audio, Network
├── 30_性能优化/        # Memory, Rendering, Code optimization
├── 40_工具链/          # Editor, Addressables, Build pipeline
├── 50_平台适配/        # iOS, Android, WebGL, Consoles
├── 60_第三方库/        # DOTween, UniTask, Zenject, Odin
├── 90_项目复盘/        # Project retrospectives
└── 100_项目实战/       # Real-world implementations (e.g., Cloud Save System)
```

### 3. `entities/` - Unity DOTS Entities Documentation

Chinese translation of Unity Entities 1.3.2 documentation (ChatGPT-translated with additional explanations).

**Online version**: https://zhangkeng.gitbook.io/entities-zhong-wen-fan-yi/

### 4. `tools/knowledge_base/` - Semantic Search Tool

ChromaDB-based knowledge management for semantic search and RAG Q&A.

**Prerequisites**: Requires Python 3.8+ and dependencies (`pip install chromadb anthropic`)

### 5. `个人知识库搭建.md` - Private Knowledge Base Setup

Guide for setting up a private RAG system using Dify + Ollama for local AI-powered knowledge management.

## When to Use Which Directory

| Scenario | Use Directory |
|----------|---------------|
| Learning a topic from scratch | `学习/` |
| Quick code snippet lookup | `UnityKnowledge/` |
| Finding best practices | `UnityKnowledge/` |
| DOTS/Entities reference | `entities/` |
| Project implementation examples | `UnityKnowledge/100_项目实战/` |

## Document Conventions

### Code Examples

All code examples use C# and follow Unity conventions:
- Use `[SerializeField]` for Inspector-exposed fields
- Include `/// <summary>` XML documentation comments
- Follow Unity naming conventions (PascalCase for public methods)
- Comments in Chinese for consistency

### Document Format

- Markdown format with Chinese content
- ASCII diagrams for architecture visualization
- Self-contained documents with clear objectives

### UnityKnowledge Document Types

Identified by filename prefix:
- `代码片段-*` - Reusable code snippets
- `最佳实践-*` - Recommended practices
- `踩坑记录-*` - Common pitfalls and solutions
- `性能数据-*` - Performance benchmarks
- `设计原理-*` - Design rationale ("why" not just "how")
- `架构决策-*` - Architecture decision records
- `系统架构-*` - System architecture overviews
- `实战案例-*` - Real-world case studies

### Unity Version Coverage

Documentation primarily covers **Unity 2021.3 LTS** and later versions, including:
- Unity 2021.3 LTS (Linerenderer & URP)
- Unity 2022.3 LTS (URP & HDRP)
- Unity 6 (when applicable)

When creating code examples, specify the minimum Unity version required if using features from specific versions.

### Tag System

Documents in `UnityKnowledge/` use tags (defined in `00_元数据与模板/标签体系.md`):
- Technical domain: `#架构`, `#渲染`, `#UI`, `#网络`, etc.
- Quality: `#最佳实践`, `#反模式`, `#踩坑记录`
- Document type: `#教程`, `#深度解析`, `#代码片段`
- Platform: `#iOS`, `#Android`, `#WebGL`
- Status: `#草稿`, `#待验证`, `#已归档`

## Knowledge Base Tool

Located at `tools/knowledge_base/`.

### Prerequisites

```bash
# Install Python dependencies
pip install chromadb anthropic

# Configure API key in config.json or set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Common Commands

```bash
# Import documents
python knowledge_base.py import ../../学习

# Semantic search
python knowledge_base.py search "如何优化UGUI的DrawCall?"

# AI Q&A with RAG
python knowledge_base.py ask "UGUI中如何减少GC分配?"

# Find related topics
python knowledge_base.py related "内存管理"

# Check status
python knowledge_base.py status
```

## Language

All documents are written in **Chinese (Simplified)**. When editing or creating documents, maintain Chinese language consistency.

## When Creating New Documents

1. **For tutorials/learning** → `学习/` - follow learning path structure
2. **For quick reference** → `UnityKnowledge/` - use appropriate template from `00_元数据与模板/`
3. Add at least 2 tags to UnityKnowledge documents
4. Include Unity version compatibility
5. Update relevant README files

## Quick Tasks

| Task | Command |
|------|---------|
| **Search knowledge base** | `cd tools/knowledge_base && python knowledge_base.py search "<query>"` |
| **Ask AI question** | `cd tools/knowledge_base && python knowledge_base.py ask "<question>"` |
| **Import new docs** | `cd tools/knowledge_base && python knowledge_base.py import <path>` |
| **Check knowledge status** | `cd tools/knowledge_base && python knowledge_base.py status` |
| **Setup private RAG** | Read `个人知识库搭建.md` for Dify + Ollama guide |
