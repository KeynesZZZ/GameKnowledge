#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的内部链接修复脚本
1. 构建完整的文件名映射（旧风格 → 新风格）
2. 更新所有Obsidian和Markdown链接
3. URL解码
4. 移除无效的模板占位符
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Windows UTF-8 encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def build_rename_map(target_dir: Path) -> dict:
    """构建文件重命名映射（旧风格 → 新风格）"""
    rename_map = {}

    # 扫描所有新风格文件
    for filepath in target_dir.rglob('*.md'):
        if not filepath.is_file() or 'readme' in filepath.name.lower():
            continue

        filename = filepath.stem

        # 检查是否为新风格（【类型】主题）
        if filename.startswith('【'):
            match = re.match(r'【(.+?)】(.+)', filename)
            if match:
                doc_type, topic = match.groups()
                # 对应的旧风格名称
                old_name = f"{doc_type}-{topic}"
                rename_map[old_name] = filename

    return rename_map


def fix_links_comprehensive(filepath: Path, rename_map: dict) -> bool:
    """全面修复文件中的所有链接"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        modified = False

        # 1. URL解码所有链接
        # [[教程-Job%20System]] → [[教程-Job System]]
        # [...](ECS%20入门.md) → [...](ECS入门.md)
        if '%' in content:
            # 解码 Obsidian 链接
            def decode_obsidian_link(m):
                decoded = unquote(m.group(1))
                return f'[[{decoded}]]'

            content = re.sub(r'\[\[([^\]]+?)\]\]', decode_obsidian_link, content)

            # 解码 Markdown 链接的URL部分
            def decode_markdown_url(m):
                text = m.group(1)
                url = unquote(m.group(2))
                return f'[{text}]({url})'

            content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', decode_markdown_url, content)

            modified = modified or content != original_content

        # 2. 更新旧风格文件名为新风格（Obsidian链接）
        # [[设计原理-对象池本质]] → [[【设计原理】对象池本质]]
        for old_name, new_name in rename_map.items():
            pattern = rf'\[\[{re.escape(old_name)}\]\]'
            if re.search(pattern, content):
                content = re.sub(pattern, f'[[{new_name}]]', content)
                modified = True

        # 3. 更新旧风格文件名为新风格（Markdown链接）
        # [...](设计原理-对象池本质.md) → [...](【设计原理】对象池本质.md)
        for old_name, new_name in rename_map.items():
            pattern = rf'\]\({re.escape(old_name)}\.md\)'
            if re.search(pattern, content):
                replacement = f']({new_name}.md)'
                content = re.sub(pattern, replacement, content)
                modified = True

        # 4. 移除无效的模板占位符
        invalid_patterns = [
            r'\[\[XXX\]\]',
            r'\[\[相关笔记[12]\]\]',
            r'\[\[笔记名\]\]',
            r'\[\[设计原理-XXX\]\]',
            r'\[\[代码片段-XXX\]\]',
            r'\[\[教程-XXX\]\]',
            r'\[\[最佳实践-XXX\]\]',
            r'\[\[10_架构设计/事件系统专题索引\]\]',  # 不存在
            r'\[\[10_架构设计/对象池专题索引\]\]',  # 不存在
            r'\[\[10_架构设计/状态机专题索引\]\]',  # 不存在
            r'\[\[10_架构设计/设计模式专题索引\]\]',  # 不存在
            r'\[\[28_存档系统/【实战案例】云端存档冲突解决架构\]\]',  # 路径错误
            r'\[\[对象池-GameObject专用实现\]\]',  # 不存在
            r'\[\[Unity GC优化最佳实践\]\]',  # 不存在
            r'\[\[00_元数据与模板/元数据规范\]\]',  # 自引用
            r'\[\[00_元数据与模板/标签体系\]\]',  # 自引用
            r'\[\[../../10_架构设计/\]\]',  # 目录链接
            r'\[\[../../100_项目实战/\]\]',  # 目录链接
            r'\[\[../100_项目实战/XX项目\]\]',  # 模板
            r'\[\[../20_核心系统/XX系统/\]\]',  # 模板
            r'\[\[../30_性能优化/XXX/【性能数据】XXX\]\]',  # 模板
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, '', content)
                modified = True

        # 5. 清理多余的空行（超过2个连续空行）
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 6. 确保文件以换行符结尾
        if content and not content.endswith('\n'):
            content += '\n'

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"❌ 处理文件失败: {filepath}")
        print(f"   错误: {e}")
        return False


def main():
    target_dir = Path('UnityKnowledge')

    print("=" * 70)
    print("🔧 全面修复：更新所有内部链接")
    print("=" * 70)
    print(f"📂 工作目录: {target_dir}\n")

    # 构建重命名映射
    print("📋 构建文件重命名映射...")
    rename_map = build_rename_map(target_dir)
    print(f"✅ 检测到 {len(rename_map)} 个重命名规则\n")

    if len(rename_map) > 0:
        print("示例映射:")
        for i, (old, new) in enumerate(list(rename_map.items())[:5]):
            print(f"  {old} → {new}")
        if len(rename_map) > 5:
            print(f"  ... 还有 {len(rename_map) - 5} 个")
        print()

    # 扫描所有文件
    md_files = list(target_dir.rglob('*.md'))
    md_files = [f for f in md_files if f.is_file() and 'readme' not in f.name.lower()]

    print(f"📄 将扫描 {len(md_files)} 个文件\n")

    # 修复链接
    fixed_count = 0
    for filepath in md_files:
        if fix_links_comprehensive(filepath, rename_map):
            fixed_count += 1
            if fixed_count <= 20:
                rel_path = filepath.relative_to(target_dir.parent)
                print(f"✅ {rel_path}")

    if fixed_count > 20:
        print(f"... 还有 {fixed_count - 20} 个文件")

    print(f"\n" + "=" * 70)
    print("✨ 修复完成!")
    print("=" * 70)
    print(f"\n📊 统计:")
    print(f"   重命名规则: {len(rename_map)} 个")
    print(f"   修复文件: {fixed_count} 个")

    print(f"\n💡 下一步:")
    print(f"   1. 运行诊断验证: python tools/diagnose_broken_links.py")
    print(f"   2. 如果结果满意，提交更改")

    return 0


if __name__ == '__main__':
    sys.exit(main())
