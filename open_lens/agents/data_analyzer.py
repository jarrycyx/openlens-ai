import os
import json
import dotenv
from IPython.display import Image, display

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.load.dump import dumps
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_openai import ChatOpenAI

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_tool_call, route_by_file_existence
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State
from ..chatbot import chatbot_with_context_manager
from ..state import load_state
from ..utils.file_utils import prepare_file_config

dotenv.load_dotenv()


with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "data_analyzer.md")) as f:
    data_analyzer_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "data_report.md")) as f:
    data_report_prompt = f.read()


execute_check_prompt = """
Now first examine if the code fulfills the following requirements and the code DOES NOT MOCK OR SIMULATE any results.
Then execute the generated code to make sure it works. Use the "python" command to execute the code, do not use virtual environments or anaconda, do not use any other commands.
At last checks if the results/outputs includes wrong codeces or unexpected/broken characters.
If the code fails, fix the code and try again.

Requirements:
{plan}

IMPORTANT: Unexpected/broken characters are typically chinese, korean, or japanese characters that do not make sense at all. Please fix the code and try again.
"""

def build_data_analyzer(config: dict) -> StateGraph:
    llm = init_chat_model(os.environ.get("MODEL", "deepseek-chat"), 
                          base_url=os.environ.get("BASE_URL", ""), 
                          model_provider="openai",
                          extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    search_tool = TavilySearch(max_results=5, search_depth="advanced")
    code_tool = OpenHandsTool(config)
    report_writer_tool = ReportWriterTool(config, file_name="data_report.md")
    tools = [report_writer_tool]
    llm_with_tools = llm.bind_tools(tools)

    def openhands_node(state: State):
        this_prompt = data_analyzer_prompt.format(question=state["question"])
        results = code_tool.invoke({"prompts": [this_prompt, execute_check_prompt.format(plan=this_prompt)]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state

    def chatbot(state: State):
        with open(os.path.join(state["save_path"], "workspace", "data_analyze", "data_show.md"), "r") as f:
            data_show = f.read()
        state["data_show"] = data_show
        this_prompt = data_report_prompt.format(question=state["question"], data_show=data_show)
        this_chatbot = chatbot_with_context_manager(config, llm_with_tools, this_prompt)
        state = this_chatbot(state)
        return state

    graph_builder = StateGraph(State)
    
    router_by_write_reports = route_by_tool_call("report_writer_tool")
    route_by_data_show = route_by_file_existence(os.path.join(config["save_path"], "workspace", "data_analyze", "data_show.md"))

    tool_node = BasicToolNode(tools, config)
    graph_builder.add_node("data_chatbot", chatbot)
    graph_builder.add_node("data_openhands_node", openhands_node)
    graph_builder.add_node("data_tools", tool_node)

    graph_builder.add_edge(START, "data_openhands_node")
    graph_builder.add_conditional_edges("data_openhands_node", route_by_data_show, {"FILE_NOT_FOUND": "data_openhands_node", "FILE_EXISTS": "data_chatbot"})
    graph_builder.add_edge("data_chatbot", "data_tools")
    graph_builder.add_conditional_edges("data_tools", router_by_write_reports, {"RETURN_TO_LLM": "data_chatbot", END: END})

    graph = graph_builder.compile()


    return graph


if __name__ == "__main__":
    config, state, last_subgraph = load_state("outputs/OL_20250821162536_What_is_the_pre_istorical_data_7082")
    graph = build_data_analyzer(config)

    graph.invoke(state)
