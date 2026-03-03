# 个人知识库

基于 ChromaDB + Claude 的智能知识管理系统。

## 快速开始

### 1. 安装依赖

```bash
pip install chromadb anthropic
```

### 2. 配置 API Key

编辑 `config.json`，添加你的 Claude API Key：

```json
{
    "claude_api_key": "your-api-key-here"
}
```

或者设置环境变量：

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. 导入文档

```bash
# 导入整个目录
python knowledge_base.py import ../../学习

# 导入单个文件
python knowledge_base.py import ./notes/my_note.md
```

### 4. 搜索知识

```bash
# 语义搜索
python knowledge_base.py search "如何优化UGUI的DrawCall?"

# AI 问答
python knowledge_base.py ask "UGUI中如何减少GC分配?"

# 查找相关知识
python knowledge_base.py related "内存管理"
```

### 5. 查看状态

```bash
python knowledge_base.py status
```

## 命令详解

| 命令 | 说明 | 示例 |
|------|------|------|
| `import <路径>` | 导入 Markdown 文档 | `python knowledge_base.py import ./docs` |
| `search <查询>` | 语义搜索知识库 | `python knowledge_base.py search "事件订阅泄漏"` |
| `ask <问题>` | AI 问答 | `python knowledge_base.py ask "如何排查内存泄漏?"` |
| `related <主题>` | 查找相关知识 | `python knowledge_base.py related "性能优化"` |
| `status` | 查看知识库状态 | `python knowledge_base.py status` |
| `clear` | 清空知识库 | `python knowledge_base.py clear` |

## 功能特点

### 智能分块

- 自动识别 Markdown 标题结构
- 按段落和章节智能分块
- 保持上下文连续性

### 语义搜索

- 基于向量相似度匹配
- 支持自然语言查询
- 返回相关度评分

### RAG 问答

- 基于知识库的智能问答
- 使用 Claude 生成回答
- 引用知识来源

### 知识关联

- 发现直接相关文档
- 推荐相关主题
- 智能建议阅读

## 配置选项

编辑 `config.json` 自定义配置：

```json
{
    "db_path": "./chroma_db",           // 数据库存储路径
    "collection_name": "knowledge_base", // 集合名称
    "chunk_size": 1000,                // 每块最大字符数
    "chunk_overlap": 200,              // 块之间的重叠字符数
    "claude_model": "claude-sonnet-4-20250514" // Claude 模型
}
```

## 与 Obsidian 配合使用

1. 将 Obsidian 库导出到 Markdown 文件
2. 使用 `import` 命令导入
3. 在 Obsidian 中使用 Smart Connections 插件实现本地 AI 问答

## 与 Claude Code 配合使用

在 Claude Code 中，你可以直接引用知识库内容：

```python
# 示例：查询知识库
import subprocess
result = subprocess.run(
    ["python", "knowledge_base.py", "search", "内存泄漏"],
    capture_output=True, text=True
)
print(result.stdout)
```

## 文件结构

```
knowledge_base/
├── knowledge_base.py   # 主脚本
├── config.json         # 配置文件
├── README.md           # 本文档
└── chroma_db/          # 向量数据库（自动创建）
```

## 注意事项

1. **首次运行**：ChromaDB 会自动下载 embedding 模型（约 100MB）
2. **API 费用**：使用 Claude API 会产生费用
3. **隐私**：所有数据存储在本地，不会上传到云端

## 更新知识库

```bash
# 重新导入更新的文档
python knowledge_base.py import ./updated_doc.md

# 或清空后重新导入
python knowledge_base.py clear
python knowledge_base.py import ../../学习
```
