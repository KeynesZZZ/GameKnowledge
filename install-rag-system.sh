#!/bin/bash

# Mac RAG 系统一键安装脚本
# 自动安装所有依赖并配置环境

# 颜色输出配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} 🚀 Mac RAG 系统一键安装器${NC}"
    echo -e "${CYAN}=============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查命令是否存在
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    fi
    return 1
}

# 安装 Homebrew（如果未安装）
install_homebrew() {
    if ! check_command "brew"; then
        print_info "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 配置 PATH
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        print_success "Homebrew 已安装"
    fi
}

# 安装 Ollama
install_ollama() {
    if ! check_command "ollama"; then
        print_info "正在安装 Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # 启动 Ollama 服务
        print_info "启动 Ollama 服务..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
        
        # 下载 bge-m3 模型
        print_info "下载 bge-m3 向量模型..."
        ollama pull bge-m3
        
        print_success "Ollama 安装完成"
    else
        print_success "Ollama 已安装"
        
        # 检查 bge-m3 模型
        if ! ollama list | grep -q "bge-m3"; then
            print_info "下载 bge-m3 向量模型..."
            ollama pull bge-m3
        fi
    fi
}

# 安装 Docker
install_docker() {
    if ! check_command "docker"; then
        print_warning "请手动安装 Docker Desktop"
        print_info "访问: https://www.docker.com/products/docker-desktop/"
        print_info "下载并安装 Docker Desktop for Mac"
        
        read -p "安装完成后按回车继续..."
    else
        print_success "Docker 已安装"
    fi
    
    # 检查 Docker 是否运行
    if docker info >/dev/null 2>&1; then
        print_success "Docker 服务正在运行"
    else
        print_error "Docker 服务未运行，请启动 Docker Desktop"
        exit 1
    fi
}

# 安装 OpenClaw
install_openclaw() {
    if ! check_command "openclaw"; then
        print_info "正在安装 OpenClaw..."
        
        # 使用 Homebrew 安装
        if check_command "brew"; then
            brew tap openclaw/tap
            brew install openclaw
        else
            print_warning "Homebrew 未安装，请手动安装 OpenClaw"
            print_info "访问: https://openclaw.io/docs/installation"
        fi
    else
        print_success "OpenClaw 已安装"
    fi
}

# 安装其他工具
install_tools() {
    print_info "安装其他必要工具..."
    
    # 安装 curl（如果不存在）
    if ! check_command "curl"; then
        brew install curl
    fi
    
    # 安装 wget（如果不存在）
    if ! check_command "wget"; then
        brew install wget
    fi
    
    # 安装 jq（JSON 处理）
    if ! check_command "jq"; then
        brew install jq
    fi
}

# 创建脚本文件
create_scripts() {
    print_info "创建 RAG 系统脚本..."
    
    # 创建桌面目录（如果不存在）
    mkdir -p ~/Desktop
    
    # 复制脚本到桌面
    cp start-rag.sh ~/Desktop/
    cp stop-rag.sh ~/Desktop/
    cp status-rag.sh ~/Desktop/
    
    # 设置执行权限
    chmod +x ~/Desktop/start-rag.sh
    chmod +x ~/Desktop/stop-rag.sh
    chmod +x ~/Desktop/status-rag.sh
    
    print_success "脚本已创建到桌面"
}

# 创建配置文件
create_config_files() {
    print_info "创建配置文件..."
    
    # 创建配置目录
    mkdir -p ~/.rag-system/configs
    
    # 复制配置文件
    cp dify-rag-config.md ~/.rag-system/configs/
    cp openclaw-config.yaml ~/.rag-system/configs/
    
    print_success "配置文件已创建"
}

# 创建日志目录
create_log_directory() {
    print_info "创建日志目录..."
    
    mkdir -p ~/.rag-system/logs
    
    print_success "日志目录已创建"
}

# 显示安装结果
show_installation_result() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${GREEN} 🎉 安装完成！${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
    echo "已安装的组件："
    
    if check_command "ollama"; then
        echo -e "  ${GREEN}✅${NC} Ollama + bge-m3 模型"
    fi
    
    if check_command "docker"; then
        echo -e "  ${GREEN}✅${NC} Docker Desktop"
    fi
    
    if check_command "openclaw"; then
        echo -e "  ${GREEN}✅${NC} OpenClaw"
    fi
    
    echo -e "  ${GREEN}✅${NC} RAG 系统脚本"
    echo -e "  ${GREEN}✅${NC} 配置文件"
    echo ""
    echo "下一步："
    echo "1. 双击桌面的 start-rag.sh 启动系统"
    echo "2. 访问 http://localhost:8000 使用 Dify"
    echo "3. 在 Dify 中配置知识库应用"
    echo ""
    echo "桌面上的脚本："
    echo "- start-rag.sh: 启动 RAG 系统"
    echo "- stop-rag.sh: 停止 RAG 系统"
    echo "- status-rag.sh: 检查系统状态"
    echo ""
    echo "配置文件位置："
    echo "- ~/.rag-system/configs/"
    echo "- ~/.rag-system/logs/"
    echo ""
    echo -e "${CYAN}=============================================${NC}"
}

# 主安装流程
main() {
    print_header
    
    echo ""
    print_info "开始安装 Mac RAG 系统..."
    echo ""
    
    # 检查系统要求
    print_info "检查系统要求..."
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS"
        exit 1
    fi
    
    # 安装流程
    install_homebrew
    install_ollama
    install_docker
    install_openclaw
    install_tools
    create_scripts
    create_config_files
    create_log_directory
    
    show_installation_result
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项："
    echo "  -h, --help     显示帮助信息"
    echo "  --skip-ollama  跳过 Ollama 安装"
    echo "  --skip-docker  跳过 Docker 检查"
    echo "  --skip-openclaw 跳过 OpenClaw 安装"
    echo ""
    echo "示例："
    echo "  $0                    # 完整安装"
    echo "  $0 --skip-docker      # 跳过 Docker 检查"
}

# 解析命令行参数
SKIP_OLLAMA=false
SKIP_DOCKER=false
SKIP_OPENCLAW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-openclaw)
            SKIP_OPENCLAW=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 运行主函数
main