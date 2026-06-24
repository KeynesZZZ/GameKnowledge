"""运行：python3 tests/test_generate_llm_index.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generate_llm_index as G


def test_render_row_contains_fields():
    meta = {
        "title": "【笔记】对象池",
        "description": "减少GC",
        "author": "llm",
        "status": "待验证",
        "updated": "2026-06-18",
    }
    row = G.render_row(meta, "10_架构设计/note.md")
    assert "【笔记】对象池" in row
    assert "llm" in row
    assert "待验证" in row
    assert "减少GC" in row


def test_missing_fields_get_dashes():
    row = G.render_row({"title": "【笔记】x"}, "a/b.md")
    assert "-" in row  # author/status/updated 缺失填 -


def test_grouping_by_top_dir_when_no_category():
    groups = G.group_key({"category": ""}, Path("20_核心系统/21_动画/x.md"))
    assert groups.startswith("20_")


def run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  ok {name}")
    print("test_generate_llm_index: OK")

if __name__ == "__main__":
    run()
