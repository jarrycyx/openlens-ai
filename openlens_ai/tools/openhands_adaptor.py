import sys, os
import re
import subprocess
import traceback
import threading
import multiprocessing
import time
import toml
import socket
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
from ..chatbot import chatbot_with_context_manager
from .openhands_mcp.server import run_server
from ..utils.file_summary import FileSummary
from ..utils.file_manager import FileManager


def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except OSError:
            return False


def get_available_port(start_port=9077):
    """Get an available port, starting from start_port"""
    port = start_port
    while not is_port_available(port):
        port += 1
        # Avoid infinite loop, set maximum attempts
        if port > start_port + 100:
            raise Exception(f"Unable to find available port, tried from {start_port} to {port}")
    return port


def fix_permissions_in_docker_container(oh_config_str: str):
    """Run sudo chmod -R 777 command in docker container"""
    try:
        oh_config = toml.loads(oh_config_str)
        image_name = oh_config["sandbox"]["runtime_container_image"]
        volumes = oh_config["sandbox"]["volumes"]
        all_volumes = [v.strip() for v in volumes.split(",")]
        cmd = [
            "docker",
            "run",
            "--rm",
            "-it",
        ]
        for v in all_volumes:
            cmd += ["-v", f"{v}"]
        cmd += [image_name, "bash", "-c", f"sudo chmod -R 777 /workspace"]
        logger.debug(f"Fix permissions command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        logger.debug(f"Fix permissions output: {result.stdout} \n {result.stderr}")
        logger.info(f"Fixed permissions in docker container {image_name} with volumes {volumes}")

        # Clean cache
        result = subprocess.run(["docker", "system", "prune", "-f"], capture_output=True, text=True)
        logger.debug(f"Clean cache output: {result.stdout} \n {result.stderr}")
        logger.info(f"Cleaned cache in docker container {image_name} with volumes {volumes}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fix permissions in docker container {image_name} with volumes {volumes}: {e}")


def run_openhands(
    cmd: str,
    config: Config,
):
    """Run Docker container with real-time output and log saving"""

    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_name = f"openhands_{time_stamp}.log"
    log_save_path = os.path.join(config.save_path, "openhands_logs", save_name)
    os.makedirs(os.path.dirname(log_save_path), exist_ok=True)
    with open(log_save_path, "w") as f:
        f.write(cmd + "\n\n\n")

    log_lines = []  # Save all log lines

    for try_i in range(5):
        try:
            # Start subprocess (core of real-time stream processing)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, shell=True
            )  # Merge stdout and stderr  # Line buffering mode

            with open(log_save_path, "a") as f:
                f.write(f"Process pid: {process.pid}\n\n")
                logger.info(f"Process pid: {process.pid}")

            # Create global variable to record the number of lines read
            line_count = {"count": 0}
            # Create daemon thread to monitor process
            monitor_thread = threading.Thread(target=monitor_process, args=(process.pid, line_count), daemon=True)
            monitor_thread.start()

            # Process output stream in real-time
            output_chunk = ""
            pattern = r"(\d{2}:\d{2}:\d{2} - openhands:)"  # Split logs with timestamp
            frontend_add_tool_call("openhands", {}, config)
            while True:
                output_line = process.stdout.readline()
                output_line = re.sub(r"\033\[[\d;]*m", "", output_line)
                if output_line == "" and process.poll() is not None:
                    break
                if output_line:
                    # Update the number of lines read
                    line_count["count"] += 1

                    if re.match(pattern, output_line):
                        clean_chunk = split_and_clean_log(output_chunk).strip("\n ")
                        if clean_chunk:
                            logger.info(clean_chunk)
                        output_chunk = ""

                    if "tenacity.RetryError" in output_line:
                        # TODO: I am not sure why this is happening in OpenHands currently, need further investigations. Related issues: https://github.com/All-Hands-AI/OpenHands/issues/8211, https://github.com/All-Hands-AI/OpenHands/issues/8211
                        logger.warning(
                            f"tenacity.RetryError occurred, killing docker process {process.pid} and retrying..."
                        )
                        os.system(f"kill -9 {process.pid}")
                    output_chunk += output_line
                    # Also save to log collection
                    log_lines.append(output_line)
                    with open(log_save_path, "a") as f:
                        f.write(output_line)

            # Check exit status
            return_code = process.poll()
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, docker_cmd)

            logger.info("Docker container executed successfully.")
            return "".join(log_lines)  # Return complete log
        except Exception as e:
            error_log = "".join(log_lines) + f"\nERROR: {str(e)}"
            # traceback.print_exc()
            return error_log


def monitor_process(pid: int, line_count: dict):
    """Daemon thread function to monitor process output line count"""
    logger.info(f"Starting process monitor for PID {pid}")
    start_count = line_count["count"]
    # Wait for 5 minutes
    time.sleep(300)
    logger.info(f"Process {pid} has been running for 5 minute, checking line count...")
    # Check if the number of lines read within 5 minutes does not exceed 10
    if line_count["count"] - start_count <= 10:
        try:
            # Terminate process
            os.kill(pid, 9)  # SIGKILL
            logger.info(f"Process {pid} killed due to insufficient output")
        except ProcessLookupError:
            # Process has already ended
            pass
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")

    last_line_count = 0
    # Check every 30 minutes if stuck
    while True:
        time.sleep(1800)
        logger.info(
            f"Process {pid} has been running for 30 minutes, current line count: {line_count['count']}, last line count: {last_line_count}"
        )
        if line_count["count"] == last_line_count:
            try:
                # Terminate process
                os.kill(pid, 9)  # SIGKILL
                logger.info(f"Process {pid} killed due to insufficient output")
                return
            except ProcessLookupError:
                # Process has already ended
                return
            except Exception as e:
                logger.error(f"Error killing process {pid}: {e}")

        last_line_count = line_count["count"]


def run_openhands_prompt(prompts, config: Config, add_file_summary: bool = True):
    """
    Run OpenHands prompts and return results

    This function accepts one or more prompts, builds OpenHands commands for each prompt
    and executes them in Docker containers, finally returning the processed results.

    Args:
        prompts (str or list): Single prompt string or list of prompts
        config (dict): Configuration dictionary containing execution environment settings

    Returns:
        str: Processed execution result, limited to the last 3000 characters
    """
    
    
    if isinstance(prompts, str):
        prompts = [prompts]
    
    file_manager = FileManager(config)
    deleted_files = file_manager.clean_repository()
    if len(deleted_files) > 0:
        deletion_report = f"""
Some files are deleted because they may be duplicates of implement different versions of the same functionality (e.g. one is the improved/optimized version of the other), or they contain simulated, fake, or mock data.
These are STRICTLY PROHIBITED in coding, please KEEP IN MIND that:
* NEVER create multiple versions of the same file with different suffixes (e.g., file_test.py, file_fix.py, file_simple.py).
* DO NOT mock or simulate results. Always generate real results using an actual workflow setup (e.g., scripts that can directly run with experimental/control group inputs to produce dependent variables).
Deleted files: {str(deleted_files)}
Keeping the above in mind, check if the remaining files are valid and follow the coding standards.
"""
        prompts.insert(0, deletion_report)

    # Get available port
    port = get_available_port(9077)
    logger.info(f"Starting VLM MCP server using port {port}")

    openhands_mcp_process = multiprocessing.Process(target=run_server, args=(config, port))
    openhands_mcp_process.start()

    all_results = ""
    for prompt in prompts:
        if add_file_summary:
            # Initialize FileSummary to get file descriptions
            file_summary = FileSummary(config)
            # Get file tree with summaries
            file_tree_with_summaries = file_summary.get_file_tree_with_summaries(max_token_cnt=1000, question=prompt)
            full_prompt = (
                prompt
                + get_lang_prompt(config.llm.language)
                + f"\n\n\nFile tree with summaries:\n\n\n{file_tree_with_summaries}"
            )
            if config.code_hint:
                full_prompt += "\n## Important Instructions\n" + config.code_hint
        else:
            full_prompt = prompt + get_lang_prompt(config.llm.language)
            if config.code_hint:
                full_prompt += "\n## Important Instructions\n" + config.code_hint

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
            f.write(full_prompt)

        max_iter = config.workflow.openhands_max_iter
        docker_name = config.docker.docker_name
        logger.info(f"Runtime docker: {docker_name}")

        with open("openlens_ai/tools/openhands_configs/config.toml", "r") as f:
            oh_config_template = f.read()
        oh_config = oh_config_template.replace("{api_key}", config.llm.chat.api_key)
        oh_config = oh_config.replace("{base_url}", config.llm.chat.base_url)
        oh_config = oh_config.replace("{code_model}", config.llm.chat.model)
        oh_config = oh_config.replace("{analyze_file_vlm_port}", str(port))

        if config.llm.condenser.model:
            oh_config = oh_config.replace("{condenser_api_key}", config.llm.condenser.api_key)
            oh_config = oh_config.replace("{condenser_base_url}", config.llm.condenser.base_url)
            oh_config = oh_config.replace("{code_condenser_model}", config.llm.condenser.model)
        else:
            logger.warning("Condenser model not specified, using chat model as condenser model.")
            oh_config = oh_config.replace("{condenser_api_key}", config.llm.chat.api_key)
            oh_config = oh_config.replace("{condenser_base_url}", config.llm.chat.base_url)
            oh_config = oh_config.replace("{code_condenser_model}", config.llm.chat.model)

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
        for try_i in range(2):  # Try at most 2 times
            # Build the command to execute in Docker container
            cmd = (
                ". openlens_ai/tools/openhands_configs/openhands_env.sh; "
                # f"chmod -R 777 {os.path.abspath(config.save_path)};"
                f"cd modules/OpenHands;"
                f'poetry run python -m openhands.core.main -f "{os.path.abspath(prompt_file)}" -i {max_iter} --config-file {os.path.abspath(this_config_path)};'
                f"cd ../../;"
                # f"chmod -R 777 {os.path.abspath(config.save_path)};"
            )
            results = run_openhands(cmd, config)
            fix_permissions_in_docker_container(oh_config)
            
            # Remove ANSI escape sequences (color codes, etc.)
            results = re.sub(r"\033\[[\d;]*m", "", results)
            results = split_and_clean_log(results)
            results = results[-10000:]
            if "AgentState.FINISHED" in results:
                logger.info(f"Docker container executed successfully.")
                break
            else:
                logger.warning(f"Docker container executed unsuccessfully. Trying again ({try_i}/5)...")
                continue

        # Add the result of the current prompt to the total result
        all_results += "=" * 20 + f"Prompt: {prompt[:20]}..." + "=" * 20
        all_results += "\n" + results

    # openhands_mcp_process termination
    if openhands_mcp_process.is_alive():
        logger.info("Terminating openhands_mcp_process...")
        openhands_mcp_process.terminate()
        openhands_mcp_process.join(timeout=5)  # Wait up to 5 seconds for process to terminate
        if openhands_mcp_process.is_alive():
            logger.warning("openhands_mcp_process did not terminate gracefully. Force killing...")
            openhands_mcp_process.kill()  # Force kill if it doesn't terminate gracefully
            openhands_mcp_process.join()

    # Limit result length to the last 3000 characters
    return all_results


def split_and_clean_log(log_text):
    # Regex match `time - openhands` as separator
    pattern = r"\n(\d{2}:\d{2}:\d{2} - openhands:)"

    # Split log
    log_entries = re.split(pattern, log_text)
    clean_entries = []
    for entry in log_entries:
        if ("agent_controller.py" in entry) and ("openhands:DEBUG" not in entry):
            clean_entries.append(entry)
    for entry_i in range(len(clean_entries)):
        if "]" in clean_entries[entry_i]:
            clean_entries[entry_i] = clean_entries[entry_i].split("]", 1)[1]  # Take the latter part
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
        """Main method for executing OpenHands operations"""
        logger.info(f"Starting OpenHands with prompt: {prompts}")
        # return str([random.randint(1000, 9999) for _ in range(10000)])
        
        all_results = run_openhands_prompt(prompts, self.config)
        return all_results


def collect_info_and_run_openhands(prompt: str, config: Config, state: State):
    pass


if __name__ == "__main__":
    from ..state import load_state

    # prompt = "Write a python script to draw a circle and save it as a png file. Then check if the content of the image using VLM tool (analyze_image_vlm and analyze_pdf_vlm)."
    prompt = "Check /workspace/manuscript/main.pdf to review if the paper is properly formatted."
    # prompt = "Search on the internet for the latest news about the OpenHands project."
    dataset_path = "data/dataset.jsonl"
    config, state, last_subgraph = load_state("outputs/power_grid_fault_id_20251121164412")
    result = run_openhands_prompt(prompt, config)
    with open("result.txt", "w") as f:
        f.write(result)

    # config = Config(
    #     dataset_path="datasets/eicu-demo",
    #     save_path="outputs/pred_aki_trend_eicu_demo_20251024143113_resume_20251024152546",
    #     thread_id="test",
    #     question="test",
    # )
    # oh_config_str = open(os.path.join(config.save_path, "openhands_config.toml"), "r").read()
    # fix_permissions_in_docker_container(oh_config_str)
