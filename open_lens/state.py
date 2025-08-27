import os
import json
import glob

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from loguru import logger
from datetime import datetime

from langchain_core.load.load import loads

from .utils.config import Config

class State(TypedDict):
    question: str
    messages: list
    plan: dict
    data_report: str
    current_subtask_index: int
    save_path: str
    thread_id: str
    subplan: str
    literature_tool_call_counter: int
    last_tool_call: str
    literature_report: str
    data_show: str
    manuscript_polish_round: int


def get_subplan(state: State) -> str:
    try:
        current_subplan_index = state["current_subtask_index"] if "current_subtask_index" in state else 1
        subplan_text = state["plan"]["sub_tasks"][current_subplan_index-1] # current_subplan_index从1开始，但是列表是从0开始
        subplan = f"\n\n# SUBTASK{current_subplan_index+1:02d}\n {subplan_text}\n"
    except:
        subplan = ""
        logger.warning("No subplan found.")
    return subplan

def load_state(save_dir: str) -> tuple[Config, State]:
    # 复制一遍save_dir，加上_resume
    new_save_dir = save_dir + "_resume_" + datetime.now().strftime("%Y%m%d%H%M%S")
    os.makedirs(new_save_dir, exist_ok=True)
    os.system("cp -r " + save_dir + "/* " + new_save_dir)
    save_dir = new_save_dir
    
    config_path = os.path.join(save_dir, "config.json")
    
    with open(config_path, "r") as f:
        config = json.load(f)
        config = Config(**config)
        print(f"Config save_path: {config.save_path} -> {save_dir}")
        config.save_path = save_dir
        config.thread_id = os.path.basename(save_dir)
    
    with open(config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
        
        
    state_dir = os.path.join(save_dir, "states")
    # 遍历里面的文件，格式是step_i.json，找最大的
    file_names = os.listdir(state_dir)
    last_subgraph = None
    if file_names:
        file_indices = [int(file_name.split("_")[1]) for file_name in file_names if file_name.endswith(".json")]
        max_index = max(file_indices)
        max_file_name = glob.glob(os.path.join(state_dir, f"step_{max_index:04d}*.json"))[0]
        
        with open(max_file_name, "r") as f:
            state_str = f.read()
            state = loads(state_str)
            last_subgraph = list(state.keys())[0]
            state = state[last_subgraph]
            print(f"State save_path: {state['save_path']} -> {save_dir}")
            state["save_path"] = save_dir
        
        print(f"Loaded state from {max_file_name}, last subgraph: {last_subgraph}")
    else:
        state = {"question": config.question, "messages": [], "thread_id": config.thread_id, "save_path": config.save_path}
        
        
    return config, state, last_subgraph
     