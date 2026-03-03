"""
个人知识库 - 基于 ChromaDB 的智能知识管理

功能：
1. 导入 Markdown 文档并智能分块
2. 向量化存储，支持语义搜索
3. RAG 问答，调用 Claude API
4. 知识关联分析

使用方法：
    # 安装依赖
    pip install chromadb anthropic

    # 导入文档
    python knowledge_base.py import ../../学习

    # 搜索
    python knowledge_base.py search "如何优化UGUI的DrawCall?"

    # 问答
    python knowledge_base.py ask "UGUI中如何减少GC分配?"

    # 查看状态
    python knowledge_base.py status
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# ChromaDB
import chromadb
from chromadb.config import Settings

# Anthropic Claude API
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ============ 配置 ============

@dataclass
class Config:
    """知识库配置"""
    # 数据库路径
    db_path: str = "./chroma_db"

    # 集合名称
    collection_name: str = "knowledge_base"

    # 分块配置
    chunk_size: int = 1000  # 每块最大字符数
    chunk_overlap: int = 200  # 块之间的重叠字符数

    # Embedding 配置
    # ChromaDB 默认使用 all-MiniLM-L6-v2 模型
    # 如果要使用 OpenAI，需要配置 API Key
    embedding_model: str = "default"  # default / openai / claude

    # Claude API (用于问答)
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-20250514"

    @classmethod
    def load(cls, config_path: str = "./config.json") -> None | 'Config':
        """从文件加载配置"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def save(self, config_path: str = "./config.json"):
        """保存配置到文件"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)


# ============ 文档分块器 ============

class MarkdownChunker:
    """Markdown 文档智能分块器"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, content: str, metadata: Dict = None) -> List[Dict]:
        """
        将 Markdown 内容智能分块

        返回：List[Dict]，每个 Dict 包含：
        - text: 块内容
        - metadata: 元数据（包含标题层级等）
        """
        chunks = []

        # 提取标题结构
        sections = self._split_by_headers(content)

        for section in sections:
            # 如果章节太大，进一步分割
            if len(section['content']) > self.chunk_size:
                sub_chunks = self._split_by_size(section['content'])
                for i, sub in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub,
                        'metadata': {
                            **(metadata or {}),
                            'title': section['title'],
                            'level': section['level'],
                            'chunk_index': i,
                            'total_chunks': len(sub_chunks)
                        }
                    })
            else:
                chunks.append({
                    'text': section['content'],
                    'metadata': {
                        **(metadata or {}),
                        'title': section['title'],
                        'level': section['level']
                    }
                })

        return chunks

    def _split_by_headers(self, content: str) -> List[Dict]:
        """按标题分割内容"""
        sections = []
        lines = content.split('\n')

        current_title = ""
        current_content = []
        current_level = 0

        for line in lines:
            # 检测 Markdown 标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # 保存当前章节
                if current_content:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_content).strip(),
                        'level': current_level
                    })

                # 开始新章节
                current_level = len(header_match.group(1))
                current_title = header_match.group(2).strip()
                current_content = [line]
            else:
                current_content.append(line)

        # 保存最后一个章节
        if current_content:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_content).strip(),
                'level': current_level
            })

        # 如果没有标题，将整个内容作为一个章节
        if not sections:
            sections.append({
                'title': 'Untitled',
                'content': content,
                'level': 0
            })

        return sections

    def _split_by_size(self, content: str) -> List[str]:
        """按大小分割内容"""
        chunks = []
        words = content.split()

        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space

            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))

                # 保留一些重叠内容
                overlap_words = current_chunk[-min(len(current_chunk), self.overlap // 5):]
                current_chunk = list(overlap_words)
                current_size = sum(len(w) + 1 for w in overlap_words)

            current_chunk.append(word)
            current_size += word_size

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks


# ============ 知识库核心类 ============

class KnowledgeBase:
    """个人知识库"""

    def __init__(self, config: Config = None):
        self.config = config or Config()

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=self.config.db_path)
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"description": "Personal knowledge base"}
        )

        # 初始化分块器
        self.chunker = MarkdownChunker(
            chunk_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap
        )

        # 初始化 Claude 客户端
        self.claude = None
        if HAS_ANTHROPIC and self.config.claude_api_key:
            self.claude = Anthropic(api_key=self.config.claude_api_key)

    # ========== 文档导入 ==========

    def import_document(self, file_path: str) -> int:
        """
        导入单个 Markdown 文档

        返回：导入的块数量
        """
        path = Path(file_path)

        if not path.exists():
            print(f"文件不存在: {file_path}")
            return 0

        # 读取内容
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据
        metadata = {
            'source': str(path),
            'filename': path.name,
            'imported_at': str(Path.cwd()),
        }

        # 从文件路径提取分类信息
        parts = path.parts
        if '学习' in parts:
            idx = parts.index('学习')
            if idx + 1 < len(parts):
                metadata['category'] = parts[idx + 1]

        # 分块
        chunks = self.chunker.chunk(content, metadata)

        # 添加到向量数据库
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{path.stem}_{i}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append(chunk['metadata'])

        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        print(f"导入 {path.name}: {len(chunks)} 个块")
        return len(chunks)

    def import_directory(self, dir_path: str, pattern: str = "**/*.md") -> int:
        """
        递归导入目录下的所有 Markdown 文档

        返回：总导入块数量
        """
        dir_path = Path(dir_path)

        if not dir_path.exists():
            print(f"目录不存在: {dir_path}")
            return 0

        total_chunks = 0
        files = list(dir_path.glob(pattern))

        print(f"找到 {len(files)} 个文件")

        for file in files:
            total_chunks += self.import_document(str(file))

        print(f"\n导入完成！共 {total_chunks} 个块")
        return total_chunks

    # ========== 搜索 ==========

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        语义搜索

        返回：List[Dict]，每个 Dict 包含：
        - text: 内容
        - metadata: 元数据
        - distance: 距离
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

        return search_results

    def search_by_category(self, query: str, category: str, n_results: int = 5) -> List[Dict]:
        """按分类搜索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"category": category},
            include=['documents', 'metadatas', 'distances']
        )

        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

        return search_results

    # ========== RAG 问答 ==========

    def ask(self, question: str, n_context: int = 5) -> str:
        """
        基于知识库回答问题（RAG）

        参数：
            question: 问题
            n_context: 使用的上下文块数量

        返回：答案字符串
        """
        if not self.claude:
            return "错误：未配置 Claude API Key。请在 config.json 中设置 claude_api_key。"

        # 1. 搜索相关内容
        search_results = self.search(question, n_results=n_context)

        if not search_results:
            return "抱歉，知识库中没有找到相关内容。"

        # 2. 构建上下文
        context_parts = []
        sources = []

        for result in search_results:
            context_parts.append(f"【{result['metadata'].get('title', 'Untitled')}】\n{result['text']}")
            source = result['metadata'].get('source', 'Unknown')
            if source not in sources:
                sources.append(source)

        context = "\n\n---\n\n".join(context_parts)

        # 3. 调用 Claude API
        prompt = f"""基于以下知识库内容回答问题。如果知识库中没有相关信息，请明确说明。

=== 知识库内容 ===
{context}

=== 问题 ===
{question}

请给出详细、准确的回答，并在回答中标注信息来源（如【标题名】）。"""

        try:
            message = self.claude.messages.create(
                model=self.config.claude_model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = message.content[0].text

            # 添加来源信息
            answer += f"\n\n---\n**参考来源**: " + ", ".join(sources[:3])

            return answer

        except Exception as e:
            return f"API 调用失败: {str(e)}"

    # ========== 知识关联 ==========

    def find_related(self, query: str, n_results: int = 10) -> Dict:
        """
        发现知识关联

        返回：
            - direct_matches: 直接匹配
            - related_topics: 相关主题
            - suggestions: 建议阅读
        """
        # 搜索相关内容
        results = self.search(query, n_results=n_results)

        # 提取主题
        topics = {}
        for result in results:
            title = result['metadata'].get('title', 'Untitled')
            category = result['metadata'].get('category', 'Unknown')

            key = f"{category}/{title}"
            if key not in topics:
                topics[key] = {
                    'title': title,
                    'category': category,
                    'source': result['metadata'].get('source', ''),
                    'relevance': 1 - result['distance']
                }
            else:
                topics[key]['relevance'] += 1 - result['distance']

        # 排序
        sorted_topics = sorted(topics.values(), key=lambda x: x['relevance'], reverse=True)

        return {
            'direct_matches': sorted_topics[:3],
            'related_topics': sorted_topics[3:6],
            'suggestions': sorted_topics[6:9]
        }

    # ========== 管理 ==========

    def status(self) -> Dict:
        """获取知识库状态"""
        count = self.collection.count()

        # 获取分类统计
        results = self.collection.get(
            include=['metadatas']
        )

        categories = {}
        for meta in results['metadatas']:
            cat = meta.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_chunks': count,
            'categories': categories,
            'db_path': self.config.db_path
        }

    def clear(self):
        """清空知识库"""
        # 删除并重建集合
        self.client.delete_collection(self.config.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"description": "Personal knowledge base"}
        )
        print("知识库已清空")


# ============ 命令行接口 ============

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              个人知识库 - ChromaDB + Claude                     ║
╚═══════════════════════════════════════════════════════════════╝
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    print_banner()

    # 加载配置
    config = Config.load()

    # 创建知识库
    kb = KnowledgeBase(config)

    command = sys.argv[1]

    if command == "import":
        # 导入文档
        if len(sys.argv) < 3:
            print("用法: python knowledge_base.py import <目录路径>")
            return

        path = sys.argv[2]
        if os.path.isdir(path):
            kb.import_directory(path)
        else:
            kb.import_document(path)

    elif command == "search":
        # 搜索
        if len(sys.argv) < 3:
            print("用法: python knowledge_base.py search <查询>")
            return

        query = " ".join(sys.argv[2:])
        results = kb.search(query)

        print(f"\n搜索: {query}")
        print("-" * 50)

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result['metadata'].get('title', 'Untitled')}")
            print(f"    来源: {result['metadata'].get('source', 'Unknown')}")
            print(f"    相关度: {1 - result['distance']:.2%}")
            print(f"    摘要: {result['text'][:200]}...")

    elif command == "ask":
        # 问答
        if len(sys.argv) < 3:
            print("用法: python knowledge_base.py ask <问题>")
            return

        question = " ".join(sys.argv[2:])
        print(f"\n问题: {question}")
        print("-" * 50)

        answer = kb.ask(question)
        print(answer)

    elif command == "related":
        # 知识关联
        if len(sys.argv) < 3:
            print("用法: python knowledge_base.py related <主题>")
            return

        topic = " ".join(sys.argv[2:])
        related = kb.find_related(topic)

        print(f"\n主题: {topic}")
        print("-" * 50)

        print("\n直接相关:")
        for item in related['direct_matches']:
            print(f"  • {item['title']} ({item['category']})")

        print("\n相关主题:")
        for item in related['related_topics']:
            print(f"  • {item['title']} ({item['category']})")

        print("\n建议阅读:")
        for item in related['suggestions']:
            print(f"  • {item['title']} ({item['category']})")

    elif command == "status":
        # 状态
        status = kb.status()

        print("\n知识库状态:")
        print("-" * 50)
        print(f"总块数: {status['total_chunks']}")
        print(f"数据库: {status['db_path']}")
        print("\n分类统计:")
        for cat, count in sorted(status['categories'].items()):
            print(f"  {cat}: {count} 块")

    elif command == "clear":
        # 清空
        confirm = input("确定要清空知识库吗？(yes/no): ")
        if confirm.lower() == 'yes':
            kb.clear()
        else:
            print("已取消")

    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
