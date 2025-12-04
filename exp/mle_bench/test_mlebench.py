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
import socket
import random
import requests
from datetime import datetime



def is_port_available(port):
    """检查端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def find_available_port(start_port=5000, max_attempts=100):
    """找到一个可用的端口"""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    # 如果都不可用，随机选择一个端口
    while True:
        port = random.randint(5000, 6000)
        if is_port_available(port):
            return port


def get_dataset_info(dataset_path):
    """获取数据集信息，包括描述和路径"""
    dataset_name = os.path.basename(dataset_path)
    public_path = os.path.join(dataset_path, "prepared", "public")
    description_path = os.path.join(public_path, "description.md")

    # 读取描述文件
    description = ""
    if os.path.exists(description_path):
        with open(description_path, "r", encoding="utf-8") as f:
            description = f.read()

    # 读取基准指令
    instructions_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
    instructions = ""
    if os.path.exists(instructions_path):
        with open(instructions_path, "r", encoding="utf-8") as f:
            instructions = f.read()

    # 组合问题
    question = f"{instructions}\n\n# Task-specific Instructions\n\n{description}"

    return {"name": dataset_name, "path": public_path, "question": question}


def start_task_grading_server(dataset_name, datasets_dir):
    """为单个任务启动grading server"""
    # 找到一个可用的端口
    port = find_available_port(start_port=random.randint(5000, 6000))

    # 使用数据集名称作为竞赛ID
    competition_id = dataset_name

    # 直接调用custom_grading_server.py
    cmd = [
        "python3",
        "/data/cyx/openlens-ai/exp/mle_bench/grading_server/custom_grading_server.py",
        "--competition-id",
        competition_id,
        "--data-dir",
        datasets_dir,
        "--port",
        str(port),
    ]

    print(f"Starting grading server for dataset: {dataset_name} on port {port}")

    # 使用Popen启动后台进程，不等待进程完成
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 等待一小段时间让进程启动
    time.sleep(1)

    # 检查进程是否仍在运行
    if process.poll() is not None:
        # 进程已经退出，获取输出
        stdout, stderr = process.communicate()
        print(f"Failed to start grading server for {dataset_name}: {stderr.decode('utf-8')}")
        return None, None, None

    print(f"Grading server for {dataset_name} started successfully on port {port}")

    # 等待服务器启动
    time.sleep(3)

    # 检查服务器是否正常运行
    try:
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        if response.status_code == 200:
            return port, competition_id, process
        else:
            print(f"Grading server for {dataset_name} health check failed, status code: {response.status_code}")
            # 停止进程
            process.terminate()
            return None, None, None
    except Exception as e:
        print(f"无法连接到grading server for {dataset_name}: {e}")
        # 停止进程
        process.terminate()
        return None, None, None


def stop_task_grading_server(port):
    """停止单个任务的grading server"""
    try:
        # 使用lsof查找占用指定端口的进程
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            # 获取进程ID
            pid = result.stdout.strip()

            # 终止进程
            os.kill(int(pid), signal.SIGTERM)
            print(f"Stopped grading server with PID {pid} on port {port}")
            return True
        else:
            print(f"No process found running on port {port}")
            return False
    except Exception as e:
        print(f"Failed to stop grading server on port {port}: {e}")
        return False


def run_single_test(dataset_info, thread_id, config_path, email, datasets_dir):
    """运行单个数据集的测试"""
    # 启动该任务的grading server
    server_port, competition_id, server_process = start_task_grading_server(dataset_info["name"], datasets_dir)
    dataset_info["question"] = dataset_info["question"].replace("{grading_server_port}", str(server_port))

    if server_port is None:
        print(f"Failed to start grading server for {dataset_info['name']}. Skipping test.")
        return False
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        cmd = [
            "python",
            "-m",
            "openlens_ai.main",
            "--question",
            dataset_info["question"],
            "--dataset-path",
            dataset_info["path"],
            "--thread-id",
            f"{thread_id}-{dataset_info['name']}-{timestamp}",
            "--notify-email",
            email,
            "--interrupt-after-subgraph",
            "none",
            "--language",
            "eng",
            "--domain",
            "general",
            "--config",
            config_path,
        ]

        print(f"Running test for dataset: {dataset_info['name']} with thread ID: {thread_id}-{dataset_info['name']}-{timestamp}")

        # 运行命令
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        # 记录结果
        log_dir = "/data/cyx/openlens-ai/exp/mle_bench/runs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"{dataset_info['name']}_thread_{thread_id}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Execution time: {end_time - start_time:.2f} seconds\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Grading server port: {server_port}\n")
            f.write(f"Competition ID: {competition_id}\n")
            f.write("\n=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)

        print(f"Completed test for dataset: {dataset_info['name']}. Log saved to: {log_file}")
        return result.returncode == 0
    finally:
        # 确保停止grading server
        if server_process is not None:
            server_process.terminate()
            print(f"Stopped grading server for {dataset_info['name']} on port {server_port}")


def main():
    parser = argparse.ArgumentParser(description="Test MLE-bench datasets")
    parser.add_argument("--processes", type=int, default=4, help="Number of processes to run in parallel")
    parser.add_argument("--config", type=str, default="exp/mle_bench/config.toml", help="Path to config file")
    parser.add_argument("--email", type=str, default="dzdzzd@126.com", help="Email for notifications")
    parser.add_argument(
        "--datasets-dir",
        type=str,
        default="/data/cyx/openlens-ai/datasets/mle-bench",
        help="Path to datasets directory",
    )

    args = parser.parse_args()

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
        tasks.append((dataset_info, thread_id, args.config, args.email, args.datasets_dir))

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
    with open(summary_file, "w", encoding="utf-8") as f:
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
