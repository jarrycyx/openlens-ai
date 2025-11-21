#!/usr/bin/env python3
import os
import zipfile
import shutil
from pathlib import Path
from collections import defaultdict
import argparse
import sys

def extract_all_zips(source_dir, extract_dir):
    """
    解压指定目录下的所有zip文件到目标目录
    
    Args:
        source_dir: 包含zip文件的源目录
        extract_dir: 解压文件的目标目录
    
    Returns:
        dict: {zip文件名: 解压后的目录路径}
    """
    zip_to_dir = {}
    
    # 确保解压目录存在
    os.makedirs(extract_dir, exist_ok=True)
    
    # 查找所有zip文件
    zip_files = [f for f in os.listdir(source_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print(f"在目录 {source_dir} 中未找到zip文件")
        return zip_to_dir
    
    print(f"找到 {len(zip_files)} 个zip文件")
    
    for zip_file in zip_files:
        zip_path = os.path.join(source_dir, zip_file)
        # 为每个zip文件创建一个单独的解压目录
        zip_name = os.path.splitext(zip_file)[0]
        zip_extract_dir = os.path.join(extract_dir, zip_name)
        os.makedirs(zip_extract_dir, exist_ok=True)
        
        print(f"正在解压 {zip_file} 到 {zip_extract_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_extract_dir)
            zip_to_dir[zip_name] = zip_extract_dir
        except Exception as e:
            print(f"解压 {zip_file} 时出错: {e}")
    
    return zip_to_dir

def map_files_by_relative_path(zip_to_dir, extensions=None):
    """
    根据相对路径映射文件，可筛选特定扩展名的文件
    
    Args:
        zip_to_dir: {zip文件名: 解压后的目录路径}
        extensions: 要筛选的文件扩展名列表，如['png', 'jpg', 'jpeg', 'pdf']，None表示不筛选
    
    Returns:
        dict: {相对路径: {zip文件名: 文件绝对路径}}
    """
    path_map = defaultdict(dict)
    
    # 如果没有指定扩展名，使用默认值
    if extensions is None:
        extensions = ['png', 'jpg', 'jpeg', 'pdf']
    
    # 将扩展名转换为小写，便于比较
    extensions = [ext.lower() for ext in extensions]
    
    for zip_name, extract_dir in zip_to_dir.items():
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                # 获取文件扩展名
                file_ext = os.path.splitext(file)[1][1:].lower()  # 去掉点号并转为小写
                
                # 如果文件扩展名在筛选列表中，则处理该文件
                if file_ext in extensions:
                    file_path = os.path.join(root, file)
                    # 计算相对于解压目录的路径
                    rel_path = os.path.relpath(file_path, extract_dir)
                    # 使用正斜杠作为路径分隔符，保持一致性
                    rel_path = rel_path.replace(os.sep, '/')
                    path_map[rel_path][zip_name] = file_path
    
    return path_map

def organize_files_by_name(path_map, output_dir, zip_to_dir, source_dir):
    """
    将相同文件名的不同版本组织在一起
    每个文件的不同版本保存在以文件名命名的子目录中，文件名以zip创建时间戳命名
    
    Args:
        path_map: {相对路径: {zip文件名: 文件绝对路径}}
        output_dir: 输出目录
        zip_to_dir: {zip文件名: 解压后的目录路径}
        source_dir: 包含zip文件的源目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 按相对路径分组，但不在输出目录中保留原始目录结构
    for rel_path, versions in path_map.items():
        # 提取文件名
        file_name = os.path.basename(rel_path)
        file_ext = os.path.splitext(file_name)[1]  # 包含点号的扩展名
        file_base = os.path.splitext(file_name)[0]  # 不含扩展名的文件名
        
        # 为每个文件创建一个以文件名命名的子目录
        file_dir_name = f"{file_base}{file_ext.replace('.', '_')}"  # 将点号替换为下划线
        file_dir = os.path.join(output_dir, file_dir_name)
        os.makedirs(file_dir, exist_ok=True)
        
        print(f"处理文件: {rel_path}")
        
        # 为每个版本的文件创建副本
        for zip_name, file_path in versions.items():
            # 直接使用源目录路径构建zip文件路径
            zip_file_path = os.path.join(source_dir, f"{zip_name}.zip")
            
            try:
                # 获取zip文件的修改时间作为时间戳
                zip_timestamp = os.path.getmtime(zip_file_path)
                # 创建目标文件路径，使用时间戳作为文件名
                dest_file_name = f"{int(zip_timestamp)}{file_ext}"
                dest_path = os.path.join(file_dir, dest_file_name)
                
                shutil.copy2(file_path, dest_path)
                print(f"  复制 {file_path} 到 {dest_path}")
            except Exception as e:
                print(f"  复制文件时出错: {e}")

def analyze_file_changes(source_dir, output_dir=None, extensions=None):
    """
    分析文件变化的主函数
    
    Args:
        source_dir: 包含zip文件的源目录
        output_dir: 输出目录，如果为None则使用源目录下的'output'子目录
        extensions: 要筛选的文件扩展名列表，如['png', 'jpg', 'jpeg', 'pdf']，None表示使用默认值
    """
    if output_dir is None:
        output_dir = os.path.join(source_dir, 'output')
    
    # 创建临时解压目录
    temp_extract_dir = os.path.join(source_dir, 'temp_extract')
    
    try:
        # 1. 解压所有zip文件
        zip_to_dir = extract_all_zips(source_dir, temp_extract_dir)
        
        if not zip_to_dir:
            print("没有找到可解压的zip文件")
            return
        
        # 2. 根据相对路径映射文件
        path_map = map_files_by_relative_path(zip_to_dir, extensions)
        
        # 3. 按文件名组织文件
        organize_files_by_name(path_map, output_dir, zip_to_dir, source_dir)
        
        print(f"\n文件分析完成，结果保存在: {output_dir}")
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
                print(f"已清理临时目录: {temp_extract_dir}")
            except Exception as e:
                print(f"清理临时目录时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='分析zip文件中的文件变化')
    parser.add_argument('source_dir', help='包含zip文件的源目录')
    parser.add_argument('-o', '--output', help='输出目录（可选）', default="outputs/file_tracking_test")
    parser.add_argument('-e', '--extensions', help='要筛选的文件扩展名，用逗号分隔（可选）', default="png,jpg,jpeg,pdf")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"错误: 源目录不存在或不是目录: {args.source_dir}")
        sys.exit(1)
    
    # 解析扩展名列表
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    analyze_file_changes(args.source_dir, args.output, extensions)

if __name__ == '__main__':
    main()