"""
generate_index.py - UnityKnowledge 索引与知识图谱生成脚本
解析所有文档的元数据和关系字段，生成多种索引视图。

用法：
    python scripts/generate_index.py                    # 生成所有索引
    python scripts/generate_index.py --format markdown  # 仅生成Markdown索引
    python scripts/generate_index.py --format mermaid   # 生成Mermaid知识图谱
    python scripts/generate_index.py --format json      # 生成JSON数据（供前端使用）

输出：
    _generated/INDEX.md          - 全量文档索引
    _generated/KNOWLEDGE_GRAPH.md - Mermaid知识图谱
    _generated/knowledge_data.json - JSON数据
    _generated/LEARNING_PATHS.md  - 自动生成的学习路径
"""

import os
import sys
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any

# ============================================================
# 配置
# ============================================================

SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]
SKIP_FILES = ["README.md"]
OUTPUT_DIR = "_generated"

# ============================================================
# 解析
# ============================================================

def extract_frontmatter(filepath: Path) -> Optional[Dict]:
    """从Markdown文件中提取YAML Frontmatter"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = filepath.read_text(encoding="gbk")
        except Exception:
            return None

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def scan_all_docs(root: Path) -> List[Dict]:
    """扫描所有文档，提取元数据"""
    docs = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".md") or filename in SKIP_FILES:
                continue
            filepath = Path(dirpath) / filename
            meta = extract_frontmatter(filepath)
            if meta:
                meta["_filepath"] = str(filepath.relative_to(root))
                meta["_filename"] = filename
                docs.append(meta)
    return docs

# ============================================================
# 索引生成
# ============================================================

def generate_markdown_index(docs: List[Dict], root: Path) -> str:
    """生成Markdown全量索引"""
    lines = [
        "# UnityKnowledge 文档索引",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}，共 {len(docs)} 篇文档",
        "",
    ]

    # 按category分组
    by_category = defaultdict(list)
    for doc in docs:
        cat = doc.get("category", "未分类")
        by_category[cat].append(doc)

    for cat in sorted(by_category.keys()):
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| 文档 | 状态 | 验证 | 更新时间 |")
        lines.append("|------|------|------|----------|")
        for doc in sorted(by_category[cat], key=lambda d: d.get("title", "")):
            title = doc.get("title", doc["_filename"])
            status = doc.get("status", "-")
            validation = doc.get("validation", "-")
            updated = str(doc.get("updated", "-"))[:10]
            filepath = doc["_filepath"].replace("\\", "/")
            lines.append(f"| [{title}]({filepath}) | {status} | {validation} | {updated} |")
        lines.append("")

    # 统计信息
    lines.append("---")
    lines.append("")
    lines.append("## 统计")
    lines.append("")

    # 按类型统计
    by_type = defaultdict(int)
    for doc in docs:
        title = doc.get("title", "")
        match = re.match(r"【(.+?)】", title)
        if match:
            by_type[match.group(1)] += 1
        else:
            by_type["其他"] += 1

    lines.append("### 按文档类型")
    lines.append("")
    lines.append("| 类型 | 数量 |")
    lines.append("|------|------|")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append(f"| {t} | {count} |")
    lines.append("")

    # 按状态统计
    by_status = defaultdict(int)
    for doc in docs:
        by_status[doc.get("status", "未标注")] += 1

    lines.append("### 按状态")
    lines.append("")
    lines.append("| 状态 | 数量 |")
    lines.append("|------|------|")
    for s, count in sorted(by_status.items(), key=lambda x: -x[1]):
        lines.append(f"| {s} | {count} |")
    lines.append("")

    return "\n".join(lines)


def generate_mermaid_graph(docs: List[Dict]) -> str:
    """生成Mermaid知识图谱"""
    lines = [
        "# UnityKnowledge 知识图谱",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "```mermaid",
        "graph LR",
    ]

    # 为每个文档生成节点ID
    doc_ids = {}
    for i, doc in enumerate(docs):
        title = doc.get("title", doc["_filename"])
        safe_id = f"doc{i}"
        doc_ids[title] = safe_id
        # 截断过长的标题
        short_title = title[:30] + "..." if len(title) > 30 else title
        lines.append(f"    {safe_id}[\"{short_title}\"]")

    lines.append("")

    # 生成关系边
    relation_styles = {
        "prerequisite": "-->|前置知识|",
        "depends_on": "-->|依赖|",
        "is_example_for": "-.->|案例|",
        "refutes": "-->|反驳|",
        "supersedes": "-->|取代|",
        "related": "---|相关|",
    }

    for doc in docs:
        title = doc.get("title", "")
        src_id = doc_ids.get(title)
        if not src_id:
            continue

        for rel_type, arrow in relation_styles.items():
            targets = doc.get(rel_type, [])
            if not isinstance(targets, list):
                continue
            for target in targets:
                # 尝试匹配目标文档
                target_clean = target.replace(".md", "").strip()
                tgt_id = doc_ids.get(target_clean)
                if tgt_id:
                    lines.append(f"    {src_id} {arrow} {tgt_id}")

    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def generate_json_data(docs: List[Dict]) -> str:
    """生成JSON数据供前端使用"""
    clean_docs = []
    for doc in docs:
        clean = {}
        for key, value in doc.items():
            if key.startswith("_"):
                clean[key.lstrip("_")] = value
            elif isinstance(value, datetime):
                clean[key] = value.isoformat()
            else:
                clean[key] = value
        clean_docs.append(clean)

    return json.dumps(clean_docs, ensure_ascii=False, indent=2)


def generate_learning_paths(docs: List[Dict]) -> str:
    """基于prerequisite关系自动生成学习路径"""
    lines = [
        "# 自动生成的学习路径",
        "",
        f"> 基于文档间的 prerequisite 关系自动生成，{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # 构建依赖图
    has_prereq = {}
    is_prereq_of = defaultdict(list)

    for doc in docs:
        title = doc.get("title", "")
        prereqs = doc.get("prerequisite", [])
        if isinstance(prereqs, list) and prereqs:
            has_prereq[title] = prereqs
            for p in prereqs:
                is_prereq_of[p.replace(".md", "").strip()].append(title)

    # 找出入口文档（没有前置知识的文档，但被其他文档依赖）
    entry_docs = []
    for doc in docs:
        title = doc.get("title", "")
        if title not in has_prereq and title in is_prereq_of:
            entry_docs.append(title)

    if entry_docs:
        lines.append("## 推荐学习入口")
        lines.append("")
        for entry in sorted(entry_docs):
            dependents = is_prereq_of.get(entry, [])
            lines.append(f"### {entry}")
            lines.append("")
            lines.append(f"被 {len(dependents)} 篇文档依赖，建议优先学习。")
            lines.append("")
            if dependents:
                lines.append("**后续可学习**：")
                for dep in sorted(dependents):
                    lines.append(f"- {dep}")
                lines.append("")

    # 显示所有依赖链
    if has_prereq:
        lines.append("## 文档依赖关系")
        lines.append("")
        lines.append("| 文档 | 前置知识 |")
        lines.append("|------|----------|")
        for title, prereqs in sorted(has_prereq.items()):
            prereq_str = ", ".join(prereqs)
            lines.append(f"| {title} | {prereq_str} |")
        lines.append("")

    return "\n".join(lines)

# ============================================================
# 主流程
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="UnityKnowledge 索引生成工具")
    parser.add_argument("--format", choices=["all", "markdown", "mermaid", "json"],
                        default="all", help="输出格式")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    output_dir = root / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)

    print(f"🔍 扫描知识库: {root}")
    docs = scan_all_docs(root)
    print(f"📄 找到 {len(docs)} 篇文档")

    if args.format in ("all", "markdown"):
        index = generate_markdown_index(docs, root)
        (output_dir / "INDEX.md").write_text(index, encoding="utf-8")
        print(f"✅ 已生成: {output_dir / 'INDEX.md'}")

        paths = generate_learning_paths(docs)
        (output_dir / "LEARNING_PATHS.md").write_text(paths, encoding="utf-8")
        print(f"✅ 已生成: {output_dir / 'LEARNING_PATHS.md'}")

    if args.format in ("all", "mermaid"):
        graph = generate_mermaid_graph(docs)
        (output_dir / "KNOWLEDGE_GRAPH.md").write_text(graph, encoding="utf-8")
        print(f"✅ 已生成: {output_dir / 'KNOWLEDGE_GRAPH.md'}")

    if args.format in ("all", "json"):
        data = generate_json_data(docs)
        (output_dir / "knowledge_data.json").write_text(data, encoding="utf-8")
        print(f"✅ 已生成: {output_dir / 'knowledge_data.json'}")

    print(f"\n🎉 索引生成完成！")


if __name__ == "__main__":
    main()
