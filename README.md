**[中文版本](README_CN.md)**

# OpenLens AI: Fully Autonomous Research Agent for Health Infomatics

<p align="center">
  <!-- <a href="https://arxiv.org/abs/2509.14778">
    <img src="https://img.shields.io/badge/arXiv-paper-red" alt="arXiv-paper" >
  </a>
  <a href="https://openlens.icu">
    <img src="https://img.shields.io/badge/Project-Page-blue" alt="Project Page" >
  </a>
  <a href="https://app.openlens.icu">
    <img src="https://img.shields.io/badge/Try-Now-green" alt="Try Now" >
  </a> -->
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/LangGraph-Powered-orange" alt="LangGraph">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>


<div align="center">
<p>
<strong>📄 Paper:</strong> <a href="https://arxiv.org/abs/2509.14778">Read our research paper on arXiv</a> 

<strong>🌐 Project Page:</strong> <a href="https://openlens.icu">Explore detailed documentation and examples</a> 

<strong>🚀 Try Now:</strong> <a href="https://openlens.icu">Use our cloud application directly in your browser</a>
<p> </p>

</p>
</div>

<table>
  <tr>
    <td style="width:3cm; text-align:center;">
      <img src="static/logo.svg" alt="Logo" width="100">
    </td>
    <td style="text-align: justify;">
      <strong>OpenLens AI</strong> is a fully autonomous research agent designed for the medical field.  
      Provide it with your dataset and a single-line research idea, and it will independently conduct literature review, design experiments, analyze data, and generate comprehensive research reports—<strong>no manual intervention required</strong>.
    </td>
  </tr>
</table>


## 🔍 Key Features

<p>
No installation required! Visit our <a href="https://openlens.icu">project page</a> to learn more about OpenLens AI or try our <a href="https://openlens.icu">cloud application</a> to experience the fully autonomous research agent without any setup.
</p>

<img src="static/papers/example.png" alt="Logo" width="100%">

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
- ⬜ **Context Manager via Long Context Model**: Integrate with long context model for context management (in addition to the current vector search-based approach)
- ⬜ **Chinese Language Support**: Full support for Chinese paper writing

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Docker (for OpenHands runtime environment)
- API keys for:
  - LLM service (e.g., DeepSeek, OpenAI, Qwen, etc.)
  - Tavily search API (for literature search)

### Installation

0. Ensure Docker Installation:

Pull the runtime directly (**recommended**):
```bash
docker --version

# Pull docker
ALIYUN_REMOTE_DOCKER_NAME=crpi-hbt8nkulkjqjqkie.cn-hangzhou.personal.cr.aliyuncs.com/cyx-docker/openlens-ai:runtime-latest
docker pull $ALIYUN_REMOTE_DOCKER_NAME
docker tag $ALIYUN_REMOTE_DOCKER_NAME openlens-ai:runtime-latest
```
or build from scratch:
```bash
# Build base docker for tex-live, torch, etc
bash openlens_ai/tools/openhands_configs/build_docker_base.sh 
# Build runtime docker to meet the requirements of OpenHands
bash openlens_ai/tools/openhands_configs/build_docker_runtime.sh 
# Check the ID of the built image
docker images
# Tag the image name with openlens-ai:runtime-latest
docker tag <IMAGE_ID> openlens-ai:runtime-latest
```

1. Clone the repository:
```bash
git clone git@github.com:jarrycyx/openlens-ai.git
cd openlens-ai
```

2. Install dependencies:
```bash
# If wish to visualize the workflow, install graphviz:
#   sudo apt-get install graphviz graphviz-dev
#   pip install pygraphviz

conda create -n py312 python=3.12 # Or with uv / venv
conda activate py312
pip install --upgrade pip
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
MODEL="glm-4.5-air"  # The main language model used for general tasks
CODE_MODEL="glm-4.5-air"  # The language model specifically used for code-related tasks
VISION_MODEL="glm-4.1v-9b-thinking"  # The vision model used for image analysis tasks
OPENAI_API_KEY="<YOUR API KEY>"  # API key for accessing the language models
BASE_URL="https://cloud.infini-ai.com/maas/v1/"  # Base URL for the model API service

RERANK_MODEL="bge-reranker-v2-m3"  # The reranking model used to improve search result relevance
RERANK_API_KEY="<YOUR API KEY>" # API key for accessing the reranking model (infiniai service)
RERANK_BASE_URL="https://cloud.infini-ai.com/maas/v1/"  # Base URL for the reranking model API service

TAVILY_API_KEY="<YOUR API KEY>"  # API key for Tavily search service used for web search

MAX_CONTEXT_TOKEN_CNT=32000  # Maximum number of tokens allowed in the context for normal operations
MAX_CONTEXT_TOKEN_CNT_LARGE=96000  # Maximum number of tokens allowed in the context for large operations
LITERATURE_SEARCH_MIN_TOOL_CALL=10  # Minimum number of tool calls for literature search

MAX_TOOL_TOKEN_CNT=2000  # Maximum number of tokens allowed in tool responses

OPENHANDS_MAX_ITER=100  # Maximum number of iterations allowed for OpenHands agent execution
MAX_SUBTASK_REDO=2  # Maximum number of retries for subtasks
MAX_LATEX_POLISH_ROUND=2  # Maximum number of rounds for LaTeX document polishing

DOCKER_NAME=openlens-ai:runtime-latest


### Optional settings

LANGSMITH_TRACING="true"  # Enable or disable LangSmith tracing for monitoring and debugging
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"  # Endpoint URL for LangSmith service
LANGSMITH_PROJECT="openlens"  # Project name in LangSmith for organizing traces
LANGSMITH_API_KEY="<YOUR API KEY>"  # API key for accessing LangSmith service

SMTP_SERVER=smtpdm.aliyun.com  # SMTP server address for sending emails
SMTP_PORT=25  # Port number for the SMTP server
EMAIL_USER=<YOUR EMAIL>  # Email address used for sending notifications
EMAIL_PASSWORD=<YOUR EMAIL SMTP PASSWORD>  # Password or app-specific password for the email account
```

### Running the Application

#### Option 1: Command Line Interface

```bash
python -m openlens_ai.build_graph --question "Your research question" --dataset-path "path/to/dataset" --thread-id "Unique id for this job"
```

Example:
```bash
python -m openlens_ai.build_graph --question "What is the prediction precision of AKI based on historical 2 day data?" --dataset-path "datasets/mimic" --thread-id "test_000"
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
  - ✅ arXiv Search and Paper Reading
  - ✅ medRxiv Search and Paper Reading
  - ✅ Google Scholar Search
  - ✅ Tavily Search
  - ⬜ IACR ePrint Search
  - ⬜ Semantic Scholar Search and Paper Reading
  - ⬜ PubMed Search

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

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Uses [OpenHands](https://github.com/All-Hands-AI/OpenHands) for code execution sandbox
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- Uses [Streamlit](https://streamlit.io/) for the web interface
- Inspired by recent advances in AI for medical research
