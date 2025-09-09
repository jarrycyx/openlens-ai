import os
import glob
import dotenv
from typing import List
from loguru import logger
import traceback

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.load.dump import dumps
from langchain_core.messages import ToolMessage, AIMessage

from ..tools.tool_utils import BasicToolNode, route_by_tool_call, route_by_keywords, route_by_latex_polish_counter
from ..tools.openhands_adaptor import OpenHandsTool
from ..tools.reports import ReportReaderTool, ReportWriterTool
from ..state import State, load_state, track_node_call
from ..utils.config import Config
from ..chatbot import chatbot_with_context_manager
from ..utils.vision_feedback import collect_fig_files, get_fig_base64, get_vision_feedback, get_vision_classification, get_latex_vision_feedback

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
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_rigor_prompt.md")) as f:
    latex_rigor_prompt = f.read()
with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "latex_literature_check.md")) as f:
    latex_literature_check_prompt = f.read()


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

    @track_node_call("latex_writer")
    def clear_state(state: State):
        state["polish_latex_counter"] = state.get("return_subtask_counter", 0)
        state["messages"] = []
        return state

    @track_node_call("latex_writer")
    def write_introduction_node(state: State):
        state["polish_latex_counter"] = state.get("return_subtask_counter", 0) + 1
        
        this_prompt = introduction_prompt.replace("{question}", state["question"])
        
        # 加入上一次的建议
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
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    @track_node_call("latex_writer")
    def write_related_node(state: State):
        this_prompt = related_works_prompt.replace("{question}", state["question"])
        
        # 加入上一次的建议
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
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    @track_node_call("latex_writer")
    def collect_result_files(state: State):
        
        ## Check for generated images using vision-language model
        fig_file_list = collect_fig_files(config)
        fig_base64_list = get_fig_base64(fig_file_list)
        workspace_dir = os.path.join(config.save_path, "workspace")
        all_feedback = ""
        available_fig_file_list = []
        figure_target_path = os.path.join(workspace_dir, "manuscript", "figures")
        os.makedirs(figure_target_path, exist_ok=True)
        for fig, base64str in fig_base64_list:
            fig_rel_path = os.path.relpath(fig, workspace_dir)
            try:
                vlm_response = get_vision_classification(base64str, config)
                if "DECISION: ACCEPT" in vlm_response:
                    # copy to manuscript/figures
                    logger.info(f"Image {fig_rel_path} is accepted by VLM.")
                    os.system(f"cp {fig} {figure_target_path}")
                    
                    # save to state for writing
                    docker_current_path = os.path.join("/workspace", "manuscript", "figures", os.path.basename(fig))
                    available_fig_file_list.append(docker_current_path)
                    
                    # write description for reference
                    host_current_path = os.path.join(figure_target_path, os.path.basename(fig))
                    current_path_ext = os.path.splitext(host_current_path)[1]
                    with open(host_current_path.replace(current_path_ext, "_description.txt"), "w") as f:
                        f.write(vlm_response)
                    continue
                elif "DECISION: REJECT" in vlm_response:
                    all_feedback += f"Image {fig_rel_path} feedback: {vlm_response}\n"
                    logger.info(f"Image {fig_rel_path} is rejected by VLM, will not include it.")
                
            except Exception as e:
                logger.warning(f"Failed to evaluate image: {e}")
                logger.warning(traceback.format_exc())
        state["available_figs"] = available_fig_file_list
        return state
        
    
    @track_node_call("latex_writer")
    def write_methods_node(state: State):
        this_prompt = methods_prompt.replace("{question}", state["question"])
        
        # 加入上一次的建议
        ai_message = [m for m in state["messages"] if isinstance(m, AIMessage)]
        if len(ai_message) > 0 and "REASON:" in ai_message[-1].content:
            logger.info("Detected REASON in the last tool message, add to the prompt.")
            reason = ai_message[-1].content
            this_prompt = this_prompt + "\n\n Last Failure Reasons: " + reason
        else:
            logger.info("No REASON in the AI tool message, use the default prompt.")
            reason = ""
        
        this_prompt = this_prompt.replace("{figures}", "\n".join(state["available_figs"]))
        results = code_tool.invoke({"prompts": [this_prompt]})
        state["messages"] += [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    @track_node_call("latex_writer")
    def write_experiments_node(state: State):
        this_prompt = exp_conclusion_prompt.replace("{question}", state["question"])
        this_prompt = this_prompt.replace("{figures}", "\n".join(state["available_figs"]))
        
        # 加入上一次的建议
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
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            )
        ]
        return state
    
    
    @track_node_call("latex_writer")
    def latex_validator_node(state: State):
        this_prompt = validator_prompt.replace("{question}", state["question"])
        this_prompt = this_prompt.replace("{figures}", "\n".join(state["available_figs"]))
        
        # 加入上一次的建议
        ai_message = [m for m in state["messages"] if isinstance(m, AIMessage)]
        if len(ai_message) > 0 and "REASON:" in ai_message[-1].content:
            logger.info("Detected REASON in the last tool message, add to the prompt.")
            reason = ai_message[-1].content
            this_prompt = this_prompt + "\n\n Last Failure Reasons: " + reason
        else:
            logger.info("No REASON in the AI tool message, use the default prompt.")
            reason = ""
        
        results = code_tool.invoke({"prompts": [this_prompt, latex_rigor_prompt, latex_literature_check_prompt]})
        
        state["messages"] += [
            ToolMessage(
                content=results,
                name="openhands_tool",
                tool_call_id="openhands_tool",
            ),
        ]
        
        
        ## Check for generated images using vision-language model
        workspace_dir = os.path.join(config.save_path, "workspace")
        fig_file_path = os.path.join(workspace_dir, "manuscript", "main.pdf")
        if os.path.exists(fig_file_path):
            fig_base64_list = get_fig_base64([fig_file_path])

            all_feedback = ""
            for fig, base64str in fig_base64_list:
                fig_rel_path = os.path.relpath(fig, workspace_dir)
                try:
                    vlm_response = get_latex_vision_feedback(base64str, config)
                    if "DECISION: ACCEPT" in vlm_response:
                        logger.info(f"Image {fig_rel_path} is accepted by VLM.")
                        continue
                    elif "DECISION: IMPROVE" in vlm_response:
                        all_feedback += f"Image {fig_rel_path} feedback: {vlm_response}\n"
                        logger.info(f"Image {fig_rel_path} is rejected by VLM, will try to improve it.")
                    
                except Exception as e:
                    logger.warning(f"Failed to evaluate image: {e}")
                    logger.warning(traceback.format_exc())
            this_prompt = f"Based on the following vision feedback, please modify the latex code to improve the pdf quality. " + \
                f"Vision feedback: " + all_feedback
            
            if not all_feedback:
                logger.info("No image feedback, will skip image improvement.")
                return state   
            code_tool.invoke({"prompts": [this_prompt]})
            
        return state
       
    concluder_tools_node = BasicToolNode(tools, config)
    conclude_chatbot = chatbot_with_context_manager(config, concluder_llm_with_tools, latex_concluder_prompt, calling_subgraph="latex_writer", context_manage="token_cnt")
    router_chatbot = chatbot_with_context_manager(config, router_llm, latex_router_prompt, calling_subgraph="latex_writer", context_manage="token_cnt")
    write_plan_router = route_by_tool_call("report_writer_tool")
    keywords_router = route_by_keywords(["DECISION: POLISH", "DECISION: END"])

    graph_builder = StateGraph(State)

    graph_builder.add_node("concluder_tools_node", concluder_tools_node)
    graph_builder.add_node("clear_state", clear_state)
    graph_builder.add_node("write_introduction", write_introduction_node)
    graph_builder.add_node("write_related_node", write_related_node)
    graph_builder.add_node("write_methods_node", write_methods_node)
    graph_builder.add_node("write_experiments_node", write_experiments_node)
    graph_builder.add_node("validator_node", latex_validator_node)
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
    
    graph_builder.add_conditional_edges(
        "validator_node",
        route_by_latex_polish_counter,
        {"MAX_REDO_REACHED": END, "NOT_REACHED": "conclude_chatbot"},
    )
    # graph_builder.add_edge("validator_node", "conclude_chatbot")
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
