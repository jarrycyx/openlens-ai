import os
import json
import glob
import csv
import re
from collections import defaultdict
from pathlib import Path


def get_base_thread_id(thread_id):
    """
    从thread_id中提取基础ID，去除resume部分
    例如: test_eicu-demo_How_accurately_can_30-day_mort-resume-2 -> test_eicu-demo_How_accurately_can_30-day_mort
    """
    if "_resume_" in thread_id:
        return "_".join(thread_id.split("_resume_")[:1])
    return thread_id


def count_resume_parts(thread_id):
    """
    计算thread_id中resume部分的数量
    """
    return thread_id.count("_resume_")


def validate_experiment_progress(experiment_root="outputs", dataset_file="exp/eval/openlens_eval_dataset.csv"):
    """
    验证实验进度的函数
    
    Args:
        experiment_root (str): 实验文件夹路径，默认为"outputs"
        dataset_file (str): 数据集对照文件路径，默认为"exp/eval/openlens_eval_dataset.csv"
    """
    # 读取数据集对照文件中的问题列表
    expected_questions = []
    if os.path.exists(dataset_file):
        with open(dataset_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                expected_questions.append(row['Question'])
        print(f"Loaded {len(expected_questions)} questions from dataset file")
        print("-" * 50)
    else:
        print(f"Dataset file {dataset_file} not found")
        expected_questions = []
    
    # 查找所有以test开头且包含config.json的文件夹
    config_files = glob.glob(os.path.join(experiment_root, "**/test*/config.json"), recursive=True)
    
    # 读取所有config.json中的信息
    experiments_data = []
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                question = config.get('question')
                dataset = config.get('dataset_path', 'unknown_dataset')
                thread_id = config.get('thread_id', '')
                
                if question and thread_id:
                    experiments_data.append({
                        'config_file': config_file,
                        'question': question,
                        'dataset': dataset,
                        'thread_id': thread_id,
                        'base_thread_id': get_base_thread_id(thread_id),
                        'resume_count': count_resume_parts(thread_id)
                    })
        except Exception as e:
            print(f"Error reading {config_file}: {e}")
    
    # 合并中断后重新执行的任务
    # 对于每个base_thread_id，只保留resume_count最多的那个
    merged_experiments = {}
    for exp in experiments_data:
        base_id = exp['base_thread_id']
        if (base_id not in merged_experiments) or (exp['resume_count'] > merged_experiments[base_id]['resume_count']):
            merged_experiments[base_id] = exp
    
    # 按question+dataset分组
    question_dataset_groups = defaultdict(list)
    for exp in merged_experiments.values():
        group_key = f"{exp['question']} | Dataset: {exp['dataset']}"
        question_dataset_groups[group_key].append(exp)
    
    # 打印每个question+dataset组合的执行数量
    print("Question + Dataset Execution Counts:")
    print("-" * 50)
    for group_key, experiments in question_dataset_groups.items():
        print(f"Group: {group_key}")
        print(f"Execution count: {len(experiments)}")
        print()
    
    # 读取每个实验的node_call_stack.json的最后一个元素
    print("Latest Node Call Stack Elements:")
    print("-" * 50)
    
    # 统计完成情况
    completed_experiments = defaultdict(int)
    
    # 准备用于保存到CSV的数据
    csv_data = []
    
    for group_key, experiments in question_dataset_groups.items():
        print(f"Group: {group_key}")
        completed_count = 0
        # 收集所有thread_id
        thread_ids = []
        latest_calls = []
        
        for experiment in experiments:
            # 添加thread_id到列表
            thread_ids.append(experiment['thread_id'])
            
            # 获取config.json所在的文件夹名
            config_dir = os.path.dirname(experiment['config_file'])
            
            # 构建node_call_stack.json的路径
            node_call_stack_path = os.path.join(
                config_dir, "node_call_stack.json"
            )
            
            if os.path.exists(node_call_stack_path):
                try:
                    with open(node_call_stack_path, 'r') as f:
                        node_calls = json.load(f)
                        if node_calls and isinstance(node_calls, list):
                            latest_call = node_calls[-1]
                            latest_calls.append(latest_call)
                            print(f"  {config_dir}: {latest_call}")
                            
                            # 如果最新节点是subgraph_latex_writer.latex_validator_node，则标记为完成
                            if latest_call == 'subgraph_latex_writer.latex_validator_node':
                                completed_count += 1
                        else:
                            latest_calls.append("Empty or invalid node_call_stack.json")
                            print(f"  {config_dir}: Empty or invalid node_call_stack.json")
                except Exception as e:
                    latest_calls.append(f"Error: {e}")
                    print(f"  {config_dir}: Error reading node_call_stack.json: {e}")
            else:
                latest_calls.append("node_call_stack.json not found")
                print(f"  {config_dir}: node_call_stack.json not found")
        
        completed_experiments[group_key] = completed_count
        print(f"  Completed experiments in this group: {completed_count}/{len(experiments)}")
        print()
        
        # 添加到CSV数据
        csv_data.append({
            'question': experiments[0]['question'],
            'dataset': experiments[0]['dataset'],
            'thread_ids': '; '.join(thread_ids),
            'latest_nodes': '; '.join(latest_calls),
            'completed': 'Yes' if completed_count == len(experiments) else 'No'
        })
    
    # 按dataset然后question的顺序排序
    csv_data.sort(key=lambda x: (x['dataset'], x['question']))
    
    # 显示每个问题的总体完成进度
    if expected_questions:
        print("Overall Progress by Question:")
        print("-" * 50)
        for question in expected_questions:
            matching_groups = [key for key in question_dataset_groups.keys() if key.startswith(question)]
            total_experiments = sum(len(question_dataset_groups[key]) for key in matching_groups)
            total_completed = sum(completed_experiments[key] for key in matching_groups)
            
            if matching_groups:
                print(f"Question: {question}")
                print(f"  Progress: {total_completed}/{total_experiments} experiments completed")
                if total_experiments > 0:
                    print(f"  Percentage: {total_completed/total_experiments*100:.1f}%")
                print()
            else:
                print(f"Question: {question}")
                print(f"  Progress: 0/0 experiments completed (no experiments found)")
                print()
    
    # 保存到CSV文件
    csv_file_path = os.path.join(experiment_root, "experiment_summary.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['question', 'dataset', 'thread_ids', 'latest_nodes', 'completed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
    
    print(f"Experiment summary saved to: {csv_file_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate experiment progress")
    parser.add_argument(
        "--experiment-root", 
        default="outputs", 
        help="Root directory for experiments (default: outputs)"
    )
    parser.add_argument(
        "--dataset-file",
        default="exp/eval/openlens_eval_dataset.csv",
        help="Dataset file for reference questions (default: exp/eval/openlens_eval_dataset.csv)"
    )
    
    args = parser.parse_args()
    validate_experiment_progress(args.experiment_root, args.dataset_file)