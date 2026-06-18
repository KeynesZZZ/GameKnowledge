# LLM-Wiki 知识库 P1（地基阶段）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有 276 篇知识库接入 Karpathy LLM-Wiki 模式的地基：新增 `author`/`sources` 字段与 `【综述】` 类型，建立跨知识库统一 lint（复用现有脚本 + 新增孤儿/sources 检查），生成 LLM 友好的 `index.md`/`log.md`，清理 CLAUDE.md 并补 ingest/query/lint 操作契约，落地 `/ingest /query /lint` skill。

**Architecture:** 所有新脚本放仓库根 `scripts/`（跨知识库工具），通过 `sys.path` 导入复用 `UnityKnowledge/scripts/` 现有的 `check_links`/`validate_metadata`/`check_doc_quality` 函数；新增 `author`/`sources` 两个字段（不与现有 `status` 生命周期 / 关系型字段冲突）；测试用纯 `python3` assert 脚本（无第三方依赖，与现有脚本风格一致）。

**Tech Stack:** Python 3.9（系统自带，无第三方依赖）、Markdown、YAML frontmatter、Claude Code skills。

---

## ⚠️ Spec 对齐说明（实现前必读）

探查发现仓库已有成熟的元数据规范与脚本，本计划据此对设计稿 `docs/superpowers/specs/2026-06-18-llm-wiki-knowledge-base-design.md` 做两处对齐（已同步修订设计稿 §4.2/§4.5a）：

1. **`status` 复用现有中文生命周期**：`Inbox/草稿/待验证/已验证/已过时/已归档`。设计稿原写的 `draft|verified|stale` 改为映射：`待验证`≈draft、`已验证`≈verified、`已过时`≈stale。"声明无据" lint = `status` 为 `已验证` 但 `sources` 为空。
2. **不新增 `relates_to`**：复用现有关系型字段 `prerequisite/depends_on/is_example_for/refutes/supersedes/related`。类型化边的 lint 支持（`refutes`/`supersedes` 校验与矛盾处理）归入 P2。
3. **矛盾检测（设计稿 §4.4 第 6 项）移至 P2**：它依赖类型化边 lint（§4.5a，属 P2）。P1 lint 实现 6 项：断链 / 孤儿页 / 缺 frontmatter / stale / 综述页缺 sources / 声明无据（断链/stale/缺frontmatter 复用现有实现，孤儿/sources 为新增）。

---

## 文件结构

**新建（仓库根 `scripts/`，跨知识库工具）：**
- `scripts/_frontmatter.py` — 共享 Frontmatter 解析/序列化（DRY，被迁移/lint/index 共用）
- `scripts/migrate_add_author.py` — 一次性回填 `author` 字段
- `scripts/lint.py` — 统一 lint（复用现有 + 新增孤儿/sources 检查）
- `scripts/generate_llm_index.py` — 生成各知识库 `index.md`

**新建测试（`tests/`，纯 python3 assert）：**
- `tests/test_frontmatter.py`、`tests/test_lint.py`、`tests/test_migrate_author.py`、`tests/test_generate_llm_index.py`
- `tests/fixtures/*.md` — 极简样本文档

**新建文档/skill：**
- `UnityKnowledge/index.md`、`AIKnowledge/index.md`（生成产物，提交）
- `UnityKnowledge/log.md`、`AIKnowledge/log.md`、`_index.md`（手写种子）
- `UnityKnowledge/00_元数据与模板/【模板】综述.md`
- `.claude/skills/ingest.md`、`.claude/skills/query.md`、`.claude/skills/lint.md`

**修改：**
- `UnityKnowledge/00_元数据与模板/元数据规范.md`、`AIKnowledge/00_元数据与模板/元数据规范.md`（加 `author`/`sources`/`【综述】`）
- `CLAUDE.md`（删失效引用 + 加三层模型/操作契约/页面约定，瘦身）
- `.claude/skills/create-doc.md`（提及 `【综述】` + `author`/`sources`）

---

## Task 1: 共享 Frontmatter 模块 + 测试

**Files:**
- Create: `scripts/_frontmatter.py`
- Create: `tests/test_frontmatter.py`
- Create: `tests/fixtures/sample_note.md`

- [ ] **Step 1: 写测试**

`tests/fixtures/sample_note.md`:
```markdown
---
title: 【笔记】示例
tags: [AI, 笔记]
created: 2026-06-18
description: 测试用
status: 待验证
related: ["其他文档"]
---

# 正文
```

`tests/test_frontmatter.py`:
```python
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
```

- [ ] **Step 2: 运行测试，确认失败（模块不存在）**

Run: `python3 tests/test_frontmatter.py`
Expected: `ModuleNotFoundError: No module named '_frontmatter'`

- [ ] **Step 3: 实现 `scripts/_frontmatter.py`**

```python
"""共享 Frontmatter 解析/序列化，无第三方依赖。被 migrate/lint/index 共用。"""
import re

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    return value.strip('"').strip("'")


def parse_frontmatter(content: str):
    """返回 (meta_dict, body)。无 frontmatter 则 ({}, 原文)。"""
    match = _FM_RE.match(content)
    if not match:
        return {}, content
    raw = match.group(1)
    body = content[match.end():]
    meta = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2)
        if value.strip():
            meta[key] = parse_scalar(value)
            i += 1
            continue
        i += 1
        items, nested = [], {}
        while i < len(lines):
            child = lines[i]
            stripped = child.strip()
            if not stripped:
                i += 1
                continue
            indent = len(child) - len(child.lstrip())
            if indent == 0:
                break
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip('"').strip("'"))
            else:
                cm = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", stripped)
                if cm:
                    nested[cm.group(1)] = parse_scalar(cm.group(2))
            i += 1
        meta[key] = items if items else (nested if nested else [])
    return meta, body


def dump_value(value):
    if isinstance(value, list):
        if not value:
            return "[]"
        escaped = [str(v).replace('"', '\\"') for v in value]
        return "[" + ", ".join(f'"{v}"' for v in escaped) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if ":" in text or "#" in text or any(c in text for c in "[]{}"):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def dump_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sk, sv in value.items():
                lines.append(f"  {sk}: {dump_value(sv)}")
        else:
            lines.append(f"{key}: {dump_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 tests/test_frontmatter.py`
Expected: 4 行 `ok test_...` + `test_frontmatter: OK`，退出码 0。

- [ ] **Step 5: 提交**

```bash
git add scripts/_frontmatter.py tests/test_frontmatter.py tests/fixtures/sample_note.md
git commit -m "feat(scripts): 共享 Frontmatter 解析模块与测试"
```

---

## Task 2: 元数据规范新增 author / sources / 【综述】

**Files:**
- Modify: `UnityKnowledge/00_元数据与模板/元数据规范.md`
- Modify: `AIKnowledge/00_元数据与模板/元数据规范.md`

- [ ] **Step 1: UnityKnowledge 元数据规范 —— 在「可选字段」表加入 author/sources**

在 `UnityKnowledge/00_元数据与模板/元数据规范.md` 的「可选字段」表格（`validation` 行之后）插入两行：

```markdown
| `author` | string | 作者来源（防幻觉的关键标记） | `human` / `llm` |
| `sources` | array | 结论来源（综述页必填，引用即契约） | `["【笔记】对象池", "外部文章A"]` |
```

- [ ] **Step 2: UnityKnowledge —— 在「类型前缀」表加入 综述**

在同一文件的「新文档优先使用 4 种轻量类型」表后追加一行：

```markdown
| 综述 | `【综述】` | `【综述】Unity性能优化全景` |
```

并在该表下方补一段说明：

```markdown
> `【综述】` 是 LLM 维护的综合页（跨文档提炼），`author` 必须为 `llm`，且 `sources` 必填、指向它综合了哪些 `author: human` 或已验证笔记 / 外部原文。这是"引用即契约"的落地。
```

- [ ] **Step 3: AIKnowledge 元数据规范 —— 同步加入 author/sources/综述**

在 `AIKnowledge/00_元数据与模板/元数据规范.md` 的「可选字段」表加入：

```markdown
| `author` | string | 作者来源 | `human` / `llm` |
| `sources` | array | 结论来源（综述必填） | `["【笔记】Prompt与上下文管理"]` |
```

并在该文件末尾「Frontmatter 示例」前补一节：

```markdown
## 综述页（LLM 维护）

`【综述】` 类型由 LLM 跨文档提炼生成，`author: llm`，`sources` 必填：

​```yaml
---
title: 【综述】AI编码工作流全景
tags: [AI编码, 工作流, 综述]
created: 2026-06-18
description: 跨多篇笔记提炼的 AI 辅助开发工作流全貌
author: llm
sources: ["【笔记】Prompt与上下文管理", "【教程】AI辅助开发工作流"]
status: 待验证
---
​```
```

- [ ] **Step 4: 验证（跑现有 validate_metadata 确认未破坏）**

Run: `cd UnityKnowledge && python3 scripts/validate_metadata.py --path 00_元数据与模板`
Expected: 不报新增字段为非法（现有 `validate_status` 只校验 status，不校验 author/sources，应通过）。

- [ ] **Step 5: 提交**

```bash
git add "UnityKnowledge/00_元数据与模板/元数据规范.md" "AIKnowledge/00_元数据与模板/元数据规范.md"
git commit -m "docs: 元数据规范新增 author/sources 字段与【综述】类型"
```

---

## Task 3: 跨知识库 author 回填迁移脚本

**Files:**
- Create: `scripts/migrate_add_author.py`
- Create: `tests/test_migrate_author.py`
- Create: `tests/fixtures/no_author.md`、`tests/fixtures/has_author.md`

- [ ] **Step 1: 写测试**

`tests/fixtures/no_author.md`:
```markdown
---
title: 【笔记】无作者
tags: [AI, 笔记]
created: 2026-06-18
description: 测试
---
```

`tests/fixtures/has_author.md`:
```markdown
---
title: 【复盘】已有作者
tags: [AI, 复盘]
created: 2026-06-18
description: 测试
author: human
---
```

`tests/test_migrate_author.py`:
```python
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
    # 把标题改成复盘
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 tests/test_migrate_author.py`
Expected: `ModuleNotFoundError: No module named 'migrate_add_author'`

- [ ] **Step 3: 实现 `scripts/migrate_add_author.py`**

```python
"""一次性：为两个知识库回填 author 字段（默认 llm；【复盘】默认 human）。不覆盖已有值。"""
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


def walk_kb(kb_root: Path) -> int:
    changed = 0
    for dirpath, dirnames, filenames in os.walk(kb_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            if migrate_file(Path(dirpath) / fn, kb_root):
                changed += 1
    return changed


def main() -> int:
    total = 0
    for kb in ("UnityKnowledge", "AIKnowledge"):
        kb_root = ROOT / kb
        if not kb_root.exists():
            continue
        c = walk_kb(kb_root)
        total += c
        print(f"{kb}: 回填 author {c} 篇")
    print(f"完成，共回填 {total} 篇")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 tests/test_migrate_author.py`
Expected: 3 行 `ok` + `OK`。

- [ ] **Step 5: 执行真实迁移（两个知识库）**

Run: `python3 scripts/migrate_add_author.py`
Expected: 打印 `UnityKnowledge: 回填 author N 篇` / `AIKnowledge: 回填 author N 篇` / `完成，共回填 N 篇`。

- [ ] **Step 6: 抽查结果**

Run: `grep -l "author: llm" UnityKnowledge/10_架构设计/*.md | head -3`
Expected: 列出若干已加 `author: llm` 的文件。
Run: `git diff --stat UnityKnowledge AIKnowledge | tail -3`
Expected: 大量 .md 被改动（仅 frontmatter 加一行 author）。

- [ ] **Step 7: 提交**

```bash
git add scripts/migrate_add_author.py tests/test_migrate_author.py tests/fixtures/no_author.md tests/fixtures/has_author.md
git add -u UnityKnowledge AIKnowledge
git commit -m "feat(scripts): 跨知识库回填 author 字段（默认 llm，复盘默认 human）"
```

> 注：`git add -u` 只加已跟踪文件的修改，不会扫入未跟踪的既有改动。提交前用 `git status` 确认只包含 author 回填相关的 .md。

---

## Task 4: 统一 lint（复用现有 + 新增孤儿/sources 检查）

**Files:**
- Create: `scripts/lint.py`
- Create: `tests/test_lint.py`
- Create: `tests/fixtures/lint_kb/` 下若干样本

- [ ] **Step 1: 写测试（构造一个迷你知识库 fixture）**

> 文件名用中文且与 `[[wikilink]]` 文本一致，确保孤儿/断链检查能正确解析（`check_orphans` 按 `stem` 建索引）。

`tests/fixtures/lint_kb/孤儿页.md`（无入链的孤儿，stem=孤儿页）:
```markdown
---
title: 【笔记】孤儿页
tags: [AI, 笔记]
created: 2026-06-18
description: 无人链接我
author: llm
---
```

`tests/fixtures/lint_kb/被引用页.md`（被链接，非孤儿）:
```markdown
---
title: 【笔记】被引用页
tags: [AI, 笔记]
created: 2026-06-18
description: 有人链接我
author: llm
---
```

`tests/fixtures/lint_kb/链接页.md`（链接到被引用页，并含一条断链）:
```markdown
---
title: 【笔记】链接页
tags: [AI, 笔记]
created: 2026-06-18
description: 我链接别人
author: llm
---
参见 [[被引用页]]，另外 [[不存在的文档]] 是断链。
```

`tests/fixtures/lint_kb/综述无源.md`（综述缺 sources → ERROR）:
```markdown
---
title: 【综述】缺来源的综述
tags: [AI, 综述]
created: 2026-06-18
description: 综述但没 sources
author: llm
status: 已验证
---
```

`tests/fixtures/lint_kb/无据已验证.md`（非综述、已验证、无 sources → 声明无据 WARN）:
```markdown
---
title: 【笔记】声明已验证但无源
tags: [AI, 笔记]
created: 2026-06-18
description: 测试声明无据
author: llm
status: 已验证
---
```

`tests/test_lint.py`:
```python
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


def run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  ok {name}")
    print("test_lint: OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 tests/test_lint.py`
Expected: `ModuleNotFoundError: No module named 'lint'`

- [ ] **Step 3: 实现 `scripts/lint.py`**

```python
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
    """无入链的文档（00_元数据与模板 / 01_Inbox 天然豁免）。返回 [(rel, msg, WARN)]。"""
    index: Dict[str, Path] = {}
    for f in files:
        index[f.stem] = f
    inbound: Set[str] = set()
    for f in files:
        for link_text, _ltype, _ln in extract_links(f):
            target = link_text.split("#")[0].split("/")[-1].replace(".md", "").strip()
            if target in index:
                inbound.add(str(index[target].relative_to(kb_root)))
    out = []
    for f in files:
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 tests/test_lint.py`
Expected: 4 行 `ok` + `OK`。

- [ ] **Step 5: 对真实知识库跑一次（基线）**

Run: `python3 scripts/lint.py`
Expected: 打印各 KB 的孤儿/sources/断链清单 + `总计 ERROR=N WARN=M`。孤儿页数量会较多（属正常 lint 信号，后续 ingest 时逐步补入链）。

- [ ] **Step 6: 提交**

```bash
git add scripts/lint.py tests/test_lint.py tests/fixtures/lint_kb/
git commit -m "feat(scripts): 统一 lint，复用 check_links 并新增孤儿页/sources 检查"
```

---

## Task 5: 各知识库 index.md 生成 + log.md / _index.md 种子

**Files:**
- Create: `scripts/generate_llm_index.py`
- Create: `tests/test_generate_llm_index.py`
- Create: `UnityKnowledge/log.md`、`AIKnowledge/log.md`、`_index.md`

- [ ] **Step 1: 写测试**

`tests/test_generate_llm_index.py`:
```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 tests/test_generate_llm_index.py`
Expected: `ModuleNotFoundError: No module named 'generate_llm_index'`

- [ ] **Step 3: 实现 `scripts/generate_llm_index.py`**

```python
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 tests/test_generate_llm_index.py`
Expected: 3 行 `ok` + `OK`。

- [ ] **Step 5: 生成真实 index.md**

Run: `python3 scripts/generate_llm_index.py`
Expected: `UnityKnowledge: 写入 ...index.md（N 篇）` / `AIKnowledge: 写入 ...index.md（N 篇）`。

- [ ] **Step 6: 写 log.md 种子（每个知识库一个）+ 根 `_index.md`**

`UnityKnowledge/log.md`:
```markdown
# UnityKnowledge 维护日志（log.md）

> append-only。每行前缀 `## [YYYY-MM-DD] ingest|query|lint | 标题`，可 `grep "^## \[" log.md | tail`。

## [2026-06-18] lint | P1 地基初始化
- 生成首版 index.md
- 全库回填 author 字段
- 统一 lint 基线跑通
```

`AIKnowledge/log.md`:（同结构，标题改为 AIKnowledge）

`_index.md`（仓库根）:
```markdown
# 知识库总入口（指针）

> 不重复内容，只指向各知识库的 index。

- [[UnityKnowledge/index|UnityKnowledge 目录]]（Unity 技术架构）
- [[AIKnowledge/index|AIKnowledge 目录]]（AI 学习与工作流）

维护日志：[[UnityKnowledge/log]]、[[AIKnowledge/log]]。
```

- [ ] **Step 7: 提交**

```bash
git add scripts/generate_llm_index.py tests/test_generate_llm_index.py
git add UnityKnowledge/index.md AIKnowledge/index.md UnityKnowledge/log.md AIKnowledge/log.md _index.md
git commit -m "feat(scripts): 生成各知识库 index.md，种子 log.md 与根 _index.md"
```

---

## Task 6: CLAUDE.md 清理 + 三层模型 / 操作契约

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 删除失效的工具引用**

在 `CLAUDE.md` 中删除以下已不存在的内容（全文搜索确认后删除整段/整行）：
- `### 1. tools/knowledge_base/` 整节（含命令示例、配置说明）
- `### 2. unity-rules-checker/` 整节
- 「Quick Reference」表中涉及 `knowledge_base.py`、`check_docs_compliance.py`、`/check-rules`、`unity-rules-checker` 的行
- 「File Relationships」中 `tools/knowledge_base/` 与 `unity-rules-checker/` 子树

> 保留 `UnityKnowledge/scripts/check_links.py`（实际存在于 `UnityKnowledge/scripts/`）的引用，但把路径从 `UnityKnowledge/check_links.py` 更正为 `UnityKnowledge/scripts/check_links.py`。

- [ ] **Step 2: 在 CLAUDE.md 顶部「Repository Purpose」之后插入「LLM-Wiki 维护模式」节**

```markdown
## LLM-Wiki 维护模式（核心）

本仓库按 Karpathy LLM-Wiki 模式运作：LLM 持续编译并维护一个会复利的 Markdown wiki，人负责 sourcing / 提问 / 验证。

### 三层模型
- **原始层 (raw)**：外部文章/论文，落 `_sources/`，不可变。捕获进 `01_Inbox/` 后提升。
- **笔记层 (wiki)**：现有笔记 + LLM 生成的 `【综述】` 页。`author: llm` 的综合页必须带 `sources:`。
- **schema 层**：本文件（CLAUDE.md）。

### 三个操作
- **ingest**：读源 → 讨论 → 写综述/更新页（碰到的真相层页加 `updated`）→ 更新 `index.md` → 追加 `log.md`。
- **query**：先读 `index.md` 下钻 → 读相关页 → 带引用作答 → 好答案回填为新页（`author: llm` + `sources:`）。
- **lint**：`python3 scripts/lint.py`。ERROR（断链 / 综述缺 sources）阻断；WARN（孤儿页 / 声明无据 / stale）报告。推翻既有结论进 review，不静默改。

### 关键字段
- `author: human|llm`：`human` 是真相源，不可被 LLM 静默改写。
- `sources: [...]`：综述页必填，引用即契约。
- `status`：复用现有 `草稿/待验证/已验证/已过时/已归档`。
- 详细 lint 规则与 Dataview 示例见 `docs/superpowers/specs/2026-06-18-llm-wiki-knowledge-base-design.md`。
```

- [ ] **Step 3: 更新 Quick Reference 表，加入新命令**

在 Quick Reference 表中加入：
```markdown
| **统一 lint** | `python3 scripts/lint.py` |
| **生成目录** | `python3 scripts/generate_llm_index.py` |
| **回填 author** | `python3 scripts/migrate_add_author.py` |
```

- [ ] **Step 4: 验证瘦身效果**

Run: `wc -c CLAUDE.md`
Expected: 比原 ~12000 字节下降（目标 < 9000）。Run: `grep -c "tools/knowledge_base\|unity-rules-checker\|check_docs_compliance" CLAUDE.md`
Expected: `0`（无残留失效引用）。

- [ ] **Step 5: 提交**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE): 删失效工具引用，新增 LLM-Wiki 三层模型与 ingest/query/lint 操作契约"
```

---

## Task 7: /ingest /query /lint skill + 综述模板 + create-doc 更新

**Files:**
- Create: `.claude/skills/ingest.md`
- Create: `.claude/skills/query.md`
- Create: `.claude/skills/lint.md`
- Create: `UnityKnowledge/00_元数据与模板/【模板】综述.md`
- Modify: `.claude/skills/create-doc.md`

- [ ] **Step 1: 写 lint skill**

`.claude/skills/lint.md`:
```markdown
# 文档 lint（健康检查）

> 对 UnityKnowledge + AIKnowledge 跑统一 lint。

## 什么时候使用
- 定期维护、ingest/query 之后
- 想找孤儿页、断链、综述缺 sources、声明无据

## 工作流程
1. 运行 `python3 scripts/lint.py`（或 `--kb UnityKnowledge` 限定单库）
2. ERROR（断链 / 综述缺 sources）：必须修
3. WARN（孤儿页 / 声明无据 / stale）：报告给用户，问是否补入链 / 补 sources
4. 推翻既有结论的修正 → 写进 review，不直接改 `author: human` 页

## 用户指令
```
/lint
/lint --kb AIKnowledge
```
```

- [ ] **Step 2: 写 ingest skill**

`.claude/skills/ingest.md`:
```markdown
# ingest（喂入新源）

> 把一个新源（外部文章 / 新笔记）整合进 wiki。

## 工作流程
1. 读源（`_sources/` 外部原文，或 `01_Inbox/` 捕获），与用户讨论要点
2. 写或更新综述/概念页：`author: llm`，`sources:` 指向真相层笔记/原文
3. 被碰到的真相层页（`author: human`）加 `updated`，不改正文结论
4. 运行 `python3 scripts/generate_llm_index.py` 更新 index
5. 追加 `log.md`：`## [YYYY-MM-DD] ingest | 标题`
6. 跑 `/lint` 确认无新断链

## 用户指令
```
/ingest _sources/某文章.md
/ingest "把这篇整理进 20_核心系统"
```
```

- [ ] **Step 3: 写 query skill**

`.claude/skills/query.md`:
```markdown
# query（提问，好答案回填）

> 基于知识库作答，把有价值的答案回填为新页（复利引擎）。

## 工作流程
1. 先读 `<KB>/index.md` 定位相关页（不要全量读 CLAUDE.md）
2. 读 2–5 篇相关页 + ripgrep 关键词补全
3. 带引用作答（每条结论指向 `sources`）
4. 若答案有复用价值 → 征得用户同意后回填为新页：综述用 `【综述】`，否则合适类型；`author: llm` + `sources:` + `status: 待验证`
5. 更新 index + 追加 `log.md`：`## [YYYY-MM-DD] query | 问题摘要`

## 用户指令
```
/query UGUI 怎么减少 DrawCall？
```
```

- [ ] **Step 4: 写综述模板**

`UnityKnowledge/00_元数据与模板/【模板】综述.md`:
```markdown
---
title: 【综述】主题
tags: [综述, <领域>]
created: 2026-06-18
updated: 2026-06-18
description: 一句话说明这篇综述综合了什么
author: llm
sources: []
status: 待验证
---

# 【综述】主题

> 本页由 LLM 跨多篇笔记/外部原文综合生成。`sources` 是引用契约，每条结论可追溯。

## 问题

本综述回答什么问题？

## 综合结论

- 

## 证据来源

- [[来源笔记1]]
- [[来源笔记2 / 外部原文]]

## 相关

- [[]]
```

- [ ] **Step 5: 更新 create-doc skill，提及综述与 author/sources**

在 `.claude/skills/create-doc.md` 的「步骤 1：选择文档类型」表中追加一行：
```markdown
| 综述 | `【综述】` | LLM 跨文档综合 | LLM 维护的综合页（`author: llm`，`sources` 必填） |
```
并在「步骤 3：填写 YAML Frontmatter」的必填字段说明后补一段：
```markdown
#### author / sources（综述必填）
- `author: human | llm`：人写笔记默认 human，LLM 生成默认 llm。
- `sources: []`：综述页必填，列出综合了哪些笔记/原文（引用即契约）。
```

- [ ] **Step 6: 提交**

```bash
git add .claude/skills/ingest.md .claude/skills/query.md .claude/skills/lint.md
git add "UnityKnowledge/00_元数据与模板/【模板】综述.md" .claude/skills/create-doc.md
git commit -m "feat(skills): 新增 /ingest /query /lint skill 与综述模板，更新 create-doc"
```

---

## 完成标准（P1）

- [ ] `python3 tests/test_frontmatter.py && python3 tests/test_migrate_author.py && python3 tests/test_lint.py && python3 tests/test_generate_llm_index.py` 全绿
- [ ] 全库 .md 已回填 `author`
- [ ] `UnityKnowledge/index.md`、`AIKnowledge/index.md`、两个 `log.md`、`_index.md` 就位
- [ ] `python3 scripts/lint.py` 可跑（孤儿页多为 WARN，断链/综述缺sources为 ERROR）
- [ ] `CLAUDE.md` 无 `tools/knowledge_base` / `unity-rules-checker` / `check_docs_compliance` 残留，含三层模型与 ingest/query/lint
- [ ] `.claude/skills/` 下有 ingest/query/lint 三个 skill

> P2（类型化边 lint + review 队列 + provenance 强制 block）、P3（pre-commit 廉价 lint + cron report-only）不在本计划内。
