import os, sys
import json
from loguru import logger

def prepare_file_config(thread_id: str, question: str, dataset_path: str, email: str):
    save_path = os.path.join("./outputs", thread_id)
    os.makedirs(save_path, exist_ok=True)

    init_state = {"question": question, "messages": [], "thread_id": thread_id, "save_path": save_path}
    config = {"save_path": save_path, "thread_id": thread_id, "question": question, "dataset_path": dataset_path, "email": email}

    # os.makedirs(os.path.join("outputs", "log"), exist_ok=True)
    logger.add(os.path.join(save_path, "streamlit.log"), 
               format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|"+thread_id, 
               colorize=False, rotation="10 MB")

    # 保存config
    with open(os.path.join(save_path, "config.json"), "w") as f:
        json.dump(config, f, indent=4)
    logger.info("Config saved to" + os.path.join(config["save_path"], "config.json"))
    logger.info(f"Config: {config}")

    # 创建workdir
    os.makedirs(os.path.join(save_path, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(save_path, "states"), exist_ok=True)

    return init_state, config, save_path