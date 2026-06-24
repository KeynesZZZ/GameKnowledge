"""统一文档 lint：跨 UnityKnowledge + AIKnowledge。
复用 UnityKnowledge/scripts 的 check_links；新增孤儿页 / 综述缺 sources / 声明无据 检查。
用法：python3 scripts/lint.py [--kb all|UnityKnowledge|AIKnowledge]
退出码：1=有 ERROR，0=仅 WARN 或无问题。"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
UNITY_SCRIPTS = ROOT / "UnityKnowledge" / "scripts"
sys.path.insert(0, str(UNITY_SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _frontmatter import parse_frontmatter  # noqa: E402
from check_links import check_links, extract_links  # noqa: E402

KBS = ["UnityKnowledge", "AIKnowledge"]
SKIP_DIRS = {".git", ".obsidian", ".claude", "scripts", "__pycache__", "_generated", "_sources"}
SKIP_FILES = {"README.md", "index.md", "log.md", "_index.md"}
SYNTHESIS_PREFIX = "【综述】"
VERIFIED_LIKE = {"已验证"}  # 声明已验证但 sources 空 → "声明无据"

ERROR = "ERROR"
WARN = "WARN"


def iter_md(kb_root: Path) -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(kb_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".md") and fn not in SKIP_FILES:
                files.append(Path(dirpath) / fn)
    return sorted(files)


def get_meta(path: Path) -> dict:
    meta, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
    return meta


def has_sources(meta: dict) -> bool:
    s = meta.get("sources", [])
    return isinstance(s, list) and len(s) > 0


def check_orphans(kb_root: Path, files: List[Path]) -> List[Tuple[str, str, str]]:
    """无入链的文档（00_元数据与模板 / 01_Inbox 天然豁免）。返回 [(rel, msg, WARN)]。

    Bug 修复：
    1. stem 冲突（同名文件存于多个目录）时，入链应同时计入所有同 stem 文件，
       而非后者覆盖前者。索引改为 stem -> [Path]。
    2. README.md 被 iter_md 跳过，但其出链也应计入 inbound（许多专题索引仅由
       域 README 链接）。candidates 不含 README，但 link_sources 含 README。
    """
    # 候选：被检查的页（不含 README，但其它 SKIP_FILES 仍跳过）
    candidates = list(files)
    # 出链来源：候选 + 所有 README.md（README 仍不计入候选）
    link_sources = list(files)
    for dirpath, dirnames, filenames in os.walk(kb_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn == "README.md":
                link_sources.append(Path(dirpath) / fn)
    link_sources = sorted(set(link_sources))

    # stem -> [Path]（处理同名冲突）
    index: Dict[str, List[Path]] = {}
    for f in candidates:
        index.setdefault(f.stem, []).append(f)

    inbound: Set[str] = set()
    for f in link_sources:
        for link_text, _ltype, _ln in extract_links(f):
            target = link_text.split("#")[0].split("/")[-1].replace(".md", "").strip()
            if target in index:
                for p in index[target]:
                    inbound.add(str(p.relative_to(kb_root)))

    out = []
    for f in candidates:
        rel = str(f.relative_to(kb_root))
        if rel.startswith(("00_元数据与模板", "01_Inbox")):
            continue
        if rel not in inbound:
            out.append((rel, "孤儿页：无入链", WARN))
    return out


def check_sources_rules(files: List[Path], kb_root: Path) -> List[Tuple[str, str, str]]:
    """综述页缺 sources（ERROR）；已验证但 sources 空（WARN，声明无据）。"""
    out = []
    for f in files:
        meta = get_meta(f)
        rel = str(f.relative_to(kb_root))
        title = str(meta.get("title", ""))
        status = str(meta.get("status", "")).strip()
        if title.startswith(SYNTHESIS_PREFIX) and not has_sources(meta):
            out.append((rel, "综述页缺少 sources（引用即契约）", ERROR))
        if status in VERIFIED_LIKE and not has_sources(meta) and not title.startswith(SYNTHESIS_PREFIX):
            out.append((rel, f"声明无据：status={status} 但 sources 为空", WARN))
    return out


def check_broken(kb_root: Path):
    """复用 check_links，返回 details dict。"""
    _total, _broken, _files, details = check_links(kb_root, ".")
    return details


def run_kb(kb_root: Path) -> List[Tuple[str, str, str]]:
    files = iter_md(kb_root)
    issues: List[Tuple[str, str, str]] = []
    issues += check_orphans(kb_root, files)
    issues += check_sources_rules(files, kb_root)
    for rel, items in check_broken(kb_root).items():
        for link, ltype, line, _sug in items:
            issues.append((rel, f"断链({ltype}) 第{line}行: {link}", ERROR))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="统一文档 lint")
    parser.add_argument("--kb", choices=["all"] + KBS, default="all")
    args = parser.parse_args()
    targets = KBS if args.kb == "all" else [args.kb]

    errors = 0
    warns = 0
    for kb in targets:
        kb_root = ROOT / kb
        if not kb_root.exists():
            continue
        issues = run_kb(kb_root)
        print(f"\n=== {kb}: {len(issues)} 项 ===")
        for rel, msg, lvl in sorted(issues):
            icon = "❌" if lvl == ERROR else "⚠️"
            print(f"  {icon} {rel}: {msg}")
            if lvl == ERROR:
                errors += 1
            else:
                warns += 1
    print(f"\n总计 ERROR={errors} WARN={warns}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
