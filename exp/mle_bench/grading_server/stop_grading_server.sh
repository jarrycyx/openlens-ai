#!/bin/bash

# 停止grading_server的脚本
# 使用方法: ./stop_grading_server.sh

# 日志目录
LOG_DIR="/data/cyx/openlens-ai/exp/mle_bench/logs"
PID_FILE="$LOG_DIR/grading_server.pid"

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "No grading server PID file found. Server may not be running."
    exit 1
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否仍在运行
if ! kill -0 "$PID" 2>/dev/null; then
    echo "Process with PID $PID is not running."
    rm -f "$PID_FILE"
    exit 1
fi

# 停止进程
echo "Stopping grading server with PID: $PID"
kill "$PID"

# 等待进程停止
sleep 2

# 检查进程是否已停止
if kill -0 "$PID" 2>/dev/null; then
    echo "Process did not stop gracefully, forcing termination..."
    kill -9 "$PID"
    sleep 1
fi

# 删除PID文件
rm -f "$PID_FILE"

echo "Grading server stopped successfully."
