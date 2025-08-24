import os
import glob
import dotenv
from typing import List

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.load.dump import dumps
from langchain_core.messages import ToolMessage

from ..tools.tool_utils import BasicToolNode
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State, load_state
from ..utils.config import Config

dotenv.load_dotenv()


with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_abstract_intro.md")) as f:
    introduction_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_related_works.md")) as f:
    related_works_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_methods.md")) as f:
    methods_prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_experiments.md")) as f:
    exp_conclusion_prompt = f.read()


def build_latex_writer(config: Config) -> StateGraph:
    llm = init_chat_model(
        os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", ""),
        model_provider="openai",
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    
    code_tool = OpenHandsTool(config)
    report_writer_tool = ReportWriterTool(config)
    
    tools = [report_writer_tool]
    llm_with_tools = llm.bind_tools(tools)

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
       
    tools_node = BasicToolNode(tools, config)

    graph_builder = StateGraph(State)

    graph_builder.add_node("clear_state", clear_state)
    graph_builder.add_node("write_introduction", write_introduction_node)
    graph_builder.add_node("write_related_node", write_related_node)
    graph_builder.add_node("write_methods_node", write_methods_node)
    graph_builder.add_node("write_experiments_node", write_experiments_node)

    graph_builder.add_edge(START, "clear_state")
    graph_builder.add_edge("clear_state", "write_introduction")
    graph_builder.add_edge("write_introduction", "write_related_node")
    graph_builder.add_edge("write_related_node", "write_methods_node")
    graph_builder.add_edge("write_methods_node", "write_experiments_node")
    graph_builder.add_edge("write_experiments_node", END)

    graph = graph_builder.compile()

    return graph



if __name__ == "__main__":
    config, state, last_subgraph = load_state("outputs/OL_20250823132617_What_is_the_pre_istorical_data__dzdzzd_126_com_1276")
    graph = build_latex_writer(config)

    graph.invoke(state)
