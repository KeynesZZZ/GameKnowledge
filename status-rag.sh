#!/bin/bash

# Mac 专用 RAG 系统状态检查脚本
# 作者: RAG 系统自动化脚本
# 版本: 1.0

# 颜色输出配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 服务配置
OLLAMA_PORT="11434"
DIFY_PORT="8000"
OPENCLAW_PORT="18789"

# 日志目录
LOG_DIR="$HOME/.rag-system/logs"
STATUS_LOG="$LOG_DIR/status-rag.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$STATUS_LOG"
}

# 带颜色的输出函数
print_header() {
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} 📊 RAG 系统状态检查${NC}"
    echo -e "${CYAN}=============================================${NC}"
    log "开始检查 RAG 系统状态..."
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

print_metric() {
    echo -e "${PURPLE}📈 $1${NC}"
    log "指标: $1"
}

# 检查服务状态
check_service_status() {
    local service=$1
    local port=$2
    local url=$3
    
    echo ""
    print_info "检查 $service 服务状态..."
    
    # 检查端口
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_success "$service 服务正在运行 (端口: $port)"
        
        # 检查 HTTP 响应
        if [ -n "$url" ]; then
            local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
            if [ "$response" = "200" ] || [ "$response" = "000" ]; then
                print_success "$service HTTP 服务正常 (响应码: $response)"
            else
                print_warning "$service HTTP 服务异常 (响应码: $response)"
            fi
        fi
        
        # 获取进程信息
        local pid=$(lsof -ti :$port 2>/dev/null | head -1)
        if [ -n "$pid" ]; then
            local cpu=$(ps -p $pid -o %cpu= 2>/dev/null | tr -d ' ')
            local mem=$(ps -p $pid -o %mem= 2>/dev/null | tr -d ' ')
            local start_time=$(ps -p $pid -o lstart= 2>/dev/null)
            
            print_metric "$service 进程信息:"
            echo "  PID: $pid"
            echo "  CPU 使用率: ${cpu}%"
            echo "  内存使用率: ${mem}%"
            echo "  启动时间: $start_time"
        fi
        
        return 0
    else
        print_error "$service 服务未运行 (端口: $port)"
        return 1
    fi
}

# 检查 Ollama 详细状态
check_ollama_details() {
    echo ""
    print_info "检查 Ollama 详细信息..."
    
    # 检查 Ollama 命令
    if command -v ollama >/dev/null 2>&1; then
        print_success "Ollama 命令可用"
        
        # 检查模型列表
        if ollama list >/dev/null 2>&1; then
            echo ""
            print_info "已安装的模型:"
            ollama list 2>/dev/null | while read -r line; do
                echo "  $line"
            done
        else
            print_warning "无法获取模型列表"
        fi
        
        # 检查运行状态
        if ollama ps >/dev/null 2>&1; then
            local running_models=$(ollama ps 2>/dev/null | wc -l)
            if [ "$running_models" -gt 1 ]; then
                print_info "当前运行的模型数量: $((running_models - 1))"
                ollama ps 2>/dev/null | tail -n +2 | while read -r line; do
                    echo "  $line"
                done
            else
                print_info "当前没有模型在运行"
            fi
        fi
    else
        print_error "Ollama 命令未找到"
    fi
}

# 检查 Docker 状态
check_docker_status() {
    echo ""
    print_info "检查 Docker 服务状态..."
    
    if command -v docker >/dev/null 2>&1; then
        print_success "Docker 命令可用"
        
        # 检查 Docker 服务
        if docker info >/dev/null 2>&1; then
            print_success "Docker 服务正在运行"
            
            # 检查 Dify 容器
            local dify_containers=$(docker ps --filter "name=dify" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
            if [ -n "$dify_containers" ]; then
                echo ""
                print_info "Dify 相关容器:"
                echo "$dify_containers" | tail -n +2 | while read -r line; do
                    echo "  $line"
                done
            else
                print_info "未找到 Dify 容器"
            fi
            
            # 检查系统资源
            local docker_stats=$(docker system df 2>/dev/null | grep -E "(Images|Containers|Local Volumes)" | head -3)
            if [ -n "$docker_stats" ]; then
                echo ""
                print_metric "Docker 资源使用情况:"
                echo "$docker_stats" | while read -r line; do
                    echo "  $line"
                done
            fi
            
        else
            print_error "Docker 服务未运行"
        fi
    else
        print_error "Docker 命令未找到"
    fi
}

# 检查 OpenClaw 配置
check_openclaw_config() {
    echo ""
    print_info "检查 OpenClaw 配置..."
    
    if command -v openclaw >/dev/null 2>&1; then
        print_success "OpenClaw 命令可用"
        
        # 检查配置文件
        local config_file="$HOME/.openclaw/config.yaml"
        if [ -f "$config_file" ]; then
            print_success "找到 OpenClaw 配置文件"
            
            # 检查监听路径
            local watch_paths=$(grep -A 5 "watchPaths" "$config_file" 2>/dev/null | grep -v "^--" | head -5)
            if [ -n "$watch_paths" ]; then
                echo ""
                print_info "监听的文件路径:"
                echo "$watch_paths" | while read -r line; do
                    echo "  $line"
                done
            fi
            
            # 检查自动索引设置
            local auto_index=$(grep "autoIndex" "$config_file" 2>/dev/null)
            if [ -n "$auto_index" ]; then
                echo ""
                print_info "自动索引配置:"
                echo "  $auto_index"
            fi
        else
            print_warning "未找到 OpenClaw 配置文件"
        fi
        
    else
        print_error "OpenClaw 命令未找到"
    fi
}

# 检查系统资源
check_system_resources() {
    echo ""
    print_info "检查系统资源使用情况..."
    
    # CPU 使用率
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    if [ -n "$cpu_usage" ]; then
        print_metric "CPU 使用率: ${cpu_usage}%"
    fi
    
    # 内存使用情况
    local memory_info=$(vm_stat | grep -E "(free|inactive|active|wired)")
    if [ -n "$memory_info" ]; then
        print_metric "内存状态:"
        echo "$memory_info" | while read -r line; do
            echo "  $line"
        done
    fi
    
    # 磁盘使用情况
    local disk_usage=$(df -h / | tail -1 | awk '{print "已用: " $3 "/" $2 " (" $5 ")"}')
    if [ -n "$disk_usage" ]; then
        print_metric "磁盘使用情况: $disk_usage"
    fi
}

# 检查网络连接
check_network_connectivity() {
    echo ""
    print_info "检查网络连接状态..."
    
    # 检查本地网络
    if ping -c 1 127.0.0.1 >/dev/null 2>&1; then
        print_success "本地网络连接正常"
    else
        print_error "本地网络连接异常"
    fi
    
    # 检查各服务端口
    local services=("Ollama:$OLLAMA_PORT" "Dify:$DIFY_PORT" "OpenClaw:$OPENCLAW_PORT")
    
    for service in "${services[@]}"; do
        local name=$(echo "$service" | cut -d':' -f1)
        local port=$(echo "$service" | cut -d':' -f2)
        
        if nc -z 127.0.0.1 $port 2>/dev/null; then
            print_success "$name 端口 $port 可访问"
        else
            print_warning "$name 端口 $port 无法访问"
        fi
    done
}

# 显示健康报告
show_health_report() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN} 📋 RAG 系统健康报告${NC}"
    echo -e "${CYAN}=============================================${NC}"
    
    local total_checks=0
    local passed_checks=0
    
    # 统计检查结果
    local services_status=0
    check_service_status "Ollama" "$OLLAMA_PORT" "http://localhost:$OLLAMA_PORT/api/tags" >/dev/null && services_status=$((services_status + 1))
    total_checks=$((total_checks + 1))
    
    check_service_status "Dify" "$DIFY_PORT" "http://localhost:$DIFY_PORT" >/dev/null && services_status=$((services_status + 1))
    total_checks=$((total_checks + 1))
    
    check_service_status "OpenClaw" "$OPENCLAW_PORT" "http://localhost:$OPENCLAW_PORT" >/dev/null && services_status=$((services_status + 1))
    total_checks=$((total_checks + 1))
    
    # 显示健康状态
    if [ "$services_status" -eq 3 ]; then
        print_success "🟢 系统状态: 健康 (所有服务运行正常)"
    elif [ "$services_status" -ge 1 ]; then
        print_warning "🟡 系统状态: 部分服务异常 ($services_status/3 服务运行中)"
    else
        print_error "🔴 系统状态: 严重 (所有服务均未运行)"
    fi
    
    echo ""
    print_metric "服务状态统计:"
    echo "  运行中的服务: $services_status/3"
    echo "  总检查项目: $total_checks"
    echo "  通过检查: $passed_checks"
    
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${GREEN}状态检查完成！${NC}"
    echo -e "${CYAN}=============================================${NC}"
    
    log "状态检查完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项："
    echo "  -h, --help     显示帮助信息"
    echo "  -q, --quick    快速检查（仅检查服务状态）"
    echo "  -d, --detailed 详细检查（包含配置和资源）"
    echo "  -r, --report   显示健康报告"
    echo ""
    echo "示例："
    echo "  $0              # 标准检查"
    echo "  $0 -q           # 快速检查"
    echo "  $0 -d           # 详细检查"
    echo "  $0 -r           # 健康报告"
}

# 快速检查模式
quick_check() {
    print_header
    
    check_service_status "Ollama" "$OLLAMA_PORT" "http://localhost:$OLLAMA_PORT/api/tags"
    check_service_status "Dify" "$DIFY_PORT" "http://localhost:$DIFY_PORT"
    check_service_status "OpenClaw" "$OPENCLAW_PORT" "http://localhost:$OPENCLAW_PORT"
    
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${GREEN}快速检查完成！${NC}"
    echo -e "${CYAN}=============================================${NC}"
}

# 详细检查模式
detailed_check() {
    print_header
    
    # 基础服务检查
    check_service_status "Ollama" "$OLLAMA_PORT" "http://localhost:$OLLAMA_PORT/api/tags"
    check_ollama_details
    
    check_service_status "Dify" "$DIFY_PORT" "http://localhost:$DIFY_PORT"
    check_docker_status
    
    check_service_status "OpenClaw" "$OPENCLAW_PORT" "http://localhost:$OPENCLAW_PORT"
    check_openclaw_config
    
    # 系统和网络检查
    check_system_resources
    check_network_connectivity
    
    # 健康报告
    show_health_report
}

# 主函数
main() {
    # 解析命令行参数
    local mode="standard"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -q|--quick)
                mode="quick"
                shift
                ;;
            -d|--detailed)
                mode="detailed"
                shift
                ;;
            -r|--report)
                mode="report"
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    case $mode in
        quick)
            quick_check
            ;;
        detailed)
            detailed_check
            ;;
        report)
            show_health_report
            ;;
        standard)
            detailed_check
            ;;
    esac
}

# 运行主函数
main "$@"