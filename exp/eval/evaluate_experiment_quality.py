import os
import csv
import json
import glob
from pathlib import Path
import dotenv
from openai import OpenAI
from multiprocessing import Pool, cpu_count
from functools import partial
import numpy as np
import traceback
import time

# 加载环境变量
dotenv.load_dotenv()


def init_llm_client():
    """初始化LLM客户端"""
    # client = OpenAI(
    #     api_key="52b052aaa86d40acbde12a7f58937073.CDUoIu9w5rwizB79",
    #     base_url="https://open.bigmodel.cn/api/paas/v4/",
    # )
    client = OpenAI(
        api_key="0",
        base_url="http://127.0.0.1:8077/v1",
    )
    
    return client


def read_file_content(file_path):
    """读取文件内容，如果文件不存在则返回提示信息"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    else:
        return "File does not exist"


def parse_evaluation_scores(evaluation_text):
    """解析评估文本中的分数"""
    # 初始化分数字典
    scores = {
        'plan_completion': 0,
        'code_execution': 0,
        'result_validity': 0,
        'paper_completeness': 0,
        'conclusion_quality': 0,
    }
    
    # 按行分割文本
    lines = evaluation_text.split('\n')
    
    # 解析各维度分数
    for line in lines:
        if '1. Plan Completion Score:' in line:
            try:
                score = line.split('Score:')[1].split('/')[0].strip()
                scores['plan_completion'] = int(score)
            except:
                scores['plan_completion'] = 0
        elif '2. Code Execution Score:' in line:
            try:
                score = line.split('Score:')[1].split('/')[0].strip()
                scores['code_execution'] = int(score)
            except:
                scores['code_execution'] = 0
        elif '3. Result Validity Score:' in line:
            try:
                score = line.split('Score:')[1].split('/')[0].strip()
                scores['result_validity'] = int(score)
            except:
                scores['result_validity'] = 0
        elif '4. Paper Completeness Score:' in line:
            try:
                score = line.split('Score:')[1].split('/')[0].strip()
                scores['paper_completeness'] = int(score)
            except:
                scores['paper_completeness'] = 0
        elif '5. Conclusion Quality Score:' in line:
            try:
                score = line.split('Score:')[1].split('/')[0].strip()
                scores['conclusion_quality'] = int(score)
            except:
                scores['conclusion_quality'] = 0
    
    return scores


def evaluate_single_experiment_parallel(experiment_root, model, experiment_data):
    """并行评估单个实验的质量"""
    print(f"Evaluating experiment: {experiment_data['question']}")
    
    # 初始化LLM客户端
    client = init_llm_client()
    
    # 从thread_ids中选择第一个作为实验路径
    thread_ids = experiment_data['thread_ids'].split('; ')
    if not thread_ids:
        print(f"  Skipping experiment, no thread_id found")
        return {
            'question': experiment_data['question'],
            'dataset': experiment_data['dataset'],
            'thread_ids': experiment_data['thread_ids'],
            'evaluation': "Skipping experiment, no thread_id found",
            'plan_completion': '',
            'code_execution': '',
            'result_validity': '',
            'paper_completeness': '',
            'conclusion_quality': '',
        }
        
    # 构建实验路径
    thread_id = thread_ids[0]
    experiment_path = os.path.join(experiment_root, thread_id)
    
    if not os.path.exists(experiment_path):
        print(f"  Skipping experiment, path does not exist: {experiment_path}")
        return {
            'question': experiment_data['question'],
            'dataset': experiment_data['dataset'],
            'thread_ids': experiment_data['thread_ids'],
            'evaluation': f"Experiment path does not exist: {experiment_path}",
            'plan_completion': '',
            'code_execution': '',
            'result_validity': '',
            'paper_completeness': '',
            'conclusion_quality': ''
        }
    
    # 构建各个文件的路径
    # 修改为查找所有subtask_*_report.md文件
    subtask_reports_dir = os.path.join(experiment_path, "workspace")
    subtask_report_paths = glob.glob(os.path.join(subtask_reports_dir, "subtask_*_report.md"))
    
    literature_check_report_path = os.path.join(experiment_path, "workspace", "manuscript", "literature_check_report.md")
    latex_quality_report_path = os.path.join(experiment_path, "workspace", "manuscript", "latex_quality_report.md")
    main_tex_path = os.path.join(experiment_path, "workspace", "manuscript", "main.tex")
    
    # 读取所有subtask报告内容
    subtask_reports_content = ""
    if subtask_report_paths:
        for report_path in sorted(subtask_report_paths):  # 按字母顺序排序以确保一致性
            content = read_file_content(report_path)
            report_name = os.path.basename(report_path)
            subtask_reports_content += f"\n\n--- {report_name} ---\n\n{content}"
    else:
        subtask_reports_content = "No subtask reports found"
    
    # 读取其他文件内容
    literature_check_report_content = read_file_content(literature_check_report_path)
    latex_quality_report_content = read_file_content(latex_quality_report_path)
    main_tex_content = read_file_content(main_tex_path)
    
    # 构建评估提示
    evaluation_prompt = f"""
Please evaluate the quality of the following experiment and analyze it according to the following five dimensions:

1. Has the experimental plan been successfully completed?
2. Are there any unresolved errors during code execution?
3. Are the experimental results reasonable and valid data obtained?
4. Is the paper structure complete? Are there any unresolved LaTeX compilation errors? Does the paper have blank images, placeholder text, or invalid content?
5. Does the paper reach an effective conclusion? Is the text accurate and elegant enough?

For each dimension, please provide a score out of 3 and a brief explanation (1 for severe issues that makes the research fundamentally wrong, 2 for moderate issues that still makes the research valid, 3 for minor/no issues).

Please follow EXACTLY the format in the example below:

1. Plan Completion Score: x/3, Reason: The experimental plan was mostly completed but some steps were skipped.
2. Code Execution Score: x/3, Reason: Code executed with minor warnings but no critical errors.
3. Result Validity Score: x/3, Reason: Results are reasonable but could be more comprehensive.
4. Paper Completeness Score: x/3, Reason: Paper structure is complete but missing some sections.
5. Conclusion Quality Score: x/3, Reason: Conclusion is well-written and supported by results.

The content of the experiment-related files is as follows:

1. Subtask reports (subtask_*_report.md):
{subtask_reports_content[:40*1000*4]}...

4. Main Tex file (main.tex):
{main_tex_content[:40*1000*4]}...
"""

    # 构建消息
    messages = [
        {"role": "system", "content": "You are a professional scientific research evaluation expert who can objectively evaluate the quality of scientific research experiments. You always follow the exact format provided in the examples when giving scores and reasons."},
        {"role": "user", "content": evaluation_prompt}
    ]
    
    
    for _ in range(10):
        try:
            # 调用LLM进行评估
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            evaluation = response.choices[0].message.content
        except Exception as e:
            evaluation = f"Error during evaluation: {str(e)}"
        
        # 解析评分
        scores = parse_evaluation_scores(evaluation)
        for k, score in scores.items():
            if score == 0:
                time.sleep(20)
                continue
    
    # 保存评估结果
    result = {
        'question': experiment_data['question'],
        'dataset': experiment_data['dataset'],
        'thread_ids': experiment_data['thread_ids'],
        'evaluation': evaluation,
        'plan_completion': scores['plan_completion'],
        'code_execution': scores['code_execution'],
        'result_validity': scores['result_validity'],
        'paper_completeness': scores['paper_completeness'],
        'conclusion_quality': scores['conclusion_quality'],
    }
    
    print(f"  Evaluation completed for: {experiment_data['question']}")
    return result


def evaluate_experiments_from_csv(csv_file_path, experiment_root="outputs", model="glm-4.5", num_processes=4):
    """从CSV文件读取实验列表并评估每个实验的质量"""
    
    # 读取CSV文件
    experiments = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                experiments.append(row)
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None
    
    # experiments = experiments[:1]
    
    print(f"Using {num_processes} processes to evaluate {len(experiments)} experiments")
    
    # 创建部分函数，固定一些参数
    evaluate_func = partial(evaluate_single_experiment_parallel, experiment_root, model)
    
    # 使用多进程并行评估实验
    try:
        with Pool(processes=num_processes) as pool:
            evaluation_results = pool.map(evaluate_func, experiments)
    except Exception as e:
        print(f"Error during parallel processing: {str(e)}")
        traceback.print_exc()
        return None
    
    # 保存评估结果到CSV文件
    output_csv_path = csv_file_path.replace('.csv', '_evaluated.csv')
    score_csv_path = csv_file_path.replace('.csv', '_scores.csv')
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['question', 'dataset', 'thread_ids', 'evaluation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in evaluation_results:
                writer.writerow({k: result[k] for k in fieldnames})
        
        with open(score_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['question', 'dataset', 'thread_ids', 'plan_completion', 'code_execution', 
                        'result_validity', 'paper_completeness', 'conclusion_quality']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in evaluation_results:
                writer.writerow({k: result[k] for k in fieldnames})
        
        print(f"Evaluation results saved to: {output_csv_path}")
        return output_csv_path
    except Exception as e:
        print(f"Error writing output CSV file: {str(e)}")
        return None
    


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate experiment quality")
    parser.add_argument(
        "--csv-file",
        default="exp/saved_exp/eval_0915/experiment_summary.csv",
        help="Experiment summary CSV file path (default: outputs/experiment_summary.csv)"
    )
    parser.add_argument(
        "--experiment-root",
        default="exp/saved_exp/eval_0915",
        help="Experiment root directory (default: outputs)"
    )
    parser.add_argument(
        "--model",
        default="glm-4.5",
        help="Model to use for evaluation (default: glm-4.5)"
    )
    parser.add_argument(
        "--num-processes",
        type=int,
        default=4,
        help="Number of processes to use (default: number of CPU cores)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file does not exist: {args.csv_file}")
        exit(1)
    
    evaluate_experiments_from_csv(args.csv_file, args.experiment_root, args.model, args.num_processes)