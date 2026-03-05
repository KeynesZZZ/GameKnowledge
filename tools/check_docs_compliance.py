#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnityKnowledge 文档合规性检查脚本

检查所有 Markdown 文档是否符合元数据规范、标签体系、文档定位指南等要求。
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DocComplianceChecker:
    """文档合规性检查器"""

    # 必填的 YAML 字段
    REQUIRED_FIELDS = ['title', 'tags', 'category', 'created', 'updated', 'description']

    # 文档类型前缀
    DOC_TYPE_PREFIXES = [
        '【设计原理】', '【教程】', '【代码片段】', '【性能数据】',
        '【最佳实践】', '【踩坑记录】', '【架构决策】', '【系统架构】',
        '【实战案例】', '【反模式】', '【模板】'
    ]

    # 技术领域标签
    TECH_DOMAIN_TAGS = [
        '架构', '渲染', '物理', '动画', 'UI', '音频', '网络', 'AI',
        '性能优化', '内存优化', '加载优化', 'DOTS'
    ]

    # 标准分类路径
    VALID_CATEGORIES = {
        '架构设计': ['代码片段', '最佳实践', '设计原理', '架构决策', '系统架构', '实战案例', '反模式'],
        '核心系统': ['动画系统', '渲染与Shader', '物理系统', '音频系统', '网络编程', 'AI与导航'],
        '性能优化': ['代码优化', '内存管理', '渲染优化', '启动时间优化'],
        '工具链': ['Editor扩展', '资源管线', '自动化构建', '热更新'],
        '平台适配': ['iOS', 'Android', 'WebGL', '主机'],
        '第三方库': ['DOTween', 'UniTask', 'Zenject', 'Odin'],
        '项目实战': ['云存档系统', '休闲游戏框架'],
        '项目复盘': [],
        '元数据与模板': ['模板']
    }

    def __init__(self, root_path: str, exclude_readme: bool = False):
        """初始化检查器

        Args:
            root_path: UnityKnowledge 目录路径
            exclude_readme: 是否排除 README 文件
        """
        self.root_path = Path(root_path)
        self.issues: List[Dict] = []
        self.exclude_readme = exclude_readme

    def check_all_docs(self) -> Dict[str, any]:
        """检查所有文档

        Returns:
            检查结果统计
        """
        print(f"🔍 开始检查文档: {self.root_path}")
        print("=" * 60)

        md_files = list(self.root_path.rglob('*.md'))

        # 排除 README 文件
        if self.exclude_readme:
            original_count = len(md_files)
            md_files = [f for f in md_files if f.name.lower() != 'readme.md']
            excluded_count = original_count - len(md_files)
            if excluded_count > 0:
                print(f"ℹ️  已排除 {excluded_count} 个 README.md 文件")

        if not md_files:
            print("❌ 未找到任何 Markdown 文件")
            return {'total': 0, 'compliant': 0, 'non_compliant': 0, 'issues': []}

        print(f"📄 找到 {len(md_files)} 个 Markdown 文件\n")

        for md_file in md_files:
            self.check_single_file(md_file)

        # 统计结果
        compliant_count = len([f for f in md_files if not any(
            i['file'] == str(f.relative_to(self.root_path)) for i in self.issues
        )])

        result = {
            'total': len(md_files),
            'compliant': compliant_count,
            'non_compliant': len(md_files) - compliant_count,
            'issues': self.issues
        }

        return result

    def check_single_file(self, file_path: Path):
        """检查单个文件

        Args:
            file_path: 文件路径
        """
        relative_path = str(file_path.relative_to(self.root_path))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查 YAML Frontmatter
            frontmatter = self.extract_frontmatter(content)
            if not frontmatter:
                self.add_issue(relative_path, 'CRITICAL', '缺少 YAML Frontmatter')
                return

            # 检查必填字段
            for field in self.REQUIRED_FIELDS:
                if field not in frontmatter:
                    self.add_issue(relative_path, 'CRITICAL', f'缺少必填字段: {field}')

            # 检查 title
            if 'title' in frontmatter:
                self.check_title(relative_path, frontmatter['title'])

            # 检查 tags
            if 'tags' in frontmatter:
                self.check_tags(relative_path, frontmatter['tags'])

            # 检查 category
            if 'category' in frontmatter:
                self.check_category(relative_path, frontmatter['category'])

            # 检查 description
            if 'description' in frontmatter:
                self.check_description(relative_path, frontmatter['description'])

            # 检查时间格式
            for time_field in ['created', 'updated']:
                if time_field in frontmatter:
                    self.check_datetime_format(relative_path, time_field, frontmatter[time_field])

            # 检查文档结构
            self.check_document_structure(relative_path, content)

        except Exception as e:
            self.add_issue(relative_path, 'ERROR', f'读取文件失败: {str(e)}')

    def extract_frontmatter(self, content: str) -> Optional[Dict]:
        """提取 YAML Frontmatter

        Args:
            content: 文件内容

        Returns:
            Frontmatter 字典，如果不存在则返回 None
        """
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return None

        frontmatter_text = match.group(1)
        frontmatter = {}

        # 简单解析 YAML（仅支持 key: value 格式）
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # 处理数组格式的 tags
                if key == 'tags' and value.startswith('['):
                    # 提取数组内容
                    tags_match = re.match(r'\[(.*?)\]', value)
                    if tags_match:
                        value = [t.strip().strip('\'"') for t in tags_match.group(1).split(',')]
                elif key == 'tags' and not isinstance(value, list):
                    value = [value]

                frontmatter[key] = value

        return frontmatter

    def check_title(self, file_path: str, title: str):
        """检查标题

        Args:
            file_path: 文件路径
            title: 标题
        """
        if not title:
            self.add_issue(file_path, 'CRITICAL', 'title 字段为空')
            return

        # 检查是否有类型前缀
        has_prefix = any(title.startswith(prefix) for prefix in self.DOC_TYPE_PREFIXES)
        if not has_prefix:
            self.add_issue(file_path, 'HIGH', f'title 缺少类型前缀: {title}')

    def check_tags(self, file_path: str, tags: any):
        """检查标签

        Args:
            file_path: 文件路径
            tags: 标签（可以是字符串或列表）
        """
        # 确保 tags 是列表
        if isinstance(tags, str):
            tags = [tags]

        if not tags or len(tags) < 2:
            self.add_issue(file_path, 'HIGH', f'tags 数量不足，当前: {len(tags) if tags else 0}，要求: ≥2')
            return

        # 检查是否有技术领域标签
        has_tech_tag = any(tag in self.TECH_DOMAIN_TAGS for tag in tags)
        if not has_tech_tag:
            self.add_issue(file_path, 'MEDIUM', f'tags 缺少技术领域标签，当前: {tags}')

    def check_category(self, file_path: str, category: str):
        """检查分类路径

        Args:
            file_path: 文件路径
            category: 分类路径
        """
        if not category:
            self.add_issue(file_path, 'HIGH', 'category 字段为空')
            return

        parts = category.split('/')
        if len(parts) != 2:
            self.add_issue(file_path, 'MEDIUM', f'category 格式不正确，应为 "一级分类/二级分类"，当前: {category}')
            return

        primary, secondary = parts
        if primary not in self.VALID_CATEGORIES:
            self.add_issue(file_path, 'MEDIUM', f'category 一级分类不标准: {primary}')
            return

        if self.VALID_CATEGORIES[primary] and secondary not in self.VALID_CATEGORIES[primary]:
            self.add_issue(file_path, 'LOW', f'category 二级分类不在标准列表中: {secondary}')

    def check_description(self, file_path: str, description: str):
        """检查描述

        Args:
            file_path: 文件路径
            description: 描述
        """
        if not description:
            self.add_issue(file_path, 'MEDIUM', 'description 字段为空')
            return

        if len(description) > 50:
            self.add_issue(file_path, 'LOW', f'description 过长，当前: {len(description)} 字，建议: ≤50 字')

    def check_datetime_format(self, file_path: str, field_name: str, datetime_str: str):
        """检查时间格式

        Args:
            file_path: 文件路径
            field_name: 字段名（created/updated）
            datetime_str: 时间字符串
        """
        if not datetime_str:
            self.add_issue(file_path, 'MEDIUM', f'{field_name} 字段为空')
            return

        try:
            datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                self.add_issue(file_path, 'LOW', f'{field_name} 时间格式不正确: {datetime_str}')

    def check_document_structure(self, file_path: str, content: str):
        """检查文档结构

        Args:
            file_path: 文件路径
            content: 文档内容
        """
        # 移除 frontmatter
        content_without_frontmatter = re.sub(r'^---\n.*?\n---', '', content, flags=re.DOTALL)

        # 检查是否有"文档定位"章节
        if '## 文档定位' not in content_without_frontmatter and '## 文档定位\n' not in content_without_frontmatter:
            self.add_issue(file_path, 'LOW', '缺少"文档定位"章节')

        # 检查是否有"相关链接"章节
        if '## 相关链接' not in content_without_frontmatter:
            self.add_issue(file_path, 'LOW', '缺少"相关链接"章节')

    def add_issue(self, file_path: str, severity: str, message: str):
        """添加问题

        Args:
            file_path: 文件路径
            severity: 严重程度 (CRITICAL/HIGH/MEDIUM/LOW)
            message: 问题信息
        """
        self.issues.append({
            'file': file_path,
            'severity': severity,
            'message': message
        })

    def print_results(self, result: Dict):
        """打印检查结果

        Args:
            result: 检查结果
        """
        print("\n" + "=" * 60)
        print("📊 检查结果统计")
        print("=" * 60)

        total = result['total']
        compliant = result['compliant']
        non_compliant = result['non_compliant']

        print(f"总文档数: {total}")
        print(f"✅ 合规文档: {compliant} ({compliant/total*100:.1f}%)")
        print(f"❌ 不合规文档: {non_compliant} ({non_compliant/total*100:.1f}%)")

        if result['issues']:
            print("\n" + "=" * 60)
            print("🔴 问题清单")
            print("=" * 60)

            # 按严重程度分组
            issues_by_severity = {
                'CRITICAL': [],
                'HIGH': [],
                'MEDIUM': [],
                'LOW': [],
                'ERROR': []
            }

            for issue in result['issues']:
                issues_by_severity[issue['severity']].append(issue)

            # 打印问题
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'ERROR']:
                issues = issues_by_severity[severity]
                if issues:
                    severity_emoji = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠',
                        'MEDIUM': '🟡',
                        'LOW': '🟢',
                        'ERROR': '💥'
                    }
                    print(f"\n{severity_emoji[severity]} {severity} ({len(issues)} 个):")
                    for issue in issues:
                        print(f"  - [{issue['file']}] {issue['message']}")

        print("\n" + "=" * 60)
        if result['non_compliant'] == 0:
            print("🎉 所有文档都符合规范！")
        else:
            print(f"⚠️  发现 {result['non_compliant']} 个文档需要修正")
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='检查 UnityKnowledge 文档合规性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python check_docs_compliance.py                    # 检查所有文档
  python check_docs_compliance.py --exclude-readme    # 排除 README 文件
  python check_docs_compliance.py UnityKnowledge      # 指定目录
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default=None,
        help='要检查的目录路径（默认: UnityKnowledge）'
    )

    parser.add_argument(
        '--exclude-readme',
        action='store_true',
        help='排除 README.md 文件'
    )

    args = parser.parse_args()

    # 确定检查路径
    if args.path:
        root_path = args.path
    else:
        # 获取脚本所在目录的上级目录中的 UnityKnowledge
        script_dir = Path(__file__).parent
        root_path = script_dir.parent / 'UnityKnowledge'

    if not Path(root_path).exists():
        print(f"❌ 错误：找不到目录 {root_path}")
        sys.exit(1)

    checker = DocComplianceChecker(root_path, exclude_readme=args.exclude_readme)
    result = checker.check_all_docs()
    checker.print_results(result)

    # 如果有不合规文档，返回非零退出码
    sys.exit(0 if result['non_compliant'] == 0 else 1)


if __name__ == '__main__':
    main()
