"""一次性：为两个知识库回填 author 字段（默认 llm；【复盘】默认 human）。不覆盖已有值。
运行：python3 scripts/migrate_add_author.py
stdout 打印每个被改文件的仓库相对路径（每行一个），便于精确 git add；汇总打到 stderr。"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import parse_frontmatter, dump_frontmatter  # noqa: E402

HUMAN_PREFIXES = ("【复盘】",)
SKIP_DIRS = {".git", ".obsidian", ".claude", "scripts", "__pycache__", "_generated", "_sources"}
SKIP_FILES = {"README.md", "index.md", "log.md", "_index.md"}


def default_author(meta: dict) -> str:
    title = str(meta.get("title", ""))
    return "human" if title.startswith(HUMAN_PREFIXES) else "llm"


def migrate_file(path: Path, root: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    if meta.get("author") in (None, "", []):
        meta["author"] = default_author(meta)
    else:
        return False  # 已有 author，不改
    new_content = dump_frontmatter(meta) + body
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def walk_kb(kb_root: Path) -> list:
    changed = []
    for dirpath, dirnames, filenames in os.walk(kb_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            p = Path(dirpath) / fn
            if migrate_file(p, kb_root):
                changed.append(p.relative_to(ROOT).as_posix())
    return changed


def main() -> int:
    total = 0
    all_changed = []
    for kb in ("UnityKnowledge", "AIKnowledge"):
        kb_root = ROOT / kb
        if not kb_root.exists():
            continue
        changed = walk_kb(kb_root)
        all_changed.extend(changed)
        total += len(changed)
        print(f"{kb}: 回填 author {len(changed)} 篇", file=sys.stderr)
    print(f"完成，共回填 {total} 篇", file=sys.stderr)
    for rel in all_changed:
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
