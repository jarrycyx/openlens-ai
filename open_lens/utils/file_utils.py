import os, sys
import json
from loguru import logger
from .config import Config


os.environ["LOGURU_LEVEL"] = 'INFO'
with open("open_lens/tools/openhands_configs/config.toml", "r") as f:
    oh_config_template = f.read()

def prepare_file_config(thread_id: str, question: str, dataset_path: str, email: str) -> tuple[dict, Config, str]:
    save_path = os.path.join("./outputs", thread_id)
    os.makedirs(save_path, exist_ok=True)
    
    oh_config = oh_config_template.replace("{api_key}", os.getenv("OPENAI_API_KEY"))
    oh_config = oh_config.replace("{base_url}", os.getenv("BASE_URL"))
    oh_config = oh_config.replace("{code_model}", os.getenv("CODE_MODEL"))
    this_config_path = os.path.join(save_path, "openhands_config.toml")
    with open(this_config_path, "w") as f:
        f.write(oh_config)
    logger.info(f"Using OpenHands config: {oh_config}")

    init_state = {"question": question, "messages": [], "thread_id": thread_id, "save_path": save_path}
    config = Config(
        save_path=save_path,
        thread_id=thread_id,
        question=question,
        dataset_path=dataset_path,
        email=email
    )

    # os.makedirs(os.path.join("outputs", "log"), exist_ok=True)
    logger.add(os.path.join(save_path, "streamlit.log"), 
               format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|"+thread_id, 
               colorize=False, rotation="10 MB", level="DEBUG")

    # 保存config
    with open(os.path.join(save_path, "config.json"), "w") as f:
        json.dump(config.model_dump(), f, indent=4)
    logger.info("Config saved to" + os.path.join(config.save_path, "config.json"))
    logger.info(f"Config: {config}")

    # 创建workdir
    os.makedirs(os.path.join(save_path, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(save_path, "states"), exist_ok=True)

    return init_state, config, save_path