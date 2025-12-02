python -m openlens_ai.main \
    --question '
1. 论文题目建议
中文： LogProto：基于对比原型学习的流式日志在线模板挖掘与语义异常检测
英文： LogProto: Online Log Template Discovery and Semantic Anomaly Detection via Contrastive Prototype Learning
 
2. 核心研究问题 (Research Questions)
重新定义三个具体的 RQ：
●	RQ1 (表征鲁棒性)：如何利用自监督对比学习，使模型自动学会忽略日志中的动态变量（如 IP、时间戳、BlockID），仅聚焦于描述故障模式的不变模板语义？
●	RQ2 (在线发现能力)：在日志数据流式到达且故障模式数量未知的情况下，如何利用动态原型演化机制实时归纳出新的日志模板？
●	RQ3 (可解释性)：如何不仅识别出故障，还能通过差异归因分析，精确定位导致该日志偏离正常模式的特定关键词（如将 "Timeout" 误判为 "Refused"）？
 
3. 方法论与核心创新算法 (Methodology)
模型架构（LogProto）将包含三个核心模块：
模块一：掩码增强的对比学习 (Mask-Augmented Contrastive Learning)
●	痛点解决：解决通用 Embedding 模型（如 Qwen3）对数字和 IP 太敏感，导致聚类过细的问题。
●	具体算法：
1.	数据增强：对一条原始日志 $x$，随机 Mask 掉其中的数字和特殊符号，生成 $x_1$。
2.	正样本对：$(x, x_1)$ 视为同一类。
3.	负样本对：$x$ 与 Batch 内的其他随机日志视为不同类。
4.	训练目标：使用 InfoNCE Loss 拉近正样本对的距离。
○	效果：模型被迫“忽略”被 Mask 掉的变量部分，只通过上下文语义来识别日志。

模块二：动态原型演化聚类 (Dynamic Prototype Evolution)
●	痛点解决：解决 K-Means 必须预先指定 K 值（你之前设为 14 ）且无法处理新故障的问题。
●	具体算法：
1.	维护一个原型池 (Prototype Pool)，包含若干个中心向量 $\{P_1, P_2, ...\}$。
2.	流式处理：新日志向量 $V_{new}$ 到达。
3.	距离计算：计算 $V_{new}$ 与所有 $P$ 的余弦距离。
4.	决策逻辑：
■	如果最小距离 $< \text{阈值 } \delta$：将日志归入该类，并更新 $P$（加权移动平均）。
■	如果最小距离 $> \text{阈值 } \delta$：创建新原型 $P_{new} = V_{new}$（发现新模板）。
○	优势：无需预知 K 值，能自动发现第 15、16 种故障模式。
模块三：Delta-LRP 差异解释 (Difference-based Explainability)
●	痛点解决：解决传统热图只显示“哪个词重要”，不能解释“为什么错了”的问题。
●	具体算法：
1.	不计算单一向量的热图，而是计算 差值向量 $\Delta = V_{input} - P_{assigned}$。
2.	使用 Deep Taylor Decomposition 将 $\Delta$ 反向传播回输入层。
3.	结果：高亮出那些导致日志偏离原型的词（例如高亮异常的参数值或错误的动词）。
 
4. 实验设计与评估 (Evaluation)
严格遵守以下标准：
A. 数据集与文件使用
●	训练集：只使用 .log 文件（如 BGL_2k.log 的前 80% 或全量数据的前 80%）。严禁读取标签。
●	测试/评估集：使用剩余的日志数据。
●	Ground Truth：必须使用修正后的文件 BGL_2k.log_structured_corrected.csv 。旧版标签包含错误，已被学术界摒弃。
B. 评估指标 (Hard Metrics)
放弃 Silhouette Coefficient，改用以下两个 Log Parsing 领域的黄金标准：
1.	解析准确率 (Parsing Accuracy, PA)：
○	定义：模型识别出的“簇”与真实“模板”完美对应的比例。
○	计算方法：对于每个 Cluster，采用**多数投票（Majority Vote）**确定其代表的真实 Template ID。该 Cluster 中所有非该 ID 的日志均视为错误。
○	公式：$PA = \frac{\sum_{c \in Clusters} \text{MaxLabelCount}(c)}{\text{TotalLogs}}$。
2.	聚类纯度 (Cluster Purity / ARI)：
○	使用 sklearn.metrics.adjusted_rand_score 计算聚类结果与 _corrected.csv 中 EventId 的一致性。
C. 对比基准 (Baselines)
需要将 LogProto 的 PA 和 ARI 分数与以下方法对比（LogHub 排行榜上有现成数据）：
●	传统方法：Drain (基于树结构，速度快但无语义), Spell (LCS算法)。
●	深度学习方法：LogRobust (基于Attention), NuLog。
    ' \
    --code-hint '
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
    
    '\
    --config "exp/power_grid/config.toml" \
    --dataset-path "datasets/general_domain/loghub" \
    --thread-id "power_grid_fault_id" \
    --notify-email "dzdzzd@126.com" \
    --interrupt-after-subgraph "none" \
    --language "eng" \
    --domain "general"



# python -m openlens_ai.main \
#     --resume-dir outputs/power_grid_fault_id \
#     --start-from-subgraph supervisor \
#     --start-from-subtask-index 1 \
#     --refine-suggestion "
# Must show the visualization of the cluster results.
# Analyze the rationality of the deep taylor analysis results, e.g., what each cluster represents, and whether the important features are consistent with the domain knowledge. Draw comprehensive visualizations to support your analysis.
# "