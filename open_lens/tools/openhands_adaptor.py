import sys, os
import re
import subprocess
import traceback
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
from loguru import logger

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from langchain_core.tools import BaseTool
from langchain.load.dump import dumps
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from ..state import State
from ..utils.frontend_utils import frontend_add_message, frontend_add_tool_call

postfix = """
Reminders: DO NOT mock or simulate results. Only write python files to generate the code and bash shell scripts to execute them.
"""

# execute_prompt = """
# Now first examine if the code fulfills the requirements and the code DOES NOT MOCK OR SIMULATE any results.
# Then execute the generated code to make sure it works. Use the "python" command to execute the code, do not use virtual environments or anaconda, do not use any other commands.
# At last checks if the results/outputs includes wrong codeces or unexpected/broken characters.
# If the code fails, fix the code and try again.
# """


def run_docker_container(cmd: str, config: dict):
    """运行Docker容器并实时输出+保存日志"""
    pwd = os.getcwd()
    workspace_dir = os.path.join(pwd, config["save_path"], "workspace")
    
    if config["dataset_path"]:
        dataset_path = os.path.join(pwd, config["dataset_path"])
        latex_template_path = os.path.join(pwd, "open_lens/tools/latex_template/neurips")
        docker_cmd = [
            "docker",
            "run",
            "-t",
            "--gpus", "all",
            "-v", "./open_lens:/helper/open_lens",
            "-v", f"{workspace_dir}:/workspace",
            "-v", f"{dataset_path}:/workspace/datasets:ro",
            "-v", f"{latex_template_path}:/workspace/latex_template:ro",
            "agent-med-gpu",
            "bash",
            "-c",
            cmd,
        ]
    else:
        latex_template_path = os.path.join(pwd, "open_lens/tools/latex_template/neurips")
        docker_cmd = [
            "docker",
            "run",
            "-t",
            "--gpus", "all",
            "-v", "./open_lens:/helper/open_lens",
            "-v", f"{workspace_dir}:/workspace",
            "-v", f"{latex_template_path}:/workspace/latex_template:ro",
            "agent-med-gpu",
            "bash",
            "-c",
            cmd,
        ]
        
        
    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_name = f"openhands_{time_stamp}.log"
    log_save_path = os.path.join(config["save_path"], "openhands_logs", save_name)
    os.makedirs(os.path.dirname(log_save_path), exist_ok=True)
    with open(log_save_path, "w") as f:
        f.write(" ".join(docker_cmd).replace("\\n", "\n") + "\n\n\n")

    log_lines = []  # 保存所有日志行

    try:
        # 启动子进程（实时流处理核心）
        process = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)  # 合并stdout和stderr  # 行缓冲模式

        # 实时处理输出流
        output_chunk = ""
        pattern = r"(\d{2}:\d{2}:\d{2} - openhands:)" # 用时间戳拆分日志
        frontend_add_tool_call("openhands", {})
        while True:
            output_line = process.stdout.readline()
            output_line = re.sub(r"\033\[[\d;]*m", "", output_line)
            if output_line == "" and process.poll() is not None:
                break
            if output_line:
                if re.match(pattern, output_line):
                    clean_chunk = split_and_clean_log(output_chunk).strip("\n ")
                    if clean_chunk:
                        logger.info(clean_chunk)
                    output_chunk = ""
                output_chunk += output_line
                # 同时保存到日志集合
                log_lines.append(output_line)    
                with open(log_save_path, "a") as f:
                    f.write(output_line)

        # 检查退出状态
        return_code = process.poll()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, docker_cmd)
        
        

        logger.info("Docker container executed successfully.")
        return "".join(log_lines)  # 返回完整日志

    except Exception as e:
        error_log = "".join(log_lines) + f"\nERROR: {str(e)}"
        traceback.print_exc()
        return error_log


def run_openhands_prompt(prompts, config: dict):
    """
    运行OpenHands提示并返回结果
    
    该函数接受一个或多个提示，为每个提示构建OpenHands命令并在Docker容器中执行，
    最终返回处理后的结果。
    
    Args:
        prompts (str or list): 单个提示字符串或提示列表
        config (dict): 配置字典，包含执行环境相关设置
        
    Returns:
        str: 处理后的执行结果，限制在最后3000个字符
    """
    if isinstance(prompts, str):
        prompts = [prompts]

    # prompts.append(execute_prompt)

    all_results = ""
    for prompt in prompts:
        # 转义引号和换行符以避免命令执行问题
        prompt = prompt.replace('"', '\\"').replace("\n", "\\n").replace("`", " ")
        prompt += postfix
        # 构建在Docker容器中执行的命令
        cmd = (
            f"cp /helper/open_lens/tools/openhands_configs/config.toml /helper/OpenHands/ && "
            f"source /helper/open_lens/tools/openhands_configs/openhands_env.sh && "
            f"cd /helper/OpenHands && "
            f"mkdir -p /workspace/manuscript/ && chmod -R 777 /workspace/manuscript/ && cp /workspace/latex_template/*.sty /workspace/manuscript/ &&"
            f'poetry run python -m openhands.core.main -t "{prompt}" --log-level ERROR'
        )
        results = run_docker_container(cmd, config)
        # 移除ANSI转义序列（颜色代码等）
        results = re.sub(r"\033\[[\d;]*m", "", results)
        results = split_and_clean_log(results)

        # 将当前提示的结果添加到总结果中
        all_results += "=" * 20 + f"Prompt: {prompt[:20]}..." + "=" * 20
        all_results += "\n" + results

    # 限制结果长度为最后3000个字符
    all_results = all_results[-10000:]
    return all_results


def split_and_clean_log(log_text):
    # 正则匹配 `时间 - openhands` 作为分隔符
    pattern = r"\n(\d{2}:\d{2}:\d{2} - openhands:)"

    # 拆分日志
    log_entries = re.split(pattern, log_text)
    clean_entries = []
    for entry in log_entries:
        if "agent_controller.py" in entry:
            clean_entries.append(entry)
    for entry_i in range(len(clean_entries)):
        if "]" in clean_entries[entry_i]:
            clean_entries[entry_i] = clean_entries[entry_i].split("]", 1)[1]  # 取后半部分
    return "\n\n".join(clean_entries)


class OpenhandsToolInput(BaseModel):
    prompts: list = Field(..., description="Prompt list to run through OpenHands.")


class OpenHandsTool(BaseTool):
    name: str = "openhands_tool"
    description: str = "Coding agent that can generate/modify workflow scripts for a given experimentation plan."
    args_schema: Type[BaseModel] = OpenhandsToolInput
    config: Optional[dict] = None

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

    def _run(self, prompts: Union[list, str]) -> str:
        """执行OpenHands操作的主要方法"""
        logger.info(f"Starting OpenHands with prompt: {prompts}")
        # return ""
        return run_openhands_prompt(prompts, self.config)


if __name__ == "__main__":
    prompt = "Write a python script to print hello world! Then execute it."
    dataset_path = "data/dataset.jsonl"
    result = run_openhands_prompt(prompt)
    with open("result.txt", "w") as f:
        f.write(result)
    # with open("result.txt", "r") as f:
    #     result = f.read()
    # result = split_and_clean_log(result)
    # logger.info(result)
