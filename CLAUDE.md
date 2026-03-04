# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Unity game development documentation repository** in Chinese. It stores learning notes, code examples, design documents, and project retrospectives. It is not a code repository - no build/test commands are needed.

## Content Structure

| Directory | Purpose | Use When |
|-----------|---------|----------|
| `学习/` | Systematic tutorials organized by learning progression (01-10 modules) | Learning a topic from scratch |
| `UnityKnowledge/` | Quick reference with numbered prefixes (00-100) for rapid lookup | Finding code snippets, best practices, implementation examples |
| `entities/` | Unity Entities 1.3.2 documentation (Chinese translation) | DOTS/Entities reference |
| `tools/knowledge_base/` | ChromaDB semantic search tool | CLI-based knowledge search |
| `个人知识库搭建.md` | Private RAG knowledge base setup guide (Ollama + Dify) | Setting up local AI Q&A system |

## Document Conventions

### Code Examples
- C# with Unity conventions: `[SerializeField]` for Inspector fields, PascalCase for public methods
- Include `/// <summary>` XML documentation
- Comments in Chinese

### UnityKnowledge Document Types (filename prefixes)
- `代码片段-*` - Reusable code snippets
- `最佳实践-*` - Recommended practices
- `踩坑记录-*` - Common pitfalls and solutions
- `性能数据-*` - Performance benchmarks
- `设计原理-*` / `架构决策-*` - Design rationale and decisions
- `系统架构-*` / `实战案例-*` - Architecture overviews and case studies

### Tag System
Documents in `UnityKnowledge/` use tags (see `00_元数据与模板/标签体系.md`):
- Domain: `#架构`, `#渲染`, `#UI`, `#网络`
- Quality: `#最佳实践`, `#反模式`, `#踩坑记录`
- Type: `#教程`, `#深度解析`, `#代码片段`
- Platform: `#iOS`, `#Android`, `#WebGL`
- Status: `#草稿`, `#待验证`, `#已归档`

## Knowledge Base Tool

Located at `tools/knowledge_base/`:

```bash
python knowledge_base.py import ../../学习                    # Import documents
python knowledge_base.py search "如何优化UGUI的DrawCall?"     # Semantic search
python knowledge_base.py ask "UGUI中如何减少GC分配?"         # AI Q&A with RAG
python knowledge_base.py related "内存管理"                   # Find related topics
python knowledge_base.py status                               # Check status
```

## Creating New Documents

1. **Tutorials/learning** → `学习/` (follow existing module structure)
2. **Quick reference** → `UnityKnowledge/` (use templates from `00_元数据与模板/`)
3. Add at least 2 tags to UnityKnowledge documents
4. Include Unity version compatibility
5. Update relevant README files

## Language

All documents are written in **Chinese (Simplified)**.
