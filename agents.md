# OpenLens AI Agents Architecture Overview

## 1. System Architecture Overview

The OpenLens AI system consists of five core agents:

1. **Supervisor Agent** – Responsible for overall task planning and coordination.
2. **Literature Reviewer Agent** – Conducts literature search and generates review reports.
3. **Data Analyzer Agent** – Processes data and generates analysis reports.
4. **Coder Agent** – Generates and executes code according to the experimental plan.
5. **LaTeX Writer Agent** – Produces academic papers in LaTeX format.

These agents communicate through shared state and utilize various tools to accomplish specific tasks.

## 2. Agent Details

### 2.1 Supervisor Agent

The Supervisor Agent serves as the coordinator and planner of the entire system, responsible for formulating research plans and coordinating other agents.

#### 2.1.1 Functional Description

The main functions of the Supervisor Agent include:

* Creating detailed research plans based on the user's research question
* Coordinating other agents to execute tasks according to the plan
* Monitoring the progress of the entire research workflow
* Adjusting the research plan as needed

#### 2.1.2 Implementation Mechanism

The Supervisor Agent uses the Tavily search tool to gather domain knowledge and combines it with a large language model to generate research plans. It employs:

* **PlanWriterTool** to write plans to files
* **PlanReaderTool** to read existing plans (if any)

Two different prompt templates are used:

* `supervisor_plan.md` – for generating initial research plans
* `supervisor_alter_plan.md` – for modifying existing plans

#### 2.1.3 Workflow

1. Check if a plan file (`plan.md`) exists
2. If not, generate a new plan using `supervisor_chatbot`
3. If it exists, read the existing plan with `plan_reader_node`
4. Execute the plan writing tool via `supervisor_tools`
5. Decide whether to end or continue the loop based on the tool's results

---

### 2.2 Literature Reviewer Agent

The Literature Reviewer Agent is dedicated to performing literature searches and generating literature review reports.

#### 2.2.1 Functional Description

The main functions include:

* Searching relevant academic literature (supports arXiv, medRxiv, etc.)
* Reading and analyzing literature content
* Producing comprehensive literature review reports

#### 2.2.2 Implementation Mechanism

The agent uses multiple literature search tools:

* `SearchArxivTool` – searches arXiv
* `SearchMedRxivTool` – searches medRxiv
* `ReadArxivPaperTool` – reads arXiv papers
* `ReadMedRxivPaperTool` – reads medRxiv papers
* `TavilySearch` – general web search

The agent operates in two main phases:

1. **Literature search phase** – using `search_llm` and search tools
2. **Report writing phase** – using `write_llm` and `ReportWriterTool`

#### 2.2.3 Workflow

1. Launch the literature search chatbot to retrieve papers
2. After reaching a minimum number of tool calls, move to report writing
3. Generate the literature review report using the report writing tool
4. Clear state and finish the workflow

---

### 2.3 Data Analyzer Agent

The Data Analyzer Agent processes datasets provided by the user, performs data analysis, and generates reports.

#### 2.3.1 Functional Description

Key functions include:

* Analyzing user-provided datasets
* Creating data visualizations
* Performing statistical analyses
* Producing data analysis reports

#### 2.3.2 Implementation Mechanism

The agent uses the OpenHands tool to execute code and process data. Main components include:

* `data_analyzer_prompt` – guiding data analysis
* `data_report_prompt` – guiding report generation
* `data_router_prompt` – routing decisions
* `OpenHandsTool` – executes data analysis code

#### 2.3.3 Workflow

1. Execute data analysis code using `openhands_node`
2. Check if a data presentation file (`data_show.md`) exists
3. If it exists, generate a data analysis report via the chatbot
4. Write the report using the tool node
5. Use `router_node` to determine the next step

---

### 2.4 Coder Agent

The Coder Agent generates and executes experimental code according to the research plan.

#### 2.4.1 Functional Description

Key functions include:

* Generating experimental code based on the research plan
* Executing the generated code
* Validating code execution results
* Improving code and results based on visual feedback

#### 2.4.2 Implementation Mechanism

The agent uses several prompt templates:

* `coder.md` – guides code generation
* `coder_validator.md` – guides code validation
* `coder_concluder.md` – guides conclusion generation
* `coder_router.md` – routing decisions

It integrates a visual-language model (VLM) to assess chart quality and improve results based on feedback.

#### 2.4.3 Workflow

1. Read the research plan
2. Generate experimental code via `openhands_coding_node`
3. Validate code execution with `openhands_validation_node`
4. Evaluate charts using the visual-language model
5. Decide whether improvements are needed
6. Generate conclusions and write to the report
7. Use routing to determine the next operation

---

### 2.5 LaTeX Writer Agent

The LaTeX Writer Agent organizes research results into academic papers.

#### 2.5.1 Functional Description

Key functions include:

* Generating different sections of a paper (Introduction, Related Work, Methods, Experiments, etc.)
* Integrating data analysis results and charts
* Producing a complete LaTeX-formatted paper
* Improving paper quality based on feedback

#### 2.5.2 Implementation Mechanism

The agent uses multiple specialized prompt templates:

* `latex_abstract_intro.md` – abstract and introduction
* `latex_related_works.md` – related work section
* `latex_methods.md` – methods section
* `latex_experiments.md` – experiments section
* `latex_validator.md` – validates paper quality
* `latex_concluder.md` – conclusion generation
* `latex_router.md` – routing decisions
* `latex_rigor_prompt.md` – improves rigor
* `latex_literature_check.md` – checks references
* `latex_figure_check.md` – evaluates chart quality

It also integrates a visual-language model to assess the quality of the generated PDF.

#### 2.5.3 Workflow

1. Clear state and collect result files
2. Generate the Introduction section
3. Generate the Related Work section
4. Generate the Methods section
5. Generate the Experiments section
6. Validate paper quality
7. Improve if necessary based on validation
8. Use routing to decide whether to continue polishing or finish

---

## 3. Inter-Agent Collaboration Mechanism

Agents in OpenLens AI collaborate through shared state, which includes:

* Research question
* Research plan
* Current subtask index
* Message history
* Various intermediate results

Workflow is managed by **LangGraph**, ensuring tasks are executed in the correct sequence and retried or adjusted if necessary.

---

## 4. Tools and Integration

The system integrates multiple tools to support agent functions:

* **Tavily Search** – for web searches
* **OpenHands** – for code execution sandbox
* **Various literature search tools** – for academic paper retrieval
* **Visual-language models** – for evaluating charts and paper quality
