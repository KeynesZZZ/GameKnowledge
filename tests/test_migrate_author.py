"""运行：python3 tests/test_migrate_author.py"""
import sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from _frontmatter import parse_frontmatter
import migrate_add_author as M

FIX = Path(__file__).resolve().parent / "fixtures"

def _tmp(name: str) -> Path:
    src = FIX / name
    tmp = FIX / (name + ".tmp")
    shutil.copyfile(src, tmp)
    return tmp

def test_default_author_is_llm():
    tmp = _tmp("no_author.md")
    changed = M.migrate_file(tmp, FIX)
    meta, _ = parse_frontmatter(tmp.read_text(encoding="utf-8"))
    tmp.unlink()
    assert changed is True
    assert meta["author"] == "llm"

def test_does_not_overwrite_existing_author():
    tmp = _tmp("has_author.md")
    changed = M.migrate_file(tmp, FIX)
    meta, _ = parse_frontmatter(tmp.read_text(encoding="utf-8"))
    tmp.unlink()
    assert changed is False
    assert meta["author"] == "human"

def test_fupan_defaults_to_human():
    tmp = _tmp("no_author.md")
    text = tmp.read_text(encoding="utf-8").replace("【笔记】无作者", "【复盘】某项目")
    tmp.write_text(text, encoding="utf-8")
    M.migrate_file(tmp, FIX)
    meta, _ = parse_frontmatter(tmp.read_text(encoding="utf-8"))
    tmp.unlink()
    assert meta["author"] == "human"

def run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  ok {name}")
    print("test_migrate_author: OK")

if __name__ == "__main__":
    run()
