import os
import json
import glob
import inspect

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from loguru import logger
from datetime import datetime

from langchain_core.load.load import loads
from langchain.load.dump import dumps

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
    return_subtask_counter: int
    node_call_stack: list = []
    resume_node_call_stack: list = []
    available_figs: list = []


def track_node_call(subgraph_name: str=""):
    def track_node_call_inner(func):
        node_name = f"subgraph_{subgraph_name}.{func.__name__}"
        def skip_func(state: State, **kwargs):
            logger.info(f"Skiping {node_name}")
            return state
        
        def wrapper(state: State, **kwargs):
            latest_state_path = os.path.join(state['save_path'], "latest_state.json")
            with open(latest_state_path, "w") as f:
                f.write(dumps(state, ensure_ascii=False, indent=4))
            
            
            # 如果找到state参数，则记录函数调用
            if state is not None:
                if ('node_call_stack' not in state) or (not isinstance(state['node_call_stack'], list)):
                    state['node_call_stack'] = []
                state['node_call_stack'].append(node_name)

                node_call_stack_path = os.path.join(state['save_path'], 'node_call_stack.json')
                with open(node_call_stack_path, 'w') as f:
                    f.write(json.dumps(state['node_call_stack'], indent=4))
                
                if ("resume_node_call_stack" in state) and state["resume_node_call_stack"]:
                    if node_name != state["resume_node_call_stack"][-1]:
                        # 如果没有到resume的最后一个节点，则跳过
                        return skip_func(state, **kwargs)
            
            # 找到了resume的节点
            state["resume_node_call_stack"] = []
            logger.info(f"Calling node: {node_name}")
            # 调用原始函数
            return func(state, **kwargs)
        
        return wrapper
    return track_node_call_inner

def get_subplan(state: State) -> str:
    try:
        current_subplan_index = state["current_subtask_index"] if "current_subtask_index" in state else 1
        subplan_text = state["plan"]["sub_tasks"][current_subplan_index-1] # current_subplan_index从1开始，但是列表是从0开始
        subplan = f"\n\n# SUBTASK{current_subplan_index:02d}\n {subplan_text}\n"
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
        logger.info(f"Config save_path: {config.save_path} -> {save_dir}")
        config.save_path = save_dir
        config.thread_id = os.path.basename(save_dir)
    
    with open(config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
        
    logger.add(os.path.join(save_dir, "logs.log"), 
               format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|"+config.thread_id, 
               colorize=False, rotation="10 MB", level="DEBUG")
    
    
    # 先尝试在state目录下加载state，这个是每个subgraph保存一次
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
            logger.info(f"State save_path: {state['save_path']} -> {save_dir}")
            state["save_path"] = save_dir
        
        logger.info(f"Loaded state from {max_file_name}, last subgraph: {last_subgraph}")
    else:
        state = {"question": config.question, "messages": [], "thread_id": config.thread_id, "save_path": config.save_path}
    
    # 再尝试从latest_state.json加载，这个是每个node保存的
    latest_state_file_name = os.path.join(save_dir, "latest_state.json")
    if os.path.exists(latest_state_file_name):
        with open(latest_state_file_name, "r", encoding="utf-8") as f:
            state = loads(f.read())
        
        if "save_path" in state:
            logger.info(f"State save_path: {state['save_path']} -> {save_dir}")
            state["save_path"] = save_dir

    
    try:
        node_call_stack_path = os.path.join(save_dir, 'node_call_stack.json')
        with open(node_call_stack_path, 'r') as f:
            node_call_stack = json.load(f)
            state['resume_node_call_stack'] = node_call_stack
            state['node_call_stack'] = []
    except Exception as e:
        logger.warning(f"Error loading node call stack: {e}")
        state['resume_node_call_stack'] = []
        state['node_call_stack'] = []
        
    return config, state, last_subgraph
     