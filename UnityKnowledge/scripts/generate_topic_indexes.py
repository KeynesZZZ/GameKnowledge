"""
generate_topic_indexes.py - UnityKnowledge 专题索引生成脚本
基于配置文件扫描知识库，自动生成专题索引文档。

用法：
    python scripts/generate_topic_indexes.py
    python scripts/generate_topic_indexes.py --topic 对象池
    python scripts/generate_topic_indexes.py --config scripts/topic_index_config.json
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from validate_metadata import extract_frontmatter


SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]
SKIP_FILES = ["README.md"]
TYPE_ORDER = [
    "设计原理",
    "教程",
    "系统架构",
    "架构决策",
    "最佳实践",
    "代码片段",
    "性能数据",
    "源码解析",
    "实战案例",
    "踩坑记录",
    "验证报告",
    "反模式",
    "架构演进",
    "其他",
]
READING_PRIORITY = ["设计原理", "教程", "系统架构", "最佳实践", "代码片段", "性能数据", "实战案例", "源码解析", "验证报告"]


def read_text(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="gbk")


def scan_docs(root: Path) -> List[Dict]:
    docs: List[Dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".md") or filename in SKIP_FILES:
                continue
            filepath = Path(dirpath) / filename
            meta = extract_frontmatter(filepath)
            if not meta:
                continue
            docs.append(
                {
                    "path": filepath.relative_to(root),
                    "meta": meta,
                    "content": read_text(filepath),
                }
            )
    return docs


def normalize(value: object) -> str:
    return str(value or "").strip().lower()


def detect_doc_type(title: str) -> str:
    match = re.match(r"^【(.+?)】", title)
    return match.group(1) if match else "其他"


def score_doc(doc: Dict, topic: Dict) -> int:
    path_text = doc["path"].as_posix()
    doc_type = detect_doc_type(str(doc["meta"].get("title", "")))
    if path_text.startswith(("00_元数据与模板/", "01_Inbox/")):
        return 0
    if not topic.get("include_topic_indexes") and path_text.endswith("专题索引.md"):
        return 0
    if doc_type in topic.get("exclude_types", ["模板", "方案"]):
        return 0

    title = normalize(doc["meta"].get("title"))
    description = normalize(doc["meta"].get("description"))
    category = normalize(doc["meta"].get("category"))
    tags = [normalize(tag) for tag in doc["meta"].get("tags", []) if isinstance(tag, str)]
    body = normalize(strip_frontmatter(doc["content"])[:4000])

    score = 0
    for include_dir in topic.get("include_dirs", []):
        if path_text.startswith(include_dir):
            score += 1
            break

    for keyword in topic.get("keywords", []):
        keyword_norm = keyword.lower()
        if keyword_norm in title:
            score += 5
        if keyword_norm in description:
            score += 3
        if keyword_norm in category:
            score += 3
        if any(keyword_norm in tag for tag in tags):
            score += 3
        if keyword_norm in body:
            score += 1
    return score


def strip_frontmatter(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.DOTALL)


def build_link(from_path: Path, to_path: Path, title: str) -> str:
    relative = os.path.relpath(to_path, start=from_path.parent).replace("\\", "/")
    if not relative.startswith("."):
        relative = f"./{relative}"
    return f"[{title}]({relative})"


def summarize_description(description: str) -> str:
    cleaned = str(description or "").strip()
    if not cleaned:
        return "补充文档说明，便于快速判断是否值得深入阅读。"
    return cleaned.rstrip("。") + "。"


def order_type(doc_type: str) -> int:
    try:
        return TYPE_ORDER.index(doc_type)
    except ValueError:
        return len(TYPE_ORDER)


def select_topic_docs(docs: List[Dict], topic: Dict) -> List[Dict]:
    scored = []
    output_path = Path(topic["output"]).as_posix()
    min_score = int(topic.get("min_score", 5))
    for doc in docs:
        if doc["path"].as_posix() == output_path:
            continue
        score = score_doc(doc, topic)
        if score >= min_score:
            doc_copy = dict(doc)
            doc_copy["score"] = score
            doc_copy["doc_type"] = detect_doc_type(str(doc["meta"].get("title", "")))
            scored.append(doc_copy)
    return sorted(
        scored,
        key=lambda item: (
            -item["score"],
            order_type(item["doc_type"]),
            str(item["meta"].get("title", "")),
        ),
    )


def extract_existing_created(output_path: Path) -> Optional[str]:
    if not output_path.exists():
        return None
    meta = extract_frontmatter(output_path)
    if not meta:
        return None
    created = meta.get("created")
    return str(created) if created else None


def build_frontmatter(topic: Dict, output_path: Path) -> str:
    created = extract_existing_created(output_path) or datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    tags = ", ".join(json.dumps(tag, ensure_ascii=False) for tag in topic.get("tags", []))
    related = ", ".join(json.dumps(item, ensure_ascii=False) for item in topic.get("related", []))
    return "\n".join(
        [
            "---",
            f"title: {json.dumps(topic['title'], ensure_ascii=False)}",
            f"tags: [{tags}]",
            f"category: {json.dumps(topic['category'], ensure_ascii=False)}",
            f'created: "{created}"',
            f'updated: "{updated}"',
            f"description: {json.dumps(topic['description'], ensure_ascii=False)}",
            "status: 待验证",
            "validation: Demo验证",
            f"related: [{related}]",
            "---",
        ]
    )


def render_topic_index(root: Path, topic: Dict, topic_docs: List[Dict]) -> str:
    output_path = root / topic["output"]
    frontmatter = build_frontmatter(topic, output_path)
    lines = [
        frontmatter,
        "",
        f"# {topic['title']}",
        "",
        f"> {topic['description']}",
        "",
        "## 文档定位",
        "",
        topic["positioning"],
        "",
        "## 专题概览",
        "",
    ]

    by_type = Counter(doc["doc_type"] for doc in topic_docs)
    by_dir = Counter(str(doc["path"]).split("/")[0] for doc in topic_docs)
    lines.append(f"- 收录文档数：{len(topic_docs)}")
    lines.append(f"- 覆盖目录数：{len(by_dir)}")
    if by_type:
        lines.append("- 文档类型分布：" + "，".join(f"{doc_type}{count}篇" for doc_type, count in sorted(by_type.items(), key=lambda item: (order_type(item[0]), -item[1]))))
    else:
        lines.append("- 当前没有匹配到文档，请调整配置关键词后重试。")
    lines.append("")

    lines.extend(["## 推荐阅读顺序", ""])
    reading_docs = []
    for doc_type in READING_PRIORITY:
        matches = [doc for doc in topic_docs if doc["doc_type"] == doc_type]
        if matches:
            reading_docs.append(matches[0])
    if reading_docs:
        for index, doc in enumerate(reading_docs, 1):
            title = str(doc["meta"].get("title", doc["path"].stem))
            link = build_link(output_path, root / doc["path"], title)
            lines.append(f"{index}. {link} - {summarize_description(doc['meta'].get('description', ''))}")
    else:
        lines.append("1. 暂无匹配文档。")
    lines.append("")

    lines.extend(["## 按文档类型", ""])
    docs_by_type: Dict[str, List[Dict]] = defaultdict(list)
    for doc in topic_docs:
        docs_by_type[doc["doc_type"]].append(doc)

    for doc_type in sorted(docs_by_type.keys(), key=order_type):
        lines.append(f"### {doc_type}")
        lines.append("")
        for doc in docs_by_type[doc_type]:
            title = str(doc["meta"].get("title", doc["path"].stem))
            link = build_link(output_path, root / doc["path"], title)
            category = str(doc["meta"].get("category", "未分类"))
            lines.append(f"- {link} - `{category}` - {summarize_description(doc['meta'].get('description', ''))}")
        lines.append("")

    lines.extend(["## 按目录", ""])
    docs_by_dir: Dict[str, List[Dict]] = defaultdict(list)
    for doc in topic_docs:
        dir_name = str(doc["path"]).split("/")[0]
        docs_by_dir[dir_name].append(doc)

    for dir_name in sorted(docs_by_dir.keys()):
        lines.append(f"### {dir_name}")
        lines.append("")
        for doc in docs_by_dir[dir_name]:
            title = str(doc["meta"].get("title", doc["path"].stem))
            link = build_link(output_path, root / doc["path"], title)
            lines.append(f"- {link}")
        lines.append("")

    lines.extend(["## 相关链接", ""])
    related = topic.get("related", [])
    if related:
        for item in related:
            lines.append(f"- {item}")
    else:
        lines.append("- [[../00_元数据与模板/文档结构规范]]")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="UnityKnowledge 专题索引生成工具")
    parser.add_argument("--topic", help="只生成指定主题")
    parser.add_argument("--config", default="scripts/topic_index_config.json", help="配置文件路径")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    config_path = root / args.config
    topics = json.loads(config_path.read_text(encoding="utf-8"))
    if args.topic:
        topics = [topic for topic in topics if topic["name"] == args.topic or topic["title"] == args.topic]
        if not topics:
            print(f"未找到主题配置: {args.topic}")
            return 1

    docs = scan_docs(root)
    print(f"🔎 扫描完成：{len(docs)} 篇文档")

    for topic in topics:
        selected_docs = select_topic_docs(docs, topic)
        content = render_topic_index(root, topic, selected_docs)
        output_path = root / topic["output"]
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ 已生成 {output_path.relative_to(root)} ({len(selected_docs)} 篇文档)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
