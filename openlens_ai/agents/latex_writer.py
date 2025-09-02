import os
import glob
import dotenv
from typing import List
from loguru import logger

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.load.dump import dumps
from langchain_core.messages import ToolMessage

from ..tools.tool_utils import BasicToolNode, route_by_tool_call, route_by_keywords
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State, load_state
from ..utils.config import Config
from ..chatbot import chatbot_with_context_manager

dotenv.load_dotenv()

results_files_extensions = [".png", ".jpg", ".jpeg", ".pdf", ".svg"]

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_abstract_intro.md")) as f:
    introduction_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_related_works.md")) as f:
    related_works_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_methods.md")) as f:
    methods_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_experiments.md")) as f:
    exp_conclusion_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_validator.md")) as f:
    validator_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_concluder.md")) as f:
    latex_concluder_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_router.md")) as f:
    latex_router_prompt = f.read()

rigor_prompt = """
Make sure each paragraph of the manuscript corresponds to a file or several lines in a file in workspace, 
record the file name and corresponding line number in /workspace/manuscript/paper_rigor_report.md
"""

def build_latex_writer(config: Config) -> StateGraph:
    concluder_llm = init_chat_model(
        os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", ""),
        model_provider="openai",
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    router_llm = init_chat_model(
        os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", ""),
        model_provider="openai",
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    vlm = init_chat_model(
        os.environ.get("VISION_MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", ""),
        model_provider="openai",
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    
    code_tool = OpenHandsTool(config)
    report_writer_tool = ReportWriterTool(config, file_name="manuscript/latex_quality_report.md")
    
    tools = [report_writer_tool]
    concluder_llm_with_tools = concluder_llm.bind_tools(tools)

    def clear_state(state: State):
        state["messages"] = []
        return state

    def write_introduction_node(state: State):
        this_prompt = introduction_prompt.format(question=state["question"])
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    def write_related_node(state: State):
        this_prompt = related_works_prompt.format(question=state["question"])
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    def collect_result_files(state: State):
        results_file_list = []
        workspace_dir = os.path.join(config.save_path, "workspace")
        for ext in results_files_extensions:
            results_file_list.extend(glob.glob(os.path.join(workspace_dir, "**", f"*{ext}"), recursive=True))
        logger.info(f"Found {len(results_file_list)} results files: {results_file_list}")
        # Copy figures/tables from /workspace/ to /workspace/manuscript/
        figure_dir = os.path.join(workspace_dir, "manuscript", "figures")
        os.makedirs(figure_dir, exist_ok=True)
        for file in results_file_list:
            logger.info(f"Copying figure file {file} to {figure_dir}")
            try:
                os.system(f"cp {file} {figure_dir}")
            except Exception as e:
                logger.warning(f"Failed to copy {file} to {figure_dir}: {e}")
        return state
        
    
    def write_methods_node(state: State):
        this_prompt = methods_prompt.format(question=state["question"])
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    def write_experiments_node(state: State):
        this_prompt = exp_conclusion_prompt.format(question=state["question"])
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    def validator_node(state: State):
        this_prompt = validator_prompt
        results = code_tool.invoke({"prompts": [this_prompt, rigor_prompt]})
        
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            ),
        ]
        return state
       
    concluder_tools_node = BasicToolNode(tools, config)
    conclude_chatbot = chatbot_with_context_manager(config, concluder_llm_with_tools, latex_concluder_prompt, context_manage="last_tool_message")
    router_chatbot = chatbot_with_context_manager(config, router_llm, latex_router_prompt, context_manage="last_tool_message")
    write_plan_router = route_by_tool_call("report_writer_tool")
    keywords_router = route_by_keywords(["DECISION: POLISH", "DECISION: END"])

    graph_builder = StateGraph(State)

    graph_builder.add_node("concluder_tools_node", concluder_tools_node)
    graph_builder.add_node("clear_state", clear_state)
    graph_builder.add_node("write_introduction", write_introduction_node)
    graph_builder.add_node("write_related_node", write_related_node)
    graph_builder.add_node("write_methods_node", write_methods_node)
    graph_builder.add_node("write_experiments_node", write_experiments_node)
    graph_builder.add_node("validator_node", validator_node)
    graph_builder.add_node("conclude_chatbot", conclude_chatbot)
    graph_builder.add_node("router_chatbot", router_chatbot)
    graph_builder.add_node("collect_result_files", collect_result_files)

    graph_builder.add_edge(START, "clear_state")
    graph_builder.add_edge("clear_state", "collect_result_files")
    graph_builder.add_edge("collect_result_files", "write_introduction")
    graph_builder.add_edge("write_introduction", "write_related_node")
    graph_builder.add_edge("write_related_node", "write_methods_node")
    graph_builder.add_edge("write_methods_node", "write_experiments_node")
    graph_builder.add_edge("write_experiments_node", "validator_node")
    # graph_builder.add_edge(START, "validator_node")
    graph_builder.add_edge("validator_node", "conclude_chatbot")
    graph_builder.add_edge("conclude_chatbot", "concluder_tools_node")
    graph_builder.add_conditional_edges("concluder_tools_node", write_plan_router, {"RETURN_TO_LLM": "conclude_chatbot", END: "router_chatbot"})
    graph_builder.add_conditional_edges(
        "router_chatbot",
        keywords_router,
        {
            "DECISION: POLISH": "write_introduction",
            "DECISION: END": END,
            "NONE": "router_chatbot",
        },
    )

    graph = graph_builder.compile()

    return graph



if __name__ == "__main__":
    config, state, last_subgraph = load_state("outputs/code_paper_success_format_wrong/pred_aki_dy_mimic_icu_csv")
    graph = build_latex_writer(config)

    graph.invoke(state)
