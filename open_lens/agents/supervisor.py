import os
import json
from typing import Annotated
from typing_extensions import TypedDict
import dotenv
from IPython.display import Image, display

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_tool_call, route_by_file_existence
from ..tools.exp_plan import PlanWriterTool, PlanReaderTool
from ..tools.reports import ReportReaderTool
from ..state import State, load_state
from ..chatbot import chatbot_with_context_manager

dotenv.load_dotenv()


with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "supervisor_plan.md")) as f:
    prompt = f.read()

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "supervisor_alter_plan.md")) as f:
    alter_prompt = f.read()

def build_supervisor(config: dict) -> StateGraph:
    search_tool = TavilySearch(max_results=5, search_depth="advanced")
    plan_writer_tool = PlanWriterTool(config)
    plan_reader_tool = PlanReaderTool(config)
    tools = [plan_writer_tool]
    
    route_supervisor = route_by_file_existence(os.path.join(config["save_path"], "plan.md"))
    
    def plan_reader_node(state: State):
        plan = plan_reader_tool.invoke({})
        state["plan"] = plan
        state["current_subtask_index"] = 0
        return state

    llm = init_chat_model(
        os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", ""),
        model_provider="openai",
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    llm_with_tools = llm.bind_tools(tools)
    chatbot = chatbot_with_context_manager(config, llm_with_tools, prompt)
    alter_chatbot = chatbot_with_context_manager(config, llm_with_tools, alter_prompt)
    
    route_by_write_plan = route_by_tool_call("plan_writer_tool")

    # def chatbot(state: State):
    #     this_prompt = prompt.format(question=state["question"])
    #     state["messages"].append({"role": "user", "content": this_prompt})
    #     max_context = int(os.environ.get("MAX_CONTEXT", 10))
    #     state["messages"] = [thinking_llm_with_tools.invoke(state["messages"][-max_context:])]
    #     return state

    graph_builder = StateGraph(State)

    tool_node = BasicToolNode(tools, config)
    graph_builder.add_node("supervisor_chatbot", chatbot)
    graph_builder.add_node("supervisor_alter_chatbot", alter_chatbot)
    graph_builder.add_node("supervisor_tools", tool_node)
    graph_builder.add_node("plan_reader_node", plan_reader_node)

    graph_builder.add_conditional_edges(START, route_supervisor, {"FILE_NOT_FOUND": "supervisor_chatbot", "FILE_EXISTS": "plan_reader_node"})
    graph_builder.add_edge("plan_reader_node", "supervisor_alter_chatbot")
    graph_builder.add_edge("supervisor_chatbot", "supervisor_tools")
    graph_builder.add_edge("supervisor_alter_chatbot", "supervisor_tools")
    graph_builder.add_conditional_edges("supervisor_tools", route_by_write_plan, {"RETURN_TO_LLM": "supervisor_chatbot", END: END})

    graph = graph_builder.compile()

    return graph



if __name__ == "__main__":
    config, state, last_subgraph = load_state("outputs/Agentmed_20250818093400_What_is_the_prediction_precision_of_AKI_based_on_h")
    graph = build_supervisor(config)

    graph.invoke(state)
