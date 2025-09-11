# OpenLens AI Agents 架构详解

## 1. 系统架构概述

OpenLens AI 系统由五个核心代理组成：

1. **监督者代理 (Supervisor Agent)** - 负责整体任务规划和协调
2. **文献审阅代理 (Literature Reviewer Agent)** - 执行文献搜索和综述生成
3. **数据分析代理 (Data Analyzer Agent)** - 处理数据并生成分析报告
4. **代码生成代理 (Coder Agent)** - 根据实验计划生成和执行代码
5. **LaTeX 写作代理 (LaTeX Writer Agent)** - 生成学术论文

这些代理通过共享状态进行通信，并使用各种工具完成特定任务。

## 2. 代理详解

### 2.1 监督者代理 (Supervisor Agent)

监督者代理是整个系统的协调者和规划者，负责制定研究计划并协调其他代理的工作。

#### 2.1.1 功能描述

监督者代理的主要功能包括：
- 根据用户研究问题制定详细的研究计划
- 协调其他代理按计划执行任务
- 监控整个研究流程的进度
- 在必要时调整研究计划

#### 2.1.2 实现机制

监督者代理使用 Tavily 搜索工具获取相关领域知识，结合大型语言模型生成研究计划。它通过 PlanWriterTool 将计划写入文件，并通过 PlanReaderTool 读取现有计划（如果存在）。

代理使用两种不同的提示模板：
- supervisor_plan.md：用于生成初始研究计划
- supervisor_alter_plan.md：用于调整现有计划

#### 2.1.3 工作流程

1. 检查是否存在现有计划文件（plan.md）
2. 如果不存在，则使用 supervisor_chatbot 生成新计划
3. 如果存在，则使用 plan_reader_node 读取现有计划
4. 通过 supervisor_tools 执行计划写入工具
5. 根据工具调用结果决定是否结束或继续循环

### 2.2 文献审阅代理 (Literature Reviewer Agent)

文献审阅代理专门负责执行文献搜索和生成文献综述报告。

#### 2.2.1 功能描述

文献审阅代理的主要功能包括：
- 搜索相关学术文献（支持 arXiv、medRxiv 等平台）
- 阅读和分析文献内容
- 生成综合性的文献综述报告

#### 2.2.2 实现机制

代理使用多种文献搜索工具：
- SearchArxivTool：搜索 arXiv 平台文献
- SearchMedRxivTool：搜索 medRxiv 平台文献
- ReadArxivPaperTool：阅读 arXiv 文献
- ReadMedRxivPaperTool：阅读 medRxiv 文献
- TavilySearch：通用网络搜索

代理分为两个主要阶段：
1. 文献搜索阶段：使用 search_llm 和搜索工具搜索相关文献
2. 报告撰写阶段：使用 write_llm 和 ReportWriterTool 生成文献综述报告

#### 2.2.3 工作流程

1. 启动文献搜索聊天机器人进行文献检索
2. 当达到最小工具调用次数后，进入报告撰写阶段
3. 使用报告写入工具生成文献综述报告
4. 清理状态并结束流程

### 2.3 数据分析代理 (Data Analyzer Agent)

数据分析代理负责处理用户提供的数据集，执行数据分析并生成报告。

#### 2.3.1 功能描述

数据分析代理的主要功能包括：
- 分析用户提供的数据集
- 生成数据可视化图表
- 执行统计分析
- 生成数据分析报告

#### 2.3.2 实现机制

代理使用 OpenHands 工具执行代码，处理数据并生成分析结果。主要组件包括：
- data_analyzer_prompt：指导数据分析的提示模板
- data_report_prompt：指导报告生成的提示模板
- data_router_prompt：用于决策的路由提示模板
- OpenHandsTool：执行数据分析代码的工具

#### 2.3.3 工作流程

1. 使用 openhands_node 执行数据分析代码
2. 检查是否存在数据展示文件（data_show.md）
3. 如果存在，则使用 chatbot 生成数据分析报告
4. 通过工具节点写入报告
5. 使用 router_node 进行下一步决策

### 2.4 代码生成代理 (Coder Agent)

代码生成代理根据研究计划生成和执行实验代码。

#### 2.4.1 功能描述

代码生成代理的主要功能包括：
- 根据研究计划生成实验代码
- 执行生成的代码
- 验证代码执行结果
- 根据视觉反馈改进代码和结果

#### 2.4.2 实现机制

代理使用多种提示模板指导代码生成：
- coder.md：指导代码生成的主要提示模板
- coder_validator.md：指导代码验证的提示模板
- coder_concluder.md：指导结论生成的提示模板
- coder_router.md：用于决策的路由提示模板

代理集成了视觉语言模型（VLM）来评估生成的图表质量，并根据反馈进行改进。

#### 2.4.3 工作流程

1. 读取研究计划
2. 使用 openhands_coding_node 生成实验代码
3. 使用 openhands_validation_node 验证代码执行结果
4. 使用视觉语言模型评估生成的图表
5. 根据评估结果决定是否需要改进
6. 生成结论并写入报告
7. 使用路由决策下一步操作

### 2.5 LaTeX 写作代理 (LaTeX Writer Agent)

LaTeX 写作代理负责将研究结果整理成学术论文格式。

#### 2.5.1 功能描述

LaTeX 写作代理的主要功能包括：
- 生成论文各个部分（引言、相关工作、方法、实验等）
- 整合数据分析结果和图表
- 生成完整的 LaTeX 格式论文
- 根据反馈改进论文质量

#### 2.5.2 实现机制

代理使用多个专门的提示模板：
- latex_abstract_intro.md：生成摘要和引言
- latex_related_works.md：生成相关工作部分
- latex_methods.md：生成方法部分
- latex_experiments.md：生成实验部分
- latex_validator.md：验证论文质量
- latex_concluder.md：生成结论
- latex_router.md：用于决策的路由提示模板
- latex_rigor_prompt.md：提高论文严谨性的提示
- latex_literature_check.md：检查文献引用
- latex_figure_check.md：检查图表质量

代理同样集成了视觉语言模型来评估生成的 PDF 质量。

#### 2.5.3 工作流程

1. 清理状态并收集结果文件
2. 生成论文引言部分
3. 生成相关工作部分
4. 生成方法部分
5. 生成实验部分
6. 验证论文质量
7. 根据验证结果决定是否需要改进
8. 通过路由决定是否继续润色或结束

## 3. 代理间协作机制

OpenLens AI 中的各个代理通过共享状态进行协作。状态包括：
- 研究问题
- 研究计划
- 当前子任务索引
- 消息历史
- 各种中间结果

代理间的工作流由 LangGraph 管理，确保任务按正确的顺序执行，并在必要时进行重试或调整。

## 4. 工具和集成

系统集成了多种工具来支持代理的功能：
- Tavily 搜索：用于网络搜索
- OpenHands：用于代码执行沙箱
- 多种文献搜索工具：用于学术文献检索
- 视觉语言模型：用于图表和论文质量评估
