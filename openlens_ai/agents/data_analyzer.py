import os
import json
import random

import glob
from loguru import logger
import traceback

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from ..tools.tool_utils import (
    BasicToolNode,
    route_tools,
    route_by_tool_call,
    route_by_file_existence,
    route_by_keywords,
)
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State
from ..chatbot import chatbot_with_context_manager
from ..state import load_state, track_node_call
from ..utils.config import Config
from ..utils.file_utils import sample_file_content

from file1agent.file_manager import FileManager


# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, "domain") and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()


# Initialize prompts as None, will be loaded in build_data_analyzer function
data_router_prompt = None


def build_data_analyzer(config: Config, file_manager: FileManager) -> StateGraph:
    # Load prompts based on domain configuration
    data_report_prompt = load_prompt_file(config, "data_report.md")

    llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    report_writer_tool = ReportWriterTool(config.save_path, file_name="data_report.md")
    tools = [report_writer_tool]
    llm_with_tools = llm.bind_tools(tools)

    @track_node_call("data_analyzer")
    def data_sample_node(state: State):
        # Initialize FileSummary to get file descriptions
        workspace_manager_config = file_manager.config
        workspace_manager_config.inclusion.ext_whitelist = [".py", ".sh", ".c", ".cpp", ".r", ".json", ".txt", ".csv"]
        
        dataset_manager = FileManager(
            config=workspace_manager_config,
            analyze_dir=config.dataset_path,
            backup_path=file_manager.backup_path,
            realloc_log=False,
            file_relationships_save_path=file_manager.file_relationships_save_path,
            summary_cache_path=file_manager.file_summary.summary_cache_path,
        )

        # Get file tree with summaries
        dataset_manager.file_summary.get_all_summaries()
        state["file_summary"] = dataset_manager.file_summary.file_cache

        # Create output directory if it doesn't exist
        output_dir = os.path.join(state["save_path"], "workspace", "data_analyze")
        os.makedirs(output_dir, exist_ok=True)

        # Prepare output content
        output_content = []
        output_content.append("# File Analysis Report\n")
        # output_content.append("## File Tree with Summaries\n")
        # output_content.append(file_tree_with_summaries)
        output_content.append("\n\n## File Content Samples\n")

        # Get all files from workspace and dataset
        workspace_path = os.path.join(state["save_path"], "workspace")
        dataset_path = config.dataset_path

        # Collect all files
        all_files = []

        # Add files from dataset
        if os.path.exists(dataset_path):
            for root, dirs, files in os.walk(dataset_path):
                for file in files:
                    if os.path.basename(file).startswith("."):
                        continue
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

        # Process each file
        for file_path in all_files:
            try:
                # Get file summary from cache
                abs_path = os.path.abspath(file_path)
                summary = state["file_summary"].get(abs_path, {}).get("summary", "No summary available")

                # Use sample_file_content function to get file samples
                first_10_lines, random_10_lines = sample_file_content(file_path)

                # Add file information to output
                output_content.append(f"### {file_path}\n")
                output_content.append(f"**Summary:** {summary}\n")
                output_content.append("**First 10 lines:**\n")
                output_content.append("```\n")
                output_content.extend(first_10_lines)
                output_content.append("```\n")

                if random_10_lines:
                    output_content.append("**Random 10 lines:**\n")
                    output_content.append("```\n")
                    output_content.extend(random_10_lines)
                    output_content.append("```\n")
                else:
                    # If it's a binary file but not an Excel file, add a note
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext not in [".xls", ".xlsx"] and file_ext not in [
                        ".txt",
                        ".md",
                        ".py",
                        ".js",
                        ".html",
                        ".css",
                        ".json",
                        ".csv",
                        ".tsv",
                    ]:
                        output_content.append("**Binary file skipped (not a text or Excel file)**\n")

                output_content.append("\n")
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                output_content.append(f"### {file_path}\n")
                output_content.append(f"**Error:** {str(e)}\n\n")

        # Write output to file
        output_path = os.path.join(output_dir, "data_show.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(output_content))

        logger.info(f"File analysis report saved to {output_path}")

        return state

    @track_node_call("data_analyzer")
    def chatbot(state: State):
        with open(os.path.join(state["save_path"], "workspace", "data_analyze", "data_show.md"), "r") as f:
            data_show = f.read()

        state["data_show"] = data_show
        this_chatbot = chatbot_with_context_manager(
            config, llm_with_tools, data_report_prompt, calling_subgraph="data_analyzer"
        )
        state = this_chatbot(state)
        return state

    graph_builder = StateGraph(State)

    router_by_write_reports = route_by_tool_call("report_writer_tool")

    tool_node = BasicToolNode(tools, config)
    graph_builder.add_node("data_chatbot", chatbot)
    graph_builder.add_node("data_sample_node", data_sample_node)
    graph_builder.add_node("data_tools", tool_node)

    graph_builder.add_edge(START, "data_sample_node")
    graph_builder.add_edge("data_sample_node", "data_chatbot")
    graph_builder.add_edge("data_chatbot", "data_tools")
    graph_builder.add_conditional_edges(
        "data_tools", router_by_write_reports, {"RETURN_TO_LLM": "data_chatbot", END: END}
    )

    graph = graph_builder.compile()

    return graph


if __name__ == "__main__":
    config, state, last_subgraph, file_manager = load_state("outputs/pred_aki_dy_mimic_icu_csv")

    graph = build_data_analyzer(config, file_manager)

    graph.invoke(state)
