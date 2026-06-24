"""生成各知识库的 LLM 友好 index.md（机器可读目录，供 agent 下钻）。
用法：python3 scripts/generate_llm_index.py"""
from __future__ import annotations
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import parse_frontmatter  # noqa: E402

KBS = ["UnityKnowledge", "AIKnowledge"]
SKIP_DIRS = {".git", ".obsidian", ".claude", "scripts", "__pycache__", "_generated", "_sources"}
SKIP_FILES = {"README.md", "index.md", "log.md", "_index.md"}


def cell(value) -> str:
    if value in (None, "", []):
        return "-"
    return str(value).replace("|", "\\|").replace("\n", " ")


def group_key(meta: dict, rel: Path) -> str:
    cat = str(meta.get("category", "")).strip()
    if cat:
        return cat
    return rel.parts[0] if rel.parts else "未分类"


def render_row(meta: dict, rel_posix: str) -> str:
    title = cell(meta.get("title") or Path(rel_posix).stem)
    desc = cell(meta.get("description"))
    author = cell(meta.get("author"))
    status = cell(meta.get("status"))
    updated = cell(meta.get("updated"))[:10]
    return f"| [{title}]({rel_posix}) | {desc} | {author} | {status} | {updated} |"


def scan(kb_root: Path):
    rows = []
    for dirpath, dirnames, filenames in os.walk(kb_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            path = Path(dirpath) / fn
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
            rel = path.relative_to(kb_root).as_posix()
            rows.append((group_key(meta, Path(rel)), render_row(meta, rel)))
    return rows


def build_index(kb_name: str, rows) -> str:
    by_group = defaultdict(list)
    for g, r in rows:
        by_group[g].append(r)
    lines = [
        f"# {kb_name} 文档目录（index.md）",
        "",
        "> LLM 维护的机器可读目录。agent 提问时先读本表下钻。格式：文档 | 摘要 | author | status | 更新",
        "",
        "| 文档 | 摘要 | author | status | 更新 |",
        "|------|------|--------|--------|------|",
    ]
    for g in sorted(by_group):
        lines.append(f"| **{g}** | | | | |")
        for r in sorted(by_group[g]):
            lines.append(r)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    for kb in KBS:
        kb_root = ROOT / kb
        if not kb_root.exists():
            continue
        rows = scan(kb_root)
        out = build_index(kb, rows)
        target = kb_root / "index.md"
        target.write_text(out, encoding="utf-8")
        print(f"{kb}: 写入 {target}（{len(rows)} 篇）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
