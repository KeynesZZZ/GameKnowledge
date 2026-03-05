# Mac 专用 Ollama + Dify + OpenClaw + 向量库 RAG 一键启动系统

## 🎯 系统概述

这是一个专为 Mac 用户设计的完整本地知识库系统，实现了：

- ✅ **一键启动**: 双击即可启动完整的 RAG 系统
- ✅ **自动同步**: Obsidian 笔记自动同步到向量库
- ✅ **本地部署**: 完全本地化，保护隐私
- ✅ **向量检索**: 基于 bge-m3 的高质量向量检索
- ✅ **可视化界面**: 通过 Dify 提供友好的 Web 界面

## 📋 系统架构

```
Obsidian 笔记 → OpenClaw 监听 → 向量库存储 → Dify RAG → 智能回答
     ↓              ↓           ↓           ↓          ↓
Markdown文件 → 自动索引 → bge-m3向量 → 智能检索 → 生成回答
```

## 🚀 快速开始

### 1. 环境要求

- **操作系统**: macOS 10.15 或更高版本
- **内存**: 建议 16GB 或更高
- **存储**: 建议 10GB 可用空间
- **网络**: 首次安装需要网络连接

### 2. 安装依赖

#### 安装 Ollama
```bash
# 一键安装命令
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 安装 Docker Desktop
1. 访问 [Docker 官网](https://www.docker.com/products/docker-desktop/)
2. 下载并安装 Docker Desktop for Mac
3. 启动 Docker Desktop

#### 安装 OpenClaw
```bash
# 使用 Homebrew 安装
brew install openclaw

# 或者从源码安装
git clone https://github.com/openclaw/openclaw.git
cd openclaw
make install
```

### 3. 下载脚本

将以下文件保存到您的桌面：

1. `start-rag.sh` - 启动脚本
2. `stop-rag.sh` - 停止脚本
3. `status-rag.sh` - 状态检查脚本

### 4. 配置 Obsidian 路径

编辑 `start-rag.sh` 文件，修改以下配置：

```bash
# ======================== 用户配置区域 ========================
# 请修改为你的 Obsidian 笔记库路径
OBSIDIAN_PATH="/Users/$(whoami)/Documents/Obsidian笔记库"
# 或者使用现有的 UnityKnowledge 路径
# OBSIDIAN_PATH="/Users/$(whoami)/git/Doc/UnityKnowledge"
# ==========================================================
```

### 5. 设置执行权限

打开终端，执行以下命令：

```bash
chmod +x ~/Desktop/start-rag.sh
chmod +x ~/Desktop/stop-rag.sh
chmod +x ~/Desktop/status-rag.sh
```

### 6. 一键启动

双击桌面的 `start-rag.sh` 文件，系统将自动：

1. 启动 Ollama 服务
2. 下载并启动 Dify Docker 容器
3. 启动 OpenClaw 网关
4. 配置 Obsidian 文件监听
5. 自动索引知识库

### 7. 访问系统

启动完成后，您可以访问：

- **Dify 界面**: http://localhost:8000
- **OpenClaw 网关**: http://localhost:18789
- **Ollama API**: http://localhost:11434

## 📖 使用指南

### 启动系统

1. 双击 `start-rag.sh`
2. 等待系统启动完成（约 2-3 分钟）
3. 看到 "✅ 全部启动完成！" 提示

### 使用 Dify

1. 打开浏览器访问 http://localhost:8000
2. 创建管理员账户
3. 配置知识库应用
4. 上传文档或连接 Obsidian 知识库
5. 开始智能问答

### 监控状态

运行状态检查脚本：

```bash
# 快速检查
./status-rag.sh -q

# 详细检查
./status-rag.sh -d

# 健康报告
./status-rag.sh -r
```

### 停止系统

1. 双击 `stop-rag.sh`
2. 系统将优雅关闭所有服务
3. 可选：使用 `-f` 参数强制停止

## ⚙️ 配置优化

### Dify RAG 配置

参考 `dify-rag-config.md` 文件中的详细配置：

- **向量检索**: Top-K=8, 相似度阈值=0.7
- **文本分块**: 大小=1000, 重叠=200
- **混合检索**: 向量权重=0.7, 关键词权重=0.3

### OpenClaw 配置

参考 `openclaw-config.yaml` 文件：

- **文件监听**: 自动检测 Markdown 文件变化
- **向量模型**: 使用 bge-m3 模型
- **索引策略**: 增量更新，实时同步

## 🔧 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
lsof -i :11434  # Ollama
lsof -i :8000   # Dify
lsof -i :18789  # OpenClaw
```

#### 2. 服务启动失败
```bash
# 查看日志
tail -f ~/.rag-system/logs/start-rag.log
```

#### 3. Docker 问题
```bash
# 重启 Docker
docker-compose down
docker-compose up -d
```

#### 4. 权限问题
```bash
# 修复权限
sudo chmod +x *.sh
```

### 性能优化

#### 1. 内存优化
- 减少 Dify 容器内存限制
- 调整 Ollama 批处理大小
- 优化向量检索参数

#### 2. 速度优化
- 启用缓存机制
- 调整分块大小
- 使用更快的模型

#### 3. 准确性优化
- 调整相似度阈值
- 优化提示词模板
- 使用重排序模型

## 📊 系统监控

### 查看日志

```bash
# 启动日志
tail -f ~/.rag-system/logs/start-rag.log

# 停止日志
tail -f ~/.rag-system/logs/stop-rag.log

# 状态检查日志
tail -f ~/.rag-system/logs/status-rag.log

# 各服务日志
tail -f ~/.rag-system/logs/ollama.log
tail -f ~/.rag-system/logs/dify.log
tail -f ~/.rag-system/logs/openclaw-gateway.log
```

### 性能指标

```bash
# 系统资源监控
./status-rag.sh -d

# 查看 Docker 状态
docker stats

# 查看 Ollama 模型
ollama list
ollama ps
```

## 🔐 安全建议

### 1. 网络安全
- 仅在本地网络使用
- 配置防火墙规则
- 定期更新软件

### 2. 数据安全
- 定期备份知识库
- 加密敏感文档
- 监控访问日志

### 3. 系统安全
- 保持系统更新
- 使用强密码
- 定期安全扫描

## 🚀 高级功能

### 1. 多知识库支持
编辑配置文件支持多个 Obsidian 库：

```bash
# 在 start-rag.sh 中添加多个路径
OBSIDIAN_PATHS=(
    "/path/to/knowledge1"
    "/path/to/knowledge2"
    "/path/to/knowledge3"
)
```

### 2. 自定义模型
支持其他向量模型：

```bash
# 下载其他模型
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
```

### 3. 插件扩展
通过 OpenClaw 插件系统扩展功能：

- 文档解析器
- 数据处理器
- 自定义检索器

## 📚 相关资源

### 官方文档
- [Ollama 文档](https://ollama.ai/docs)
- [Dify 文档](https://docs.dify.ai/)
- [OpenClaw 文档](https://openclaw.io/docs)

### 模型资源
- [bge-m3 模型](https://huggingface.co/BAAI/bge-m3)
- [向量模型对比](https://huggingface.co/spaces/mteb/leaderboard)

### 社区支持
- [GitHub Issues](https://github.com/your-repo/issues)
- [技术论坛](https://forum.your-domain.com)
- [Discord 社区](https://discord.gg/your-invite)

## 📞 技术支持

如遇到问题，请按以下步骤操作：

1. **查看日志**: 检查 `~/.rag-system/logs/` 目录下的日志文件
2. **状态检查**: 运行 `./status-rag.sh -d` 获取详细状态
3. **搜索文档**: 查看本 README 的故障排除部分
4. **提交问题**: 在 GitHub 提交详细的问题报告

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🙏 致谢

感谢以下开源项目的支持：

- [Ollama](https://ollama.ai/) - 本地大模型运行框架
- [Dify](https://dify.ai/) - LLM 应用开发平台
- [OpenClaw](https://openclaw.io/) - 知识库管理工具
- [bge-m3](https://huggingface.co/BAAI/bge-m3) - 多语言向量模型

---

**享受您的本地 RAG 知识库系统！** 🎉

如有问题或建议，欢迎提交 Issue 或 Pull Request。