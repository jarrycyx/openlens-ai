**[中文版本](README_CN.md)**

# OpenLens AI: A Fully Autonomous Multimodal Research Agent

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

<strong>🚀 Try Now:</strong> <a href="https://app.openlens.icu">Use our cloud application directly in your browser</a>
<p> </p>

</p>
</div>

<table>
  <tr>
    <td style="width:3cm; text-align:center;">
      <img src="static/logo.svg" alt="Logo" width="100">
    </td>
    <td style="text-align: justify;">
      <strong>OpenLens AI</strong> is a fully autonomous multimodal agent designed for medical/ML/stats research, or any data-driven project, and is optimized for medical + AI research.
      Provide it with your dataset and a single-line research idea, and it will independently conduct literature review, design experiments, analyze data, and generate comprehensive research reports—<strong>no manual intervention required</strong>.
    </td>
  </tr>
</table>

🔥 **New:** General domain supported (e.g. software, machine learning, etc.)

🔥 **New:** Chinese language support for figures and papers.

## 🔍 Key Features

<p>
No installation required! Visit our <a href="https://openlens.icu">project page</a> to learn more about OpenLens AI or try our <a href="https://openlens.icu">cloud application</a> to experience the fully autonomous research agent without any setup.
</p>

<img src="static/papers/example.png" alt="Logo" width="100%">

- ✅ **Automated Literature Review**: Search and summarize papers based on your research question
- ✅ **Data Analysis**: Analyze datasets and generate comprehensive reports
- ✅ **Experiment Design**: Suggest and validate experimental approaches
- ✅ **Code Generation and Execution**: Generate and execute code for data analysis and experiments with [OpenHands](https://github.com/All-Hands-AI/OpenHands)
- ✅ **LaTeX Paper Generation**: Automated creation and management of research papers and reports in LaTeX format
- ✅ **Interactive UI**: Streamlit-based interface for monitoring and interacting with the research process
- ✅ **Context Management**: Automated management of contextual information for agents via vector search
- ✅ **Agent File Management**: Identify and remove duplicate files and mock data with [👕 file1.agent](https://github.com/jarrycyx/file1agent)
- ✅ **Vision-Language Feedback**: Integrate with VLM for visualization and feedback
- ✅ **Chinese Language Support**: Full support for Chinese paper writing
- ⬜ **Powerpoint-Based Figures**: Automated generation of Powerpoint-based figures for demonstrations for better visual quality (to replace the current graphviz-based figures)
- ⬜ **Context Manager via Long Context Model**: Integrate with long context model for context management (in addition to the current vector search-based approach)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=jarrycyx/openlens-ai&type=date&legend=top-left)](https://www.star-history.com/#jarrycyx/openlens-ai&type=date&legend=top-left)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Docker (for OpenHands runtime environment)
- API keys for:
  - LLM service (e.g., DeepSeek, OpenAI, Qwen, etc.)
  - Tavily search API (for literature search)

### Installation


0. Clone the repository:
```bash
git clone git@github.com:jarrycyx/openlens-ai.git --recurse-submodules
cd openlens-ai
```

1. Ensure Docker Installation:

Pull the runtime directly (**recommended**):
```bash
docker --version

# Pull docker
ALIYUN_REMOTE_DOCKER_NAME=crpi-hbt8nkulkjqjqkie.cn-hangzhou.personal.cr.aliyuncs.com/cyx-docker/openlens-ai:runtime-latest
docker pull $ALIYUN_REMOTE_DOCKER_NAME
docker tag $ALIYUN_REMOTE_DOCKER_NAME openlens-ai:runtime-latest
```
or build from scratch (if needing to support Chinese paper writing, download [windows-fonts.tar.gz](https://github.com/jarrycyx/openlens-ai/releases/download/v0.1.0/windows-fonts.tar.gz) or collect fonts in ```C://windows/Fonts/```):
```bash
# Optional: Collect Chinese fonts
cd openlens_ai/tools/openhands_configs/ && tar -xzvf windows-fonts.tar.gz

# Build base docker for tex-live, etc
bash openlens_ai/tools/openhands_configs/build_docker_base.sh 
# Build runtime docker to meet the requirements of OpenHands
bash openlens_ai/tools/openhands_configs/build_docker_runtime.sh 
# Check the ID of the built image
docker images
# Tag the image name with openlens-ai:runtime-latest
docker tag <IMAGE_ID> openlens-ai:runtime-latest
```

2. Install dependencies:
First install [file1.agent](https://github.com/jarrycyx/file1agent):
```bash
cd modules/file1agent
pip install -e .
cd ../../
```
Then ````cd modules/OpenHands``` and install OpenHands following the [instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

Then install Openhands with mamba:
```bash
# Download and install Mamba (a faster version of conda)
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# Install Python 3.12, nodejs, and poetry
mamba install python=3.12
mamba install conda-forge::nodejs
mamba install conda-forge::poetry
```

or with conda:
```bash
cd modules/OpenHands
conda create -n py312 python=3.12 # Or with uv / venv
conda activate py312
conda install conda-forge::nodejs
conda install conda-forge::poetry
make build
```

Install python dependencies:
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

In your `config.toml` file, configure the following:

```yaml
[llm]
language = "chs"  # Language setting: "chs" for Chinese, "eng" for English

[llm.chat] # Main language model used for general tasks and coding
model = "glm-4.5-air"  # The main language model used for general tasks
base_url = "https://cloud.infini-ai.com/maas/v1/"  # Base URL for the model API service
api_key = "<YOUR API KEY>"  # API key for accessing the language models

[llm.vision]
model = "glm-4.1v-9b-thinking"  # The vision model used for image analysis tasks
base_url = "https://open.bigmodel.cn/api/paas/v4/"  # Base URL for the vision model API service
api_key = "<YOUR API KEY>"  # API key for accessing the vision model

[rerank]
rerank_model = "bge-reranker-v2-m3"  # The reranking model used to improve search result relevance
rerank_api_key = "<YOUR API KEY>" # API key for accessing the reranking model (infiniai service)
rerank_base_url = "https://cloud.infini-ai.com/maas/v1/"  # Base URL for the reranking model API service

[tools]
tavily_api_key = "<YOUR API KEY>"  # API key for Tavily search service used for web search

[docker]
docker_name = "openlens-ai:runtime-latest"  # Name of the Docker container used for the agent environment

```

See [config.full-example.toml](config.full-example.toml) for more detailed configuration options.

### Running the Application

#### Option 1: Command Line Interface


Example:
```bash
python -m openlens_ai.main \
  --question "What are the temporal patterns of vital sign deterioration preceding cardiac arrest events in critical care settings?" \
  --dataset-path "datasets/eicu-demo" \
  --thread-id "pred_aki_trend_eicu_demo" \
  --notify-email "dzdzzd@126.com" \
  --interrupt-after-subgraph "none" \
  --language "chs" \
  --domain "medical" # Domain setting: "medical" for healthcare, "general" for other domains
```

#### Option 2: Interactive Web Interface

Configure your https settings in `.streamlit/config.toml` if needed. Otherwise comment ```sslKeyFile``` and ```sslCertFile``` out.

```bash
streamlit run start_app.py
```

Then open your browser to `http://localhost:8501` to access the interactive interface.

## 🧠 Architecture

OpenLens AI uses a multi-module architecture powered by LangGraph:

1. **Literature Reviewer**: Searches and analyzes relevant literature
2. **Data Analyzer**: Processes and analyzes datasets
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

## 🧩 Optional: GitHub Integration (Automatic Artifact Publishing)

OpenLens AI can **optionally** publish generated code artifacts to GitHub.
If you don't configure this section, nothing will be pushed.

### 1. Configure GitHub in `config.toml`

Add or edit the `[git]` section:

```toml
[git]
# Optional: fixed repository to push to
# repo_url = "git@github.com:<YOUR_USERNAME>/<YOUR_REPO>.git"
repo_url    = ""

branch      = "main"                # Target branch for commits
token       = "<YOUR GITHUB TOKEN>" # GitHub Personal Access Token (PAT)
repo_prefix = "openlens-"           # Prefix for auto-created repo names
private     = true                  # Whether auto-created repos should be private
```
If `repo_url` is **set** → artifacts are pushed to that repository.

If `repo_url` is **empty** but token is set → OpenLens AI may automatically create a new repo under your GitHub account and push there.

>💡 Recommended: put your real token only in a local `config.local.toml` (ignored by Git) and keep `config.full-example.toml` as a public template with `<YOUR GITHUB TOKEN>` placeholders.

### 2. How to generate a GitHub token (short version)
1. Go to **GitHub → Settings → Developer settings → Personal access tokens**

2. Create a new token:

     - Fine-grained PAT (recommended) or classic PAT
     
3. Repository access scope:

    - ✅ All repositories — required if you want OpenLens AI to **automatically create new repositories** under your GitHub account.
    - ✅ Only select repositories — **more secure**, recommended if you only need to **push to a pre-existing fixed repository**.


4. Give it minimal permissions, typically:

     - Contents → Read and write: Permission to read/write contents

     - Administration → Read and write: Access to repositories under your account

5. Copy the token and fill it into:

```toml
[git]
token = "github_pat_XXXXXXXXXXXXXXXX"
```
or set it as an environment variable GITHUB_TOKEN.

### 3. Security notes
- 🔒 Treat your GitHub token like a password:

   - **Do not commit it to Git**, especially in public repositories

  - Store it only in local config files (e.g., `config.local.toml`, `.env`) that are in `.gitignore`

- 🧹 If you suspect a leak:

  - Go to **GitHub → Settings → Developer settings → Tokens** and **revoke** the token immediately

- 🎯 Use the **minimum necessary permissions** for your use case

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
- Inspired by recent advances in AI for research
