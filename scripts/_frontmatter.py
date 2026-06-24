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
