from typing import Annotated, Sequence
import json
import os

from loguru import logger
import asyncio

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END, START
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.tools.structured import StructuredTool
from langchain_core.messages.utils import count_tokens_approximately, get_buffer_string
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_tavily import TavilySearch

from ..state import State, track_node_call
from ..chatbot import chatbot_with_context_manager, react_pre_model_wrapper
from ..tools.reports import ReportWriterTool

# from ..tools.literature import PaperSearchTool
from ..tools.tool_utils import route_by_file_existence, BasicToolNode
from ..tools.paper_search_tool import (
    SearchArxivTool,
    SearchPubMedTool,
    ReadArxivPaperTool,
    ReadMedRxivPaperTool,
    SearchMedRxivTool,
    SearchSemanticTool,
    ReadSemanticPaperTool,
)
from ..utils.file_utils import prepare_files_folders
from ..utils.config import Config





# 加载提示模板
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "literature_review_report.md")) as f:
    report_prompt_template = f.read()
# 加载提示模板
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "literature_search.md")) as f:
    search_prompt_template = f.read()


def build_literature_review_subgraph(config: Config):
    """
    构建文献调研子图，使用paperscraper搜索文献并通过嵌入模型进行RAG处理生成文献调研报告
    """

    # 初始化语言模型
    search_llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    write_llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    search_tools = [
        SearchArxivTool(),
        ReadArxivPaperTool(),
        # SearchPubMedTool(),
        SearchMedRxivTool(),
        ReadMedRxivPaperTool(),
        # SearchSemanticTool(),
        # ReadSemanticPaperTool(),
        TavilySearch(max_results=10)
    ]

    llm_react = create_react_agent(search_llm, search_tools, pre_model_hook=react_pre_model_wrapper(config.question, config))

    report_tools = [ReportWriterTool(config, file_name="literature_review.md")]
    llm_report_writer = write_llm.bind_tools(report_tools)

    # 使用项目中的chatbot接口
    literature_search_chatbot = chatbot_with_context_manager(
        config, llm_react, search_prompt_template, context_manage="vector_search", calling_subgraph="literature_review"
    )
    write_report_chatbot = chatbot_with_context_manager(
        config, llm_report_writer, report_prompt_template, context_manage="vector_search", calling_subgraph="literature_review"
    )
    
    @track_node_call("literature_review")
    def clear_literature_state(state: State):
        state["messages"] = []
        literature_review_path = os.path.join(config.save_path, "workspace", "literature_review.md")
        with open(literature_review_path, "r") as f:
            literature_review_str = f.read()
        state["literature_report"] = literature_review_str
        return state

    # 创建文献调研子图
    graph = StateGraph(State)

    min_react_tool_call = config.workflow.literature_search_min_tool_call
    route_by_tool_counter = lambda state: "REACHED_TOOL_LIMIT" if (state["literature_tool_call_counter"] >= min_react_tool_call) else "CONTINUE"
    route_by_report = route_by_file_existence(os.path.join(config.save_path, "workspace", "literature_review.md"))
    report_tool_node = BasicToolNode(report_tools, config)

    # 添加节点
    graph.add_node("literature_search_chatbot", literature_search_chatbot)
    graph.add_node("write_report_chatbot", write_report_chatbot)
    graph.add_node("report_tool_node", report_tool_node)
    graph.add_node("clear_literature_state", clear_literature_state)

    # 添加边
    graph.add_edge(START, "literature_search_chatbot")
    graph.add_conditional_edges(
        "literature_search_chatbot", route_by_tool_counter, {"CONTINUE": "literature_search_chatbot", "REACHED_TOOL_LIMIT": "write_report_chatbot"}
    )
    graph.add_edge("write_report_chatbot", "report_tool_node")
    graph.add_conditional_edges("report_tool_node", route_by_report, {"FILE_NOT_FOUND": "write_report_chatbot", "FILE_EXISTS": "clear_literature_state"})
    graph.add_edge("clear_literature_state", END)

    return graph.compile()


if __name__ == "__main__":
    init_state, config, save_path = prepare_files_folders(
        "literature_search_test_20250813", 
        "What are the latest advancements in medical AI agents that can analyze multi-format datasets, answer research questions, and produce experimental reports?", 
        ""
    )

    graph = build_literature_review_subgraph(config)
    graph.invoke(init_state)