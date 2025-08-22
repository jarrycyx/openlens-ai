import os
import json
import dotenv
from IPython.display import Image, display

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.load.dump import dumps
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import ToolMessage

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_keywords, route_by_tool_call
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.exp_plan import PlanReaderTool, PlanWriterTool, subtask_route_tools
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State, load_state, get_subplan
from ..chatbot import chatbot_with_context_manager
from ..utils.config import Config

dotenv.load_dotenv()


with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "coder.md")) as f:
    prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "coder_validator.md")) as f:
    validator_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "coder_concluder.md")) as f:
    coder_concluder_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "coder_router.md")) as f:
    coder_router_prompt = f.read()


def build_coder(config: Config) -> StateGraph:
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
    code_tool = OpenHandsTool(config)
    plan_reader_tool = PlanReaderTool(config)
    report_writer_tool = ReportWriterTool(config)
    concluder_tools = [report_writer_tool]
    concluder_llm_with_tools = concluder_llm.bind_tools(concluder_tools)

    def openhands_coding_node(state: State):
        subplan = get_subplan(state)
        this_prompt = prompt.format(question=state["question"], subplan=subplan)
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state

    def openhands_validation_node(state: State):
        subplan = get_subplan(state)
        this_prompt = validator_prompt.format(question=state["question"], subplan=subplan)
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] = [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state

    def plan_reader_node(state: State):
        plan = plan_reader_tool.invoke({})
        state["plan"] = plan
        state["current_subtask_index"] = 0
        return state

    def subtask_continue_node(state: State):
        state["current_subtask_index"] = state.get("current_subtask_index", -1) + 1
        return state

    def subtask_return_node(state: State):
        return state

    concluder_tools_node = BasicToolNode(concluder_tools, config)
    conclude_openhands_chatbot = chatbot_with_context_manager(config, concluder_llm_with_tools, coder_concluder_prompt, context_manage="last_tool_message")
    route_chatbot = chatbot_with_context_manager(config, router_llm, coder_router_prompt, context_manage="last_tool_message")
    write_plan_router = route_by_tool_call("report_writer_tool")
    keywords_router = route_by_keywords(["DECISION: CONTINUE_NEXT_SUBTASK", "DECISION: RETURN_TO_LAST_SUBTASK", "DECISION: ALTER_PLAN"])

    graph_builder = StateGraph(State)

    graph_builder.add_node("coder_openhands", openhands_coding_node)
    graph_builder.add_node("validation_openhands", openhands_validation_node)
    graph_builder.add_node("conclude_openhands_chatbot", conclude_openhands_chatbot)
    graph_builder.add_node("route_chatbot", route_chatbot)
    graph_builder.add_node("subtask_continue", subtask_continue_node)
    graph_builder.add_node("subtask_return", subtask_return_node)
    graph_builder.add_node("read_plan", plan_reader_node)
    graph_builder.add_node("concluder_tool_node", concluder_tools_node)

    graph_builder.add_edge(START, "read_plan")
    graph_builder.add_edge("read_plan", "coder_openhands")
    graph_builder.add_edge("coder_openhands", "validation_openhands")
    graph_builder.add_edge("validation_openhands", "conclude_openhands_chatbot")
    graph_builder.add_edge("conclude_openhands_chatbot", "concluder_tool_node")
    graph_builder.add_conditional_edges("concluder_tool_node", write_plan_router, {"RETURN_TO_LLM": "conclude_openhands_chatbot", END: "route_chatbot"})
    graph_builder.add_conditional_edges(
        "route_chatbot",
        keywords_router,
        {
            "DECISION: CONTINUE_NEXT_SUBTASK": "subtask_continue",
            "DECISION: RETURN_TO_LAST_SUBTASK": "subtask_return",
            "DECISION: ALTER_PLAN": END,
            "NONE": "route_chatbot",
        },
    )
    graph_builder.add_conditional_edges("subtask_continue", subtask_route_tools, {"NEXT_TASK": "coder_openhands", END: END})
    graph_builder.add_edge("subtask_return", "coder_openhands")

    graph = graph_builder.compile()

    return graph


if __name__ == "__main__":
    config, state, last_subgraph = load_state("outputs/OL_20250822143511_What_is_the_pre_istorical_data__dzdzzd_126_com_2125_2_resume_20250822154505")
    graph = build_coder(config)

    graph.invoke(state)
