import os
import sys
import json
import random
from datetime import datetime
from loguru import logger
from pathlib import Path
from typing import Any, Dict, Tuple, List, Optional
from pydantic import BaseModel
import glob
import zipfile
import shutil
import toml
import tqdm
import pandas as pd

from .config import Config


def sample_file_content(file_path: str, max_size: int = 100 * 1024 * 1024) -> Tuple[List[str], List[str]]:
    """
    Sample content from a file, handling both text and binary files.

    For text files, returns first 10 lines and random 10 lines.
    For Excel files (xls/xlsx), returns first 10 rows and random 10 rows.
    For other binary files, returns empty lists.

    Args:
        file_path: Path to the file to sample
        max_size: Maximum size in bytes to read from the file

    Returns:
        Tuple of (first_samples, random_samples) where each is a list of strings
    """
    try:
        # Check if file is binary
        is_binary = False
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read(1024)  # Try to read a small chunk as text
        except UnicodeDecodeError:
            is_binary = True

        if is_binary:
            # Handle binary files
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in [".xls", ".xlsx"]:
                # Handle Excel files
                try:
                    df = pd.read_excel(file_path)

                    # Convert DataFrame to string representation
                    df_str = df.to_string()
                    lines = df_str.split("\n")

                    # Get first 10 lines
                    first_10_lines = lines[:10]

                    # Get random 10 lines (if file has more than 10 lines)
                    random_10_lines = []
                    if len(lines) > 10:
                        random_indices = random.sample(range(10, len(lines)), min(10, len(lines) - 10))
                        random_10_lines = [lines[i] for i in sorted(random_indices)]

                    return first_10_lines, random_10_lines
                except Exception as e:
                    logger.warning(f"Error reading Excel file {file_path}: {e}")
                    return [], []
            else:
                # Skip other binary files
                return [], []
        else:
            # Handle text files
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines(max_size)  # Read up to max_size of content

            # Get first 10 lines
            first_10_lines = lines[:10]

            # Get random 10 lines (if file has more than 10 lines)
            random_10_lines = []
            if len(lines) > 10:
                random_indices = random.sample(range(10, len(lines)), min(10, len(lines) - 10))
                random_10_lines = [lines[i] for i in sorted(random_indices)]

            return first_10_lines, random_10_lines
    except Exception as e:
        logger.warning(f"Error sampling file {file_path}: {e}")
        return [], []


def collect_files(config: Config, max_size: int = 10 * 1024 * 1024, compressed_dir_name="compressed"):
    save_path = config.save_path

    # Define the file patterns to collect, with priority order
    file_patterns = [
        "*.py",
        "*.md",
        "*.tex",
        "*.pdf",
        "*.json",
        "*.svg",
        "*.txt",
        "*.bib",
        "*.sty",
        "*.log",
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*",
    ]
    
    
    if config.workflow.e2e_test:
        logger.info("E2E test mode, will not backup files.")
    else:
        # file_patterns = ['*.py', '*.json', '*.md', '*.txt', '*.tex', '*.bib', '*.sty', '*.log', '*.pdf', '*']

        # Collect all matching files
        exclude_path = ["backup/openlens_ai"]
        files = []
        for pattern in file_patterns:
            this_pattern_files = glob.glob(os.path.join(save_path, "**", pattern), recursive=True)
            for f in this_pattern_files:
                if any(exclude in f for exclude in exclude_path):
                    continue
                if f not in files and os.path.isfile(f):
                    files.append(f)

        # Create the compressed folder path
        compressed_dir = os.path.join(save_path, compressed_dir_name)
        os.makedirs(compressed_dir, exist_ok=True)

        # Create the zip file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"files_{timestamp}.zip"
        zip_filepath = os.path.join(compressed_dir, zip_filename)

        # Compress the files into the zip archive
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            total_size = 0
            for file in tqdm.tqdm(files, desc="Compressing files"):
                if "compressed" in file:
                    continue
                try:
                    # Check if file has read permission
                    with open(file, "rb"):
                        pass
                    # Check if adding this file will exceed the max_size
                    file_size = os.path.getsize(file)
                    if total_size + file_size > max_size:
                        # logger.info(f"警告: 添加文件 {file} 后zip文件大小将超过10MB限制，已跳过.")
                        continue

                    # Add the file to the zip archive, maintaining the relative path structure
                    arcname = os.path.relpath(file, save_path)
                    zipf.write(file, arcname)
                    total_size += file_size
                except Exception as e:
                    logger.warning(f"Warning: Cannot add file {file} to zip archive. Error: {e}")

        full_zip_filename = f"all_files.zip"
        full_zip_filepath = os.path.join(compressed_dir, full_zip_filename)
        shutil.copy(zip_filepath, full_zip_filepath)

    # # 将文件打包成zip
    # with zipfile.ZipFile(full_zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
    #     total_size = 0
    #     for file in files:
    #         if "compressed" in file:
    #             continue
    #         try:
    #             # 检查有没有读取权限
    #             with open(file, 'rb'):
    #                 pass

    #             # 将文件添加到zip中，保持相对路径结构
    #             arcname = os.path.relpath(file, save_path)
    #             zipf.write(file, arcname)
    #         except Exception as e:
    #             logger.info(f"警告: 无法读取文件 {file}，已跳过. 错误: {e}")

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
        state_path = os.path.join(config.save_path, "latest_state.json")
        with open(state_path, "r") as f:
            state = json.load(f)
        latest_md += "\n\n".join(state["node_call_stack"])
    except Exception as e:
        logger.warning(f"Error loading node call stack: {e}")

    try:
        usage_md, usage_table = collect_token_usage(config)
        latest_md += "\n\n" + usage_md
    except Exception as e:
        logger.warning(f"Error collecting token usage: {e}")

    return zip_filepath, latest_md[:10000]  # Only return the first 10000 characters to prevent email size limit


def collect_token_usage(config: Config, overall: bool = True) -> str:
    """
    Collect token usage from all JSON files in openhands_traj and llm_calls subdirectories.

    Args:
        config: Config object containing save_path

    Returns:
        str: Formatted string with token usage summary
    """
    save_path = Path(config.save_path)

    # Model usage statistics
    model_stats = {}

    def recursive_search_token_usage(data: Any) -> None:
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
                recursive_search_token_usage(value)

        elif isinstance(data, list):
            # Continue searching recursively in list items
            for item in data:
                recursive_search_token_usage(item)

    # TODO: delete this block because openhands_llm_log is now available
    # # Process Openhands traj directory
    # dir_name = "openhands_traj"
    # dir_path = save_path / dir_name
    # if dir_path.exists():
    #     # Process all JSON files in the directory
    #     for json_file in dir_path.glob("*.json"):
    #         try:
    #             with open(json_file, 'r', encoding='utf-8') as f:
    #                 data = json.load(f)
    #                 logger.debug(f"Processing {json_file}")
    #             if isinstance(data, list):
    #                 for data_item in data:
    #                     if isinstance(data_item, dict) and "action" in data_item:
    #                         # WARNING: In Openhand traj, both action and observation have token_usage, collect only action, otherwise may double count
    #                         recursive_search_token_usage(data_item)
    #         except (json.JSONDecodeError, IOError) as e:
    #             logger.warning(f"Could not read {json_file}: {e}")
    #             continue

    # Process llm_calls and openhands_llm_log directory
    for dir_name in ["llm_calls", "openhands_llm_log"]:
        dir_path = save_path / dir_name
        if dir_path.exists():
            # Process all JSON files in the directory
            for json_file in dir_path.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    recursive_search_token_usage(data)
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
        df_data.append(
            {
                "Model": model_name,
                "Generation": f"{completion_tokens/1e6: .2f} M",
                "Prompt": f"{prompt_tokens/1e6: .2f} M",
            }
        )

    if overall:
        output_lines.append(f"### Overall Totals:")
        output_lines.append(f"  - Completion tokens: {total_completion_tokens/1e6: .2f} M")
        output_lines.append(f"  - Prompt tokens: {total_prompt_tokens/1e6: .2f} M")

    output_str = "\n".join(output_lines)
    logger.info(output_str)

    # Create pandas DataFrame
    df = pd.DataFrame(df_data)
    if "Model" in df.columns:
        df = df.set_index("Model")
    try:
        df.to_csv(os.path.join(save_path, "token_usage.csv"))
    except Exception as e:
        logger.warning(f"Error saving token usage csv: {e}")

    # Return both string summary and DataFrame
    return output_str, df



if __name__ == "__main__":
    config = Config(save_path="outputs/pred_aki_trend_eicu_demo_20251024184352")
    collect_token_usage(config)
