import os
import json
import dotenv
import shutil
from loguru import logger
import traceback

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from ..tools.tool_utils import BasicToolNode, route_tools, route_by_keywords, route_by_tool_call, route_by_subtask_redo_counter
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.exp_plan import PlanReaderTool, PlanWriterTool, subtask_route_tools
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State, load_state, get_subplan, track_node_call
from ..chatbot import chatbot_with_context_manager
from ..utils.config import Config
from ..utils.vision_feedback import collect_fig_files, get_fig_base64, get_vision_feedback

dotenv.load_dotenv()

fig_files_extensions = [".png", ".jpg", ".jpeg", ".pdf", ".svg"]

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

    @track_node_call("coder")
    def openhands_coding_node(state: State):
        subplan = get_subplan(state)
        this_prompt = prompt.format(question=state["question"], subplan=subplan)
        
        ai_message = [m for m in state["messages"] if isinstance(m, AIMessage)]
        if len(ai_message) > 0 and "REASON:" in ai_message[-1].content:
            logger.info("Detected REASON in the last tool message, add to the prompt.")
            reason = ai_message[-1].content
            this_prompt = this_prompt + "\n\n Last Failure Reasons: " + reason
        else:
            logger.info("No REASON in the AI tool message, use the default prompt.")
            reason = ""
            
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

    @track_node_call("coder")
    def openhands_validation_node(state: State):
        subplan = get_subplan(state)
        this_prompt = validator_prompt.format(question=state["question"], subplan=subplan)
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] += [
            # ToolMessage(
            #     content=results,
            #     name="openhands_tool",
            #     tool_call_id="openhands_tool",
            # ), # Commenting out the ToolMessage because this tool is manually invoked and may cause issues, use HumanMessage instead.
            HumanMessage(content=results)
        ]
        
        ## Check for generated images using vision-language model
        current_subtask_i = state["current_subtask_index"]
        subtask_dir = os.path.join(config.save_path, "workspace", f"subtask_{current_subtask_i:02d}")
        fig_file_list = collect_fig_files(config, base_dir=subtask_dir)
        fig_base64_list = get_fig_base64(fig_file_list)
        workspace_dir = os.path.join(config.save_path, "workspace")
        all_feedback = ""
        for fig, base64str in fig_base64_list:
            fig_rel_path = os.path.relpath(fig, workspace_dir)
            try:
                vlm_response = get_vision_feedback(base64str, config)
                if "DECISION: ACCEPT" in vlm_response:
                    logger.info(f"Image {fig_rel_path} is accepted by VLM.")
                    continue
                elif "DECISION: IMPROVE" in vlm_response:
                    all_feedback += f"Image {fig_rel_path} feedback: {vlm_response}\n"
                    logger.info(f"Image {fig_rel_path} is rejected by VLM, will try to improve it.")
                
            except Exception as e:
                logger.warning(f"Failed to evaluate image: {e}")
                logger.warning(traceback.format_exc())
            
        if not all_feedback:
            logger.info("No image feedback, will skip image improvement.")
            return state   
        this_prompt = f"Based on the following vision feedback, please modify the python code to improve the experiments. " + \
            f"Vision feedback: " + all_feedback
        code_tool.invoke({"prompts": [this_prompt]})
            
        
        return state

    @track_node_call("coder")
    def plan_reader_node(state: State):
        plan = plan_reader_tool.invoke({})
        state["plan"] = plan
        state["current_subtask_index"] = 1
        return state

    @track_node_call("coder")
    def subtask_continue_node(state: State):
        state["current_subtask_index"] = state.get("current_subtask_index", 0) + 1
        state["return_subtask_counter"] = 0
        return state

    @track_node_call("coder")
    def subtask_restart_node(state: State):
        state["return_subtask_counter"] = state.get("return_subtask_counter", 0) + 1
        current_subtask_i = state["current_subtask_index"]
        try:
            subtask_dir = os.path.join(config.save_path, "workspace", f"subtask_{current_subtask_i:02d}")
            if os.path.exists(subtask_dir):
                logger.info(f"Removing dir {subtask_dir}")
                shutil.rmtree(subtask_dir)
            else:
                logger.info(f"Dir {subtask_dir} does not exist.")
        except Exception as e:
            logger.warning(f"Failed to remove dir {subtask_dir}: {e}")
        logger.info(f"Removed dir subtask_{current_subtask_i:02d} for re-doing the subtask.")
        return state
    
    @track_node_call("coder")
    def subtask_fix_node(state: State):
        state["return_subtask_counter"] = state.get("return_subtask_counter", 0) + 1
        # Just keep the current_subtask_index unchanged
        return state

    concluder_tools_node = BasicToolNode(concluder_tools, config)
    conclude_openhands_chatbot = chatbot_with_context_manager(config, concluder_llm_with_tools, coder_concluder_prompt, context_manage="token_cnt", calling_subgraph="coder")
    route_chatbot = chatbot_with_context_manager(config, router_llm, coder_router_prompt, context_manage="token_cnt", calling_subgraph="coder")
    write_plan_router = route_by_tool_call("report_writer_tool")
    keywords_router = route_by_keywords([
        "DECISION: CONTINUE_NEXT_SUBTASK", 
        "DECISION: REDO_LAST_SUBTASK", 
        "DECISION: FIX_LAST_SUBTASK",
        "DECISION: ALTER_PLAN"])

    graph_builder = StateGraph(State)

    graph_builder.add_node("coder_openhands", openhands_coding_node)
    graph_builder.add_node("validation_openhands", openhands_validation_node)
    graph_builder.add_node("conclude_openhands_chatbot", conclude_openhands_chatbot)
    graph_builder.add_node("route_chatbot", route_chatbot)
    graph_builder.add_node("subtask_continue", subtask_continue_node)
    graph_builder.add_node("subtask_restart", subtask_restart_node)
    graph_builder.add_node("subtask_fix", subtask_fix_node)
    graph_builder.add_node("read_plan", plan_reader_node)
    graph_builder.add_node("concluder_tool_node", concluder_tools_node)

    graph_builder.add_edge(START, "read_plan")
    graph_builder.add_edge("read_plan", "coder_openhands")
    graph_builder.add_edge("coder_openhands", "validation_openhands")
    graph_builder.add_conditional_edges(
        "validation_openhands",
        route_by_subtask_redo_counter,
        {"MAX_REDO_REACHED": "subtask_continue", "NOT_REACHED": "conclude_openhands_chatbot"},
    )
    graph_builder.add_edge("conclude_openhands_chatbot", "concluder_tool_node")
    graph_builder.add_conditional_edges("concluder_tool_node", write_plan_router, {"RETURN_TO_LLM": "conclude_openhands_chatbot", END: "route_chatbot"})
    graph_builder.add_conditional_edges(
        "route_chatbot",
        keywords_router,
        {
            "DECISION: CONTINUE_NEXT_SUBTASK": "subtask_continue",
            "DECISION: REDO_LAST_SUBTASK": "subtask_restart",
            "DECISION: FIX_LAST_SUBTASK": "subtask_fix",
            "DECISION: ALTER_PLAN": END,
            "NONE": "route_chatbot",
        },
    )
    graph_builder.add_conditional_edges("subtask_continue", subtask_route_tools, {"NEXT_TASK": "coder_openhands", END: END})
    graph_builder.add_edge("subtask_restart", "coder_openhands")
    graph_builder.add_edge("subtask_fix", "coder_openhands")

    graph = graph_builder.compile()

    return graph


if __name__ == "__main__":
    config, state, last_subgraph, new_save_dir = load_state("outputs/pred_aki_dy_mimic_icu_csv")
    graph = build_coder(config)

    graph.invoke(state, {"recursion_limit": 100})
