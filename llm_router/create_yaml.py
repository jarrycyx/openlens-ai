#!/usr/bin/env python3
"""
Script to generate model_list.yaml from API key files.
Each txt file contains one API key per line.
"""

import yaml
import argparse
import os
import sys
import requests
from typing import List, Dict, Any, Tuple
from multiprocessing import Pool, cpu_count
from functools import partial
import numpy as np
from dotenv import load_dotenv
load_dotenv()


forward_names = {
    "zai-org/GLM-4.5": "glm-4.5",
    "zai-org/GLM-4.5-Air": "glm-4.5-air",
    "zai-org/GLM-4.5V": "glm-4.5v",
    "Qwen/Qwen3-235B-A22B-Instruct-2507": "qwen3-235b-a22b-instruct-2507",
    "Qwen/Qwen3-Coder-30B-A3B-Instruct": "qwen3-coder-30b-a3b-instruct",
    "Qwen/Qwen3-Coder-480B-A35B-Instruct": "qwen3-coder-480b-a35b-instruct",
    "BAAI/bge-reranker-v2-m3": "bge-reranker-v2-m3",
    "Qwen/Qwen3-30B-A3B-Instruct-2507": "qwen3-30b-a3b-instruct-2507"
}

for a, b in forward_names.items():
    print(f"Mapping model name {a} to {b}")

def read_api_keys(file_path: str) -> List[str]:
    """
    Read API keys from a txt file, one key per line.
    
    Args:
        file_path: Path to the txt file containing API keys
        
    Returns:
        List of API keys
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"API key file not found: {file_path}")
    
    api_keys = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            key = line.strip()
            if key:  # Skip empty lines
                api_keys.append(key)
    
    return api_keys


def check_balance(api_key: str) -> Tuple[str, bool, float]:
    """
    Check the balance of an API key using SiliconFlow API.
    
    Args:
        api_key: The API key to check
        
    Returns:
        Tuple of (api_key, is_valid, balance) where is_valid indicates if the key is valid
        and balance is the account balance
    """
    try:
        url = "https://api.siliconflow.cn/v1/user/info"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") and "data" in data:
                balance_str = data["data"].get("balance", "0")
                balance = float(balance_str)
                return api_key, True, balance
        return api_key, False, 0.0
    except Exception as e:
        print(f"Warning: Failed to check balance for key: {e}")
        return api_key, False, 0.0


def create_model_list(api_key_files: List[str], 
                      model_names: List[str], 
                      api_bases: List[str],
                      min_balance: float = 0.2,
                      processes: int = None) -> Dict[str, Any]:
    """
    Create model list configuration from API keys, model names and API bases.
    
    Args:
        api_key_files: List of paths to txt files containing API keys
        model_names: List of model names
        api_bases: List of API base URLs
        min_balance: Minimum balance required for a key to be included
        processes: Number of processes to use for balance checking (default: CPU count)
        
    Returns:
        Dictionary containing the model list configuration
    """
    model_list = []
    
    # Read all API keys from all files
    all_api_keys = []
    for file_path in api_key_files:
        keys = read_api_keys(file_path)
        all_api_keys.extend(keys)
    np.random.shuffle(all_api_keys)
    
    # Filter keys by balance using multiprocessing
    valid_keys = []
    if all_api_keys:
        # Determine number of processes
        if processes is None:
            processes = min(cpu_count(), len(all_api_keys))
        
        print(f"Checking balances for {len(all_api_keys)} keys using {processes} processes...")
        
        # Create process pool and check balances
        with Pool(processes=processes) as pool:
            results = pool.map(check_balance, all_api_keys)
        
        # Process results
        all_balance = 0
        for api_key, is_valid, balance in results:
            all_balance += balance
            if is_valid and balance >= min_balance:
                valid_keys.append((api_key, balance))
                print(f"Key {api_key[:8]}... has balance {balance} (≥ {min_balance}), including")
            elif is_valid:
                print(f"Key {api_key[:8]}... has balance {balance} (< {min_balance}), excluding")
            else:
                print(f"Key {api_key[:8]}... is invalid or failed balance check, excluding")
        print(f"Total keys: {len(valid_keys)} with combined balance: {all_balance}")
    
    # Create model entries for each combination of key, model_name, and api_base
    entry_index = 1
    for api_key, balance in valid_keys:
        for model_name in model_names:
            for api_base in api_bases:
                model_entry = {
                    "model_name": forward_names.get(model_name, model_name),
                    "litellm_params": {
                        "model": f"openai/{model_name}",
                        "api_base": api_base,
                        "api_key": api_key
                    }
                }
                
                model_list.append(model_entry)
                entry_index += 1
    
    return {"model_list": model_list}


def main():
    parser = argparse.ArgumentParser(description="Generate model_list.yaml from API key files")
    parser.add_argument(
        "--api-key-files", 
        nargs="+", 
        required=True,
        help="Paths to txt files containing API keys (one key per line)"
    )
    parser.add_argument(
        "--extra", 
        default="llm_router/extra_model_list.yaml",
        help="Paths to txt files containing API keys (one key per line)"
    )
    parser.add_argument(
        "--model-names", 
        nargs="+", 
        default=["zai-org/GLM-4.5", "zai-org/GLM-4.5-Air", "Qwen/Qwen3-235B-A22B-Instruct-2507", "Qwen/Qwen3-Coder-30B-A3B-Instruct", "Qwen/Qwen3-Coder-480B-A35B-Instruct", "zai-org/GLM-4.5V", "Qwen/Qwen3-30B-A3B-Instruct-2507"],
        help="Model names to use"
    )
    parser.add_argument(
        "--api-bases", 
        nargs="+", 
        default=["https://api.siliconflow.cn/v1/"],
        help="API base URLs"
    )
    parser.add_argument(
        "--min-balance",
        type=float,
        default=0.2,
        help="Minimum balance required for a key (default: 0.2)"
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=None,
        help="Number of processes to use for balance checking (default: CPU count)"
    )
    parser.add_argument(
        "--output", 
        default="model_list.yaml",
        help="Output YAML file path (default: model_list.yaml)"
    )
    
    args = parser.parse_args()
    
    try:
        # Generate the model list configuration
        config = create_model_list(
            args.api_key_files, 
            args.model_names, 
            args.api_bases,
            args.min_balance,
            args.processes
        )
        
        extra_model_list = yaml.safe_load(open(args.extra, "r"))["model_list"]
        
        config["router_settings"] = {
            "routing_strategy": "simple-shuffle",
        }
        config["litellm_settings"] = {
            "num_retries": 3,
            "set_verbose": True,
            "success_callback": ["langsmith"],
            
        }
        config["environment_variables"] = {
            "LANGSMITH_API_KEY": os.environ.get("LANGSMITH_API_KEY", ""),
            "LANGSMITH_PROJECT": "litellm",
            # "LANGSMITH_BASE_URL": os.environ.get("LANGSMITH_BASE_URL", ""),
        }
        config["model_list"].extend(extra_model_list)
        print(f"Adding extra model list: {extra_model_list}")
        
        # Write to YAML file
        with open(args.output, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"Successfully generated {args.output}")
        print(f"- Processed {len(args.api_key_files)} API key files")
        print(f"- Generated {len(config['model_list'])} model entries")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()