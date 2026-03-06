"""
validate_metadata.py - UnityKnowledge 元数据校验脚本（无第三方依赖版本）
用于CI流水线中检查新提交文档的元数据完整性。

用法：
    python scripts/validate_metadata.py                    # 校验所有文档
    python scripts/validate_metadata.py --path 10_架构设计  # 校验指定目录
    python scripts/validate_metadata.py --strict            # 严格模式（检查可选字段）

退出码：
    0 - 全部通过
    1 - 存在错误
    2 - 存在警告（仅严格模式）
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================
# 配置
# ============================================================

REQUIRED_FIELDS = ["title", "tags", "category", "created", "updated", "description"]

VALID_PREFIXES = [
    "【代码片段】", "【最佳实践】", "【踩坑记录】", "【性能数据】",
    "【设计原理】", "【架构决策】", "【系统架构】", "【实战案例】",
    "【教程】", "【源码解析】", "【验证报告】", "【反模式】",
    "【架构演进】", "【方案】", "【模板】"
]

VALID_STATUS = [
    "提议", "讨论中", "已采纳", "已实施", "已验证", "已过时", "已拒绝", "已归档"
]

VALID_VALIDATION = ["未经测试", "Demo验证", "项目实战", "多项目验证"]

SKIP_FILES = ["README.md"]

SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]

# ============================================================
# 轻量YAML解析（仅解析Frontmatter所需的简单结构）
# ============================================================

def parse_simple_yaml(text: str) -> Dict:
    """
    轻量YAML解析器，支持：
    - key: value（字符串、数字、日期）
    - key: [item1, item2]（行内数组）
    - key:（多行数组，每行 - item）
    - key:（嵌套对象，缩进的 subkey: value）
    """
    result = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 跳过空行和注释
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # 匹配 key: value
        m = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value_str = m.group(2).strip()

        if value_str:
            # 行内数组: [item1, item2]
            arr_match = re.match(r'^\[(.*)\]$', value_str)
            if arr_match:
                items = [item.strip().strip('"').strip("'") for item in arr_match.group(1).split(",") if item.strip()]
                result[key] = items
            # 带引号的字符串
            elif (value_str.startswith('"') and value_str.endswith('"')) or \
                 (value_str.startswith("'") and value_str.endswith("'")):
                result[key] = value_str[1:-1]
            # 布尔值
            elif value_str.lower() in ("true", "false"):
                result[key] = value_str.lower() == "true"
            else:
                result[key] = value_str
            i += 1
        else:
            # 值为空，检查下一行是否是数组或嵌套对象
            i += 1
            sub_items = []
            sub_dict = {}
            is_array = False
            is_dict = False

            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()

                if not next_stripped or next_stripped.startswith("#"):
                    i += 1
                    continue

                # 检查缩进
                indent = len(next_line) - len(next_line.lstrip())
                if indent == 0:
                    break

                if next_stripped.startswith("- "):
                    is_array = True
                    item = next_stripped[2:].strip().strip('"').strip("'")
                    sub_items.append(item)
                elif ":" in next_stripped:
                    is_dict = True
                    sub_m = re.match(r'^\s*(\w[\w_]*)\s*:\s*(.*)', next_line)
                    if sub_m:
                        sub_key = sub_m.group(1)
                        sub_val = sub_m.group(2).strip()
                        # 嵌套数组
                        arr_m = re.match(r'^\[(.*)\]$', sub_val)
                        if arr_m:
                            sub_dict[sub_key] = [x.strip().strip('"').strip("'") for x in arr_m.group(1).split(",") if x.strip()]
                        elif sub_val.lower() in ("true", "false"):
                            sub_dict[sub_key] = sub_val.lower() == "true"
                        elif sub_val:
                            sub_dict[sub_key] = sub_val.strip('"').strip("'")
                        else:
                            sub_dict[sub_key] = ""
                else:
                    break
                i += 1

            if is_array:
                result[key] = sub_items
            elif is_dict:
                result[key] = sub_dict
            else:
                result[key] = None

    return result


def extract_frontmatter(filepath: Path) -> Optional[Dict]:
    """从Markdown文件中提取YAML Frontmatter"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = filepath.read_text(encoding="gbk")
        except Exception:
            return None

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        return parse_simple_yaml(match.group(1))
    except Exception:
        return None

# ============================================================
# 校验规则
# ============================================================

def validate_required_fields(meta: Dict, filepath: Path) -> List[str]:
    """检查必填字段"""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in meta or meta[field] is None or meta[field] == "":
            errors.append(f"  \u274c 缺少必填字段: {field}")
    return errors


def validate_title_prefix(meta: Dict, filepath: Path) -> List[str]:
    """检查标题前缀是否合规"""
    errors = []
    title = meta.get("title", "")
    if title and not any(title.startswith(prefix) for prefix in VALID_PREFIXES):
        errors.append(f"  \u26a0\ufe0f 标题缺少类型前缀: '{title}'")
    return errors


def validate_tags(meta: Dict, filepath: Path) -> List[str]:
    """检查标签数量"""
    errors = []
    tags = meta.get("tags", [])
    if not isinstance(tags, list):
        errors.append(f"  \u274c tags 应为数组格式，当前为: {type(tags).__name__}")
    elif len(tags) < 2:
        errors.append(f"  \u26a0\ufe0f tags 至少需要2个，当前只有 {len(tags)} 个")
    return errors


def validate_status(meta: Dict, filepath: Path) -> List[str]:
    """检查status字段值是否合规"""
    errors = []
    status = meta.get("status")
    if status and status not in VALID_STATUS:
        errors.append(f"  \u26a0\ufe0f status 值不合规: '{status}'")
    return errors


def validate_validation_field(meta: Dict, filepath: Path) -> List[str]:
    """检查validation字段值是否合规"""
    errors = []
    validation = meta.get("validation")
    if validation and validation not in VALID_VALIDATION:
        errors.append(f"  \u26a0\ufe0f validation 值不合规: '{validation}'")
    return errors


def validate_dates(meta: Dict, filepath: Path) -> List[str]:
    """检查日期格式"""
    errors = []
    for field in ["created", "updated"]:
        value = meta.get(field)
        if value:
            if isinstance(value, datetime):
                continue
            val_str = str(value).strip()
            ok = False
            for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    datetime.strptime(val_str, fmt)
                    ok = True
                    break
                except ValueError:
                    continue
            if not ok:
                errors.append(f"  \u26a0\ufe0f {field} 日期格式不正确: '{value}'")
    return errors


def validate_relations(meta: Dict, filepath: Path) -> List[str]:
    """检查关系型字段格式"""
    errors = []
    relation_fields = ["prerequisite", "depends_on", "is_example_for", "refutes", "supersedes", "related"]
    for field in relation_fields:
        value = meta.get(field)
        if value is not None and not isinstance(value, list):
            errors.append(f"  \u26a0\ufe0f {field} 应为数组格式，当前为: {type(value).__name__}")
    return errors


def validate_applicability(meta: Dict, filepath: Path) -> List[str]:
    """检查适用场景字段格式"""
    errors = []
    app = meta.get("applicability")
    if app is not None:
        if not isinstance(app, dict):
            errors.append(f"  \u26a0\ufe0f applicability 应为对象格式")
        else:
            for key in ["project_scale", "project_type"]:
                if key in app and not isinstance(app[key], list):
                    errors.append(f"  \u26a0\ufe0f applicability.{key} 应为数组格式")
            if "performance_critical" in app and not isinstance(app["performance_critical"], bool):
                errors.append(f"  \u26a0\ufe0f applicability.performance_critical 应为布尔值")
    return errors

# ============================================================
# 主流程
# ============================================================

def validate_file(filepath: Path, strict: bool = False) -> Tuple[List[str], List[str]]:
    """校验单个文件，返回 (errors, warnings)"""
    errors = []
    warnings = []

    meta = extract_frontmatter(filepath)
    if meta is None:
        errors.append(f"  \u274c 缺少YAML Frontmatter或格式错误")
        return errors, warnings

    # 必填字段
    errors.extend(validate_required_fields(meta, filepath))

    # 标题前缀
    prefix_issues = validate_title_prefix(meta, filepath)
    if strict:
        errors.extend(prefix_issues)
    else:
        warnings.extend(prefix_issues)

    # 标签
    tag_issues = validate_tags(meta, filepath)
    warnings.extend(tag_issues)

    # 日期格式
    warnings.extend(validate_dates(meta, filepath))

    # status
    warnings.extend(validate_status(meta, filepath))

    # validation
    warnings.extend(validate_validation_field(meta, filepath))

    # 关系型字段
    warnings.extend(validate_relations(meta, filepath))

    # 适用场景
    warnings.extend(validate_applicability(meta, filepath))

    return errors, warnings


def scan_directory(root: Path, strict: bool = False) -> Tuple[int, int, int]:
    """扫描目录，返回 (total, error_count, warning_count)"""
    total = 0
    error_count = 0
    warning_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过特殊目录
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            if filename in SKIP_FILES:
                continue

            filepath = Path(dirpath) / filename
            try:
                rel_path = filepath.relative_to(root)
            except ValueError:
                rel_path = filepath
            total += 1

            errors, warnings = validate_file(filepath, strict)

            if errors or warnings:
                print(f"\n\U0001f4c4 {rel_path}")
                for e in errors:
                    print(e)
                    error_count += 1
                for w in warnings:
                    print(w)
                    warning_count += 1

    return total, error_count, warning_count


def main():
    parser = argparse.ArgumentParser(description="UnityKnowledge 元数据校验工具")
    parser.add_argument("--path", default=".", help="要校验的目录路径（相对于知识库根目录）")
    parser.add_argument("--strict", action="store_true", help="严格模式：警告也视为错误")
    args = parser.parse_args()

    # 确定根目录
    script_dir = Path(__file__).parent
    root = script_dir.parent
    target = root / args.path

    if not target.exists():
        print(f"\u274c 路径不存在: {target}")
        sys.exit(1)

    print(f"\U0001f50d 正在校验: {target}")
    print(f"\U0001f4cb 模式: {'严格' if args.strict else '标准'}")
    print("=" * 60)

    total, error_count, warning_count = scan_directory(target, args.strict)

    print("\n" + "=" * 60)
    print(f"\U0001f4ca 校验完成")
    print(f"   总文档数: {total}")
    print(f"   \u274c 错误: {error_count}")
    print(f"   \u26a0\ufe0f 警告: {warning_count}")
    print(f"   \u2705 通过: {total - error_count}")

    if error_count > 0:
        sys.exit(1)
    elif args.strict and warning_count > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
