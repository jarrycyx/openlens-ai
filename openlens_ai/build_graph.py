import os, sys

import traceback
import threading


from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain.load.dump import dumps
from langchain_core.messages import AIMessage

# pip install langgraph-checkpoint-sqlite pysqlite3

from loguru import logger

from file1agent.file_manager import FileManager

from .utils.file_utils import collect_files
from .utils.send_email import send_email, send_localized_email
from .tools.tool_utils import route_by_keywords
from .agents.supervisor import build_supervisor
from .agents.coder import build_coder
from .agents.data_analyzer import build_data_analyzer
from .agents.literature_reviewer import build_literature_review_subgraph
from .agents.latex_writer import build_latex_writer
from .state import State, load_state, track_node_call  # Import load_state function from state module
from .utils.frontend_messages import frontend_add_message, frontend_add_tool_call, frontend_update_node
from .utils.config import Config

graph = None
stop_sending_emails = threading.Event()
all_subgraphs = ["literature_reviewer", "data_analyzer", "supervisor", "coder", "latex_writer"]


def send_periodic_emails(config: Config):
    """Send progress emails every 60 minutes"""
    logger.info("Starting to send periodic emails...")

    cnt = 0
    while not stop_sending_emails.wait(600):
        # Update file compression package and token usage every 10 minutes
        try:
            zipfile, latest_md = collect_files(config)
            cnt += 1
            # Send email every 30*10 minutes
            if cnt % 30 == 0:
                send_localized_email(
                    config=config,
                    template_key="job_still_running",
                    recipients=config.notify_email,
                    attachments=zipfile,
                    latest_md=latest_md,
                )
                cnt = 0
        except Exception as e:
            logger.error(f"Error sending periodic email: {e}")


def build_graph(config: Config, start_subgraph: str = None, file_manager: FileManager = None):
    @track_node_call(subgraph_name="end")
    def end_node(state: State):
        state["status"] = "completed"
        return state

    try:

        graph_builder = StateGraph(State)

        keywords_router = route_by_keywords(["DECISION: ALTER_PLAN", "DECISION: REANALYZE_DATA"])

        supervisor_subgraph = build_supervisor(config, file_manager)
        coder_subgraph = build_coder(config, file_manager)
        data_analyzer_subgraph = build_data_analyzer(config, file_manager)
        literature_review_subgraph = build_literature_review_subgraph(config, file_manager)
        latex_writer_subgraph = build_latex_writer(config, file_manager)

        graph_builder.add_node("supervisor", supervisor_subgraph)
        graph_builder.add_node("coder", coder_subgraph)
        graph_builder.add_node("data_analyzer", data_analyzer_subgraph)
        graph_builder.add_node("literature_reviewer", literature_review_subgraph)
        graph_builder.add_node("latex_writer", latex_writer_subgraph)
        graph_builder.add_node("end", end_node)
        
        if (not config.workflow.enable_literature_review) and (start_subgraph == "literature_reviewer"):
            start_subgraph = "data_analyzer"
        

        if start_subgraph and (start_subgraph in all_subgraphs):
            graph_builder.add_edge(START, start_subgraph)
        else:
            graph_builder.add_edge(START, "literature_reviewer")
        graph_builder.add_edge("literature_reviewer", "data_analyzer")
        # graph_builder.add_edge(START, "data_analyzer")
        graph_builder.add_edge("data_analyzer", "supervisor")
        graph_builder.add_edge("supervisor", "coder")
        # graph_builder.add_conditional_edges(
        #     "coder",
        #     keywords_router,
        #     {"DECISION: ALTER_PLAN": "supervisor", "DECISION: REANALYZE_DATA": "data_analyzer", "NONE": "latex_writer"},
        # )
        if config.workflow.enable_latex_writer:
            graph_builder.add_edge("coder", "latex_writer")
            graph_builder.add_edge("latex_writer", "end")
        else:
            graph_builder.add_edge("coder", "end")
            
        graph_builder.add_edge("end", END)

        graph = graph_builder.compile()

        try:
            with open(os.path.join(config.save_path, "graph_mermaid.txt"), "w") as f:
                f.write(graph.get_graph(xray=True).draw_mermaid())

            try:
                graph_image = graph.get_graph(xray=True).draw_mermaid_png()
            except Exception as e:
                error_info = traceback.format_exc()
                logger.info(f"Failed to build mermaid graph: {e}")
                graph_image = graph.get_graph(xray=True).draw_png()
            # Save
            with open(os.path.join(config.save_path, "overall_graph_image.png"), "wb") as f:
                f.write(graph_image)
            # with open(os.path.join(config.save_path, "workspace", "graph_mermaid.txt"), "w") as f:
            #     f.write(graph.get_graph(xray=True).draw_mermaid())
        except Exception as e:
            error_info = traceback.format_exc()
            frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
            logger.info(f"Failed to build graph: {e}")
            logger.info(error_info)
        return graph
    except Exception as e:
        error_info = traceback.format_exc()
        frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
        logger.info(f"Failed to build graph: {e}")
        logger.info(error_info)
        send_localized_email(
            config=config,
            template_key="failed_to_build",
            recipients=config.notify_email,
            attachments=None,
            error=str(e),
            error_info=error_info,
        )


# async def arun_graph(graph, save_path, init_state):
#     step_i = 0
#     async for event in graph.astream(init_state):
#         step_i += 1
#         state_name = list(event.keys())[0]
#         with open(os.path.join(save_path, "states", f"step_{step_i}_{state_name}.json"), "w") as f:
#             json_str = dumps(event, ensure_ascii=False, indent=4)
#             f.write(json_str)


def get_next_node(graph: CompiledStateGraph, this_node_name: str):
    for a, b in graph.builder.edges:
        if a == this_node_name:
            return b


def get_last_node(graph: CompiledStateGraph, this_node_name: str):
    for a, b in graph.builder.edges:
        if a == this_node_name:
            return b


def run_graph(config: Config, graph: CompiledStateGraph, init_state: State, interrupt_after_subgraph="none"):
    logger.info(f"Main process is running with PID {os.getpid()}")

    # Start thread for sending periodic emails
    email_thread = threading.Thread(target=send_periodic_emails, args=(config,), daemon=True)
    email_thread.start()

    try:

        step_i = 0
        # First try to load state in the state directory, this is saved once for each subgraph
        state_dir = os.path.join(config.save_path, "states")
        # Traverse the files inside, format is step_i.json, find the largest
        file_names = os.listdir(state_dir)
        if file_names:
            file_indices = [int(file_name.split("_")[1]) for file_name in file_names if file_name.endswith(".json")]
            max_index = max(file_indices)
            logger.info(f"State from step {max_index}")
            step_i = max_index
        for event in graph.stream(init_state, {"recursion_limit": 100}):
            # event: [("...", "..."), {}]
            if len(list(event.keys())) > 0:
                state_name = list(event.keys())[0]
                frontend_update_node(state_name, config)
                step_i += 1

                if state_name == interrupt_after_subgraph:
                    logger.info(f"Interrupted after {state_name}")

                    try:
                        zipfile, latest_md = collect_files(config)
                    except Exception as e:
                        error_info = traceback.format_exc()
                        logger.error(f"Failed to collect files: {e}")
                        logger.info(error_info)
                        zipfile, latest_md = None, ""
                    send_localized_email(
                        config=config,
                        template_key="subgraph_paused",
                        recipients=config.notify_email,
                        attachments=zipfile,
                        state_name=state_name,
                        latest_md=latest_md,
                    )
                    # Do not send success email
                    return

                with open(os.path.join(config.save_path, "states", f"step_{step_i:04d}_{state_name}.json"), "w") as f:
                    json_str = dumps(event, ensure_ascii=False, indent=4)
                    f.write(json_str)
                # Send progress email
                try:
                    zipfile, latest_md = collect_files(config)
                except Exception as e:
                    error_info = traceback.format_exc()
                    logger.error(f"Failed to collect files: {e}")
                    logger.info(error_info)
                    zipfile, latest_md = None, ""
                send_localized_email(
                    config=config,
                    template_key="subgraph_complete",
                    recipients=config.notify_email,
                    attachments=zipfile,
                    state_name=state_name,
                    latest_md=latest_md,
                )
    except Exception as e:
        error_info = traceback.format_exc()
        frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
        logger.info(f"Failed to run graph: {e}")
        logger.info(error_info)
        try:
            zipfile, latest_md = collect_files(config)
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Failed to collect files: {e}")
            logger.info(error_info)
            zipfile, latest_md = None, ""
        send_localized_email(
            config=config,
            template_key="failed_to_run",
            recipients=config.notify_email,
            attachments=zipfile,
            error=str(e),
            error_info=error_info,
            latest_md=latest_md,
        )
        stop_sending_emails.set()
        email_thread.join(timeout=5)
        sys.exit(0)
    finally:
        # Stop sending periodic emails
        send_localized_email(
            config=config,
            template_key="job_complete",
            recipients=config.notify_email,
            attachments=zipfile,
            latest_md=latest_md,
        )
        stop_sending_emails.set()
        email_thread.join(timeout=5)
        sys.exit(0)
