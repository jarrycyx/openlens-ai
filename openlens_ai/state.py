import os, sys
import json
import glob
import shutil

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from loguru import logger
from datetime import datetime

from langchain_core.load.load import loads
from langchain.load.dump import dumps

from file1agent.file_manager import FileManager

from .utils.config import Config


class State(TypedDict):
    question: str  # Can be different from config.question because refine suggestion maybe added
    messages: list
    plan: dict
    data_report: str
    current_subtask_index: int = 1  # 1 means the first subtask
    save_path: str
    thread_id: str = ""
    subplan: str = ""
    literature_tool_call_counter: int = 0
    last_tool_call: str = ""
    literature_report: str = ""
    data_show: str = ""
    return_subtask_counter: int = 0
    polish_latex_counter: int = 0
    node_call_stack: list = []
    resume_node_call_stack: list = []
    status: str = "running"
    file_summary: dict = {}
    available_figs: list = []

    artifact_manifest_path: str | None
    artifact_code_stats: dict | None
    artifact_ok_to_publish: bool | None
    artifact_logs: list[str] | None
    artifact_published: bool | None
    artifact_repo_url: str | None

def track_node_call(subgraph_name: str = ""):
    def track_node_call_inner(func):
        node_name = f"subgraph_{subgraph_name}.{func.__name__}"

        def skip_func(state: State, **kwargs):
            logger.info(f"Skiping {node_name}")
            return state

        def wrapper(state: State, **kwargs):

            # Log the node call if state is provided
            if state:
                if ("node_call_stack" not in state) or (not isinstance(state["node_call_stack"], list)):
                    state["node_call_stack"] = []
                state["node_call_stack"].append(node_name)

                if ("resume_node_call_stack" in state) and state["resume_node_call_stack"]:
                    if node_name != state["resume_node_call_stack"][-1]:
                        # Skip if not the last node in resume_node_call_stack
                        return skip_func(state, **kwargs)

            # 找到了resume的节点
            state["resume_node_call_stack"] = []

            latest_state_path = os.path.join(state["save_path"], "latest_state.json")
            with open(latest_state_path, "w") as f:
                f.write(dumps(state, ensure_ascii=False, indent=4))

            logger.info(f"Calling node: {node_name}")
            # 调用原始函数
            _return = func(state, **kwargs)
            
            return _return

        return wrapper

    return track_node_call_inner


def get_subplan(state: State) -> str:
    try:
        current_subplan_index = state["current_subtask_index"] if "current_subtask_index" in state else 1
        subplan_text = state["plan"]["sub_tasks"][
            current_subplan_index - 1
        ]  # current_subplan_index从1开始，但是列表是从0开始
        subplan = f"\n\n# SUBTASK{current_subplan_index:02d}\n {subplan_text}\n"
    except Exception as e:
        subplan = ""
        logger.warning(f"No subplan found. Error: {e}")
    return subplan


def load_state(
    save_dir: str, copy_to_new: bool = False, start_from_subgraph: str = "", start_from_subtask_index: int = 1
) -> tuple[Config, State]:

    config_path = os.path.join(save_dir, "config.toml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if copy_to_new:
        # 复制一遍save_dir，加上_resume_时间戳
        new_save_dir = save_dir + "_resume_" + datetime.now().strftime("%Y%m%d%H%M%S")
        os.makedirs(new_save_dir, exist_ok=True)
        os.system("cp -r " + save_dir + "/* " + new_save_dir)
        save_dir = new_save_dir

    # Load config and update save_path thread_id
    config = Config.from_toml(config_path)

    if copy_to_new:
        logger.info(f"Config save_path: {config.save_path} -> {save_dir}")
        config.save_path = save_dir
        config.resume_dir_id = config.thread_id
        config.thread_id = os.path.basename(save_dir)
        config.save_toml(config_path)

    # Load logger
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.remove()
    logger.add(
        os.path.join(save_dir, f"logs_{timestamp}_pid{os.getpid()}.log"),
        format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|" + config.thread_id,
        colorize=False,
        rotation="10 MB",
        level="DEBUG",
    )
    logger.add(
        sys.stdout,
        format="<green>{time:YYYYMMDDHHmmss}</green>|<level>{level}</level>|{message}|<yellow>{file}:{line}</yellow>|"
        + f"<cyan>{config.thread_id}</cyan>",
        colorize=True,
        level="INFO",
    )

    file_manager = FileManager(
        analyze_dir=os.path.join(config.save_path, "workspace"),
        config={
            "llm": {
                "chat": dict(config.llm.chat),
                "vision": dict(config.llm.vision),
            },
            "rerank": dict(config.rerank),
        },
        realloc_log=False,  # Already configured loguru
        backup_path=os.path.join(config.save_path, "backup", "deleted"),
        file_relationships_save_path=os.path.join(config.save_path, ".f1a_cache", "file_relationships.json"),
        summary_cache_path=os.path.join(config.save_path, ".f1a_cache", "file_summary_cache.json"),
    )

    # Load state from latest_state.json
    latest_state_file_name = os.path.join(save_dir, "latest_state.json")
    if os.path.exists(latest_state_file_name):
        with open(latest_state_file_name, "r", encoding="utf-8") as f:
            state = loads(f.read())

        if ("save_path" in state) and (state["save_path"] != save_dir):
            logger.info(f"State save_path: {state['save_path']} -> {save_dir}")
            state["save_path"] = save_dir

    if start_from_subtask_index is not None:
        state["current_subtask_index"] = start_from_subtask_index
        logger.info(f"Start from subtask index: {start_from_subtask_index}")

    # Load node_call_stack and get last subgraph
    last_subgraph = None
    try:
        node_call_stack = state["node_call_stack"]

        resume_node_call_stack = []
        if start_from_subgraph:
            logger.debug(f"start_from_subgraph is set to {start_from_subgraph}, will resume from {start_from_subgraph}")
            # If start_from_subgraph is in node, add it to the last node in resume_node_call_stack so that it will be executed
            for node in node_call_stack:
                if start_from_subgraph in node:
                    logger.debug(f"Found start_from_subgraph in node_call_stack: {node}")
                    resume_node_call_stack.append(node)
                    break
        else:
            for node in node_call_stack:
                # Only add nodes that are not end_node
                # task will skip nodes in resume_node_call_stack until the last
                if "end_node" in node:
                    break
                else:
                    resume_node_call_stack.append(node)
        
        if resume_node_call_stack:
            start_from_subgraph = resume_node_call_stack[-1].split(".")[0].replace("subgraph_", "")
        else:
            start_from_subgraph = start_from_subgraph
                

        logger.info(f"Will skip nodes in resume_node_call_stack until the last: {resume_node_call_stack}")

        state["resume_node_call_stack"] = resume_node_call_stack
    except Exception as e:
        logger.warning(f"Error loading node call stack: {e}")
        state["resume_node_call_stack"] = []
        state["node_call_stack"] = []

    # Create backup folder
    backup_path = os.path.join(save_dir, "backup")
    os.makedirs(backup_path, exist_ok=True)

    # Copy openlens_ai folder
    if os.path.exists("openlens_ai"):
        shutil.copytree("openlens_ai", os.path.join(backup_path, "openlens_ai"), dirs_exist_ok=True)

    return config, state, start_from_subgraph, file_manager


def prepare_state(config: Config) -> Config:

    save_path = os.path.join("./outputs", config.thread_id)
    if os.path.exists(save_path):
        config.thread_id = config.thread_id + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join("./outputs", config.thread_id)
    config.save_path = save_path
    os.makedirs(save_path, exist_ok=True)

    # os.makedirs(os.path.join("outputs", "log"), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.remove()
    logger.add(
        os.path.join(save_path, f"logs_{timestamp}_pid{os.getpid()}.log"),
        format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|" + config.thread_id,
        colorize=False,
        rotation="10 MB",
        level="DEBUG",
    )
    logger.add(
        sys.stdout,
        format="<green>{time:YYYYMMDDHHmmss}</green>|<level>{level}</level>|{message}|<yellow>{file}:{line}</yellow>|"
        + f"<cyan>{config.thread_id}</cyan>",
        colorize=True,
        level="INFO",
    )

    # 创建备份文件夹并复制openlens_ai文件夹和.env文件
    backup_path = os.path.join(save_path, "backup")
    os.makedirs(backup_path, exist_ok=True)

    # 复制openlens_ai文件夹
    if os.path.exists("openlens_ai"):
        shutil.copytree(
            "openlens_ai",
            os.path.join(backup_path, "openlens_ai"),
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".*", "*.iso", "windows-fonts", "*.tar.gz"),
        )

    # 保存config为toml
    config.save_toml(os.path.join(save_path, "config.toml"))
    logger.info(f"Config saved to {os.path.join(save_path, 'config.toml')}")

    # 准备openhands_config.toml
    with open("openlens_ai/tools/openhands_configs/config.toml", "r") as f:
        oh_config_template = f.read()
    oh_config = oh_config_template.replace("{api_key}", config.llm.chat.api_key)
    oh_config = oh_config.replace("{base_url}", config.llm.chat.base_url)
    oh_config = oh_config.replace("{code_model}", config.llm.chat.model)
    oh_config = oh_config.replace("{api_key}", config.llm.chat.api_key)

    if config.llm.condenser.model:
        oh_config = oh_config.replace("{condenser_api_key}", config.llm.condenser.api_key)
        oh_config = oh_config.replace("{condenser_base_url}", config.llm.condenser.base_url)
        oh_config = oh_config.replace("{code_condenser_model}", config.llm.condenser.model)
    else:
        logger.warning("Condenser model not specified, using chat model as condenser model.")
        oh_config = oh_config.replace("{condenser_api_key}", config.llm.chat.api_key)
        oh_config = oh_config.replace("{condenser_base_url}", config.llm.chat.base_url)
        oh_config = oh_config.replace("{code_condenser_model}", config.llm.chat.model)

    oh_config = oh_config.replace("{tavily_key}", config.tools.tavily_api_key)
    this_config_path = os.path.join(save_path, "openhands_config.toml")
    with open(this_config_path, "w") as f:
        f.write(oh_config)
    logger.debug(f"Using OpenHands config: {oh_config}")

    init_state = {"question": config.question, "messages": [], "thread_id": config.thread_id, "save_path": save_path}
    os.makedirs(os.path.join(save_path, "states"), exist_ok=True)

    # 创建workdir
    os.makedirs(os.path.join(save_path, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(save_path, "states"), exist_ok=True)

    os.makedirs(os.path.join(save_path, "openhands_traj"))

    file_manager = FileManager(
        analyze_dir=os.path.join(config.save_path, "workspace"),
        config={
            "llm": {
                "chat": dict(config.llm.chat),
                "vision": dict(config.llm.vision),
            },
            "rerank": dict(config.rerank),
            "inclusion": {
                "mode": "whitelist"
            }
        },
        realloc_log=False,  # Already configured loguru
        backup_path=os.path.join(config.save_path, "backup", "deleted"),
        file_relationships_save_path=os.path.join(config.save_path, ".f1a_cache", "file_relationships.json"),
        summary_cache_path=os.path.join(config.save_path, ".f1a_cache", "file_summary_cache.json"),
    )

    return init_state, config, file_manager
