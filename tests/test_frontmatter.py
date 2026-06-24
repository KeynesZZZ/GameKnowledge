"""纯 assert 测试，运行：python3 tests/test_frontmatter.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from _frontmatter import parse_frontmatter, dump_frontmatter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_note.md"

def test_parse_reads_fields():
    content = FIXTURE.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    assert meta["title"] == "【笔记】示例"
    assert meta["tags"] == ["AI", "笔记"]
    assert meta["status"] == "待验证"
    assert meta["related"] == ["其他文档"]
    assert body.lstrip().startswith("# 正文")

def test_roundtrip_preserves_fields():
    content = FIXTURE.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    again, _ = parse_frontmatter(dump_frontmatter(meta) + body)
    assert again["title"] == meta["title"]
    assert again["tags"] == meta["tags"]

def test_no_frontmatter_returns_empty():
    meta, body = parse_frontmatter("# 只有正文\n\n无 frontmatter")
    assert meta == {}
    assert "只有正文" in body

def test_add_new_field():
    meta = {"title": "【笔记】x", "tags": ["a", "b"]}
    out = dump_frontmatter(meta)
    assert out.startswith("---\n")
    assert "title: 【笔记】x" in out

def run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"  ok {name}")
    print("test_frontmatter: OK")

if __name__ == "__main__":
    run()
