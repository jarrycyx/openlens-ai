#!/bin/bash

# 默认目录路径
DEFAULT_DIR="/data/cyx/openlens-ai/outputs/pred_aki_dy_mimic_icu_csv_20251118173506/openhands_traj"

# 检查是否提供了目录参数
if [ $# -eq 0 ]; then
    echo "使用默认目录: $DEFAULT_DIR"
    DIR=$DEFAULT_DIR
else
    DIR=$1
fi

# 检查目录是否存在
if [ ! -d "$DIR" ]; then
    echo "错误: 目录 $DIR 不存在"
    exit 1
fi

# 输出文件路径
OUTPUT_DIR="/data/cyx/openlens-ai/exp"
OUTPUT_FILE="$OUTPUT_DIR/token_costs_plot.png"

# 运行Python脚本
echo "开始分析目录: $DIR"
python3 /data/cyx/openlens-ai/exp/analyze_token_costs.py "$DIR" --output "$OUTPUT_FILE"

echo "分析完成，图表已保存到: $OUTPUT_FILE"
