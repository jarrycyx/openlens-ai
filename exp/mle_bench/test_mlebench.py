#!/usr/bin/env python3
import os
import sys
import argparse
import multiprocessing
from pathlib import Path
import subprocess
import time
import signal
import atexit

def get_dataset_info(dataset_path):
    """获取数据集信息，包括描述和路径"""
    dataset_name = os.path.basename(dataset_path)
    public_path = os.path.join(dataset_path, "prepared", "public")
    description_path = os.path.join(public_path, "description.md")
    
    # 读取描述文件
    description = ""
    if os.path.exists(description_path):
        with open(description_path, 'r', encoding='utf-8') as f:
            description = f.read()
    
    # 读取基准指令
    instructions_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
    instructions = ""
    if os.path.exists(instructions_path):
        with open(instructions_path, 'r', encoding='utf-8') as f:
            instructions = f.read()
    
    # 组合问题
    question = f"{instructions}\n\n# Task-specific Instructions\n\n{description}"
    
    return {
        "name": dataset_name,
        "path": public_path,
        "question": question
    }

def run_single_test(dataset_info, thread_id, config_path, email):
    """运行单个数据集的测试"""
    cmd = [
        "python", "-m", "openlens_ai.main",
        "--question", dataset_info["question"],
        "--dataset-path", dataset_info["path"],
        "--thread-id", f"{thread_id}-{dataset_info['name']}",
        "--notify-email", email,
        "--interrupt-after-subgraph", "none",
        "--language", "eng",
        "--domain", "medical",
        "--config", config_path
    ]
    
    print(f"Running test for dataset: {dataset_info['name']} with thread ID: {thread_id}-{dataset_info['name']}")
    
    # 运行命令
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # 记录结果
    log_dir = "/data/cyx/openlens-ai/exp/mle_bench/runs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{dataset_info['name']}_thread_{thread_id}.log")
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Execution time: {end_time - start_time:.2f} seconds\n")
        f.write(f"Return code: {result.returncode}\n")
        f.write("\n=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
    
    print(f"Completed test for dataset: {dataset_info['name']}. Log saved to: {log_file}")
    return result.returncode == 0

def start_grading_server(datasets_dir):
    """启动grading_server"""
    script_path = "/data/cyx/openlens-ai/exp/mle_bench/grading_server/start_grading_server.sh"
    cmd = [script_path, datasets_dir]
    
    print(f"Starting grading server with datasets directory: {datasets_dir}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to start grading server: {result.stderr}")
        return False
    
    print("Grading server started successfully")
    return True

def stop_grading_server():
    """停止grading_server"""
    script_path = "/data/cyx/openlens-ai/exp/mle_bench/grading_server/stop_grading_server.sh"
    cmd = [script_path]
    
    print("Stopping grading server...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to stop grading server: {result.stderr}")
        return False
    
    print("Grading server stopped successfully")
    return True

def main():
    parser = argparse.ArgumentParser(description="Test MLE-bench datasets")
    parser.add_argument("--processes", type=int, default=1, help="Number of processes to run in parallel")
    parser.add_argument("--config", type=str, default="exp/config.toml", help="Path to config file")
    parser.add_argument("--email", type=str, default="dzdzzd@126.com", help="Email for notifications")
    parser.add_argument("--datasets-dir", type=str, default="/data/cyx/openlens-ai/datasets/mle-bench", 
                       help="Path to datasets directory")
    parser.add_argument("--skip-server", action="store_true", help="Skip starting/stopping grading server")
    
    args = parser.parse_args()
    
    # 注册退出时停止服务器的函数
    if not args.skip_server:
        atexit.register(stop_grading_server)
        
        # 启动grading_server
        if not start_grading_server(args.datasets_dir):
            print("Failed to start grading server. Exiting.")
            sys.exit(1)
        
        # 等待服务器完全启动
        print("Waiting for grading server to be fully ready...")
        time.sleep(5)
    
    # 获取所有数据集
    datasets_dir = Path(args.datasets_dir)
    dataset_dirs = [d for d in datasets_dir.iterdir() if d.is_dir() and (d / "prepared" / "public").exists()]
    
    print(f"Found {len(dataset_dirs)} datasets")
    
    # 获取每个数据集的信息
    datasets_info = []
    for dataset_dir in dataset_dirs:
        info = get_dataset_info(str(dataset_dir))
        datasets_info.append(info)
        print(f"Added dataset: {info['name']}")
    
    # 创建进程池
    pool = multiprocessing.Pool(processes=args.processes)
    
    # 准备参数
    tasks = []
    for i, dataset_info in enumerate(datasets_info):
        thread_id = f"mlebench-{i % args.processes}"
        tasks.append((dataset_info, thread_id, args.config, args.email))
    
    # 运行任务
    results = pool.starmap(run_single_test, tasks)
    
    # 关闭进程池
    pool.close()
    pool.join()
    
    # 统计结果
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\nTest completed: {success_count}/{total_count} datasets passed")
    
    # 保存汇总结果
    summary_file = "/data/cyx/openlens-ai/exp/mle_bench/runs/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"MLE-bench Test Summary\n")
        f.write(f"=====================\n")
        f.write(f"Total datasets: {total_count}\n")
        f.write(f"Successful: {success_count}\n")
        f.write(f"Failed: {total_count - success_count}\n")
        f.write(f"Success rate: {success_count/total_count*100:.2f}%\n")
        
        for i, (dataset_info, result) in enumerate(zip(datasets_info, results)):
            status = "SUCCESS" if result else "FAILED"
            f.write(f"{i+1}. {dataset_info['name']}: {status}\n")
    
    print(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()
