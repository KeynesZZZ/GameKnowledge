# Dify RAG 配置优化指南

## 概述
本文档提供 Dify 平台的最优 RAG（检索增强生成）配置参数，确保回答精度和检索效果达到最佳状态。

## 核心配置参数

### 1. 向量检索参数
```yaml
# 检索设置
retrieval:
  top_k: 8                    # 检索文档数量 (推荐: 6-10)
  score_threshold: 0.7        # 相似度阈值 (推荐: 0.6-0.8)
  rerank_model: "bge-reranker-base"  # 重排序模型
  rerank_top_k: 4           # 重排序后保留数量

# 混合检索
hybrid_search:
  enable: true              # 启用混合检索
  keyword_weight: 0.3       # 关键词检索权重
  vector_weight: 0.7        # 向量检索权重
  
# 多路召回
multi_retrieval:
  enable: true
  methods:
    - vector                 # 向量检索
    - keyword               # 关键词检索
    - semantic              # 语义检索
```

### 2. 文本分块策略
```yaml
# 分块设置
chunking:
  strategy: "recursive"      # 分块策略: recursive, sliding_window, fixed
  chunk_size: 1000          # 分块大小 (推荐: 800-1200)
  chunk_overlap: 200        # 重叠大小 (推荐: 150-300)
  separators: ["\n\n", "\n", "。", "！", "？"]  # 分隔符
  
# 预处理
preprocessing:
  remove_extra_spaces: true  # 移除多余空格
  remove_urls: true          # 移除URL
  remove_emails: true        # 移除邮箱
  normalize_unicode: true    # 标准化Unicode
```

### 3. 提示词模板优化
```yaml
# 系统提示词
system_prompt: |
  你是一个专业的知识助手，基于提供的上下文信息回答问题。
  请确保回答准确、相关，并在不确定时明确说明。

# 用户提示词模板
user_prompt_template: |
  基于以下上下文信息回答问题：
  
  {context}
  
  问题：{question}
  
  回答要求：
  1. 只使用提供的上下文信息
  2. 如果信息不足，请明确说明
  3. 保持回答简洁准确
  4. 在回答末尾标注信息来源

# 重排序提示词
rerank_prompt: |
  请重新排序以下文档，使其与问题最相关：
  
  问题：{question}
  文档列表：{documents}
```

## 模型配置优化

### 1. 向量模型配置
```yaml
# 向量模型
embedding_model:
  name: "bge-m3"                    # 向量模型名称
  dimension: 1024                   # 向量维度
  max_length: 8192                  # 最大输入长度
  batch_size: 32                    # 批处理大小
  normalize: true                     # 向量归一化
  
# 重排序模型
rerank_model:
  name: "bge-reranker-base"         # 重排序模型
  max_length: 512                   # 最大输入长度
  batch_size: 16                    # 批处理大小
```

### 2. 生成模型配置
```yaml
# 生成模型
generation_model:
  name: "llama2:13b"                # 生成模型名称
  temperature: 0.7                  # 温度参数 (推荐: 0.5-0.8)
  top_p: 0.9                        # Top-p 采样 (推荐: 0.8-0.95)
  max_tokens: 2048                  # 最大生成长度
  presence_penalty: 0.1              # 存在惩罚 (推荐: 0-0.3)
  frequency_penalty: 0.1           # 频率惩罚 (推荐: 0-0.3)
```

## 高级优化策略

### 1. 多阶段检索
```yaml
# 多阶段检索
multi_stage_retrieval:
  enable: true
  stages:
    - name: "coarse"                # 粗检索
      top_k: 20
      threshold: 0.5
    - name: "fine"                  # 精检索
      top_k: 10
      threshold: 0.7
    - name: "rerank"                # 重排序
      top_k: 5
      threshold: 0.8
```

### 2. 查询优化
```yaml
# 查询优化
query_optimization:
  enable: true
  expansion:
    enable: true                    # 查询扩展
    synonyms: true                  # 同义词扩展
    hyponyms: true                  # 下位词扩展
    hypernyms: true                # 上位词扩展
  
  rewriting:
    enable: true                    # 查询重写
    remove_stopwords: true          # 移除停用词
    stemming: true                  # 词干提取
    lemmatization: true            # 词形还原
```

### 3. 上下文优化
```yaml
# 上下文优化
context_optimization:
  enable: true
  max_context_length: 4000          # 最大上下文长度
  context_selection:
    strategy: "relevance"           # 选择策略: relevance, diversity, recency
    diversity_weight: 0.3           # 多样性权重
    recency_weight: 0.2             # 时效性权重
  
  context_compression:
    enable: true                    # 上下文压缩
    compression_ratio: 0.8          # 压缩比例
    preserve_key_info: true         # 保留关键信息
```

## 性能优化配置

### 1. 缓存策略
```yaml
# 缓存配置
cache:
  enable: true                      # 启用缓存
  type: "redis"                     # 缓存类型
  ttl: 3600                        # 缓存时间 (秒)
  max_size: 1000                   # 最大缓存数量
  
# 向量缓存
vector_cache:
  enable: true
  ttl: 7200                        # 向量缓存时间
  max_size: 5000                   # 最大向量缓存数
```

### 2. 并发优化
```yaml
# 并发设置
concurrency:
  max_workers: 8                    # 最大工作线程数
  max_connections: 100              # 最大连接数
  timeout: 30                       # 超时时间 (秒)
  retry_attempts: 3                 # 重试次数
  
# 批处理
batch_processing:
  enable: true                      # 启用批处理
  batch_size: 32                    # 批处理大小
  max_wait_time: 5                  # 最大等待时间 (秒)
```

## 质量评估指标

### 1. 检索质量指标
```yaml
# 检索评估
retrieval_metrics:
  precision_at_k: 5                 # P@K 评估
  recall_at_k: 5                    # R@K 评估
  mean_reciprocal_rank: true        # MRR 评估
  normalized_discounted_cumulative_gain: true  # NDCG 评估
  
# 相关性评估
relevance_metrics:
  exact_match: true                 # 精确匹配
  semantic_similarity: true         # 语义相似度
  answer_correctness: true          # 答案正确性
```

### 2. 生成质量指标
```yaml
# 生成评估
generation_metrics:
  bleu_score: true                  # BLEU 分数
  rouge_score: true                 # ROUGE 分数
  bert_score: true                  # BERTScore
  perplexity: true                  # 困惑度
  
# 人工评估
human_evaluation:
  relevance: 5                       # 相关性评分 (1-5)
  accuracy: 5                        # 准确性评分 (1-5)
  completeness: 5                    # 完整性评分 (1-5)
  fluency: 5                         # 流畅性评分 (1-5)
```

## 故障排除指南

### 1. 检索效果差
**问题**: 检索到的文档不相关
**解决方案**:
- 降低 `score_threshold` 到 0.5-0.6
- 增加 `top_k` 到 10-15
- 启用混合检索 (`hybrid_search.enable: true`)
- 检查向量模型是否合适

### 2. 回答不准确
**问题**: 生成的回答不准确或不相关
**解决方案**:
- 调整 `temperature` 到 0.3-0.5
- 优化提示词模板
- 增加上下文相关性检查
- 启用查询优化

### 3. 响应速度慢
**问题**: 系统响应时间过长
**解决方案**:
- 启用缓存机制
- 优化批处理大小
- 减少 `top_k` 值
- 使用更快的模型

### 4. 内存使用过高
**问题**: 系统内存占用过高
**解决方案**:
- 减少批处理大小
- 启用向量压缩
- 限制缓存大小
- 优化分块策略

## 最佳实践建议

### 1. 模型选择
- **向量模型**: 推荐使用 `bge-m3` 或 `text-embedding-ada-002`
- **重排序模型**: 推荐使用 `bge-reranker-base`
- **生成模型**: 根据需求选择 `llama2:13b` 或 `gpt-3.5-turbo`

### 2. 参数调优顺序
1. 首先调整检索参数 (`top_k`, `score_threshold`)
2. 然后优化分块策略 (`chunk_size`, `chunk_overlap`)
3. 最后调整生成参数 (`temperature`, `top_p`)

### 3. 监控指标
- 检索准确率 (Precision@K, Recall@K)
- 生成质量 (BLEU, ROUGE, 人工评分)
- 系统性能 (响应时间, 吞吐量)
- 资源使用 (CPU, 内存, 磁盘)

### 4. 持续优化
- 定期收集用户反馈
- 监控关键性能指标
- A/B 测试不同配置
- 迭代优化参数设置

## 配置文件示例

### Dify 环境变量配置
```bash
# Dify 环境变量
DIFY_RAG_TOP_K=8
DIFY_RAG_SCORE_THRESHOLD=0.7
DIFY_RAG_CHUNK_SIZE=1000
DIFY_RAG_CHUNK_OVERLAP=200
DIFY_RAG_TEMPERATURE=0.7
DIFY_RAG_MAX_TOKENS=2048

# 模型配置
DIFY_EMBEDDING_MODEL=bge-m3
DIFY_RERANK_MODEL=bge-reranker-base
DIFY_GENERATION_MODEL=llama2:13b
```

### Docker Compose 配置
```yaml
version: '3.8'
services:
  dify:
    environment:
      - RAG_TOP_K=8
      - RAG_SCORE_THRESHOLD=0.7
      - RAG_CHUNK_SIZE=1000
      - RAG_CHUNK_OVERLAP=200
      - RAG_TEMPERATURE=0.7
      - RAG_MAX_TOKENS=2048
      - EMBEDDING_MODEL=bge-m3
      - RERANK_MODEL=bge-reranker-base
    volumes:
      - ./config/rag.yaml:/app/config/rag.yaml
      - ./logs:/app/logs
```

## 总结

通过合理配置这些参数，可以显著提升 RAG 系统的性能和质量。建议根据具体应用场景和数据特点进行针对性调优，并持续监控和优化系统表现。