import openai
import time
import argparse
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def test_openai_performance(api_key, model, prompt, num_requests, max_workers, base_url=None, api_version=None, organization=None):
    """
    测试 OpenAI API 的吞吐量和延迟性能
    
    参数:
        api_key: OpenAI API 密钥
        model: 要测试的模型名称
        prompt: 发送的提示文本
        num_requests: 要发送的请求总数
        max_workers: 并发工作线程数
        base_url: 自定义API端点URL (可选)
        api_version: API版本 (可选)
        organization: 组织ID (可选)
    """
    # 配置OpenAI客户端
    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        organization=organization
    )
    
    # 存储统计信息
    latencies = []
    successful_requests = 0
    failed_requests = 0
    start_times = [0] * num_requests
    end_times = [0] * num_requests
    total_input_tokens = 0
    total_output_tokens = 0
    
    def make_request(request_num):
        nonlocal successful_requests, failed_requests, total_input_tokens, total_output_tokens
        try:
            start_time = time.time()
            start_times[request_num-1] = start_time
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            end_time = time.time()
            end_times[request_num-1] = end_time
            latency = end_time - start_time
            latencies.append(latency)
            successful_requests += 1
            
            # 统计 token 信息
            input_tokens = response.usage.prompt_tokens if response.usage and response.usage.prompt_tokens else 0
            output_tokens = response.usage.completion_tokens if response.usage and response.usage.completion_tokens else 0
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            print(f"请求 {request_num} 完成 | 延迟: {latency:.2f}s | 响应: {response.choices[0].message.content[:30]}...")
            return latency
        except Exception as e:
            failed_requests += 1
            print(f"请求 {request_num} 失败: {str(e)}")
            return None
    
    print(f"\n{'='*50}")
    print(f"开始测试 - 模型: {model}, 总请求数: {num_requests}, 并发数: {max_workers}")
    if base_url:
        print(f"使用自定义端点: {base_url}")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    start_test_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(
            make_request, 
            range(1, num_requests + 1)
        )
    
    end_test_time = time.time()
    total_time = end_test_time - start_test_time
    
    # 计算延迟统计信息
    if successful_requests > 0:
        latencies_array = np.array(latencies)
        avg_latency = np.mean(latencies_array)
        min_latency = np.min(latencies_array)
        max_latency = np.max(latencies_array)
        percentile_50 = np.percentile(latencies_array, 50)
        percentile_90 = np.percentile(latencies_array, 90)
        percentile_95 = np.percentile(latencies_array, 95)
        percentile_99 = np.percentile(latencies_array, 99)
        
        # 计算吞吐量
        throughput = successful_requests / total_time
        
        # 计算 token 吞吐量
        input_tps = total_input_tokens / total_time
        output_tps = total_output_tokens / total_time
        total_tps = (total_input_tokens + total_output_tokens) / total_time
        
        # 计算实际并发量（基于请求重叠时间）
        active_requests = []
        for i in range(num_requests):
            if start_times[i] > 0 and end_times[i] > 0:
                active_requests.append((start_times[i], end_times[i]))
        
        max_concurrent = calculate_max_concurrency(active_requests)
    else:
        avg_latency = min_latency = max_latency = percentile_50 = percentile_90 = percentile_95 = percentile_99 = throughput = max_concurrent = 0
        input_tps = output_tps = total_tps = 0
    
    print("\n==================== 测试结果 ====================")
    print(f"测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总测试时间: {total_time:.2f} 秒")
    print(f"请求成功率: {successful_requests}/{num_requests} ({(successful_requests/num_requests)*100:.1f}%)")
    
    if successful_requests > 0:
        print("\n---------- 延迟统计 ----------")
        print(f"平均延迟: {avg_latency:.3f} 秒")
        print(f"最小延迟: {min_latency:.3f} 秒")
        print(f"最大延迟: {max_latency:.3f} 秒")
        print(f"P50 (中位数) 延迟: {percentile_50:.3f} 秒")
        print(f"P90 延迟: {percentile_90:.3f} 秒")
        print(f"P95 延迟: {percentile_95:.3f} 秒")
        print(f"P99 延迟: {percentile_99:.3f} 秒")
        
        print("\n---------- 吞吐量统计 ----------")
        print(f"请求吞吐量: {throughput:.2f} 请求/秒")
        print(f"输入Token吞吐量: {input_tps:.2f} tokens/秒")
        print(f"输出Token吞吐量: {output_tps:.2f} tokens/秒")
        print(f"总Token吞吐量: {total_tps:.2f} tokens/秒")
        print(f"平均输入Token数/请求: {total_input_tokens/successful_requests:.1f}")
        print(f"平均输出Token数/请求: {total_output_tokens/successful_requests:.1f}")
        print(f"最大观测并发量: {max_concurrent}")
        
        # 打印延迟分布直方图
        print("\n---------- 延迟分布直方图 ----------")
        plot_latency_histogram(latencies_array)
    else:
        print("\n没有成功的请求，无法计算性能指标")

def calculate_max_concurrency(intervals):
    """计算最大并发请求数"""
    if not intervals:
        return 0
    
    # 提取所有时间点并标记是开始还是结束
    points = []
    for start, end in intervals:
        points.append((start, 'start'))
        points.append((end, 'end'))
    
    # 按时间排序
    points.sort()
    
    max_concurrent = 0
    current_concurrent = 0
    
    for point in points:
        if point[1] == 'start':
            current_concurrent += 1
            if current_concurrent > max_concurrent:
                max_concurrent = current_concurrent
        else:
            current_concurrent -= 1
    
    return max_concurrent

def plot_latency_histogram(latencies, bins=10):
    """打印简单的文本直方图显示延迟分布"""
    hist, bin_edges = np.histogram(latencies, bins=bins)
    
    max_count = max(hist)
    scale = 50 / max_count if max_count > 0 else 1
    
    for i in range(bins):
        lower = bin_edges[i]
        upper = bin_edges[i+1]
        count = hist[i]
        bar = '#' * int(count * scale)
        print(f"{lower:.3f}-{upper:.3f}s: {bar} ({count})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OpenAI API 性能和吞吐量测试工具')
    parser.add_argument('--api-key', required=True, help='OpenAI API 密钥')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='要测试的模型名称')
    parser.add_argument('--prompt', default='请用中文回答：什么是人工智能？', help='发送的提示文本')
    parser.add_argument('--num-requests', type=int, default=10, help='要发送的请求总数')
    parser.add_argument('--max-workers', type=int, default=5, help='并发工作线程数')
    parser.add_argument('--base-url', help='自定义API端点URL (例如: https://api.openai.com/v1)')
    parser.add_argument('--api-version', help='API版本 (可选)')
    parser.add_argument('--organization', help='组织ID (可选)')
    
    args = parser.parse_args()
    
    test_openai_performance(
        api_key=args.api_key,
        model=args.model,
        prompt=args.prompt,
        num_requests=args.num_requests,
        max_workers=args.max_workers,
        base_url=args.base_url,
        api_version=args.api_version,
        organization=args.organization
    )