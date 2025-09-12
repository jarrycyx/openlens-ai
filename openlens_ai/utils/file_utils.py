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
import glob
import zipfile
import shutil

with open("openlens_ai/tools/openhands_configs/config.toml", "r") as f:
    oh_config_template = f.read()



def collect_files(config: Config, max_size: int = 10 * 1024 * 1024, compressed_dir_name="compressed"):
    save_path = config.save_path
    
    # 定义需要收集的文件类型，这里是包含优先级的
    file_patterns = ['*.py', '*.md', '*.tex', '*.pdf', '*.json', '*.svg', '*.txt', '*.bib', '*.sty', '*.log',
                     '*.png', '*.jpg', '*.jpeg', '*']
    # file_patterns = ['*.py', '*.json', '*.md', '*.txt', '*.tex', '*.bib', '*.sty', '*.log', '*.pdf', '*']
    
    # 收集所有匹配的文件
    files = []
    for pattern in file_patterns:
        this_pattern_files = glob.glob(os.path.join(save_path, '**', pattern), recursive=True)
        for f in this_pattern_files:
            if f not in files and os.path.isfile(f):
                files.append(f)
    
    # 创建压缩文件夹路径
    compressed_dir = os.path.join(save_path, compressed_dir_name)
    os.makedirs(compressed_dir, exist_ok=True)
    
    # 创建以时间戳命名的zip文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"files_{timestamp}.zip"
    zip_filepath = os.path.join(compressed_dir, zip_filename)
    
    # 将文件打包成zip
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        total_size = 0
        for file in files:
            if "compressed" in file:
                continue
            try:
                # 检查有没有读取权限
                with open(file, 'rb'):
                    pass
                # 检查添加此文件后是否会超过大小限制
                file_size = os.path.getsize(file)
                if total_size + file_size > max_size:
                    # logger.info(f"警告: 添加文件 {file} 后zip文件大小将超过10MB限制，已跳过.")
                    continue
                    
                # 将文件添加到zip中，保持相对路径结构
                arcname = os.path.relpath(file, save_path)
                zipf.write(file, arcname)
                total_size += file_size
            except Exception as e:
                logger.info(f"警告: 无法读取文件 {file}，已跳过. 错误: {e}")
                
                
    
    # 创建以时间戳命名的zip文件
    full_zip_filename = f"all_files.zip"
    full_zip_filepath = os.path.join(compressed_dir, full_zip_filename)
    
    # 将文件打包成zip
    with zipfile.ZipFile(full_zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        total_size = 0
        for file in files:
            if "compressed" in file:
                continue
            try:
                # 检查有没有读取权限
                with open(file, 'rb'):
                    pass
                    
                # 将文件添加到zip中，保持相对路径结构
                arcname = os.path.relpath(file, save_path)
                zipf.write(file, arcname)
            except Exception as e:
                logger.info(f"警告: 无法读取文件 {file}，已跳过. 错误: {e}")
    
    # # 按修改时间排序.md文件，返回最新的一个
    # md_files = [f for f in files if f.endswith('.md')]
    # latest_md_file = None
    # latest_md = ""
    # if md_files:
    #     md_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    #     latest_md_file = md_files[0]
    # if latest_md_file:
    #     with open(latest_md_file, 'r', encoding='utf-8') as f:
    #         latest_md = f.read()
    
    
    latest_md = f"## Question\n{config.question}\n\n## Dataset\n{config.dataset_path}\n\n## Job progress:\n"
    try:
        node_call_stack_path = os.path.join(config.save_path, 'node_call_stack.json')
        with open(node_call_stack_path, 'r') as f:
            node_call_stack = json.load(f)
        latest_md += "\n\n".join(node_call_stack)
    except Exception as e:
        logger.warning(f"Error loading node call stack: {e}")
        
    try:
        usage_md, usage_table = collect_token_usage(config)
        latest_md += ("\n\n" + usage_md)
    except Exception as e:
        logger.warning(f"Error collecting token usage: {e}")
        
    return zip_filepath, latest_md[:10000]  # 只返回前10000字符，防止邮件过大



def collect_token_usage(config: Config, overall: bool = True) -> str:
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
                
                if "/" in model_name:
                    model_name = model_name.split("/")[-1]
                model_name = model_name.lower()
                    
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
    
    # Prepare data for pandas DataFrame
    import pandas as pd
    df_data = []
    
    for model_name, stats in model_stats.items():
        completion_tokens = stats["completion_tokens"]
        prompt_tokens = stats["prompt_tokens"]
        total_completion_tokens += completion_tokens
        total_prompt_tokens += prompt_tokens
        
        output_lines.append(f"### Model: {model_name}")
        output_lines.append(f"- Completion tokens: {completion_tokens/1e6: .2f} M")
        output_lines.append(f"- Prompt tokens: {prompt_tokens/1e6: .2f} M")
        output_lines.append("")
        
        # Add data to DataFrame
        df_data.append({
            'Model': model_name,
            'Generation': f"{completion_tokens/1e6: .2f} M",
            'Prompt': f"{prompt_tokens/1e6: .2f} M"
        })
    
    if overall:
        output_lines.append(f"### Overall Totals:")
        output_lines.append(f"  - Completion tokens: {total_completion_tokens/1e6: .2f} M")
        output_lines.append(f"  - Prompt tokens: {total_prompt_tokens/1e6: .2f} M")
    
    output_str = "\n".join(output_lines)
    logger.info(output_str)
    
    # Create pandas DataFrame
    df = pd.DataFrame(df_data)
    if "Model" in df.columns:
        df = df.set_index('Model')
    try:
        df.to_csv(os.path.join(save_path, "token_usage.csv"))
    except Exception as e:
        logger.warning(f"Error saving token usage csv: {e}")
    
    # Return both string summary and DataFrame
    return output_str, df


def prepare_file_config(thread_id: str, question: str, dataset_path: str, email: str = "") -> tuple[dict, Config, str]:
    save_path = os.path.join("./outputs", thread_id)
    if os.path.exists(save_path):
        thread_id = thread_id + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join("./outputs", thread_id)
    os.makedirs(save_path, exist_ok=True)
    
    # 创建备份文件夹并复制openlens_ai文件夹和.env文件
    backup_path = os.path.join(save_path, "backup")
    os.makedirs(backup_path, exist_ok=True)
    
    # 复制openlens_ai文件夹
    if os.path.exists("openlens_ai"):
        shutil.copytree("openlens_ai", os.path.join(backup_path, "openlens_ai"), dirs_exist_ok=True)
    
    # # 复制.env文件
    # if os.path.exists(".env"):
    #     shutil.copy2(".env", os.path.join(backup_path, ".env"))
    # 保存环境变量
    with open(os.path.join(backup_path, "env.sh"), "w") as fp:
        # json.dump(dict(os.environ), fp, indent=4)
        for key, val in dict(os.environ).items():
            fp.write(f"{key}=\"{val}\"\n")
    
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
