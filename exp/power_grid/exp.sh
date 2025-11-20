python -m openlens_ai.main \
    --question '
研究主题
主题：基于深度学习的运维日志精准解析，故障模式自动归纳及Deep Taylor可解释分析

核心研究问题
RQ：如何利用深度学习模型，将海量、非结构化的运维日志（如Kubernetes事件、微服务错误日志），自动、精准地分类归纳为少数几种可理解的故障模式？并对模型预测做出可解释分析。

问题背景： 运维人员每天面对成千上万条日志，虽然已有日志聚合工具，但它们大多只做关键词匹配和简单统计，无法理解日志背后的语义，从而自动归纳出“这100条不同的日志，其实都在描述同一个底层故障（例如‘服务发现失败’）”。

核心创新点
创新点一：无需标注数据，实现日志的“语义聚类”

传统方法： 依赖人工预先定义规则或标记大量数据来训练分类器，费时费力，且无法适应新出现的日志类型。

创新做法：
直接采集原始日志数据。
使用文本嵌入模型，将每条日志转换为一个高维的语义向量。
对这些向量进行聚类分析（如使用K-means），自动发现日志中隐藏的、语义相似的“模式群组”。
使用Deep Taylor算法，计算输入日志对输出结果的重要性热图，对模型分类预测进行可解释分析。

优势： 完全无监督，无需任何人工标注，结果可解释。

建议使用Qwen3-Embedding-0.6B作为文本嵌入模型，通过modelscope download --model Qwen/Qwen3-Embedding-0.6B --cache_dir /workspace下载

使用方式如下

# Requires transformers>=4.51.0
# Requires sentence-transformers>=2.7.0

from sentence_transformers import SentenceTransformer

# Load the model
model = SentenceTransformer("/workspace/Qwen/Qwen3-Embedding-0___6B")

# We recommend enabling flash_attention_2 for better acceleration and memory saving,
# together with setting `padding_side` to "left":
# model = SentenceTransformer(
#     "Qwen/Qwen3-Embedding-0.6B",
#     model_kwargs={"attn_implementation": "flash_attention_2", "device_map": "auto"},
#     tokenizer_kwargs={"padding_side": "left"},
# )

# The queries and documents to embed
queries = [
    "What is the capital of China?",
    "Explain gravity",
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

# Encode the queries and documents. Note that queries benefit from using a prompt
# Here we use the prompt called "query" stored under `model.prompts`, but you can
# also pass your own prompt via the `prompt` argument
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

# Compute the (cosine) similarity between the query and document embeddings
similarity = model.similarity(query_embeddings, document_embeddings)
print(similarity)
# tensor([[0.7646, 0.1414],
#         [0.1355, 0.6000]])
    
    ' \
    --config "exp/power_grid/config.toml" \
    --dataset-path "datasets/general_domain/loghub" \
    --thread-id "power_grid_fault_id" \
    --notify-email "dzdzzd@126.com" \
    --interrupt-after "none" \
    --language "eng" \
    --domain "general"
