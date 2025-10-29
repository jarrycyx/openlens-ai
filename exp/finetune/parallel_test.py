#!/usr/bin/env python3
"""
并行测试脚本，用于根据新的finetune数据集格式测试所有评估问题
"""

import csv
import subprocess
import concurrent.futures
import argparse
import os
from pathlib import Path

def load_questions(csv_file):
    """从CSV文件加载问题，支持新的数据集格式"""
    questions = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append({
                'question': row['Question'],
                'dataset': row['Dataset'],
                'difficulty': row['Difficulty'],
                'lang': row['Lang']
            })
    return questions

def run_test(question_data, thread_id, email):
    """运行单个测试"""
    question = question_data['question']
    dataset_path = question_data['dataset']
    difficulty = question_data['difficulty']
    lang = question_data['lang']
    
    cmd = [
        'python', '-m', 'openlens_ai.main',
        '--question', question,
        '--dataset-path', dataset_path,
        '--thread-id', thread_id,
        '--language', lang,
        '--notify-email', email
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Difficulty: {difficulty}, Language: {lang}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: {dataset_path} - {thread_id} (Difficulty: {difficulty}, Lang: {lang})")
    else:
        print(f"FAILED: {dataset_path} - {thread_id} (Difficulty: {difficulty}, Lang: {lang})")
        print(f"Error: {result.stderr}")
    
    return result.returncode == 0

def create_thread_id(question_data):
    """为测试创建线程ID"""
    question = question_data['question']
    dataset_path = question_data['dataset']
    difficulty = question_data['difficulty']
    lang = question_data['lang']
    
    # 从数据集路径提取名称
    dataset_name = Path(dataset_path).name
    # 简化问题作为标识符
    question_part = ''.join(c for c in question if c.isalnum() or c in ' _-')[:20]
    return f"test_{dataset_name}_{difficulty}_{lang}_{question_part}".replace(' ', '_')

def main():
    parser = argparse.ArgumentParser(description='并行测试脚本 - 支持新的finetune数据集格式')
    parser.add_argument('--csv-file', default='exp/finetune/openlens_finetune_v2.csv', 
                        help='包含问题的CSV文件路径 (默认: exp/finetune/openlens_finetune_v2.csv)')
    parser.add_argument('--email', default='dzdzzd@126.com', 
                        help='接收通知的邮箱')
    parser.add_argument('--max-workers', type=int, default=2, 
                        help='并行执行的最大工作线程数')
    parser.add_argument('--difficulty', choices=['Easy', 'Medium', 'Hard'], 
                        help='只运行指定难度的问题')
    parser.add_argument('--lang', choices=['chs', 'eng'], 
                        help='只运行指定语言的问题')
    parser.add_argument('--start-index', type=int, default=0, help='从问题列表的起始索引开始执行测试')
    
    args = parser.parse_args()
    
    # os.system("bash llm_router/env_api_perf.sh")
    
    
    # 加载所有问题
    questions = load_questions(args.csv_file)
    print(f"Loaded {len(questions)} questions from {args.csv_file}")
    
    # 根据难度和语言筛选问题
    if args.difficulty:
        questions = [q for q in questions if q['difficulty'] == args.difficulty]
        print(f"筛选后剩余 {len(questions)} 个 {args.difficulty} 难度的问题")
    
    if args.lang:
        questions = [q for q in questions if q['lang'] == args.lang]
        print(f"筛选后剩余 {len(questions)} 个 {args.lang} 语言的问题")
    
    # 准备所有测试任务
    tasks = []
    for question_data in questions:
        thread_id = create_thread_id(question_data)
        tasks.append((question_data, thread_id, args.email))
            
    tasks = tasks[args.start_index:]
    print(f"跳过 {args.start_index} 个问题")
    
    print(f"准备执行 {len(tasks)} 个测试任务，使用 {args.max_workers} 个并行工作线程")
    
    # 并行执行测试
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(run_test, question_data, thread_id, email): (question_data, thread_id)
            for question_data, thread_id, email in tasks
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_task):
            question_data, thread_id = future_to_task[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
            except Exception as exc:
                print(f'任务 {thread_id} 产生异常: {exc}')
    
    print(f"\n测试完成: {success_count}/{len(tasks)} 个任务成功执行")

if __name__ == "__main__":
    main()