#!/bin/bash

# 启动自定义grading_server的脚本
# 使用方法: ./start_grading_server.sh [数据集路径] [端口]

# 设置默认值
DATASET_PATH=${1:-"/data/cyx/openlens-ai/datasets/mle-bench"}
PORT=${2:-5000}
HOST="0.0.0.0"

# 设置环境变量
export COMPETITION_ID="test-competition"
export PRIVATE_DATA_DIR="$DATASET_PATH"

# 创建日志目录
LOG_DIR="/data/cyx/openlens-ai/exp/mle_bench/logs"
mkdir -p "$LOG_DIR"

# 启动服务器
echo "Starting grading server..."
echo "Data directory: $DATASET_PATH"
echo "Server will be available at http://$HOST:$PORT"
echo "Logs will be saved to: $LOG_DIR/grading_server.log"

# 启动服务器并记录日志
nohup python /data/cyx/openlens-ai/exp/mle_bench/grading_server/custom_grading_server.py \
    --data-dir "$DATASET_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    > "$LOG_DIR/grading_server.log" 2>&1 &

# 保存进程ID
SERVER_PID=$!
echo $SERVER_PID > "$LOG_DIR/grading_server.pid"

echo "Grading server started with PID: $SERVER_PID"
echo "To stop the server, run: kill $SERVER_PID"

# 等待服务器启动
echo "Waiting for server to start..."
sleep 3

# 检查服务器是否正常运行
if curl -s "http://$HOST:$PORT/health" > /dev/null; then
    echo "Grading server is running successfully!"
else
    echo "Warning: Grading server may not have started correctly. Check the logs for details."
fi
