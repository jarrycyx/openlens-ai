import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import argparse
import toml
import toml


class ModelConfig(BaseModel):
    """Chat model configuration"""
    model: str = Field(default="", description="Chat model name")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    api_key: Optional[str] = Field(default=None, description="API key for chat service")

class LLMConfig(BaseModel):
    """Language model configuration"""
    language: str = Field(default="chs", description="Language for the model")
    chat: ModelConfig = Field(default_factory=ModelConfig, description="Chat model configuration")
    condenser: ModelConfig = Field(default_factory=ModelConfig, description="Condenser model configuration")
    vision: ModelConfig = Field(default_factory=ModelConfig, description="Vision model configuration")


class RerankConfig(BaseModel):
    """Rerank model configuration"""
    rerank_api_key: Optional[str] = Field(default=None, description="API key for rerank service")
    rerank_base_url: Optional[str] = Field(default=None, description="Base URL for rerank service")
    rerank_model: str = Field(default="BAAI/bge-reranker-v2-m3", description="Rerank model name")
    file_duplicate_threshold: float = Field(default=0.8, description="Threshold for considering files as duplicates based on reranking score")


class ToolsConfig(BaseModel):
    """Tools configuration"""
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily API key")
    langsmith_tracing: str = Field(default="false", description="Enable LangSmith tracing")
    langsmith_endpoint: Optional[str] = Field(default=None, description="LangSmith endpoint")
    langsmith_project: str = Field(default="openlens", description="LangSmith project name")
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")


class ContextConfig(BaseModel):
    """Context configuration"""
    max_context_token_cnt: int = Field(default=32000, description="Maximum context token count")
    max_context_token_cnt_large: int = Field(default=96000, description="Maximum context token count for large models")
    max_tool_token_cnt: int = Field(default=2000, description="Maximum token count for tool responses")


class EmailServerConfig(BaseModel):
    """Email server configuration"""
    smtp_server: Optional[str] = Field(default=None, description="SMTP server for email notifications")
    smtp_port: int = Field(default=587, description="SMTP port")
    email_user: Optional[str] = Field(default=None, description="Email username")
    email_password: Optional[str] = Field(default=None, description="Email password")


class WorkflowConfig(BaseModel):
    """Workflow configuration"""
    openhands_max_iter: int = Field(default=10, description="Maximum iterations for OpenHands")
    max_subtask_redo: int = Field(default=3, description="Maximum subtask redo attempts")
    max_latex_polish_round: int = Field(default=5, description="Maximum LaTeX polish rounds")
    literature_search_min_tool_call: int = Field(default=10, description="Minimum tool calls for literature search")
    min_sub_tasks: int = Field(default=3, description="Minimum number of subtasks for the experiment plan")
    enable_literature_review: bool = Field(default=False, description="Enable or disable the literature review feature")
    enable_latex_writer: bool = Field(default=False, description="Enable or disable the LaTeX writer feature")


class DockerConfig(BaseModel):
    """Docker configuration"""
    docker_name: str = Field(default="openhands", description="Docker container name")


class FrontendConfig(BaseModel):
    """Frontend configuration"""
    # Currently empty, but can be extended as needed
    frontend_admin_email: str = Field(default="none", description="Admin email for frontend access")

class GitConfig(BaseModel):
    """Git / GitHub 相关配置。"""
    repo_url: str | None = None      # 显式指定的远端仓库；为空则自动创建
    branch: str = "main"             # 默认分支
    token: str | None = None         # 默认 token；为空则回退到环境变量 GITHUB_TOKEN
    repo_prefix: str = "openlens-"   # 自动创建仓库时用的前缀
    private: bool = True             # 自动创建的仓库是否设为 private

class Config(BaseModel):
    """
    Configuration model for OpenLens AI application.
    This model represents the configuration structure used throughout the application.
    """
    # Running settings
    save_path: str = Field(default="outputs", description="Path to save outputs")
    thread_id: str = Field(default="", description="Thread ID for the experiment")
    question: str = Field(default="", description="Research question")
    refine_suggestion: str = Field(default="", description="Human's feedback for refining the research, only needed when current result is not satisfactory")
    code_hint: str = Field(default="", description="Important points to consider in the research")
    dataset_path: str = Field(default="", description="Path to the dataset")
    notify_email: str = Field(default="", description="Email for notifications")
    domain: str = Field(default="medical", description="Domain for prompts: 'general' or 'medical'")
    
    # Configuration sections
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    rerank: RerankConfig = Field(default_factory=RerankConfig, description="Rerank configuration")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="Tools configuration")
    context: ContextConfig = Field(default_factory=ContextConfig, description="Context configuration")
    email_server: EmailServerConfig = Field(default_factory=EmailServerConfig, description="Email server configuration")
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig, description="Workflow configuration")
    docker: DockerConfig = Field(default_factory=DockerConfig, description="Docker configuration")
    frontend: FrontendConfig = Field(default_factory=FrontendConfig, description="Frontend configuration")
    git: GitConfig = Field(default_factory=GitConfig, description="Git/GitHub configuration")
    
    @classmethod
    def from_toml(cls, toml_path: str) -> 'Config':
        """Load configuration from a TOML file"""
        with open(toml_path, 'r') as file:
            config_data = toml.load(file)
        
        # Create config instance with default sub-configs
        config = cls(**config_data)
        
        # Setup ENV
        os.environ["LANGSMITH_TRACING"] = config.tools.langsmith_tracing
        os.environ["LANGSMITH_ENDPOINT"] = config.tools.langsmith_endpoint
        os.environ["LANGSMITH_PROJECT"] = config.tools.langsmith_project
        os.environ["LANGSMITH_API_KEY"] = config.tools.langsmith_api_key
        
        os.environ["TAVILY_API_KEY"] = config.tools.tavily_api_key
        
        return config
    
    def save_toml(self, toml_path: str):
        """Save configuration to a TOML file"""
        # Convert the config to a dictionary
        config_dict = self.model_dump()
        
        with open(toml_path, 'w') as file:
            toml.dump(config_dict, file)
    
def get_lang_prompt(lang: str) -> str:
    """
    Get language-specific prompt suffix based on the language parameter.
    
    Args:
        lang: Language code ('eng' or 'chs')
        
    Returns:
        Language-specific prompt suffix string
    """
    if lang == "chs":
        return "\n\n确保使用中文书写所有的论文文字、程序注释、思考过程、执行报告、文献综述，但不要强行翻译专有名词和引用文献的标题、人名、期刊名（例如LSTM，RCT，ICU，Lucas，Schmidgall）"
    elif lang == "eng":
        return ""
    else:
        # Default to English for unsupported languages
        return ""
