import sys, os
import re
import subprocess
import traceback
import threading
import time
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
from loguru import logger
import random


from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from langchain_core.tools import BaseTool
from langchain.load.dump import dumps
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from ..state import State
from ..utils.frontend_messages import frontend_add_message, frontend_add_tool_call
from ..utils.config import Config, get_lang_prompt
from ..tools.file_search_keyword import FileSearchTool
from ..chatbot import chatbot_with_context_manager



postfix = """
Reminders: DO NOT mock or simulate results. Only write python files to generate the code and bash shell scripts to execute them.
"""

# execute_prompt = """
# Now first examine if the code fulfills the requirements and the code DOES NOT MOCK OR SIMULATE any results.
# Then execute the generated code to make sure it works. Use the "python" command to execute the code, do not use virtual environments or anaconda, do not use any other commands.
# At last checks if the results/outputs includes wrong codeces or unexpected/broken characters.
# If the code fails, fix the code and try again.
# """


def run_openhands(
    cmd: str,
    config: Config,
):
    """运行Docker容器并实时输出+保存日志"""

    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_name = f"openhands_{time_stamp}.log"
    log_save_path = os.path.join(config.save_path, "openhands_logs", save_name)
    os.makedirs(os.path.dirname(log_save_path), exist_ok=True)
    with open(log_save_path, "w") as f:
        f.write(cmd + "\n\n\n")

    log_lines = []  # 保存所有日志行

    for try_i in range(5):
        try:
            # 启动子进程（实时流处理核心）
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, shell=True)  # 合并stdout和stderr  # 行缓冲模式

            with open(log_save_path, "a") as f:
                f.write(f"Process pid: {process.pid}\n\n")
                logger.info(f"Process pid: {process.pid}")

            # 创建全局变量来记录读取的行数
            line_count = {"count": 0}
            # 创建守护线程来监控进程
            monitor_thread = threading.Thread(target=monitor_process, args=(process.pid, line_count), daemon=True)
            monitor_thread.start()

            # 实时处理输出流
            output_chunk = ""
            pattern = r"(\d{2}:\d{2}:\d{2} - openhands:)"  # 用时间戳拆分日志
            frontend_add_tool_call("openhands", {}, config)
            while True:
                output_line = process.stdout.readline()
                output_line = re.sub(r"\033\[[\d;]*m", "", output_line)
                if output_line == "" and process.poll() is not None:
                    break
                if output_line:
                    # 更新读取的行数
                    line_count["count"] += 1

                    if re.match(pattern, output_line):
                        clean_chunk = split_and_clean_log(output_chunk).strip("\n ")
                        if clean_chunk:
                            logger.info(clean_chunk)
                        output_chunk = ""

                    if "tenacity.RetryError" in output_line:
                        # TODO: I am not sure why this is happening in OpenHands currently, need further investigations. Related issues: https://github.com/All-Hands-AI/OpenHands/issues/8211, https://github.com/All-Hands-AI/OpenHands/issues/8211
                        logger.warning(f"tenacity.RetryError occurred, killing docker process {process.pid} and retrying...")
                        os.system(f"kill -9 {process.pid}")
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
            break
        except Exception as e:
            error_log = "".join(log_lines) + f"\nERROR: {str(e)}"
            # traceback.print_exc()
            return error_log


def monitor_process(pid: int, line_count: dict):
    """监控进程输出行数的守护线程函数"""
    logger.info(f"Starting process monitor for PID {pid}")
    start_count = line_count["count"]
    # 等待1分钟
    time.sleep(300)
    logger.info(f"Process {pid} has been running for 5 minute, checking line count...")
    # 检查1分钟内读取的行数是否不超过10行
    if line_count["count"] - start_count <= 10:
        try:
            # 结束进程
            os.kill(pid, 9)  # SIGKILL
            logger.info(f"Process {pid} killed due to insufficient output")
        except ProcessLookupError:
            # 进程已经结束
            pass
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")

    last_line_count = 0
    # 每隔30分钟检查是否卡住
    while True:
        time.sleep(1800)
        logger.info(f"Process {pid} has been running for 30 minutes, current line count: {line_count['count']}, last line count: {last_line_count}")
        if line_count["count"] == last_line_count:
            try:
                # 结束进程
                os.kill(pid, 9)  # SIGKILL
                logger.info(f"Process {pid} killed due to insufficient output")
                return
            except ProcessLookupError:
                # 进程已经结束
                return
            except Exception as e:
                logger.error(f"Error killing process {pid}: {e}")

        last_line_count = line_count["count"]


def run_openhands_prompt(prompts, config: Config):
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
        pwd = os.getcwd()
        workspace_dir = os.path.join(pwd, config.save_path, "workspace")
        openhands_traj_path = os.path.join(pwd, config.save_path, "openhands_traj")
        openhands_llm_log_path = os.path.join(pwd, config.save_path, "openhands_llm_log")
        latex_template_path = os.path.join(pwd, "openlens_ai/tools/latex_template/blank")
        dot_openhands_path = os.path.join(pwd, "openlens_ai/tools/openhands_configs/dot_openhands")
        os.makedirs(os.path.join(workspace_dir, "manuscript"), exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, "data_analyze"), exist_ok=True)
        os.makedirs(openhands_traj_path, exist_ok=True)
        os.makedirs(openhands_llm_log_path, exist_ok=True)
        
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        prompt_file = os.path.join(pwd, config.save_path, "openhands_logs", f"prompt_{time_stamp}.txt")
        os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
        with open(prompt_file, "w") as f:
            f.write(prompt + get_lang_prompt(config.llm.language))

        max_iter = config.workflow.openhands_max_iter
        docker_name = config.docker.docker_name
        logger.info(f"Runtime docker: {docker_name}")

        with open("openlens_ai/tools/openhands_configs/config.toml", "r") as f:
            oh_config_template = f.read()
        oh_config = oh_config_template.replace("{api_key}", config.llm.chat.api_key)
        oh_config = oh_config.replace("{base_url}", config.llm.chat.base_url)
        oh_config = oh_config.replace("{code_model}", config.llm.chat.model)
        oh_config = oh_config.replace("{condenser_api_key}", config.llm.condenser.api_key)
        oh_config = oh_config.replace("{condenser_base_url}", config.llm.condenser.base_url)
        oh_config = oh_config.replace("{code_condenser_model}", config.llm.condenser.model)
        
        oh_config = oh_config.replace("{tavily_key}", config.tools.tavily_api_key)
        oh_config = oh_config.replace("{openhands_traj_path}", openhands_traj_path)
        oh_config = oh_config.replace("{log_completions_folder}", openhands_llm_log_path)
        oh_config = oh_config.replace("{runtime_container_image}", docker_name)

        if config.dataset_path:
            dataset_path = os.path.join(pwd, config.dataset_path)
            assert os.path.exists(dataset_path), f"Dataset path {dataset_path} does not exist."
            oh_config = oh_config.replace(
                "{sandbox_volumes}",
                f"{os.path.abspath(workspace_dir)}:/workspace/:rw,"
                f"{os.path.abspath(config.dataset_path)}:/workspace/datasets/:ro,"
                f"{os.path.abspath(latex_template_path)}:/workspace/latex_template/:ro,"
                f"{os.path.abspath(dot_openhands_path)}:/workspace/.openhands/:ro",
            )
        else:
            oh_config = oh_config.replace(
                "{sandbox_volumes}",
                f"{os.path.abspath(workspace_dir)}:/workspace/:rw,"
                f"{os.path.abspath(latex_template_path)}:/workspace/latex_template/:ro,"
                f"{os.path.abspath(dot_openhands_path)}:/workspace/.openhands/:ro",
            )

        this_config_path = os.path.join(config.save_path, "openhands_config.toml")
        with open(this_config_path, "w") as f:
            f.write(oh_config)
        logger.debug(f"Using OpenHands config: {oh_config}")
        for try_i in range(5):
            # 构建在Docker容器中执行的命令
            cmd = (
                ". openlens_ai/tools/openhands_configs/openhands_env.sh; "
                # f"chmod -R 777 {os.path.abspath(config.save_path)};"
                f"cd modules/OpenHands;"
                f'poetry run python -m openhands.core.main -f "{os.path.abspath(prompt_file)}" -i {max_iter} --config-file {os.path.abspath(this_config_path)};'
                f"cd ../../;"
                # f"chmod -R 777 {os.path.abspath(config.save_path)};"
            )
            results = run_openhands(cmd, config)
            # 移除ANSI转义序列（颜色代码等）
            results = re.sub(r"\033\[[\d;]*m", "", results)
            results = split_and_clean_log(results)
            results = results[-40000:]
            if "AgentState.FINISHED" in results:
                logger.info(f"Docker container executed successfully.")
                break
            else:
                logger.warning(f"Docker container executed unsuccessfully. Trying again ({try_i}/5)...")
                continue

        # 将当前提示的结果添加到总结果中
        all_results += "=" * 20 + f"Prompt: {prompt[:20]}..." + "=" * 20
        all_results += "\n" + results

    # 限制结果长度为最后3000个字符
    return all_results


def split_and_clean_log(log_text):
    # 正则匹配 `时间 - openhands` 作为分隔符
    pattern = r"\n(\d{2}:\d{2}:\d{2} - openhands:)"

    # 拆分日志
    log_entries = re.split(pattern, log_text)
    clean_entries = []
    for entry in log_entries:
        if ("agent_controller.py" in entry) and ("openhands:DEBUG" not in entry):
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

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def _run(self, prompts: Union[list, str]) -> str:
        """执行OpenHands操作的主要方法"""
        logger.info(f"Starting OpenHands with prompt: {prompts}")
        # return str([random.randint(1000, 9999) for _ in range(10000)])
        return run_openhands_prompt(prompts, self.config)


def collect_info_and_run_openhands(prompt: str, config: Config, state: State):
    pass


if __name__ == "__main__":
    prompt = "Write a python script to print hello world! Then execute it."
    dataset_path = "data/dataset.jsonl"
    config = Config(
        dataset_path="outputs/test/data",
        save_path="outputs/test",
        thread_id="test",
        question="test",
    )
    result = run_openhands_prompt(prompt, config)
    with open("result.txt", "w") as f:
        f.write(result)
    # with open("result.txt", "r") as f:
    #     result = f.read()
    # result = split_and_clean_log(result)
    # logger.info(result)
