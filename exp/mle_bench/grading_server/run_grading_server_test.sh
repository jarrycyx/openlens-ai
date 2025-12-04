#!/bin/bash

# MLE-bench Grading Server 测试脚本
# 此脚本用于在不运行openlens的情况下测试grading server

set -e

# 默认参数
DATA_DIR="/data/cyx/openlens-ai/datasets/mle-bench/aerial-cactus-identification/prepared/private"
PORT=5000

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -d, --data-dir DIR    指定私有数据目录路径 (默认: $DATA_DIR)"
    echo "  -p, --port PORT       指定服务器端口 (默认: $PORT)"
    echo "  -h, --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认参数"
    echo "  $0 -d /path/to/data -p 8080          # 指定数据目录和端口"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查数据目录是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo "错误: 数据目录不存在: $DATA_DIR"
    echo "请确保已下载并解压了mle-bench数据集"
    exit 1
fi

# 创建日志目录
LOG_DIR="/data/cyx/openlens-ai/exp/mle_bench/logs"
mkdir -p "$LOG_DIR"

# 运行测试
echo "开始测试grading server..."
echo "数据目录: $DATA_DIR"
echo "端口: $PORT"
echo "日志目录: $LOG_DIR"
echo ""

# 运行Python测试脚本
python3 /data/cyx/openlens-ai/exp/mle_bench/grading_server/test_grading_server.py

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "测试成功完成!"
else
    echo ""
    echo "测试失败，请检查日志获取更多信息。"
    exit 1
fi
