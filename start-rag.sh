#!/bin/bash

# Mac 专用 Ollama + Dify + OpenClaw + 向量库 RAG 一键启动脚本
# 作者: RAG 系统自动化脚本
# 版本: 1.0

# ======================== 用户配置区域 ========================
# 请修改为你的 Obsidian 笔记库路径
OBSIDIAN_PATH="/Users/$(whoami)/Documents/Obsidian笔记库"
# 或者使用现有的 UnityKnowledge 路径
# OBSIDIAN_PATH="/Users/$(whoami)/git/Doc/UnityKnowledge"

# 服务端口配置
OLLAMA_PORT="11434"
DIFY_PORT="8000"
OPENCLAW_PORT="18789"

# 日志文件路径
LOG_DIR="$HOME/.rag-system/logs"
START_LOG="$LOG_DIR/start-rag.log"
# ==========================================================

# 颜色输出配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$START_LOG"
}

# 带颜色的输出函数
print_header() {
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} 🚀 Obsidian + Dify + Ollama + OpenClaw 一键启动${NC}"
    echo -e "${CYAN}=============================================${NC}"
    log "开始启动 RAG 系统..."
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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "未找到命令: $1"
        return 1
    fi
    return 0
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "$service 端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 检查服务是否运行
check_service() {
    local service=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_success "$service 已在端口 $port 运行"
        return 0
    else
        print_info "$service 未在端口 $port 运行"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0
    
    print_info "等待 $service 启动..."
    
    while [ $attempt -lt $max_attempts ]; do
        if check_service "$service" "$port"; then
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done
    
    print_error "$service 启动超时"
    return 1
}

# 启动 Ollama
start_ollama() {
    echo ""
    print_info "1️⃣ 启动 Ollama（允许局域网/容器访问）"
    
    # 检查 Ollama 是否已安装
    if ! check_command "ollama"; then
        print_error "请先安装 Ollama: https://ollama.ai"
        exit 1
    fi
    
    # 设置环境变量
    export OLLAMA_HOST=0.0.0.0:$OLLAMA_PORT
    export OLLAMA_ORIGINS="*"
    
    # 检查是否已在运行
    if check_service "Ollama" "$OLLAMA_PORT"; then
        print_info "Ollama 已在运行，跳过启动"
        return 0
    fi
    
    # 启动 Ollama
    print_info "正在启动 Ollama 服务..."
    nohup ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    
    # 等待启动
    if wait_for_service "Ollama" "$OLLAMA_PORT"; then
        print_success "Ollama 启动成功"
        
        # 检查模型
        print_info "检查 bge-m3 模型..."
        if ollama list | grep -q "bge-m3"; then
            print_success "bge-m3 模型已就绪"
        else
            print_warning "bge-m3 模型未找到，开始下载..."
            ollama pull bge-m3
        fi
        
        return 0
    else
        print_error "Ollama 启动失败"
        return 1
    fi
}

# 启动 Dify
start_dify() {
    echo ""
    print_info "2️⃣ 启动 Dify Docker 服务"
    
    # 检查 Docker
    if ! check_command "docker"; then
        print_error "请先安装 Docker Desktop"
        exit 1
    fi
    
    if ! check_command "docker-compose"; then
        print_error "请先安装 docker-compose"
        exit 1
    fi
    
    # 检查 Dify 目录
    local dify_dir="$HOME/dify/docker"
    if [ ! -d "$dify_dir" ]; then
        print_info "创建 Dify 目录..."
        mkdir -p "$dify_dir"
        cd "$dify_dir"
        
        # 下载 Dify docker-compose 文件
        print_info "下载 Dify 配置文件..."
        curl -L https://github.com/langgenius/dify/raw/main/docker/docker-compose.yaml -o docker-compose.yaml
        curl -L https://github.com/langgenius/dify/raw/main/docker/.env.example -o .env
        
        # 配置环境变量
        sed -i '' 's/EXPOSE_NGINX_PORT=.*/EXPOSE_NGINX_PORT=8000/' .env
        sed -i '' 's/EXPOSE_NGINX_SSL_PORT=.*/EXPOSE_NGINX_SSL_PORT=8443/' .env
    fi
    
    cd "$dify_dir"
    
    # 检查是否已在运行
    if check_service "Dify" "$DIFY_PORT"; then
        print_info "Dify 已在运行，跳过启动"
        return 0
    fi
    
    # 启动 Dify
    print_info "正在启动 Dify 服务..."
    docker-compose up -d > "$LOG_DIR/dify.log" 2>&1
    
    sleep 10
    
    if check_service "Dify" "$DIFY_PORT"; then
        print_success "Dify 启动成功"
        return 0
    else
        print_error "Dify 启动失败，查看日志: $LOG_DIR/dify.log"
        return 1
    fi
}

# 启动 OpenClaw
start_openclaw() {
    echo ""
    print_info "3️⃣ 启动 OpenClaw 网关"
    
    # 检查 OpenClaw
    if ! check_command "openclaw"; then
        print_error "请先安装 OpenClaw: https://openclaw.io"
        return 1
    fi
    
    # 检查是否已在运行
    if check_service "OpenClaw" "$OPENCLAW_PORT"; then
        print_info "OpenClaw 已在运行，跳过启动"
        return 0
    fi
    
    # 启动 OpenClaw 网关
    print_info "正在启动 OpenClaw 网关..."
    openclaw gateway start > "$LOG_DIR/openclaw-gateway.log" 2>&1 &
    
    sleep 5
    
    if check_service "OpenClaw" "$OPENCLAW_PORT"; then
        print_success "OpenClaw 网关启动成功"
        
        # 配置 OpenClaw
        echo ""
        print_info "4️⃣ OpenClaw 自动监听 Obsidian 笔记"
        
        # 检查 Obsidian 路径
        if [ ! -d "$OBSIDIAN_PATH" ]; then
            print_warning "Obsidian 路径不存在: $OBSIDIAN_PATH"
            print_info "请修改脚本中的 OBSIDIAN_PATH 变量"
            return 1
        fi
        
        # 配置 OpenClaw
        openclaw config set tools.file.watchPaths "[\"$OBSIDIAN_PATH\"]"
        openclaw config set tools.file.autoIndex true
        
        # 重新索引知识库
        print_info "重新索引知识库..."
        openclaw knowledge reindex > "$LOG_DIR/openclaw-index.log" 2>&1 &
        
        print_success "OpenClaw 配置完成"
        return 0
    else
        print_error "OpenClaw 启动失败"
        return 1
    fi
}

# 显示最终状态
show_status() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} ✅ 全部启动完成！${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo "Dify 地址：http://localhost:$DIFY_PORT"
    echo "OpenClaw 网关：http://localhost:$OPENCLAW_PORT"
    echo "Ollama 地址：http://localhost:$OLLAMA_PORT"
    echo "Obsidian 监听目录：$OBSIDIAN_PATH"
    echo "日志目录：$LOG_DIR"
    echo ""
    echo -e "${GREEN}现在可以直接去 Dify 使用向量库 RAG 啦！${NC}"
    echo -e "${CYAN}=============================================${NC}"
    
    log "RAG 系统启动完成"
}

# 主函数
main() {
    print_header
    
    # 启动服务
    local success=true
    
    start_ollama || success=false
    start_dify || success=false
    start_openclaw || success=false
    
    if [ "$success" = true ]; then
        show_status
        exit 0
    else
        print_error "部分服务启动失败，请检查日志"
        exit 1
    fi
}

# 运行主函数
main

read -p "按回车退出..."