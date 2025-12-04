#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# 添加mle-bench模块路径
sys.path.insert(0, '/data/cyx/openlens-ai/modules/mle-bench')

def start_grading_server(data_dir, port=5000):
    """启动grading server"""
    print(f"启动grading server，数据目录: {data_dir}")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PRIVATE_DATA_DIR'] = data_dir
    env['COMPETITION_ID'] = 'aerial-cactus-identification'  # 使用一个已知的竞赛ID
    
    # 启动服务器进程
    cmd = [
        sys.executable, 
        '/data/cyx/openlens-ai/exp/mle_bench/grading_server/custom_grading_server.py',
        '--data-dir', data_dir,
        '--host', '127.0.0.1',
        '--port', str(port)
    ]
    
    process = subprocess.Popen(
        cmd, 
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务器启动
    time.sleep(5)
    
    # 检查服务器是否正常运行
    try:
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        if response.status_code == 200:
            print("Grading server已成功启动")
            return process
        else:
            print(f"Grading server启动失败，状态码: {response.status_code}")
            process.terminate()
            return None
    except Exception as e:
        print(f"无法连接到grading server: {e}")
        process.terminate()
        return None

def create_test_submission():
    """创建一个测试提交文件，基于真实测试数据随机生成分数"""
    import random
    import csv
    
    # 真实测试数据路径
    test_data_path = "/data/cyx/openlens-ai/datasets/mle-bench/aerial-cactus-identification/prepared/private/test.csv"
    test_file = "/tmp/test_submission.csv"
    
    # 读取真实测试数据的ID
    ids = []
    with open(test_data_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        for row in reader:
            ids.append(row[0])
    
    # 创建测试提交文件
    with open(test_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "has_cactus"])
        
        # 为所有ID生成随机分数（0到1之间的随机浮点数）
        for id in ids:
            score = random.random()  # 生成0到1之间的随机浮点数
            writer.writerow([id, score])
    
    return test_file

def test_validation_endpoint(port=5000):
    """测试验证端点"""
    print("测试验证端点...")
    
    # 创建测试提交文件
    test_file = create_test_submission()
    
    try:
        # 发送POST请求到验证端点
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"http://127.0.0.1:{port}/validate", 
                files=files, 
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("验证成功!")
            print(f"响应: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"验证失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"测试验证端点时出错: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

def stop_grading_server(process):
    """停止grading server"""
    if process:
        print("停止grading server...")
        process.terminate()
        process.wait()
        print("Grading server已停止")

def main():
    # 设置参数
    data_dir = "/data/cyx/openlens-ai/datasets/mle-bench"
    port = 5000
    
    # 检查数据目录是否存在
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在: {data_dir}")
        print("请确保已下载并解压了mle-bench数据集")
        return 1
    
    # 启动grading server
    server_process = start_grading_server(data_dir, port)
    if not server_process:
        return 1
    
    try:
        # 测试验证端点
        success = test_validation_endpoint(port)
        return 0 if success else 1
    finally:
        # 停止grading server
        stop_grading_server(server_process)

if __name__ == "__main__":
    sys.exit(main())
