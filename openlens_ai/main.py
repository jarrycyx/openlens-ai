import os, sys
import json

import traceback
import argparse  # 新增argparse模块
import re
from loguru import logger
from datetime import datetime
import random

from .utils.file_utils import prepare_files_folders, collect_files
from .utils.send_email import send_email
from .utils.config import Config
from .state import State, load_state  # 从state模块导入load_state函数
from .build_graph import build_graph, run_graph  # 从build_graph模块导入build_graph函数


def main(config: Config, interrupt_after="none"):  # 新的执行_流程
    init_state, config = prepare_files_folders(config)
    graph = build_graph(config, None)
    # 发送进度邮件
    send_email(
        config=config,
        subject=f"OpenLens Job Started | {config.thread_id}",
        content=f"## Question\n{config.question}\n\n## Dataset\n{config.dataset_path}\n\nThe job can take a while (any time from 30 minutes to several hours) to complete. Will keep you updated with the progress.",
        recipients=config.notify_email,
        attachments=None,
    )
    run_graph(config, graph, init_state, interrupt_after=interrupt_after)
    
def main_resume(save_dir: str, interrupt_after="literature_reviewer"):
    config, state, last_subgraph = load_state(save_dir)
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
            config=config,
            subject=f"OpenLens Job Resumed | {config.thread_id}",
            content=latest_md,
            recipients=config.notify_email,
            attachments=zipfile,
        )
        start_from = all_subgraphs[last_subgraph_index + 1]
        logger.info(f"Resuming from subgraph {start_from}")
        graph = build_graph(config, start_from)
        run_graph(config, graph, state, interrupt_after=interrupt_after)
    



def parse_args():
    parser = argparse.ArgumentParser(description="Run the agent-med graph workflow")
    
    # Core arguments
    parser.add_argument("--question", type=str, help="The research question to investigate")
    parser.add_argument("--dataset-path", type=str, help="Path to the dataset")
    parser.add_argument("--thread-id", type=str, help="Thread ID for the run")
    parser.add_argument("--notify-email", type=str, help="Email address for notifications", default="openlens_ai/tools/latex_template/blank")
    parser.add_argument("--language", type=str, help="Language for the run", default="chs")
    
    # Config file
    parser.add_argument("--config", type=str, default="config.toml", help="Path to the config file")
    
    # Execution control
    parser.add_argument("--interrupt-after", type=str, default="none", help="Interrupt after the specified subgraph, use to limit user trial.")
    parser.add_argument("--resume-from", type=str, help="Resume from a specific saved directory")

    return parser.parse_args()

def cli_main():
    args = parse_args()
    
    
    if args.resume_from:
        logger.info(f"Resuming from {args.resume_from}")
        main_resume(args.resume_from, interrupt_after=args.interrupt_after)
    else: 
        config = Config.from_toml(args.config)
        # Create config from environment variables and command line arguments
        if args.question:
            question = args.question
            dataset_path = args.dataset_path
            notify_email = args.notify_email
        else:
            logger.error("Please provide a question, dataset path, and thread ID.")
            # 使用默认值
            question = "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?"
            dataset_path = "datasets/eicu"
            notify_email = "dzdzzd@126.com"
            # 使用当前日期    
            question_show = re.sub(r'[^\w]', '_', question.strip())
        
        if args.thread_id:
            thread_id = args.thread_id
        else:
            thread_id = "ol_" + datetime.now().strftime("%Y%m%d%H%M%S") + \
                f"_{question_show[:15]}" + f"_{question_show[-15:]}" + \
                    "_" + notify_email.replace("@", "_").replace(".", "_") + "_" + \
                    str(random.randint(1000, 9999))

        # main(question, dataset_path, thread_id)
        config.question = question
        config.dataset_path = dataset_path
        config.thread_id = thread_id
        config.notify_email = notify_email
        config.llm.language = args.language
        
        main(config, interrupt_after=args.interrupt_after)
    
    

if __name__ == "__main__":
    cli_main()