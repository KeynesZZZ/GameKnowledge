# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Unity game development learning documentation repository** containing systematic study notes in Chinese. It is not a code repository - it stores learning notes, code examples, and design documents for a Match-3 + Roguelike game project.

## Content Structure

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

tools/
└── knowledge_base/     # ChromaDB 个人知识库脚本
```

## Document Conventions

### Code Examples

All code examples use C# and follow Unity conventions:
- Use `[SerializeField]` for Inspector-exposed fields
- Include `/// <summary>` XML documentation comments
- Follow Unity naming conventions (PascalCase for public methods)

### Document Format

- Use Markdown format with Chinese content
- Include ASCII diagrams for architecture visualization
- Provide both conceptual explanation and practical code examples
- Each document should be self-contained with clear learning objectives

### Code Block Sections

Documents typically include:
1. **Conceptual explanation** - Theory and principles
2. **Code examples** - Practical implementations with comments
3. **Best practices** - Optimization tips and common pitfalls
4. **Summary table** - Quick reference for key points

## Language

All documents are written in **Chinese (Simplified)**. When editing or creating documents, maintain Chinese language consistency. Code comments should also be in Chinese for consistency.

## Knowledge Base Tool

Located at `tools/knowledge_base/`:
- `knowledge_base.py` - ChromaDB-based intelligent knowledge management
- Supports importing Markdown documents for semantic search
- Integrates with Claude API for RAG-based Q&A

## When Creating New Documents

1. Follow the existing structure and style in `学习/` directory
2. Include practical C# code examples with Chinese comments
3. Add ASCII architecture diagrams where helpful
4. Update the relevant `README.md` or learning path file
