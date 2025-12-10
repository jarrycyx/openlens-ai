#!/bin/bash

# 创建目标目录（如果不存在）
mkdir -p exp/eval_fig/figs

# 查找当前目录中的所有PNG和JPG图片（路径中包含workspace）并复制到目标目录
echo "正在查找并复制路径中包含workspace的PNG和JPG图片..."
find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | grep -i workspace | while read file; do
    cp "$file" exp/eval_fig/figs/
done

echo "图片复制完成。"

# 进入目标目录并压缩所有图片
cd exp/eval_fig/figs
echo "正在压缩图片..."
zip -r ../figs.zip ./*

echo "压缩完成。压缩文件位于: exp/eval_fig/figs.zip"

# 返回原目录
cd - > /dev/null

echo "操作完成！"