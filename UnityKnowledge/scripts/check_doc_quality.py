"""
check_doc_quality.py - UnityKnowledge 文档质量检查脚本
在元数据与断链校验之外，补充结构、占位符、过期文档和 Inbox 积压检查。

用法：
    python scripts/check_doc_quality.py
    python scripts/check_doc_quality.py --path 10_架构设计
    python scripts/check_doc_quality.py --strict
    python scripts/check_doc_quality.py --skip-links

退出码：
    0 - 无错误
    1 - 存在错误
    2 - 仅存在警告（严格模式）
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from check_links import check_links
from validate_metadata import extract_frontmatter


SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]
SKIP_FILES = ["README.md"]
STRUCTURE_SECTIONS = ["文档定位", "相关链接"]
PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bXXX\b"),
    re.compile(r"\[\[(?:相关文档|待补充|示例文档)\]\]"),
    re.compile(r"参见\s*\|\s*\|"),
    re.compile(r"→\s*$"),
    re.compile(r"待补充"),
    re.compile(r"待整理"),
]
STALE_STATUSES = {"已过时", "已归档"}
INBOX_DIR = "01_Inbox"


@dataclass
class Issue:
    level: str
    kind: str
    message: str
    line: Optional[int] = None


def iter_markdown_files(root: Path, target_path: str = ".") -> List[Path]:
    target = root / target_path
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".md") and filename not in SKIP_FILES:
                files.append(Path(dirpath) / filename)
    return sorted(files)


def read_text(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="gbk")


def strip_code_blocks(text: str) -> str:
    lines = []
    in_code_block = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            lines.append(line)
    return "\n".join(lines)


def section_body(text: str, section_name: str) -> Optional[str]:
    pattern = rf"(?ms)^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def find_line_number(text: str, pattern: re.Pattern[str]) -> Optional[int]:
    for index, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            return index
    return None


def parse_date(value: object) -> Optional[datetime]:
    if value is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def collect_duplicate_titles(metas: Dict[Path, Dict]) -> Dict[str, List[Path]]:
    title_to_paths: Dict[str, List[Path]] = defaultdict(list)
    for path, meta in metas.items():
        title = str(meta.get("title", "")).strip()
        if title:
            title_to_paths[title].append(path)
    return {title: paths for title, paths in title_to_paths.items() if len(paths) > 1}


def check_structure(filepath: Path, text: str, issues: List[Issue]) -> None:
    for section in STRUCTURE_SECTIONS:
        body = section_body(text, section)
        if body is None:
            issues.append(Issue("ERROR", "结构缺失", f"缺少 `## {section}` 章节"))
            continue
        if section == "相关链接":
            has_link = bool(re.search(r"\[\[.+?\]\]|\[[^\]]+\]\([^)]+\)", body))
            if not has_link:
                issues.append(Issue("WARN", "链接为空", "`相关链接` 章节存在，但没有真实链接"))


def check_placeholders(filepath: Path, text: str, issues: List[Issue]) -> None:
    clean_text = strip_code_blocks(text)
    for pattern in PLACEHOLDER_PATTERNS:
        line = find_line_number(clean_text, pattern)
        if line is not None:
            issues.append(Issue("WARN", "占位符", f"发现疑似占位内容：`{pattern.pattern}`", line))


def check_staleness(filepath: Path, meta: Dict, issues: List[Issue], stale_days: int, inbox_days: int, now: datetime) -> None:
    updated = parse_date(meta.get("updated"))
    status = str(meta.get("status", "")).strip()
    rel_path = filepath.as_posix()
    if updated is None:
        return

    age_days = (now - updated).days
    if INBOX_DIR in rel_path and age_days > inbox_days:
        issues.append(Issue("WARN", "Inbox积压", f"Inbox 文档已 {age_days} 天未整理，建议归类或归档"))
    elif status not in STALE_STATUSES and age_days > stale_days:
        issues.append(Issue("WARN", "长期未更新", f"文档已 {age_days} 天未更新"))

    if status == "Inbox" and INBOX_DIR not in rel_path:
        issues.append(Issue("WARN", "状态异常", "status 为 `Inbox`，但文件不在 `01_Inbox/` 下"))


def build_markdown_report(
    root: Path,
    scanned_files: int,
    issues_by_file: Dict[str, List[Issue]],
    broken_link_summary: Optional[Tuple[int, int, int]],
) -> str:
    counter = Counter(issue.level for issues in issues_by_file.values() for issue in issues)
    lines = [
        "# 文档质量检查报告",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}，扫描 {scanned_files} 篇文档",
        "",
        "## 总览",
        "",
        f"- 错误：{counter.get('ERROR', 0)}",
        f"- 警告：{counter.get('WARN', 0)}",
        f"- 受影响文件：{len(issues_by_file)}",
    ]

    if broken_link_summary is not None:
        total_links, broken_links, files_count = broken_link_summary
        lines.extend(
            [
                f"- 链接检查：{total_links} 个链接，{broken_links} 个断链，影响 {files_count} 个文件",
                "",
            ]
        )
    else:
        lines.append("")

    by_kind = Counter(issue.kind for issues in issues_by_file.values() for issue in issues)
    lines.extend(["## 问题分布", ""])
    for kind, count in by_kind.most_common():
        lines.append(f"- {kind}: {count}")
    lines.append("")

    lines.extend(["## 详细问题", ""])
    for rel_path in sorted(issues_by_file.keys()):
        lines.append(f"### {rel_path}")
        lines.append("")
        for issue in issues_by_file[rel_path]:
            location = f" (第{issue.line}行)" if issue.line else ""
            lines.append(f"- [{issue.level}] {issue.kind}{location}: {issue.message}")
        lines.append("")

    return "\n".join(lines)


def run_quality_checks(root: Path, target_path: str, stale_days: int, inbox_days: int) -> Tuple[List[Path], Dict[Path, List[Issue]], Dict[Path, Dict]]:
    files = iter_markdown_files(root, target_path)
    issues_by_file: Dict[Path, List[Issue]] = {}
    metas: Dict[Path, Dict] = {}
    now = datetime.now()

    for filepath in files:
        rel_path = filepath.relative_to(root)
        issues: List[Issue] = []
        text = read_text(filepath)
        meta = extract_frontmatter(filepath)

        if meta is None:
            issues.append(Issue("ERROR", "元数据缺失", "缺少或无法解析 YAML Frontmatter"))
        else:
            metas[filepath] = meta
            check_structure(filepath, text, issues)
            check_staleness(rel_path, meta, issues, stale_days, inbox_days, now)

        check_placeholders(filepath, text, issues)

        if issues:
            issues_by_file[filepath] = issues

    duplicates = collect_duplicate_titles(metas)
    for title, paths in duplicates.items():
        for filepath in paths:
            issues_by_file.setdefault(filepath, []).append(
                Issue("WARN", "标题重复", f"标题 `{title}` 与其他文档重复")
            )

    return files, issues_by_file, metas


def main() -> int:
    parser = argparse.ArgumentParser(description="UnityKnowledge 文档质量检查工具")
    parser.add_argument("--path", default=".", help="要检查的目录路径")
    parser.add_argument("--strict", action="store_true", help="严格模式：警告也返回非零退出码")
    parser.add_argument("--skip-links", action="store_true", help="跳过断链检查")
    parser.add_argument("--stale-days", type=int, default=180, help="多少天未更新视为长期未更新")
    parser.add_argument("--inbox-days", type=int, default=30, help="Inbox 文档超过多少天视为积压")
    parser.add_argument(
        "--report",
        default="_generated/DOC_QUALITY_REPORT.md",
        help="Markdown 报告输出路径，留空则不写文件",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    output_dir = root / "_generated"
    output_dir.mkdir(exist_ok=True)

    print(f"🩺 正在检查文档质量: {root / args.path}")
    print("=" * 60)

    files, issues_by_file, _ = run_quality_checks(root, args.path, args.stale_days, args.inbox_days)

    broken_summary: Optional[Tuple[int, int, int]] = None
    if not args.skip_links:
        total_links, broken_links, files_count, broken_details = check_links(root, args.path)
        broken_summary = (total_links, broken_links, files_count)
        for rel_path, issues in broken_details.items():
            filepath = root / rel_path
            for link, link_type, line, suggestions in issues:
                message = f"{link_type} 断链: `{link}`"
                if suggestions:
                    message += f"；可尝试：{', '.join(suggestions)}"
                issues_by_file.setdefault(filepath, []).append(
                    Issue("ERROR", "断链", message, line)
                )

    error_count = sum(1 for issues in issues_by_file.values() for issue in issues if issue.level == "ERROR")
    warn_count = sum(1 for issues in issues_by_file.values() for issue in issues if issue.level == "WARN")

    for filepath in sorted(issues_by_file.keys()):
        rel_path = filepath.relative_to(root)
        print(f"\n📄 {rel_path}")
        for issue in issues_by_file[filepath]:
            icon = "❌" if issue.level == "ERROR" else "⚠️"
            line_text = f" 第{issue.line}行" if issue.line else ""
            print(f"  {icon}{line_text} [{issue.kind}] {issue.message}")

    print("\n" + "=" * 60)
    print(f"扫描文档: {len(files)}")
    print(f"错误: {error_count}")
    print(f"警告: {warn_count}")
    print(f"受影响文件: {len(issues_by_file)}")
    if broken_summary is not None:
        total_links, broken_links, files_count = broken_summary
        print(f"链接检查: {total_links} 个链接，{broken_links} 个断链，影响 {files_count} 个文件")

    if args.report:
        report_path = root / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_markdown_report(root, len(files), {str(path.relative_to(root)): issues for path, issues in issues_by_file.items()}, broken_summary)
        report_path.write_text(report, encoding="utf-8")
        print(f"报告已写入: {report_path}")

    if error_count:
        return 1
    if warn_count and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
