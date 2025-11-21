import os, sys
import json

import traceback
import argparse
import re
from loguru import logger
from datetime import datetime
import random

from .utils.file_utils import prepare_files_folders, collect_files
from .utils.send_email import send_email, send_localized_email
from .utils.config import Config
from .state import State, load_state
from .build_graph import build_graph, run_graph, all_subgraphs 


def main(config: Config, interrupt_after_subgraph="none") -> None:
    init_state, config = prepare_files_folders(config)
    graph = build_graph(config, None)
    # 发送进度邮件
    send_localized_email(
        config=config,
        template_key="job_start",
        recipients=config.notify_email,
        attachments=None,
        latest_md="",
    )
    run_graph(config, graph, init_state, interrupt_after_subgraph=interrupt_after_subgraph)


def main_resume(
    save_dir: str, refine_suggestion: str = "", start_from_subgraph: str = "none", start_from_subtask_index: int = 0, interrupt_after_subgraph="none"
) -> None:
    config, state, last_subgraph = load_state(save_dir, 
                                              start_from_subgraph=start_from_subgraph, 
                                              start_from_subtask_index=start_from_subtask_index)
    config.refine_suggestion = refine_suggestion
    if config.refine_suggestion.strip():
        state["question"] = f"# Refine suggestion: {refine_suggestion}\n\n\n # Original question: {config.question}"
        logger.info(f"Refine suggestion: {refine_suggestion}")  
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
        run_graph(config, graph, state, interrupt_after_subgraph=interrupt_after_subgraph)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the agent-med graph workflow")

    # Core arguments
    parser.add_argument("--question", type=str, help="The research question to investigate")
    parser.add_argument("--refine-suggestion", type=str, help="Human's feedback for refining the research, only needed when resuming from a result.")
    parser.add_argument("--important", type=str, help="Important points to consider in the research")
    parser.add_argument("--dataset-path", type=str, help="Path to the dataset")
    parser.add_argument("--thread-id", type=str, help="Thread ID for the run")
    parser.add_argument("--notify-email", type=str, help="Email address for notifications", default="")
    parser.add_argument("--language", type=str, help="Language for the run, chs or eng", default="chs", choices=["chs", "eng"])
    parser.add_argument("--domain", type=str, default="medical", choices=["general", "medical"], help="Domain to use for prompts (general or medical)")

    # Config file
    parser.add_argument("--config", type=str, default="config.toml", help="Path to the config file")

    # Execution control
    parser.add_argument("--interrupt-after-subgraph", type=str, default="none", help="Interrupt after the specified subgraph, use to limit user trial.")
    parser.add_argument("--start-from-subgraph", type=str, default="none", help="Start from the specified subgraph, use to resume from a specific subgraph.")
    parser.add_argument(
        "--start-from-subtask-index", type=int, default=0, help="Start from the specified subtask index, use to resume from a specific subtask."
    )
    parser.add_argument("--resume-dir", type=str, help="Resume from a specific saved directory")

    return parser.parse_args()


def cli_main():
    args = parse_args()

    if args.resume_dir:
        if args.question:
            logger.error("--question should not be provided when resuming from a directory.")
            sys.exit(1)
        if args.dataset_path:
            logger.error("--dataset-path should not be provided when resuming from a directory.")
            sys.exit(1)
        if args.notify_email:
            logger.error("--notify-email should not be provided when resuming from a directory.")
            sys.exit(1)
        if args.thread_id:
            logger.error("--thread-id should not be provided when resuming from a directory.")
            sys.exit(1)
        if args.important:
            logger.error("--important should not be provided when resuming from a directory.")
            sys.exit(1)
        
        logger.info(f"Resuming from {args.resume_dir}")
        main_resume(
            args.resume_dir,
            refine_suggestion=args.refine_suggestion,
            interrupt_after_subgraph=args.interrupt_after_subgraph,
            start_from_subgraph=args.start_from_subgraph,
            start_from_subtask_index=args.start_from_subtask_index,
        )
    else:
        if args.refine_suggestion:
            logger.error("--refine-suggestion should not be provided when not resuming from a directory.")
            sys.exit(1)
        
        config = Config.from_toml(args.config)
        # Create config from environment variables and command line arguments
        if args.question and args.dataset_path and args.notify_email:
            question = args.question
            notify_email = args.notify_email
        else:
            logger.error("Please provide a question, dataset path, and email.")
            sys.exit(1)
            # # 使用默认值
            # question = (
            #     "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?"
            # )
            # dataset_path = "datasets/eicu"
            # notify_email = "dzdzzd@126.com"
            # # 使用当前日期
            # question_show = re.sub(r"[^\w]", "_", question.strip())

        config.question = question
        config.important = args.important
        config.dataset_path = dataset_path
        config.thread_id = thread_id
        config.notify_email = notify_email
        config.llm.language = args.language
        config.domain = args.domain

        main(config, interrupt_after_subgraph=args.interrupt_after_subgraph)


if __name__ == "__main__":
    cli_main()
