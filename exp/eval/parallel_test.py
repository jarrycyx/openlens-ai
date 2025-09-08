#!/usr/bin/env python3
"""
并行测试脚本，用于在两个数据集上测试所有评估问题
"""

import csv
import subprocess
import concurrent.futures
import argparse
import os
from pathlib import Path

def load_questions(csv_file):
    """从CSV文件加载问题"""
    questions = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row['Question'])
    return questions

def run_test(question, dataset_path, thread_id, email):
    """运行单个测试"""
    cmd = [
        'python', '-m', 'openlens_ai.build_graph',
        '--question', question,
        '--dataset-path', dataset_path,
        '--thread-id', thread_id,
        '--email', email
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: {dataset_path} - {thread_id}")
    else:
        print(f"FAILED: {dataset_path} - {thread_id}")
        print(f"Error: {result.stderr}")
    
    return result.returncode == 0

def create_thread_id(question, dataset_path):
    """为测试创建线程ID"""
    # 从数据集路径提取名称
    dataset_name = Path(dataset_path).name
    # 简化问题作为标识符
    question_part = ''.join(c for c in question if c.isalnum() or c in ' _-')[:30]
    return f"test_{dataset_name}_{question_part}".replace(' ', '_')

def main():
    parser = argparse.ArgumentParser(description='并行测试脚本')
    parser.add_argument('--csv-file', default='exp/eval/openlens_eval_dataset.csv', 
                        help='包含问题的CSV文件路径')
    parser.add_argument('--email', default='dzdzzd@126.com', 
                        help='接收通知的邮箱')
    parser.add_argument('--max-workers', type=int, default=4, 
                        help='并行执行的最大工作线程数')
    parser.add_argument('--datasets', nargs='+', 
                        default=['datasets/mimic-iv-icu', 'datasets/eicu-demo'],
                        help='要测试的数据集路径列表')
    
    args = parser.parse_args()
    
    # os.system("bash llm_router/env_api_perf.sh")
    
    
    # 加载所有问题
    questions = load_questions(args.csv_file)
    print(f"Loaded {len(questions)} questions from {args.csv_file}")
    
    # 准备所有测试任务
    tasks = []
    for question in questions:
        for dataset_path in args.datasets:
            thread_id = create_thread_id(question, dataset_path)
            tasks.append((question, dataset_path, thread_id, args.email))
    
    print(f"准备执行 {len(tasks)} 个测试任务，使用 {args.max_workers} 个并行工作线程")
    
    # 并行执行测试
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(run_test, question, dataset_path, thread_id, email): (question, dataset_path, thread_id)
            for question, dataset_path, thread_id, email in tasks
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_task):
            question, dataset_path, thread_id = future_to_task[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
            except Exception as exc:
                print(f'任务 {thread_id} 产生异常: {exc}')
    
    print(f"\n测试完成: {success_count}/{len(tasks)} 个任务成功执行")

if __name__ == "__main__":
    main()