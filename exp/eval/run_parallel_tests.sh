#!/bin/bash

# OpenLens AI 并行测试脚本

echo "开始并行测试..."

# 使用默认设置运行测试
python exp/eval/parallel_test.py \
    --csv-file exp/eval/openlens_eval_dataset.csv \
    --email "dzdzzd@126.com" \
    --max-workers 4 \
    --datasets datasets/mimic-iv-icu datasets/eicu-demo

echo "并行测试完成"