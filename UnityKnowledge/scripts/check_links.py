"""
check_links.py - UnityKnowledge 链接检查脚本（无第三方依赖版本）
检查文档中的Obsidian双向链接和Markdown链接是否指向实际存在的文件。

用法：
    python scripts/check_links.py                # 检查所有文档
    python scripts/check_links.py --path 10_架构设计  # 检查指定目录

退出码：
    0 - 全部通过
    1 - 存在断链
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# ============================================================
# 配置
# ============================================================

SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]

# ============================================================
# 文件索引
# ============================================================

def build_file_index(root: Path) -> Dict[str, Path]:
    """构建文件名到路径的索引"""
    index = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".md"):
                filepath = Path(dirpath) / filename
                name_no_ext = filename[:-3]
                index[name_no_ext] = filepath
                index[filename] = filepath
    return index


def extract_links(filepath: Path) -> List[Tuple[str, str, int]]:
    """提取文档中的所有链接，返回 [(link_text, link_type, line_number)]"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = filepath.read_text(encoding="gbk")
        except Exception:
            return []

    links = []
    in_code_block = False
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Obsidian双向链接: [[xxx]] 或 [[xxx|显示文本]]
        for match in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", line):
            links.append((match.group(1).strip(), "obsidian", i))

        # Markdown链接: [text](path) - 排除http链接和纯锚点
        for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", line):
            url = match.group(2).strip()
            if not url.startswith(("http://", "https://", "#", "mailto:")):
                links.append((url, "markdown", i))

    return links


def resolve_obsidian_link(link: str, source_file: Path, root: Path, file_index: Dict[str, Path]) -> bool:
    """解析Obsidian链接，判断目标是否存在"""
    link_clean = link.split("#")[0].strip()
    if not link_clean:
        return True

    # 1. 直接匹配文件名
    if link_clean in file_index:
        return True
    if link_clean + ".md" in file_index:
        return True

    # 2. 只取最后一段文件名匹配
    basename = link_clean.split("/")[-1]
    if basename in file_index:
        return True
    if basename + ".md" in file_index:
        return True

    # 3. 相对路径解析
    source_dir = source_file.parent
    target = source_dir / link_clean
    if target.exists():
        return True
    target_md = source_dir / (link_clean + ".md")
    if target_md.exists():
        return True

    # 4. 从根目录解析
    target = root / link_clean
    if target.exists():
        return True
    target_md = root / (link_clean + ".md")
    if target_md.exists():
        return True

    return False


def resolve_markdown_link(link: str, source_file: Path, root: Path) -> bool:
    """解析Markdown链接，判断目标是否存在"""
    link_clean = link.split("#")[0].split("?")[0].strip()
    if not link_clean:
        return True

    source_dir = source_file.parent
    target = source_dir / link_clean
    return target.exists()


def find_similar(link: str, file_index: Dict[str, Path]) -> List[str]:
    """模糊匹配，找到可能的正确文件名"""
    link_clean = link.split("#")[0].split("/")[-1].replace(".md", "").strip()
    if not link_clean:
        return []

    suggestions = []
    link_lower = link_clean.lower()
    for name in file_index:
        name_lower = name.lower().replace(".md", "")
        if link_lower in name_lower or name_lower in link_lower:
            suggestions.append(name)

    # 去重并限制数量
    seen = set()
    unique = []
    for s in suggestions:
        base = s.replace(".md", "")
        if base not in seen:
            seen.add(base)
            unique.append(s)
    return unique[:5]

# ============================================================
# 主流程
# ============================================================

def check_links(root: Path, target_path: str = "."):
    """检查链接"""
    file_index = build_file_index(root)
    target = root / target_path

    total_links = 0
    broken_count = 0
    files_with_issues = 0
    broken_details = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            filepath = Path(dirpath) / filename
            links = extract_links(filepath)
            file_broken = []

            for link_text, link_type, line_num in links:
                total_links += 1
                if link_type == "obsidian":
                    exists = resolve_obsidian_link(link_text, filepath, root, file_index)
                else:
                    exists = resolve_markdown_link(link_text, filepath, root)

                if not exists:
                    broken_count += 1
                    suggestions = find_similar(link_text, file_index)
                    file_broken.append((link_text, link_type, line_num, suggestions))

            if file_broken:
                files_with_issues += 1
                try:
                    rel_path = filepath.relative_to(root)
                except ValueError:
                    rel_path = filepath
                broken_details[str(rel_path)] = file_broken

    return total_links, broken_count, files_with_issues, broken_details


def main():
    parser = argparse.ArgumentParser(description="UnityKnowledge 链接检查工具")
    parser.add_argument("--path", default=".", help="要检查的目录路径")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent

    print(f"\U0001f517 正在检查链接: {root / args.path}")
    print("=" * 60)

    total, broken, files_count, details = check_links(root, args.path)

    if details:
        for filepath, issues in sorted(details.items()):
            print(f"\n\U0001f4c4 {filepath}")
            for link, ltype, line, suggestions in issues:
                icon = "\U0001f517" if ltype == "obsidian" else "\U0001f4ce"
                print(f"  {icon} 第{line}行 断链: {link}")
                if suggestions:
                    print(f"     \U0001f4a1 可能是: {', '.join(suggestions[:3])}")

    print("\n" + "=" * 60)
    print(f"\U0001f4ca 检查完成")
    print(f"   总链接数: {total}")
    print(f"   \u274c 断链: {broken}")
    print(f"   \U0001f4c4 涉及文件: {files_count}")
    print(f"   \u2705 有效: {total - broken}")

    if broken > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
