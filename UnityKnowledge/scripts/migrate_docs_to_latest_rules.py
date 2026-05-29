"""
migrate_docs_to_latest_rules.py - 一次性迁移 UnityKnowledge 文档到最新规则。

处理内容：
- 补齐/规范 YAML Frontmatter
- 将旧团队状态映射到个人知识库轻量生命周期
- 补齐 status / validation / related
- 修正常见旧 category
- 给缺少“文档定位”或“相关链接”的正式文档补最小章节
- 避免修改 README、scripts 和 Obsidian 配置

用法：
    python3 UnityKnowledge/scripts/migrate_docs_to_latest_rules.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-05-29 00:00"

VALID_PREFIXES = [
    "【代码片段】", "【最佳实践】", "【踩坑记录】", "【性能数据】",
    "【设计原理】", "【架构决策】", "【系统架构】", "【实战案例】",
    "【教程】", "【源码解析】", "【验证报告】", "【反模式】",
    "【架构演进】", "【方案】", "【模板】"
]

STATUS_MAP = {
    "提议": "草稿",
    "讨论中": "草稿",
    "已采纳": "待验证",
    "已实施": "待验证",
    "已拒绝": "已归档",
    "已验证": "已验证",
    "已过时": "已过时",
    "已归档": "已归档",
    "草稿": "草稿",
    "待验证": "待验证",
    "Inbox": "Inbox",
}

VALID_VALIDATION = {"未经测试", "Demo验证", "项目实战", "多项目验证"}


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
    return value.strip('"').strip("'")


def parse_frontmatter(content: str):
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
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
        m = re.match(r"^([A-Za-z_][\w_]*)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2)
        if value.strip():
            meta[key] = parse_scalar(value)
            i += 1
            continue

        i += 1
        items = []
        nested = {}
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
                cm = re.match(r"^([A-Za-z_][\w_]*)\s*:\s*(.*)$", stripped)
                if cm:
                    nested[cm.group(1)] = parse_scalar(cm.group(2))
            i += 1
        meta[key] = items if items else nested if nested else []
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
    if ":" in text or "#" in text:
        return '"' + text.replace('"', '\\"') + '"'
    return text


def dump_frontmatter(meta: dict) -> str:
    order = [
        "title", "tags", "category", "created", "updated", "description",
        "unity_version", "status", "validation", "dependencies", "related",
        "prerequisite", "depends_on", "is_example_for", "refutes", "supersedes",
    ]
    keys = [key for key in order if key in meta]
    keys.extend(sorted(key for key in meta if key not in keys))
    lines = ["---"]
    for key in keys:
        value = meta[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_val in value.items():
                lines.append(f"  {sub_key}: {dump_value(sub_val)}")
        else:
            lines.append(f"{key}: {dump_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def infer_prefix(path: Path, title: str) -> str:
    name = path.stem
    for prefix in VALID_PREFIXES:
        if title.startswith(prefix) or name.startswith(prefix):
            return prefix
    if "模板" in path.name:
        return "【模板】"
    if "README" == path.name:
        return "【教程】"
    if "方案" in name:
        return "【方案】"
    if "性能" in name or "Benchmark" in name:
        return "【性能数据】"
    if "架构决策" in name or "ADR" in name:
        return "【架构决策】"
    if "系统架构" in name:
        return "【系统架构】"
    if "代码片段" in name:
        return "【代码片段】"
    if "踩坑" in name or "Bug" in name:
        return "【踩坑记录】"
    if "最佳实践" in name or "清单" in name:
        return "【最佳实践】"
    if "源码解析" in name:
        return "【源码解析】"
    if "实战案例" in name:
        return "【实战案例】"
    if "反模式" in name:
        return "【反模式】"
    if "架构演进" in name:
        return "【架构演进】"
    if "验证报告" in name:
        return "【验证报告】"
    if "设计原理" in name:
        return "【设计原理】"
    return "【教程】"


def clean_title(path: Path, meta: dict) -> str:
    original = str(meta.get("title") or path.stem)
    if any(original.startswith(prefix) for prefix in VALID_PREFIXES):
        return original
    prefix = infer_prefix(path, original)
    return f"{prefix}{original}"


def doc_type_from_title(title: str) -> str:
    for prefix in VALID_PREFIXES:
        if title.startswith(prefix):
            return prefix.strip("【】")
    return "教程"


def infer_category(path: Path, title: str, current: str | None) -> str:
    if current and current != "代码片段/Unity":
        return current
    rel = path.relative_to(ROOT)
    parts = rel.parts
    doc_type = doc_type_from_title(title)
    if parts[0] == "00_元数据与模板":
        if doc_type == "模板":
            return "元数据与模板/模板"
        if doc_type in {"最佳实践"}:
            return "元数据与模板/最佳实践"
        return "元数据与模板/规范"
    if parts[0] == "01_Inbox":
        return "Inbox/工作流"
    if parts[0] == "10_架构设计":
        return f"架构设计/{doc_type}"
    if parts[0] == "20_核心系统":
        return "核心系统/" + (parts[1].split("_", 1)[-1] if len(parts) > 1 else doc_type)
    if parts[0] == "25_DOTS技术栈":
        return f"DOTS技术栈/{doc_type}"
    if parts[0] == "30_性能优化":
        return "性能优化/" + (parts[1].split("_", 1)[-1] if len(parts) > 1 else doc_type)
    if parts[0] == "35_高级主题":
        return f"高级主题/{doc_type}"
    if parts[0] == "36_高级编程":
        return f"高级编程/{doc_type}"
    if parts[0] == "40_工具链":
        return "工具链/" + (parts[1].split("_", 1)[-1] if len(parts) > 1 else doc_type)
    if parts[0] == "50_平台适配":
        return f"平台适配/{doc_type}"
    if parts[0] == "60_第三方库":
        return f"第三方库/{doc_type}"
    if parts[0] == "90_项目复盘":
        return f"项目复盘/{doc_type}"
    if parts[0] == "100_项目实战":
        return "项目实战/" + (parts[1].split("_", 1)[-1] if len(parts) > 1 else doc_type)
    return f"未分类/{doc_type}"


def infer_tags(path: Path, title: str, meta: dict) -> list[str]:
    raw = meta.get("tags", [])
    if isinstance(raw, str):
        tags = [raw]
    else:
        tags = list(raw) if isinstance(raw, list) else []
    tags = [str(tag).strip().lstrip("#") for tag in tags if str(tag).strip()]
    for tag in ["Unity", doc_type_from_title(title)]:
        if tag not in tags:
            tags.append(tag)
    category = str(meta.get("category", ""))
    for keyword in ["架构", "性能优化", "UI", "网络", "动画", "物理", "渲染", "工具链", "内存管理"]:
        if (keyword in str(path) or keyword in title or keyword in category) and keyword not in tags:
            tags.append(keyword)
    return tags[:8]


def infer_validation(title: str, current: str | None) -> str:
    if current in VALID_VALIDATION:
        return current
    doc_type = doc_type_from_title(title)
    if doc_type == "实战案例":
        return "项目实战"
    if doc_type in {"性能数据", "验证报告"}:
        return "Demo验证"
    if doc_type in {"模板", "教程", "最佳实践", "系统架构", "架构决策"}:
        return "Demo验证"
    return "未经测试"


def has_heading(body: str, heading: str) -> bool:
    return re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE) is not None


def ensure_body_sections(body: str, title: str, path: Path) -> str:
    if path.name == "README.md":
        return body
    body = body.rstrip() + "\n"
    additions = []
    if not has_heading(body, "文档定位"):
        additions.append(
            "## 文档定位\n\n"
            f"本文档用于沉淀 `{title}` 相关知识，说明其适用场景、核心内容和实践注意事项。\n"
        )
    if not has_heading(body, "相关链接"):
        additions.append("## 相关链接\n\n- [[../00_元数据与模板/文档结构规范]]\n")
    if additions:
        body = body.rstrip() + "\n\n" + "\n\n".join(additions) + "\n"
    return body


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if path.name == "README.md":
        return True
    return any(part in {".obsidian", "scripts", "__pycache__"} for part in rel.parts)


def migrate_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    title = clean_title(path, meta)
    meta["title"] = title
    meta["tags"] = infer_tags(path, title, meta)
    meta["category"] = infer_category(path, title, meta.get("category"))
    meta["created"] = meta.get("created") or TODAY
    meta["updated"] = TODAY
    meta["description"] = meta.get("description") or f"{title} 的知识整理、实践要点和相关链接"

    old_status = str(meta.get("status") or "待验证")
    if doc_type_from_title(title) == "模板":
        meta["status"] = "已归档"
    else:
        meta["status"] = STATUS_MAP.get(old_status, "待验证")
    meta["validation"] = infer_validation(title, meta.get("validation"))
    if "related" not in meta or not isinstance(meta.get("related"), list):
        meta["related"] = []

    body = ensure_body_sections(body, title, path)
    new_content = dump_frontmatter(meta) + body
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".obsidian", "scripts", "__pycache__"}]
        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            path = Path(dirpath) / filename
            if should_skip(path):
                continue
            total += 1
            if migrate_file(path):
                changed += 1
    print(f"Migrated {changed}/{total} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
