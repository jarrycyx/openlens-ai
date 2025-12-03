import os
import json
from typing import Annotated
from typing_extensions import TypedDict


from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch

from file1agent.file_manager import FileManager

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_tool_call, route_by_file_existence
from ..tools.exp_plan import PlanWriterTool, PlanReaderTool
from ..tools.reports import ReportReaderTool
from ..state import State, load_state, track_node_call
from ..chatbot import chatbot_with_context_manager
from ..utils.config import Config




# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, 'domain') and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()

# Initialize prompts as None, will be loaded in build_supervisor function
prompt = None
alter_prompt = None

def build_supervisor(config: Config, file_manager: FileManager) -> StateGraph:
    # Load prompts based on domain configuration
    global prompt, alter_prompt
    prompt = load_prompt_file(config, "supervisor_plan.md")
    alter_prompt = load_prompt_file(config, "supervisor_alter_plan.md")
    
    search_tool = TavilySearch(max_results=5, search_depth="advanced")
    plan_writer_tool = PlanWriterTool(config)
    plan_reader_tool = PlanReaderTool(config)
    tools = [plan_writer_tool]
    
    route_supervisor = route_by_file_existence(os.path.join(config.save_path, "plan.md"))
    
    def plan_reader_node(state: State):
        plan = plan_reader_tool.invoke({})
        state["plan"] = plan
        state["current_subtask_index"] = 1
        return state

    llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    llm_with_tools = llm.bind_tools(tools)
    chatbot = chatbot_with_context_manager(config, llm_with_tools, prompt, calling_subgraph="supervisor")
    alter_chatbot = chatbot_with_context_manager(config, llm_with_tools, alter_prompt, calling_subgraph="supervisor")
    
    route_by_write_plan = route_by_tool_call("plan_writer_tool")

    # def chatbot(state: State):
    #     this_prompt = prompt.format(question=state["question"])
    #     state["messages"].append({"role": "user", "content": this_prompt})
    #     max_context = int(config.max_context) if hasattr(config, 'max_context') else 10
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
    config, state, last_subgraph, file_manager = load_state("outputs/OL_20250826181001_What_is_the_pre_istorical_data__dzdzzd_126_com_6373")
    graph = build_supervisor(config, file_manager)

    graph.invoke(state)
