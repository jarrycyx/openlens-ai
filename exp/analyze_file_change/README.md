# 文件变化分析工具

这个工具用于分析不同版本zip文件中的文件变化，将相同文件名的不同版本组织在一起，方便比较分析。

## 功能特点

- 从多个zip文件中提取文件
- 按文件名分组，保留所有版本
- 支持文件扩展名筛选（默认筛选png、jpg、jpeg、pdf格式）
- 使用zip文件的创建时间戳作为版本标识
- 自动清理临时文件

## 使用方法

### 基本用法

```bash
python analyze_file_changes.py <zip文件目录>
```

### 指定输出目录

```bash
python analyze_file_changes.py <zip文件目录> -o <输出目录>
```

### 文件扩展名筛选

```bash
# 使用默认扩展名筛选（png, jpg, jpeg, pdf）
python analyze_file_changes.py <zip文件目录>

# 指定特定扩展名
python analyze_file_changes.py <zip文件目录> -e "png,jpg"

# 筛选PDF文件
python analyze_file_changes.py <zip文件目录> -e "pdf"
```

## 参数说明

- `zip_dir`: 包含zip文件的目录路径
- `-o, --output`: 输出目录路径（默认：./file_analysis_output）
- `-e, --extensions`: 要筛选的文件扩展名，用逗号分隔（默认：png,jpg,jpeg,pdf）

## 工作流程

1. 扫描指定目录中的所有zip文件
2. 在临时目录中解压所有zip文件
3. 按相对路径映射文件，并根据扩展名筛选
4. 将相同文件名的不同版本组织在一起
5. 使用zip文件的创建时间戳作为版本标识
6. 将结果保存到输出目录
7. 清理临时文件

## 输出结构

输出目录中，每个文件名对应一个子目录，子目录中包含该文件的所有版本：

```
输出目录/
├── 文件名1_扩展名/
│   ├── 时间戳1.扩展名
│   ├── 时间戳2.扩展名
│   └── ...
├── 文件名2_扩展名/
│   ├── 时间戳1.扩展名
│   ├── 时间戳2.扩展名
│   └── ...
└── ...
```

## 示例

```bash
# 分析默认扩展名的文件
python analyze_file_changes.py /path/to/zips

# 分析PDF文件并指定输出目录
python analyze_file_changes.py /path/to/zips -o /path/to/output -e "pdf"

# 分析多种图像格式
python analyze_file_changes.py /path/to/zips -e "png,jpg,jpeg,svg"
```

## 注意事项

- 确保有足够的磁盘空间用于临时文件
- 工具会自动创建输出目录（如果不存在）
- 处理完成后会自动清理临时文件
- 文件名中的点号会被替换为下划线，以避免创建子目录
- 默认情况下只处理png、jpg、jpeg和pdf格式的文件
- 相同文件名的不同版本会保存在以文件名命名的子目录中，文件名以zip创建时间戳命名

## 示例脚本

运行 `example_usage.py` 可以查看工具的使用示例：

```bash
python example_usage.py
```

或者直接运行示例脚本：

```bash
./run_example.sh
```