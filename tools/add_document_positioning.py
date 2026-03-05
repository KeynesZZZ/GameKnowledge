#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为文档添加"文档定位"章节
根据文档类型和内容自动生成合适的"文档定位"章节
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Windows UTF-8 encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 文档类型到定位模板的映射
DOC_TYPE_PATTERNS: Dict[str, Dict[str, str]] = {
    "设计原理": {
        "template": """本文档从**底层机制角度**深入讲解{topic}的本质原理。

{related_docs}
""",
        "angle": "底层机制角度"
    },
    "教程": {
        "template": """本文档从**使用角度**讲解{topic}。

{related_docs}
""",
        "angle": "使用角度"
    },
    "代码片段": {
        "template": """本文档从**实践角度**提供{topic}的可复制代码。

{related_docs}
""",
        "angle": "实践角度"
    },
    "最佳实践": {
        "template": """本文档从**最佳实践角度**总结{topic}的推荐做法。

{related_docs}
""",
        "angle": "最佳实践角度"
    },
    "踩坑记录": {
        "template": """本文档从**问题解决角度**记录{topic}的常见问题和解决方案。

{related_docs}
""",
        "angle": "问题解决角度"
    },
    "性能数据": {
        "template": """本文档从**性能测试角度**提供{topic}的客观数据和测试结果。

{related_docs}
""",
        "angle": "性能测试角度"
    },
    "架构决策": {
        "template": """本文档从**方案对比角度**分析{topic}的不同方案。

{related_docs}
""",
        "angle": "方案对比角度"
    },
    "系统架构": {
        "template": """本文档从**系统设计角度**讲解{topic}的整体架构。

{related_docs}
""",
        "angle": "系统设计角度"
    },
}


def extract_doc_info(content: str, filepath: Path) -> Dict[str, any]:
    """从文档内容中提取信息"""
    info = {
        "title": "",
        "doc_type": "",
        "topic": "",
        "has_positioning": False,
        "has_related_links": False
    }

    # 提取 title
    title_match = re.search(r'title:\s*(.+)', content)
    if title_match:
        info["title"] = title_match.group(1).strip()

    # 从标题中提取文档类型和主题
    for doc_type in ["设计原理", "教程", "代码片段", "最佳实践", "踩坑记录", "性能数据", "架构决策", "系统架构"]:
        if doc_type in info["title"]:
            info["doc_type"] = doc_type
            # 提取主题（去除文档类型前缀）
            info["topic"] = info["title"].replace(f"【{doc_type}】", "").strip()
            break

    # 检查是否已有"文档定位"章节
    info["has_positioning"] = "## 文档定位" in content

    # 检查是否已有"相关链接"章节
    info["has_related_links"] = "## 相关链接" in content

    return info


def find_related_docs(topic: str, doc_type: str, all_docs: List[Path]) -> List[str]:
    """根据主题查找相关文档"""
    related = []
    topic_keywords = topic.replace("-", "").replace(" ", "")

    for doc_path in all_docs:
        filename = doc_path.stem
        # 简单匹配：文件名包含主题关键词
        if topic_keywords[:4] in filename.replace("-", "").replace(" ", ""):
            related.append(f"[[{doc_path.parent.name}/{filename}]]")

    # 限制返回数量
    return related[:3]


def generate_positioning_section(info: Dict, all_docs: List[Path]) -> str:
    """生成文档定位章节"""
    if not info["doc_type"]:
        return None

    pattern = DOC_TYPE_PATTERNS.get(info["doc_type"])
    if not pattern:
        return None

    # 查找相关文档
    related_docs = find_related_docs(info["topic"], info["doc_type"], all_docs)

    if related_docs:
        related_text = "**相关文档**：" + "、".join(related_docs[:3])
    else:
        related_text = ""

    positioning = pattern["template"].format(
        topic=info["topic"],
        related_docs=related_text
    ).strip()

    return f"""## 文档定位

{positioning}

---
"""


def add_positioning_to_file(filepath: Path, positioning: str) -> bool:
    """为文件添加文档定位章节"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找插入位置（在第一个一级标题之后）
        lines = content.split('\n')
        insert_idx = -1

        for i, line in enumerate(lines):
            if line.startswith('# ') and not line.startswith('##'):
                # 找到第一个一级标题
                # 跳过标题行本身和可能的引用行
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == '' or lines[j].startswith('>'):
                        continue
                    else:
                        insert_idx = j
                        break
                break

        if insert_idx == -1:
            insert_idx = 2  # 默认在第3行插入

        # 插入文档定位章节
        lines.insert(insert_idx, positioning)
        new_content = '\n'.join(lines)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"❌ 处理文件失败: {filepath}")
        print(f"   错误: {e}")
        return False


def scan_directory(directory: Path) -> List[Path]:
    """扫描目录获取所有 Markdown 文件"""
    md_files = list(directory.rglob('*.md'))
    # 排除 README 文件
    md_files = [f for f in md_files if 'readme' not in f.name.lower()]
    return md_files


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='为文档添加"文档定位"章节')
    parser.add_argument('path', nargs='?', default='UnityKnowledge',
                       help='要扫描的目录路径（默认：UnityKnowledge）')
    parser.add_argument('--dry-run', action='store_true',
                       help='只显示将要修改的文件，不实际修改')

    args = parser.parse_args()

    target_dir = Path(args.path)

    if not target_dir.exists():
        print(f"❌ 目录不存在: {target_dir}")
        return 1

    print(f"🔍 扫描目录: {target_dir}")
    md_files = scan_directory(target_dir)
    print(f"📄 找到 {len(md_files)} 个 Markdown 文件")

    # 统计
    stats = {
        "total": len(md_files),
        "has_positioning": 0,
        "needs_positioning": 0,
        "processed": 0,
        "skipped": 0
    }

    files_to_process = []

    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            info = extract_doc_info(content, filepath)

            if info["has_positioning"]:
                stats["has_positioning"] += 1
            else:
                stats["needs_positioning"] += 1
                if info["doc_type"] and info["topic"]:
                    positioning = generate_positioning_section(info, md_files)
                    if positioning:
                        files_to_process.append((filepath, positioning, info))
        except Exception as e:
            print(f"❌ 读取文件失败: {filepath}")
            print(f"   错误: {e}")

    print(f"\n📊 统计结果:")
    print(f"   总文件数: {stats['total']}")
    print(f"   已有文档定位: {stats['has_positioning']}")
    print(f"   需要添加: {stats['needs_positioning']}")

    if not files_to_process:
        print("\n✅ 所有文件都已有文档定位章节！")
        return 0

    print(f"\n📝 将要处理 {len(files_to_process)} 个文件:\n")

    for filepath, positioning, info in files_to_process[:10]:  # 只显示前10个
        print(f"   [{info['doc_type']}] {info['title']}")

    if len(files_to_process) > 10:
        print(f"   ... 还有 {len(files_to_process) - 10} 个文件")

    if args.dry_run:
        print("\n🔍 --dry-run 模式，不实际修改文件")
        return 0

    # 询问是否继续
    print(f"\n是否继续？(yes/no): ", end='')
    try:
        response = input().strip().lower()
        if response not in ['yes', 'y', '是']:
            print("❌ 已取消")
            return 0
    except KeyboardInterrupt:
        print("\n❌ 已取消")
        return 0

    # 处理文件
    print(f"\n⚙️ 开始处理...\n")

    for filepath, positioning, info in files_to_process:
        success = add_positioning_to_file(filepath, positioning)
        if success:
            stats["processed"] += 1
            print(f"✅ [{info['doc_type']}] {info['title']}")
        else:
            stats["skipped"] += 1

    print(f"\n✨ 完成!")
    print(f"   成功处理: {stats['processed']}")
    print(f"   跳过: {stats['skipped']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
