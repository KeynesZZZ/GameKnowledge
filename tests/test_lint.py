"""运行：python3 tests/test_lint.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint as L

FIX = Path(__file__).resolve().parent / "fixtures" / "lint_kb"


def test_orphan_detection():
    files = L.iter_md(FIX)
    orphans = {rel for rel, _msg, _lvl in L.check_orphans(FIX, files)}
    assert "孤儿页.md" in orphans
    assert "被引用页.md" not in orphans


def test_synthesis_without_sources_flagged():
    files = L.iter_md(FIX)
    issues = {rel: msg for rel, msg, _lvl in L.check_sources_rules(files, FIX)
              if "综述无源" in rel}
    assert "综述无源.md" in issues
    assert "sources" in issues["综述无源.md"]


def test_unverified_claim_flagged():
    files = L.iter_md(FIX)
    issues = [(rel, msg) for rel, msg, _lvl in L.check_sources_rules(files, FIX)
              if "无据已验证" in rel]
    assert any("声明无据" in msg for _, msg in issues)


def test_broken_link_detected():
    details = L.check_broken(FIX)
    # 链接页.md 含 [[不存在的文档]] 断链
    assert any("链接页" in rel for rel in details)


def test_synthesis_with_sources_not_flagged():
    # 综述页有 sources → 不应被 flag（综述守卫的负例）
    files = L.iter_md(FIX)
    issues = [rel for rel, _msg, _lvl in L.check_sources_rules(files, FIX)
              if "综述有源" in rel]
    assert issues == []


def test_stem_collision_not_orphan():
    # stem 冲突：a/同名.md 与 b/同名.md 共用 stem，被 [[同名]] 链接 → 两者都不应算孤儿
    files = L.iter_md(FIX)
    orphans = {rel for rel, _msg, _lvl in L.check_orphans(FIX, files)}
    assert "a/同名.md" not in orphans
    assert "b/同名.md" not in orphans


def run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  ok {name}")
    print("test_lint: OK")

if __name__ == "__main__":
    run()
