#!/bin/bash

# Mac 专用 RAG 系统停止脚本
# 作者: RAG 系统自动化脚本
# 版本: 1.0

# 颜色输出配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志目录
LOG_DIR="$HOME/.rag-system/logs"
STOP_LOG="$LOG_DIR/stop-rag.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$STOP_LOG"
}

# 带颜色的输出函数
print_header() {
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} 🛑 RAG 系统服务停止脚本${NC}"
    echo -e "${CYAN}=============================================${NC}"
    log "开始停止 RAG 系统服务..."
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "成功: $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "警告: $1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "错误: $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "信息: $1"
}

# 停止 Ollama
stop_ollama() {
    print_info "正在停止 Ollama 服务..."
    
    # 查找并停止 ollama 进程
    if pgrep -f ollama > /dev/null; then
        pkill -f ollama
        sleep 2
        
        # 确认是否已停止
        if ! pgrep -f ollama > /dev/null; then
            print_success "Ollama 服务已停止"
        else
            print_warning "Ollama 进程仍在运行，强制终止..."
            pkill -9 -f ollama
        fi
    else
        print_info "Ollama 服务未在运行"
    fi
}

# 停止 Dify Docker 服务
stop_dify() {
    print_info "正在停止 Dify Docker 服务..."
    
    local dify_dir="$HOME/dify/docker"
    
    if [ -d "$dify_dir" ]; then
        cd "$dify_dir"
        
        # 检查是否有 docker-compose 文件
        if [ -f "docker-compose.yaml" ]; then
            # 停止服务
            docker-compose down > "$LOG_DIR/dify-stop.log" 2>&1
            
            if [ $? -eq 0 ]; then
                print_success "Dify Docker 服务已停止"
            else
                print_error "停止 Dify Docker 服务失败"
            fi
        else
            print_warning "未找到 Dify docker-compose 文件"
        fi
    else
        print_info "Dify 目录不存在，跳过停止"
    fi
}

# 停止 OpenClaw
stop_openclaw() {
    print_info "正在停止 OpenClaw 服务..."
    
    # 查找并停止 openclaw 进程
    if pgrep -f openclaw > /dev/null; then
        pkill -f openclaw
        sleep 2
        
        # 确认是否已停止
        if ! pgrep -f openclaw > /dev/null; then
            print_success "OpenClaw 服务已停止"
        else
            print_warning "OpenClaw 进程仍在运行，强制终止..."
            pkill -9 -f openclaw
        fi
    else
        print_info "OpenClaw 服务未在运行"
    fi
}

# 清理临时文件和进程
cleanup() {
    print_info "正在清理临时文件和进程..."
    
    # 清理可能的僵尸进程
    local processes=("ollama" "openclaw" "docker-compose")
    
    for proc in "${processes[@]}"; do
        if pgrep -f "$proc" > /dev/null; then
            print_warning "发现残留的 $proc 进程，正在清理..."
            pkill -f "$proc" 2>/dev/null || true
        fi
    done
    
    # 清理临时文件
    if [ -d "/tmp/ollama" ]; then
        print_info "清理 Ollama 临时文件..."
        rm -rf /tmp/ollama/* 2>/dev/null || true
    fi
    
    print_success "清理完成"
}

# 显示停止结果
show_status() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${GREEN} ✅ RAG 系统服务已停止！${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
    echo "已停止的服务："
    echo "- Ollama (端口: 11434)"
    echo "- Dify Docker (端口: 8000)"
    echo "- OpenClaw (端口: 18789)"
    echo ""
    echo "日志文件位置: $LOG_DIR"
    echo ""
    
    log "RAG 系统停止完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项："
    echo "  -h, --help     显示帮助信息"
    echo "  -f, --force    强制停止所有相关进程"
    echo "  -c, --cleanup  停止后清理临时文件"
    echo ""
    echo "示例："
    echo "  $0              # 正常停止服务"
    echo "  $0 -f           # 强制停止所有进程"
    echo "  $0 -c           # 停止并清理临时文件"
}

# 强制停止模式
force_stop() {
    print_warning "正在强制停止所有 RAG 相关进程..."
    
    # 强制终止所有相关进程
    pkill -9 -f ollama 2>/dev/null || true
    pkill -9 -f openclaw 2>/dev/null || true
    pkill -9 -f docker-compose 2>/dev/null || true
    
    # 停止所有 Docker 容器（可选）
    print_info "正在停止 Docker 容器..."
    docker stop $(docker ps -q) 2>/dev/null || true
    
    sleep 3
    print_success "强制停止完成"
}

# 主函数
main() {
    print_header
    
    # 解析命令行参数
    local force=false
    local cleanup=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -c|--cleanup)
                cleanup=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [ "$force" = true ]; then
        force_stop
    else
        # 正常停止流程
        stop_ollama
        stop_dify
        stop_openclaw
    fi
    
    if [ "$cleanup" = true ]; then
        cleanup
    fi
    
    show_status
}

# 运行主函数
main "$@"

read -p "按回车退出..."