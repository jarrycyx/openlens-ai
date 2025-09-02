# OpenLens AI 📚🔍💡: Fully Autonomous Research Agent for Health Infomatics

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/LangGraph-Powered-orange" alt="LangGraph">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

**OpenLens AI** is a fully autonomous research agent designed for the medical field. Provide it with your dataset and a single-line research idea, and it will independently conduct literature review, design experiments, analyze data, and generate comprehensive research reports—**no manual intervention required**.

## 🔍 Key Features

- ✅ **Automated Literature Review**: Search and summarize medical papers based on your research question
- ✅ **Data Analysis**: Analyze medical datasets and generate comprehensive reports
- ✅ **Experiment Design**: Suggest and validate experimental approaches
- ✅ **Code Generation and Execution**: Generate and execute code for data analysis and experiments with [OpenHands](https://github.com/All-Hands-AI/OpenHands)
- ✅ **Multi-Agent Collaboration**: Coordinate multiple specialized agents to handle complex research tasks
- ✅ **LaTeX Paper Generation**: Automated creation and management of research papers and reports in LaTeX format
- ✅ **Interactive UI**: Streamlit-based interface for monitoring and interacting with the research process
- ✅ **Context Management**: Automated management of contextual information for agents via vector search
- ✅ **Vision-Language Feedback**: Integrate with VLM for visualization and feedback
- ⬜ **Powerpoint-Based Figures**: Automated generation of Powerpoint-based figures for demonstrations for better visual quality (to replace the current graphviz-based figures)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Docker (for OpenHands runtime environment)
- API keys for:
  - LLM service (e.g., DeepSeek, OpenAI, Qwen, etc.)
  - Tavily search API (for literature search)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-med
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and model settings
```

### Configuration

In your `.env` file, configure the following:

```bash

MODEL="qwen3-235b-a22b-instruct-2507"
API_KEY="<YOUR API KEY>"
BASE_URL="https://cloud.infini-ai.com/maas/v1/"
RERANK_MODEL="bge-reranker-v2-m3"

TAVILY_API_KEY="<YOUR API KEY>"

LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="<YOUR API KEY>"

MAX_CONTEXT_TOKEN_CNT=32000
MAX_CONTEXT_TOKEN_CNT_LARGE=96000
LITERATURE_SEARCH_MIN_TOOL_CALL=10

MAX_TOOL_TOKEN_CNT=2000

SMTP_SERVER=smtp.yeah.net
SMTP_PORT=25
EMAIL_USER=<YOUR EMAIL>
EMAIL_PASSWORD=<YOUR EMAIL SMTP PASSWORD>
```

### Running the Application

#### Option 1: Command Line Interface

```bash
python -m openlens_ai.build_graph --question "Your research question" --dataset-path "path/to/dataset"
```

Example:
```bash
python -m openlens_ai.build_graph --question "What is the prediction precision of AKI based on historical 2 day data?" --dataset-path "datasets/mimic"
```

#### Option 2: Interactive Web Interface

```bash
streamlit run start_app.py
```

Then open your browser to `http://localhost:8501` to access the interactive interface.

## 🧠 Architecture

OpenLens AI uses a multi-agent architecture powered by LangGraph:

1. **Literature Reviewer**: Searches and analyzes relevant medical literature
2. **Data Analyzer**: Processes and analyzes medical datasets
3. **Supervisor**: Coordinates the research process and makes high-level decisions
4. **Coder**: Generates code and technical solutions for data processing
5. **LaTeX Writer**: Generates LaTeX documents for research papers and reports

Agents communicate through a shared state and can call various tools including:
- Web search (Tavily)
- Code execution (OpenHands)
- File operations
- Vector search for context management
- **Literature Search Tools**:
  - arXiv Search and Paper Reading
  - PubMed Search
  - bioRxiv Search and Paper Reading
  - medRxiv Search and Paper Reading
  - Google Scholar Search
  - IACR ePrint Search
  - Semantic Scholar Search and Paper Reading

## 📁 Project Structure

```
openlens_ai/
├── agents/              # Agent implementations
│   ├── coder.py
│   ├── data_analyzer.py
│   ├── latex_writer.py   # LaTeX document generation agent
│   ├── literature_reviewer.py
│   └── supervisor.py
├── prompts/             # LLM prompt templates
├── tools/               # Custom tools and utilities
├── utils/               # Helper functions
├── build_graph.py       # Main graph construction
├── chatbot.py           # Chatbot interface
├── frontend.py          # Streamlit frontend
└── state.py             # State management
```

## 🛠️ Customization

### Adding New Agents

1. Create a new agent in [openlens_ai/agents/](openlens_ai/agents/)
2. Follow the pattern in existing agents like [coder.py](openlens_ai/agents/coder.py)
3. Register the agent in [build_graph.py](openlens_ai/build_graph.py)

### Adding New Tools

1. Add tool implementation in [openlens_ai/tools/](openlens_ai/tools/)
2. Register the tool in the appropriate agent
3. Update prompts if needed

## 📊 Example Use Cases

1. **Disease Prediction Modeling**:
   ```
   Question: "What is the prediction precision of AKI based on historical 2 day data?"
   Dataset: MIMIC-III critical care dataset
   ```

2. **Drug Interaction Research**:
   ```
   Question: "What are the latest findings on drug interactions for hypertension medications?"
   Dataset: Clinical trial data
   ```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Powered by [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- Uses [OpenHands](https://github.com/All-Hands-AI/OpenHands) for code execution sandbox
- Inspired by recent advances in AI for medical research