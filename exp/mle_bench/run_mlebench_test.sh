#!/bin/bash

# MLE-bench测试运行脚本
# 使用方法: ./run_mlebench_test.sh [进程数] [数据集目录]

# 设置默认进程数
PROCESSES=${1:-1}

# 设置数据集目录
DATASETS_DIR=${2:-"/data/cyx/openlens-ai/datasets/mle-bench"}

# 设置配置文件路径
CONFIG_PATH="/data/cyx/openlens-ai/exp/mle_bench/config.toml"

# 设置通知邮箱
EMAIL="dzdzzd@126.com"

# 创建日志目录
mkdir -p /data/cyx/openlens-ai/exp/mle_bench/runs

echo "开始运行MLE-bench测试..."
echo "进程数: $PROCESSES"
echo "配置文件: $CONFIG_PATH"
echo "通知邮箱: $EMAIL"
echo "数据集目录: $DATASETS_DIR"
echo "日志目录: /data/cyx/openlens-ai/exp/mle_bench/runs"
echo ""

# 运行测试脚本（它会自动启动和停止grading_server）
echo "运行测试脚本..."
python exp/mle_bench/test_mlebench.py \
    --processes $PROCESSES \
    --config $CONFIG_PATH \
    --email $EMAIL \
    --datasets-dir $DATASETS_DIR

echo ""
echo "测试完成！查看日志目录获取详细结果: /data/cyx/openlens-ai/exp/mle_bench/runs"
