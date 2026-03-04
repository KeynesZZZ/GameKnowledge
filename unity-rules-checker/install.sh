#!/bin/bash

###############################################################################
# Unity开发规则检查工具 - 安装脚本 (Linux/Mac)
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查是否在Unity项目目录中
check_unity_project() {
    if [ ! -d "Assets" ]; then
        print_error "未检测到Unity项目（找不到Assets目录）"
        print_info "请在Unity项目根目录中运行此脚本"
        return 1
    fi
    print_success "检测到Unity项目"
    return 0
}

# 创建备份
backup_existing() {
    local target_dir="$1"
    if [ -d "$target_dir" ]; then
        local backup_dir="${target_dir}_backup_$(date +%Y%m%d_%H%M%S)"
        print_warning "发现现有配置，正在备份到: $backup_dir"
        cp -r "$target_dir" "$backup_dir"
        print_success "备份完成"
    fi
}

# 安装SKILL文件
install_skills() {
    print_header "安装Claude Code SKILL"

    local skill_source=".claude/skills/check-rules.md"
    local skill_target="../.claude/skills/check-rules.md"

    # 创建目标目录
    mkdir -p "../.claude/skills"

    # 复制SKILL文件
    if [ -f "$skill_source" ]; then
        cp "$skill_source" "$skill_target"
        print_success "已安装: check-rules.md"
    else
        print_error "找不到源文件: $skill_source"
        return 1
    fi
}

# 安装Hook文件
install_hooks() {
    print_header "安装Git Hooks（可选）"

    if [ ! -d "../.git" ]; then
        print_warning "未检测到Git仓库，跳过Hook安装"
        return 0
    fi

    read -p "是否安装Git pre-commit Hook？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "跳过Hook安装"
        return 0
    fi

    local hook_source=".claude/hooks/pre-commit.md"
    local hook_target="../.git/hooks/pre-commit"
    local config_source=".claude/hooks/config.json"
    local config_target="../.claude/hooks/config.json"

    # 创建目标目录
    mkdir -p "../.claude/hooks"

    # 复制Hook文件
    if [ -f "$hook_source" ]; then
        cp "$hook_source" "$hook_target"
        chmod +x "$hook_target"
        print_success "已安装: pre-commit Hook"
    fi

    # 复制配置文件
    if [ -f "$config_source" ]; then
        cp "$config_source" "$config_target"
        print_success "已安装: Hook配置文件"
    fi

    print_info "Git Hook将在每次提交前自动检查代码规则"
}

# 安装规则文档
install_docs() {
    print_header "安装规则文档"

    local docs_source="docs/开发规则清单.md"
    local docs_target="../docs/开发规则清单.md"

    # 创建目标目录
    mkdir -p "../docs"

    # 复制文档
    if [ -f "$docs_source" ]; then
        cp "$docs_source" "$docs_target"
        print_success "已安装: 开发规则清单.md"
    else
        print_warning "找不到规则文档: $docs_source"
        print_info "SKILL将使用内置规则（功能可能受限）"
    fi
}

# 验证安装
verify_installation() {
    print_header "验证安装"

    local errors=0

    if [ -f "../.claude/skills/check-rules.md" ]; then
        print_success "SKILL文件已安装"
    else
        print_error "SKILL文件未找到"
        ((errors++))
    fi

    if [ -f "../docs/开发规则清单.md" ]; then
        print_success "规则文档已安装"
    else
        print_warning "规则文档未找到（可选）"
    fi

    if [ -f "../.git/hooks/pre-commit" ]; then
        print_success "Git Hook已安装"
    fi

    return $errors
}

# 显示使用说明
show_usage() {
    print_header "安装完成！"

    cat << EOF

${GREEN}Unity开发规则检查工具安装成功！${NC}

使用方法：
1. 在Claude Code中运行：
   /check-rules Assets/Scripts/YourScript.cs

2. 检查整个目录：
   /check-rules Assets/Scripts

3. 只检查CRITICAL规则：
   /check-rules Assets/Scripts --severity=CRITICAL

4. 查看帮助：
   /check-rules --help

文档位置：
- 规则清单: ./docs/开发规则清单.md
- SKILL文件: ./.claude/skills/check-rules.md

卸载方法：
rm -rf .claude/skills/check-rules.md
rm -rf .claude/hooks
rm -rf docs/开发规则清单.md
rm -f .git/hooks/pre-commit

EOF

    if [ -f "../.git/hooks/pre-commit" ]; then
        print_info "Git Hook已配置，提交代码时将自动检查"
    fi
}

# 主安装流程
main() {
    clear
    print_header "Unity开发规则检查工具 - 安装向导"

    # 检查Unity项目
    if ! check_unity_project; then
        exit 1
    fi

    # 显示版本信息
    if [ -f "VERSION" ]; then
        print_info "工具版本: $(cat VERSION | head -1)"
    fi

    echo ""
    read -p "是否继续安装？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "安装已取消"
        exit 0
    fi

    # 备份现有配置
    backup_existing "../.claude"
    backup_existing "../docs"

    # 执行安装
    install_skills
    install_docs
    install_hooks

    # 验证
    if verify_installation; then
        show_usage
    else
        print_error "安装过程中出现问题，请检查错误信息"
        exit 1
    fi
}

# 运行主程序
main
