#!/usr/bin/env python3
import os
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import argparse
import glob

def extract_accumulated_cost(json_file_path):
    """从JSON文件中提取最大的accumulated_cost值"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用正则表达式查找所有accumulated_cost值
        import re
        pattern = r'"accumulated_cost":\s*([\d.]+)'
        matches = re.findall(pattern, content)
        
        if not matches:
            print(f"警告: 文件 {json_file_path} 中未找到accumulated_cost")
            return None
            
        # 转换为浮点数并返回最大值
        costs = [float(match) for match in matches]
        return max(costs)
    except Exception as e:
        print(f"处理文件 {json_file_path} 时出错: {e}")
        return None

def analyze_directory(directory_path):
    """分析目录中的所有JSON文件"""
    # 查找所有JSON文件
    json_files = glob.glob(os.path.join(directory_path, '**/*.json'), recursive=True)
    
    results = []
    
    for json_file in json_files:
        # 获取文件创建时间
        creation_time = os.path.getctime(json_file)
        creation_datetime = datetime.fromtimestamp(creation_time)
        
        # 提取accumulated_cost
        cost = extract_accumulated_cost(json_file)
        
        if cost is not None:
            results.append({
                'file_path': json_file,
                'file_name': os.path.basename(json_file),
                'creation_time': creation_datetime,
                'cost': cost
            })
    
    # 按创建时间排序
    results.sort(key=lambda x: x['creation_time'])
    
    return results

def plot_costs(results, output_path):
    """绘制token消耗图表，左边是单个文件的token消耗，右边是累计token消耗"""
    if not results:
        print("没有数据可绘制")
        return
    
    # 提取时间和成本数据
    times = [result['creation_time'] for result in results]
    costs = [result['cost'] for result in results]
    
    # 计算累计token消耗
    cumulative_costs = []
    total = 0
    for cost in costs:
        total += cost
        cumulative_costs.append(total)
    
    # 创建双图布局
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左图：单个文件的token消耗
    ax1.plot(times, costs, marker='o', linestyle='-', alpha=0.7, color='blue')
    ax1.set_title('Token Consumption Per File', fontsize=14)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Accumulated Cost', fontsize=12)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # 右图：累计token消耗
    ax2.plot(times, cumulative_costs, marker='o', linestyle='-', alpha=0.7, color='red')
    ax2.set_title('Cumulative Token Consumption', fontsize=14)
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Total Accumulated Cost', fontsize=12)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='分析JSON文件中的token消耗')
    parser.add_argument('directory', help='要分析的目录路径')
    parser.add_argument('--output', '-o', default='/data/cyx/openlens-ai/exp/token_costs_plot.png', 
                       help='输出图表的路径')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"开始分析目录: {args.directory}")
    results = analyze_directory(args.directory)
    
    if results:
        print(f"找到 {len(results)} 个有效的JSON文件")
        print("\n前5个文件的数据:")
        for i, result in enumerate(results[:5]):
            print(f"{i+1}. {result['file_name']}: {result['cost']} (创建时间: {result['creation_time']})")
        
        plot_costs(results, args.output)
        print(f"分析完成，图表已保存到: {args.output}")
    else:
        print("分析失败，未找到有效数据")

if __name__ == "__main__":
    main()
