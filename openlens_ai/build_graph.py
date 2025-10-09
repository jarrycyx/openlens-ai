import os, sys
import json
import dotenv
import asyncio
import traceback
import argparse  # 新增argparse模块
from datetime import datetime
import threading
import re
import random

dotenv.load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.load.dump import dumps
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

# pip install langgraph-checkpoint-sqlite pysqlite3

from loguru import logger

from .utils.file_utils import prepare_file_config, collect_files
from .utils.send_email import send_email
from .tools.tool_utils import BasicToolNode, route_tools, route_by_keywords
from .tools.openhands_adaptor import OpenHandsTool
from .agents.supervisor import build_supervisor
from .agents.coder import build_coder
from .agents.data_analyzer import build_data_analyzer
from .agents.literature_reviewer import build_literature_review_subgraph
from .agents.latex_writer import build_latex_writer
from .state import State, load_state  # 从state模块导入load_state函数
from .utils.frontend_utils import frontend_add_message, frontend_add_tool_call, frontend_update_node
from .utils.config import Config

graph = None
stop_sending_emails = threading.Event()
all_subgraphs = ["literature_reviewer", "data_analyzer", "supervisor", "coder", "latex_writer"]


def send_periodic_emails(config: Config):
    """每60分钟发送一次进度邮件"""
    logger.info("Starting to send periodic emails...")
    while not stop_sending_emails.wait(18000):  # 600秒 = 10分钟
        try:
            zipfile, latest_md = collect_files(config)
            send_email(
                subject=f"OpenLens Job Progress | {config.thread_id}",
                content=f"Job is still running. Current progress:\n\n{latest_md}",
                recipients=config.email,
                attachments=zipfile,
            )
        except Exception as e:
            logger.error(f"Error sending periodic email: {e}")

def build_graph(config: Config, start_subgraph: str = None):
    try:
        graph_builder = StateGraph(State)

        keywords_router = route_by_keywords(["DECISION: ALTER_PLAN", "DECISION: REANALYZE_DATA"])

        supervisor_subgraph = build_supervisor(config)
        coder_subgraph = build_coder(config)
        data_analyzer_subgraph = build_data_analyzer(config)
        literature_review_subgraph = build_literature_review_subgraph(config)
        latex_writer_subgraph = build_latex_writer(config)
        
        graph_builder.add_node("supervisor", supervisor_subgraph)
        graph_builder.add_node("coder", coder_subgraph)
        graph_builder.add_node("data_analyzer", data_analyzer_subgraph)
        graph_builder.add_node("literature_reviewer", literature_review_subgraph)
        graph_builder.add_node("latex_writer", latex_writer_subgraph)

        
        if start_subgraph and (start_subgraph in all_subgraphs):
            graph_builder.add_edge(START, start_subgraph)
        else:
            graph_builder.add_edge(START, "literature_reviewer")
        graph_builder.add_edge("literature_reviewer", "data_analyzer")
        # graph_builder.add_edge(START, "data_analyzer")
        graph_builder.add_edge("data_analyzer", "supervisor")
        graph_builder.add_edge("supervisor", "coder")
        graph_builder.add_conditional_edges(
            "coder",
            keywords_router,
            {"DECISION: ALTER_PLAN": "supervisor", "DECISION: REANALYZE_DATA": "data_analyzer", "NONE": "latex_writer"},
        )
        graph_builder.add_edge("latex_writer", END)

        graph = graph_builder.compile()

        try:
            with open(os.path.join(config.save_path, "graph_mermaid.txt"), "w") as f:
                f.write(graph.get_graph(xray=True).draw_mermaid())
                
            try:
                graph_image = graph.get_graph(xray=True).draw_mermaid_png()
            except Exception as e:
                error_info = traceback.format_exc()
                logger.info(f'Failed to build mermaid graph: {e}')
                graph_image = graph.get_graph(xray=True).draw_png()
            # 保存
            with open(os.path.join(config.save_path, "overall_graph_image.png"), "wb") as f:
                f.write(graph_image)
            # with open(os.path.join(config.save_path, "workspace", "graph_mermaid.txt"), "w") as f:
            #     f.write(graph.get_graph(xray=True).draw_mermaid())
        except Exception as e:
            error_info = traceback.format_exc()
            frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
            logger.info(f'Failed to build graph: {e}')
            logger.info(error_info)
        return graph
    except Exception as e:
        error_info = traceback.format_exc()
        frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
        logger.info(f'Failed to build graph: {e}')
        logger.info(error_info)
        send_email(
            subject=f"OpenLens Job Failed | {config.thread_id}",
            content=f"Failed to run build: {e}\n{error_info}",
            recipients=config.email,
            attachments=None,
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
    for (a, b) in graph.builder.edges:
        if a == this_node_name:
            return b
        
def get_last_node(graph: CompiledStateGraph, this_node_name: str):
    for (a, b) in graph.builder.edges:
        if a == this_node_name:
            return b


def run_graph(config: Config, graph: CompiledStateGraph, save_path: str, init_state: State):
    logger.info(f"Main process is running with PID {os.getpid()}")
    
    # 启动定期发送邮件的线程
    email_thread = threading.Thread(target=send_periodic_emails, args=(config,), daemon=True)
    email_thread.start()
    
    try:
        
        step_i = 0
        # 先尝试在state目录下加载state，这个是每个subgraph保存一次
        state_dir = os.path.join(save_path, "states")
        # 遍历里面的文件，格式是step_i.json，找最大的
        file_names = os.listdir(state_dir)
        if file_names:
            file_indices = [int(file_name.split("_")[1]) for file_name in file_names if file_name.endswith(".json")]
            max_index = max(file_indices)
            logger.info(f"State from step {max_index}")
            step_i = 0
        for event in graph.stream(init_state, {"recursion_limit": 100}):
            # event: [("...", "..."), {}]
            if len(list(event.keys())) > 0:
                state_name = list(event.keys())[0]
                frontend_update_node(state_name, config)
                step_i += 1
                with open(os.path.join(save_path, "states", f"step_{step_i:04d}_{state_name}.json"), "w") as f:
                    json_str = dumps(event, ensure_ascii=False, indent=4)
                    f.write(json_str)
                
                # 发送进度邮件
                try:
                    zipfile, latest_md = collect_files(config)
                except Exception as e:
                    error_info = traceback.format_exc()
                    logger.error(f"Failed to collect files: {e}")
                    logger.info(error_info)
                    zipfile, latest_md = None, ""
                send_email(
                    subject=f"OpenLens Job Update | {config.thread_id}",
                    content=f"Subgraph {state_name} complete.\n\n{latest_md}",
                    recipients=config.email,
                    attachments=zipfile,
                )
    except Exception as e:
        error_info = traceback.format_exc()
        frontend_add_message(AIMessage(content=f"Error: {e}\n{error_info}"), config)
        logger.info(f'Failed to run graph: {e}')
        logger.info(error_info)
        try:
            zipfile, latest_md = collect_files(config)
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Failed to collect files: {e}")
            logger.info(error_info)
            zipfile, latest_md = None, ""
        send_email(
            subject=f"OpenLens Job Failed | {config.thread_id}",
            content=f"Failed to run graph: {e}\n{error_info}\n\n{latest_md}",
            recipients=config.email,
            attachments=zipfile,
        )
        stop_sending_emails.set()
        email_thread.join(timeout=5)
        sys.exit(0)
    finally:
        # 停止定期发送邮件
        send_email(
            subject=f"OpenLens Job Successful | {config.thread_id}",
            content=f"All subgraphs completed successfully.\n\n{latest_md}",
            recipients=config.email,
            attachments=zipfile,
        )
        stop_sending_emails.set()
        email_thread.join(timeout=5)
        sys.exit(0)


def main(question=None, dataset_path=None, thread_id=None, email=""):  # 新的执行_流程
    init_state, config, save_path = prepare_file_config(thread_id, question, dataset_path, email)
    global graph
    graph = build_graph(config, None)
    # 发送进度邮件
    send_email(
        subject=f"OpenLens Job Started | {config.thread_id}",
        content=f"## Question\n{config.question}\n\n## Dataset\n{config.dataset_path}\n\nThe job can take a while (any time from 30 minutes to several hours) to complete. Will keep you updated with the progress.",
        recipients=config.email,
        attachments=None,
    )
    run_graph(config, graph, save_path, init_state)
    
def main_resume(save_dir: str):
    config, state, last_subgraph, new_save_dir = load_state(save_dir)
    if last_subgraph:
        logger.info(f"Last completed subgraph: {last_subgraph}")
        last_subgraph_index = all_subgraphs.index(last_subgraph)
    else:
        last_subgraph_index = -1
    if last_subgraph_index == len(all_subgraphs) - 1:
        logger.info("No more subgraphs to run.")
        return
    else:                
        try:
            zipfile, latest_md = collect_files(config)
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Failed to collect files: {e}")
            logger.info(error_info)
            zipfile, latest_md = None, ""
        # 发送进度邮件
        send_email(
            subject=f"OpenLens Job Resumed | {config.thread_id}",
            content=latest_md,
            recipients=config.email,
            attachments=zipfile,
        )
        start_from = all_subgraphs[last_subgraph_index + 1]
        logger.info(f"Resuming from subgraph {start_from}")
        graph = build_graph(config, start_from)
        run_graph(config, graph, new_save_dir, state)
    



def parse_args():
    parser = argparse.ArgumentParser(description="Run the agent-med graph workflow")
    parser.add_argument("--question", type=str, help="The research question to investigate")
    parser.add_argument("--dataset-path", type=str, help="Path to the dataset")
    parser.add_argument("--thread-id", type=str, help="Thread ID for the run")
    parser.add_argument("--email", type=str, help="Email address for notifications", default="")
    parser.add_argument("--api-key", type=str, help="API key for the chat model")
    parser.add_argument("--chat-model", type=str, help="Chat model to use")
    parser.add_argument("--base-url", type=str, help="Base URL for the chat model")
    parser.add_argument("--code-model", type=str, help="Code model to use")
    parser.add_argument("--vision-model", type=str, help="Vision model to use")
    
    parser.add_argument("--resume-from", type=str, help="Resume from a specific saved directory")

    return parser.parse_args()

def cli_main():
    args = parse_args()

    # Set environment variables if provided
    if args.api_key:
        logger.info(f"Setting OPENAI_API_KEY environment variable to {args.api_key}")
        os.environ["OPENAI_API_KEY"] = args.api_key
    if args.chat_model:
        logger.info(f"Setting MODEL environment variable to {args.chat_model}")
        os.environ["MODEL"] = args.chat_model
    if args.base_url:
        logger.info(f"Setting BASE_URL environment variable to {args.base_url}")
        os.environ["BASE_URL"] = args.base_url
    if args.code_model:
        logger.info(f"Setting CODE_MODEL environment variable to {args.code_model}")
        os.environ["CODE_MODEL"] = args.code_model
    if args.vision_model:
        logger.info(f"Setting VISION_MODEL environment variable to {args.vision_model}")
        os.environ["VISION_MODEL"] = args.vision_model

    
    if args.resume_from:
        logger.info(f"Resuming from {args.resume_from}")
        main_resume(args.resume_from)
    else: 
        if not args.question or not args.dataset_path or not args.thread_id:
            logger.error("Please provide a question, dataset path, and thread ID.")
            # # 使用默认值
            # question = "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?"
            # dataset_path = "datasets/eicu"
            # email = "dzdzzd@126.com"
            # # 使用当前日期    
            # question_show = re.sub(r'[^\w]', '_', question.strip())
            # thread_id = "OL_" + datetime.now().strftime("%Y%m%d%H%M%S") + \
            #     f"_{question_show[:15]}" + f"_{question_show[-15:]}" + \
            #         "_" + email.replace("@", "_").replace(".", "_") + "_" + \
            #         str(random.randint(1000, 9999))
        else:
            question = args.question
            dataset_path = args.dataset_path
            thread_id = args.thread_id
            email = args.email

        # main(question, dataset_path, thread_id)
        main(question, dataset_path, thread_id, email)
    
    

if __name__ == "__main__":
    cli_main()