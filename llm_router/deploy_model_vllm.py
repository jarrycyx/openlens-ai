import subprocess
import os
import time
import psutil
import argparse

def start_vllm_process(model_path, max_len="64000", port="8000", gpu="0", log_to_file=False, extra_args=""):
    gpu_per_process = len(gpu.split(","))
    
    cmd = [
        "vllm", "serve", model_path, 
        "--max-model-len", max_len, 
        # "--tensor-parallel-size", f"{gpu_per_process}", 
        "--pipeline-parallel-size", f"{gpu_per_process}", 
        "--port", port,
        # "--enable-expert-parallel",
        # "--gpu-memory-utilization", 0.9,
        "--enable-auto-tool-choice",
        "--served-model-name", "llm"
    ]
    
    if extra_args:
        cmd += extra_args.split(" ")
    
    if "glm" in model_path.lower():
        tool_parser = "glm45"
        reasoning_parser = "glm45"
        cmd += ["--tool-call-parser", tool_parser, "--reasoning-parser", reasoning_parser]
    elif "qwen3" in model_path.lower():
        if "coder" in model_path.lower():
            tool_parser = "qwen3_coder"
            cmd += ["--tool-call-parser", tool_parser]
        else:
            tool_parser = "hermes"
            cmd += ["--tool-call-parser", tool_parser]
    else:
        print("Model type not recognized. Using hermes parser.")
        cmd += ["--tool-call-parser", "hermes"]
    
    
    if "AWQ" not in model_path:
        cmd += ["--config-format", "hf"]
    
        
    this_os_env = os.environ.copy()
    this_os_env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    # this_os_env["CUDA_LAUNCH_BLOCKING"] = "1"
    print(f"Running command: {' '.join(cmd)} on GPU: {gpu}")
    
    if log_to_file:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        log_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(log_dir, exist_ok=True)
        log_fp = os.path.join(log_dir, f"vllm_log_{timestamp}_{port}.txt")
        with open(log_fp, "w") as fp:
            p = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT, env=this_os_env)
    else:
        p = subprocess.Popen(cmd, env=this_os_env)
    return p

def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        gone, alive = psutil.wait_procs(children, timeout=5)
        for child in alive:
            child.kill()
        parent.terminate()
        parent.wait()
    except psutil.NoSuchProcess:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy model with vLLM")
    parser.add_argument("-m", "--model", type=str, required=True, help="Model path")
    parser.add_argument("-p", "--port", type=str, default="8000", help="API port")
    parser.add_argument("-g", "--gpu", type=str, default="0", help="GPU IDs to use")
    parser.add_argument("--max-len", type=str, default="64000", help="Maximum length of input")
    parser.add_argument("--log-to-file", action="store_true", help="Log to file")
    parser.add_argument("--enforce-eager", action="store_true", help="Enable eager mode")
    # 后面可以附加更多参数，比如--dtype
    parser.add_argument("--extra", nargs=argparse.REMAINDER, type=str, help="Additional arguments for vLLM")
    
    args = parser.parse_args()
    
    print(f"All args: {args}")
    
    gpu_list = str(args.gpu).split(",")
    port_list = str(args.port).split(",")
    assert len(gpu_list) % len(port_list) == 0, "Port number must be divisible by GPU number"
    
    gpu_per_process = len(gpu_list) // len(port_list)
    gpu_alloc_list = [gpu_list[i:i+gpu_per_process] for i in range(0, len(gpu_list), gpu_per_process)]
    
    proc_list = []
    for gpu_group, port in zip(gpu_alloc_list, port_list):
        print(f"Starting vLLM on GPUs: {gpu_group}, port: {port}")
        p = start_vllm_process(
            model_path=args.model,
            port=port,
            max_len=args.max_len,
            gpu=",".join(gpu_group),
            log_to_file=args.log_to_file,
            extra_args=" ".join(args.extra),
        )
        proc_list.append(p)
    
    print("Waiting for models to initialize...")
    time.sleep(60)
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopping vLLM server...")
        for process in proc_list:
            kill_process_tree(process.pid)