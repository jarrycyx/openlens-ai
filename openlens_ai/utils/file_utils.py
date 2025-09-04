import os
import sys
import json
import random
from datetime import datetime
from loguru import logger
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel
from .config import Config

with open("openlens_ai/tools/openhands_configs/config.toml", "r") as f:
    oh_config_template = f.read()

def collect_token_usage(config: Config) -> str:
    """
    Collect token usage from all JSON files in openhands_traj and llm_calls subdirectories.
    
    Args:
        config: Config object containing save_path
        
    Returns:
        str: Formatted string with token usage summary
    """
    save_path = Path(config.save_path)
    
    # Directories to search
    search_dirs = ["openhands_traj", "llm_calls"]
    
    # Model usage statistics
    model_stats = {}
    
    def recursive_search_token_usage(data: Any, model_stats: Dict) -> None:
        """
        Recursively search for token_usage and model_name fields in JSON data.
        """
        if isinstance(data, dict):
            # Check if this dict contains token_usage and model_name
            if (("token_usage" in data) or ("usage" in data)) and (("model_name" in data) or ("model" in data)):
                if "model_name" in data:
                    model_name = data["model_name"]
                else:
                    model_name = data["model"]
                    
                if "token_usage" in data:
                    token_usage = data["token_usage"]
                else:
                    token_usage = data["usage"]
                
                if model_name not in model_stats:
                    model_stats[model_name] = {"completion_tokens": 0, "prompt_tokens": 0}
                
                if "completion_tokens" in token_usage:
                    model_stats[model_name]["completion_tokens"] += token_usage["completion_tokens"]
                if "prompt_tokens" in token_usage:
                    model_stats[model_name]["prompt_tokens"] += token_usage["prompt_tokens"]
            
            # Continue searching recursively
            for value in data.values():
                recursive_search_token_usage(value, model_stats)
                
        elif isinstance(data, list):
            # Continue searching recursively in list items
            for item in data:
                recursive_search_token_usage(item, model_stats)

    # Process each directory
    for dir_name in search_dirs:
        dir_path = save_path / dir_name
        
        if not dir_path.exists():
            continue
            
        # Process all JSON files in the directory
        for json_file in dir_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # logger.info(f"Processing {json_file}")
                    recursive_search_token_usage(data, model_stats)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not read {json_file}: {e}")
                continue
    
    # Format the output
    output_lines = ["## Token Usage Summary:"]
    total_completion_tokens = 0
    total_prompt_tokens = 0
    
    for model_name, stats in model_stats.items():
        completion_tokens = stats["completion_tokens"]
        prompt_tokens = stats["prompt_tokens"]
        total_completion_tokens += completion_tokens
        total_prompt_tokens += prompt_tokens
        
        output_lines.append(f"### Model: {model_name}")
        output_lines.append(f"- Completion tokens: {completion_tokens/1e6: .2f} M")
        output_lines.append(f"- Prompt tokens: {prompt_tokens/1e6: .2f} M")
        output_lines.append("")
    
    output_lines.append(f"### Overall Totals:")
    output_lines.append(f"  - Completion tokens: {total_completion_tokens/1e6: .2f} M")
    output_lines.append(f"  - Prompt tokens: {total_prompt_tokens/1e6: .2f} M")
    
    output_str = "\n".join(output_lines)
    logger.info(output_str)
    return output_str


def prepare_file_config(thread_id: str, question: str, dataset_path: str, email: str) -> tuple[dict, Config, str]:
    save_path = os.path.join("./outputs", thread_id)
    if os.path.exists(save_path):
        thread_id = thread_id + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join("./outputs", thread_id)
    os.makedirs(save_path, exist_ok=True)
    
    oh_config = oh_config_template.replace("{api_key}", os.getenv("OPENAI_API_KEY"))
    oh_config = oh_config.replace("{base_url}", os.getenv("BASE_URL"))
    oh_config = oh_config.replace("{code_model}", os.getenv("CODE_MODEL"))
    oh_config = oh_config.replace("{tavily_key}", os.getenv("TAVILY_API_KEY", ""))
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
    logger.add(os.path.join(save_path, "logs.log"), 
               format="{time:YYYYMMDDHHmmss}|{level}|{message}|{file}:{line}|"+thread_id, 
               colorize=False, rotation="10 MB", level="DEBUG")
    # logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

    # 保存config
    with open(os.path.join(save_path, "config.json"), "w") as f:
        json.dump(config.model_dump(), f, indent=4)
    logger.info("Config saved to" + os.path.join(config.save_path, "config.json"))
    logger.info(f"Config: {config}")

    # 创建workdir
    os.makedirs(os.path.join(save_path, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(save_path, "states"), exist_ok=True)
    
    os.makedirs(os.path.join(save_path, "openhands_traj"))
    

    return init_state, config, save_path