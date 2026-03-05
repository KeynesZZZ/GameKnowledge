# 🚀 Mac RAG 系统 - 5分钟快速上手指南

## 第一步：一键安装（2分钟）

### 自动安装（推荐）
```bash
# 下载安装脚本
curl -O https://raw.githubusercontent.com/your-repo/mac-rag-system/main/install-rag-system.sh

# 运行安装
chmod +x install-rag-system.sh
./install-rag-system.sh
```

### 手动安装（备选）
1. **安装 Ollama**: https://ollama.ai
2. **安装 Docker Desktop**: https://docker.com
3. **安装 OpenClaw**: `brew install openclaw`

## 第二步：配置 Obsidian 路径（1分钟）

编辑桌面上的 `start-rag.sh`，修改这一行：
```bash
OBSIDIAN_PATH="/Users/你的用户名/Documents/Obsidian笔记库"
```

## 第三步：一键启动（1分钟）

双击桌面上的 `start-rag.sh`，看到：
```
✅ 全部启动完成！
Dify 地址：http://localhost:8000
OpenClaw 网关：http://localhost:18789
Ollama 地址：http://localhost:11434
```

## 第四步：使用 Dify（1分钟）

1. 打开浏览器访问：http://localhost:8000
2. 点击"创建应用" → "从模板创建"
3. 选择"知识库问答"模板
4. 上传文档或连接 Obsidian 知识库
5. 开始智能问答！

## 🎯 常用操作

### 检查系统状态
```bash
# 快速检查
./status-rag.sh -q

# 详细检查
./status-rag.sh -d
```

### 停止系统
```bash
# 正常停止
./stop-rag.sh

# 强制停止
./stop-rag.sh -f
```

### 查看日志
```bash
# 启动日志
tail -f ~/.rag-system/logs/start-rag.log

# 服务状态
tail -f ~/.rag-system/logs/status-rag.log
```

## 📋 故障速查

| 问题 | 解决方案 |
|------|----------|
| 端口被占用 | 检查端口：`lsof -i :8000` |
| Docker 未启动 | 打开 Docker Desktop |
| Ollama 连接失败 | 重启 Ollama：`ollama serve` |
| 文档未同步 | 检查 Obsidian 路径配置 |
| 回答不准确 | 调整 Top-K=8, 阈值=0.7 |

## 🔧 最优配置（直接复制使用）

### Dify 配置
```yaml
# 检索设置
top_k: 8
score_threshold: 0.7

# 分块设置
chunk_size: 1000
chunk_overlap: 200

# 模型设置
embedding: bge-m3
temperature: 0.7
```

### OpenClaw 配置
```yaml
# 监听配置
watchPaths: ["/Users/你的用户名/Documents/Obsidian笔记库"]
autoIndex: true
indexInterval: 300

# 向量配置
vector_size: 1024
distance: "Cosine"
```

## 🎉 完成！

现在您可以：
- ✅ 在 Obsidian 中写笔记
- ✅ 自动同步到向量库
- ✅ 通过 Dify 智能问答
- ✅ 完全本地化部署

**享受您的个人知识库助手！** 🚀

---

## 📞 需要帮助？

1. **查看日志**: `~/.rag-system/logs/`
2. **状态检查**: `./status-rag.sh -d`
3. **重新启动**: `./stop-rag.sh && ./start-rag.sh`
4. **社区支持**: 提交 Issue 获取帮助