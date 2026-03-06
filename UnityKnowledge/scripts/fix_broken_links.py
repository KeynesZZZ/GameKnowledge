"""
fix_broken_links.py - 批量修复断链（第三轮 - 最终版）
基于 check_links.py 的检查结果，自动替换旧格式链接为正确路径。
"""

import os
from pathlib import Path

ROOT = Path(r"E:\Other\Doc\UnityKnowledge")

REPLACEMENTS = [
    # ========== 第一轮 ==========
    ("../../10_架构设计/系统架构-存档系统.md", "../../10_架构设计/【系统架构】存档系统.md"),
    ("../../10_架构设计/设计原理-为什么要用设计模式.md", "../../10_架构设计/【设计原理】为什么要用设计模式.md"),
    ("./01-休闲游戏云存档系统", "./01_休闲游戏云存档系统"),
    ("../../25_DOTS技术栈/【教程】DOTS学习路径.md", "../25_DOTS技术栈/【教程】DOTS学习路径.md"),
    ("../../25_DOTS技术栈/【教程】JobSystem详解.md", "../25_DOTS技术栈/【教程】JobSystem详解.md"),
    ("./Shader基础语法.md", "./【教程】HLSL与Shader基础.md"),
    ("./URP管线配置.md", "./【最佳实践】URP常用配置.md"),
    ("./自定义Shader实战.md", "./【实战案例】自定义Shader.md"),
    ("../32_内存管理/【最佳实践】GC优化清单.md", "../../30_性能优化/32_内存管理/【最佳实践】GC优化清单.md"),
    ("../10_架构设计/教程-输入系统使用指南.md", "./【设计原理】新输入系统架构深度解析.md"),
    ("性能数据-UGUI-DrawCall影响因素全面测试.md", "【性能数据】UGUI DrawCall影响因素全面测试.md"),
    ("../20_核心系统/网络系统/教程-场景加载最佳实践.md", "../27_场景系统/【设计原理】场景加载底层机制.md"),
    ("../20_核心系统/网络系统/教程-云存档最佳实践.md", "../28_存档系统/【实战案例】云端存档冲突解决架构.md"),
    ("../20_核心系统/网络系统/教程-序列化最佳实践.md", "../28_存档系统/【设计原理】序列化机制深度对比.md"),
    ("../../20_核心系统/网络系统/教程-", "../../20_核心系统/29_网络系统/【教程】网络编程学习路径.md"),
    ("../30_性能优化/教程-粒子系统性能优化.md", "../../30_性能优化/33_渲染优化/【最佳实践】粒子系统优化.md"),
    ("性能数据-foreach-vs-for.md", "【性能数据】foreach vs for.md"),

    # ========== 第二轮 ==========
    ("./内存管理/", "./32_内存管理/"),
    ("./渲染优化/", "./33_渲染优化/"),
    ("./代码优化/", "./31_代码优化/"),
    ("./启动时间优化/", "./34_启动时间优化/"),
    ("../30_性能优化/教程-性能优化_学习路径.md", "./【教程】性能优化学习路径.md"),
    ("../../35_高级主题/教程-Unity内存管理.md", "../../35_高级主题/【设计原理】Unity内存管理.md"),
    ("../35_高级主题/教程-内存泄漏排查实战.md", "../35_高级主题/【实战案例】内存泄漏排查实战.md"),
    ("../../35_高级主题/教程-内存泄漏排查实战.md", "../../35_高级主题/【实战案例】内存泄漏排查实战.md"),
    ("../../30_性能优化/教程-渲染性能优化.md", "../../30_性能优化/【教程】渲染性能优化.md"),
    ("../../30_性能优化/教程-性能分析工具.md", "../../30_性能优化/【教程】性能分析工具.md"),
    ("(性能分析工具.md)", "(./【教程】性能分析工具.md)"),
    ("(CPU优化技术.md)", "(./【教程】CPU优化技术.md)"),
    ("(Unity内存管理.md)", "(../35_高级主题/【设计原理】Unity内存管理.md)"),
    ("(渲染性能优化.md)", "(./【教程】渲染性能优化.md)"),
    ("(打包与热更新.md)", "(../35_高级主题/【教程】打包与热更新.md)"),
    ("../../40_工具链/第三方库-UniTask.md", "../../60_第三方库/【教程】UniTask异步编程.md"),
    ("../../10_架构设计/代码片段-零GC字符串拼接.md", "../../30_性能优化/32_内存管理/【最佳实践】GC优化清单.md"),
    ("../../30_性能优化/教程-CPU优化技术.md", "../../30_性能优化/【教程】CPU优化技术.md"),
    ("../../36_高级编程/教程-高级编程_学习路径.md", "../../36_高级编程/【教程】高级编程学习路径.md"),
    ("../../30_性能优化/32_内存管理/../../30_性能优化/32_内存管理/【最佳实践】GC优化清单.md",
     "../../30_性能优化/32_内存管理/【最佳实践】GC优化清单.md"),

    # ========== 第三轮 ==========

    # --- 22_渲染系统 双重替换修复 ---
    ("【代码片段】【代码片段】Shader基础模板.md", "【代码片段】Shader基础模板.md"),

    # --- 30_性能优化/31_代码优化/Dictionary性能 路径修复 ---
    ("../../36_高级编程/【教程】C#高级特性.md", "../../../36_高级编程/【教程】C#高级特性.md"),

    # --- 40_工具链 ---
    ("../40_工具链/编辑器扩展/教程-编辑器扩展_学习路径.md", "./41_编辑器扩展/【教程】编辑器扩展学习路径.md"),
    ("(Editor扩展开发.md)", "(【教程】Editor扩展开发.md)"),
    ("../40_工具链/Editor扩展开发.md", "../40_工具链/【教程】Editor扩展开发.md"),
    ("(热更新方案对比.md)", "(【设计原理】热更新方案对比.md)"),
    ("../00_元数据与模板/开发规则清单.md", "./【教程】自动化规则检查工具.md"),

    # --- 50_平台适配 ---
    ("(iOS 专项.md)", "(【最佳实践】iOS专项.md)"),
    ("(Android 专项.md)", "(【最佳实践】Android专项.md)"),

    # --- 60_第三方库 ---
    ("(DOTween 深度使用.md)", "(【教程】DOTween深度使用.md)"),
    ("(UniTask 异步编程.md)", "(【教程】UniTask异步编程.md)"),
    ("../36_高级编程/教程-)", "../36_高级编程/【教程】高级编程学习路径.md)"),

    # --- unity-rules-checker 内部引用（指向不存在的子目录，改为自引用说明） ---
    ("(unity-rules-checker/README.md)", "(./【代码片段】可移植规则检查工具包.md)"),
    ("(unity-rules-checker/QUICKSTART.md)", "(./【代码片段】可移植规则检查工具包.md#快速开始)"),
    ("(unity-rules-checker/docs/开发规则清单.md)", "(./【教程】自动化规则检查工具.md)"),
    ("(unity-rules-checker/CHANGELOG.md)", "(./【代码片段】可移植规则检查工具包.md#更新日志)"),
]

SKIP_DIRS = [".git", ".claude", "scripts", "node_modules", "__pycache__", "_generated"]

def fix_all():
    fixed_count = 0
    files_fixed = set()

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            filepath = Path(dirpath) / filename

            try:
                content = filepath.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = filepath.read_text(encoding="gbk")
                except Exception:
                    continue

            original = content
            for old_text, new_text in REPLACEMENTS:
                if old_text in content:
                    content = content.replace(old_text, new_text)

            if content != original:
                filepath.write_text(content, encoding="utf-8")
                rel = filepath.relative_to(ROOT)
                files_fixed.add(str(rel))
                for old_text, new_text in REPLACEMENTS:
                    count = original.count(old_text)
                    if count > 0:
                        fixed_count += count
                        print(f"  \u2705 {rel}: '{old_text}' -> '{new_text}' ({count}处)")

    print(f"\n{'='*60}")
    print(f"\U0001f4ca 修复完成")
    print(f"   修复文件数: {len(files_fixed)}")
    print(f"   修复链接数: {fixed_count}")

if __name__ == "__main__":
    fix_all()
