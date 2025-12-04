# MLE-bench 测试工具

这个目录包含了用于测试MLE-bench数据集的工具和脚本。

## 文件说明

### 核心脚本

- `test_mlebench.py`: 主要的测试脚本，用于运行MLE-bench数据集的测试
- `run_mlebench_test.sh`: 便捷的运行脚本，用于启动测试

### Grading Server相关文件

所有grading server相关文件位于`grading_server/`文件夹中：

- `custom_grading_server.py`: 自定义的grading_server，支持指定数据目录路径
- `start_grading_server.sh`: 启动grading_server的脚本
- `stop_grading_server.sh`: 停止grading_server的脚本
- `test_grading_server.py`: 独立测试grading_server的脚本
- `run_grading_server_test.sh`: 便捷的grading_server测试脚本

## 使用方法

### 1. 使用便捷脚本运行测试

```bash
# 使用默认设置运行测试（1个进程，默认数据集目录）
./run_mlebench_test.sh

# 指定进程数运行测试
./run_mlebench_test.sh 4

# 指定进程数和数据集目录
./run_mlebench_test.sh 4 /path/to/datasets
```

### 2. 直接使用Python脚本

```bash
# 使用默认设置运行测试
python test_mlebench.py

# 指定参数运行测试
python test_mlebench.py \
    --processes 4 \
    --config /path/to/config.toml \
    --email your.email@example.com \
    --datasets-dir /path/to/datasets

# 跳过启动/停止grading_server（如果服务器已经在运行）
python test_mlebench.py --skip-server
```

### 3. 手动管理grading_server

```bash
# 启动grading_server
./grading_server/start_grading_server.sh /path/to/datasets

# 停止grading_server
./grading_server/stop_grading_server.sh

# 或者直接使用Python脚本启动
python grading_server/custom_grading_server.py \
    --data-dir /path/to/datasets \
    --host 0.0.0.0 \
    --port 5000
```

## 参数说明

### test_mlebench.py 参数

- `--processes`: 并行运行的进程数（默认：1）
- `--config`: 配置文件路径（默认：exp/config.toml）
- `--email`: 通知邮箱（默认：dzdzzd@126.com）
- `--datasets-dir`: 数据集目录路径（默认：/data/cyx/openlens-ai/datasets/mle-bench）
- `--skip-server`: 跳过启动/停止grading_server

### custom_grading_server.py 参数

- `--data-dir`: 私有数据目录路径（默认：/private/data）
- `--host`: 服务器绑定主机（默认：0.0.0.0）
- `--port`: 服务器绑定端口（默认：5000）

## 日志和输出

- 测试日志保存在 `/data/cyx/openlens-ai/exp/mle_bench/runs/` 目录
- grading_server日志保存在 `/data/cyx/openlens-ai/exp/mle_bench/logs/` 目录
- 测试结果汇总保存在 `/data/cyx/openlens-ai/exp/mle_bench/runs/summary.txt`

## 注意事项

1. 确保在运行测试前已正确安装所有依赖
2. 测试脚本会自动处理grading_server的启动和停止
3. 如果grading_server已经在运行，可以使用`--skip-server`参数跳过服务器管理
4. 测试过程中可能会产生大量日志，请确保有足够的磁盘空间
5. 多进程运行时，请确保系统有足够的资源

## 故障排除

### grading_server启动失败

1. 检查数据集目录路径是否正确
2. 检查端口是否已被占用
3. 查看grading_server日志获取详细错误信息

### 测试失败

1. 检查数据集目录结构是否正确
2. 确保每个数据集都有`prepared/public/description.md`文件
3. 检查配置文件路径是否正确
4. 查看测试日志获取详细错误信息

## 独立测试Grading Server

如果您只想测试grading server的功能，而不需要运行完整的openlens系统，可以使用以下方法：

### 1. 使用便捷脚本测试

```bash
# 使用默认参数测试
./grading_server/run_grading_server_test.sh

# 指定数据目录和端口
./grading_server/run_grading_server_test.sh -d /path/to/data -p 8080
```

### 2. 直接使用Python测试脚本

```bash
# 运行测试脚本
python grading_server/test_grading_server.py
```

### 3. 手动测试

```bash
# 启动grading server
export PRIVATE_DATA_DIR="/path/to/private/data"
export COMPETITION_ID="aerial-cactus-identification"
python grading_server/custom_grading_server.py --data-dir "$PRIVATE_DATA_DIR" --host 127.0.0.1 --port 5000

# 在另一个终端中测试健康检查端点
curl http://127.0.0.1:5000/health

# 测试验证端点
curl -X POST -F "file=@/path/to/submission.csv" http://127.0.0.1:5000/validate
```

### 测试说明

- `test_grading_server.py` 脚本会自动启动grading server，发送测试请求，然后停止服务器
- 测试过程中会基于真实测试数据创建CSV文件作为测试提交
- 默认使用`aerial-cactus-identification`数据集进行测试
- 测试提交文件会使用真实测试数据中的所有ID，并为每个ID生成0到1之间的随机浮点数作为预测分数
- 测试结果会显示在控制台中

### 注意事项

1. 确保指定的数据目录存在且包含必要的验证文件
2. 测试脚本会自动处理服务器的启动和停止
3. 如果端口被占用，可以使用`-p`参数指定其他端口
