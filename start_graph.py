import argparse
import sys, os
from datetime import datetime


from open_lens.build_graph import main, graph


# 使用默认值
question = """
What is the prediction precision of AKI based on historical 2 day data? The prediction is performed every day dynamically on ICU patients.
"""
dataset_path = "datasets/mimic"
# 使用当前日期
thread_id = "Test_" + datetime.now().strftime("%Y%m%d%H%M%S") + f"_{question.strip()[:50].replace(' ', '_')}"


main(question, dataset_path, thread_id)
