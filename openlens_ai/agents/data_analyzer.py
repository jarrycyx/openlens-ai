import os
import json

import glob
from loguru import logger
import traceback

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_tool_call, route_by_file_existence, route_by_keywords
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State
from ..chatbot import chatbot_with_context_manager
from ..state import load_state, track_node_call
from ..utils.config import Config




# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, 'domain') and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()

# Initialize prompts as None, will be loaded in build_data_analyzer function
data_analyzer_prompt = None
data_report_prompt = None
data_router_prompt = None


execute_check_prompt = """
Now first examine if the code fulfills the following requirements and the code DOES NOT MOCK OR SIMULATE any results.
Then execute the generated code to make sure it works. Use the "python" command to execute the code, do not use virtual environments or anaconda, do not use any other commands.
At last checks if the results/outputs includes wrong codeces or unexpected/broken characters.
If the code fails, fix the code and try again.

Requirements:
{plan}

IMPORTANT: Unexpected/broken characters are typically chinese, korean, or japanese characters that do not make sense at all. Please fix the code and try again.
"""

def build_data_analyzer(config: Config) -> StateGraph:
    # Load prompts based on domain configuration
    global data_analyzer_prompt, data_report_prompt, data_router_prompt
    data_analyzer_prompt = load_prompt_file(config, "data_analyzer.md")
    data_report_prompt = load_prompt_file(config, "data_report.md")
    data_router_prompt = load_prompt_file(config, "data_router.md")
    
    llm = init_chat_model(config.llm.chat.model, 
                          base_url=config.llm.chat.base_url, 
                          model_provider="openai",
                                            openai_api_key=config.llm.chat.api_key,
                          extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    router_llm = init_chat_model(config.llm.chat.model,
                                 base_url=config.llm.chat.base_url,
                                 model_provider="openai",
                                                          openai_api_key=config.llm.chat.api_key,
                                 extra_body={"chat_template_kwargs": {"enable_thinking": True}})
    search_tool = TavilySearch(max_results=5, search_depth="advanced")
    code_tool = OpenHandsTool(config)
    report_writer_tool = ReportWriterTool(config, file_name="data_report.md")
    tools = [report_writer_tool]
    llm_with_tools = llm.bind_tools(tools)

    @track_node_call("data_analyzer")
    def openhands_node(state: State):
        this_prompt = data_analyzer_prompt.format(question=state["question"])
        
        router_messages = [m for m in state["messages"] if isinstance(m, AIMessage)]
        if router_messages:
            last_router_message = router_messages[-1]
            results = ""
            if "DECISION" in last_router_message.content:
                logger.info("Found previous router decision, adding to prompt. " + last_router_message.content)
                this_prompt += "\n\nPrevious coding results:\n" + last_router_message.content
                results = code_tool.invoke({"prompts": [this_prompt]})
            state["messages"] += [
                # ToolMessage(
                #     content=results,
                #     name="openhands_tool",
                #     tool_call_id="openhands_tool",
                # ), # Commenting out the ToolMessage because this tool is manually invoked and may cause issues, use HumanMessage instead.
                HumanMessage(content=results)
            ]
            return state
        
        results = code_tool.invoke({"prompts": [this_prompt, execute_check_prompt.format(plan=this_prompt)]})
        
        return state

    @track_node_call("data_analyzer")
    def chatbot(state: State):
        with open(os.path.join(state["save_path"], "workspace", "data_analyze", "data_show.md"), "r") as f:
            data_show = f.read()
        
        state["data_show"] = data_show
        this_chatbot = chatbot_with_context_manager(config, llm_with_tools, data_report_prompt, calling_subgraph="data_analyzer")
        state = this_chatbot(state)
        return state

    def router_node(state: State):
        router_chatbot = chatbot_with_context_manager(config, router_llm, data_router_prompt, context_manage="token_cnt_large", calling_subgraph="data_analyzer")
        state = router_chatbot(state)
        return state

    graph_builder = StateGraph(State)
    
    router_by_write_reports = route_by_tool_call("report_writer_tool")
    route_by_data_show = route_by_file_existence(os.path.join(config.save_path, "workspace", "data_analyze", "data_show.md"))
    keywords_router = route_by_keywords(["DECISION: CONTINUE", "DECISION: RETURN"])

    tool_node = BasicToolNode(tools, config)
    graph_builder.add_node("data_chatbot", chatbot)
    graph_builder.add_node("data_openhands_node", openhands_node)
    graph_builder.add_node("data_tools", tool_node)
    graph_builder.add_node("data_router", router_node)

    graph_builder.add_edge(START, "data_openhands_node")
    graph_builder.add_conditional_edges("data_openhands_node", route_by_data_show, {"FILE_NOT_FOUND": "data_openhands_node", "FILE_EXISTS": "data_chatbot"})
    graph_builder.add_edge("data_chatbot", "data_tools")
    graph_builder.add_conditional_edges("data_tools", router_by_write_reports, {"RETURN_TO_LLM": "data_chatbot", END: "data_router"})
    graph_builder.add_conditional_edges("data_router", keywords_router, {"DECISION: CONTINUE": END, "DECISION: RETURN": "data_openhands_node", "NONE": "data_router"})

    graph = graph_builder.compile()


    return graph


if __name__ == "__main__":
    config, state, last_subgraph, new_save_dir = load_state("outputs/pred_aki_dy_eicu_demo_20250903143709")
    graph = build_data_analyzer(config)

    graph.invoke(state)