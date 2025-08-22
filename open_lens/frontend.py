import os

os.environ["STREAMLIT_RUNNING"] = "True"

import streamlit as st
from datetime import datetime
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from loguru import logger
import random
import re
import json
import glob
import subprocess
import time

from .build_graph import build_graph, run_graph
from .utils.file_utils import prepare_file_config
from .utils.frontend_utils import WorkspaceMonitor, display_messages_from_file
from .utils.config import Config
from .state import load_state
from .utils.process_manager import process_manager

def load_saved_sessions(email_filter=None):
    """Load saved sessions from outputs directory, optionally filtered by email"""
    if not email_filter or len(email_filter) <= 5:
        return []
    
    sessions = []
    email_show = email_filter.replace("@", "_").replace(".", "_")
    pattern = os.path.join("./outputs", f"OL_*{email_show}*")
    for path in glob.glob(pattern):
        if os.path.isdir(path):
            config_path = os.path.join(path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        config = Config(**config)
                    # 获取会话的邮箱
                    email = config.email
                    # 如果提供了邮箱过滤器，则只添加匹配的会话
                    if email_filter is None or email_filter == "" or email == email_filter:
                        sessions.append(config)
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
    return sorted(sessions, key=lambda x: x.thread_id, reverse=True)


def start_new_session(sidebar_container_empty, base_url, api_key, model, code_model):
    """Handle the start new session mode"""
    # 输入字段
    question = st.text_area(
        "Research Question",
        "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
        height=150,
    )

    # Dataset selection with dropdown
    dataset_option = st.selectbox(
        "Dataset Source",
        ["MIMIC-IV", "eICU", "PLAGH", "Upload My Own"],
        # ["MIMIC-IV", "eICU", "Upload My Own"],
        help="Select a pre-existing dataset or upload your own data"
    )
    
    # Initialize dataset_path
    dataset_path = ""
    
    # Handle dataset selection
    if dataset_option == "MIMIC-IV":
        dataset_path = "datasets/mimic"
        st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_mimic")
    elif dataset_option == "eICU":
        dataset_path = "datasets/eicu"
        st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_eicu")
    elif dataset_option == "PLAGH":
        dataset_path = "datasets/301_pros"
        st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_plagh")
    elif dataset_option == "Upload My Own":
        st.info("Please upload your dataset files below. They will be saved to ./datasets/user_upload/")
        uploaded_files = st.file_uploader(
            "Upload Dataset Files", 
            accept_multiple_files=True,
            type=["csv", "txt", "json", "parquet", "xls", "xlsx"],
            help="Upload your dataset files"
        )
        
        # Create user_upload directory if it doesn't exist
        user_upload_dir = "datasets/user_upload"
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Handle file uploads
        if uploaded_files:
            # Create a subdirectory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            upload_subdir = os.path.join(user_upload_dir, f"upload_{timestamp}_{random.randint(1000, 9999):04d}")
            os.makedirs(upload_subdir, exist_ok=True)
            
            # Save uploaded files
            for uploaded_file in uploaded_files:
                file_path = os.path.join(upload_subdir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            dataset_path = upload_subdir
            st.success(f"Files uploaded successfully to: {upload_subdir}")
            st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_uploaded")
        else:
            st.warning("Please upload at least one file for your dataset")
            dataset_path = None
    
    # email = st.text_input("Email (will update with you the progress)", "openlens@yeah.net")
    email = st.text_input("Email (will update with you the progress)", "")

    # 生成线程ID
    question_show = re.sub(r'[^\w]', '_', question.strip())
    thread_id = "OL_" + datetime.now().strftime("%Y%m%d%H%M%S") + \
        f"_{question_show[:15]}" + f"_{question_show[-15:]}" + \
            "_" + email.replace("@", "_").replace(".", "_") + "_" + \
            str(random.randint(1000, 9999))

    # 显示当前进程数量
    process_count = process_manager.get_process_count()

    btn1, btn2 = st.columns(2)
    btn1 = btn1.button("Run Agent", type="secondary")
    # btn2 = btn2.container(horizontal_alignment="right").button("Abort", type="primary")
    
    if btn1:
        if question and dataset_path and (len(email) > 5):
            # 检查进程数量是否已满
            if process_manager.is_full():
                st.error(f"Maximum number of processes ({process_manager.MAX_PROCESSES}) reached. Please wait for some processes to finish.")
                return
                
            st.chat_message("human").write("**Question:** " + question + "\n\n**Dataset Path:** " + dataset_path)
            
            if not process_manager.is_full():
                # 启动新进程运行任务
                process = subprocess.Popen([
                    "python", "-m", "open_lens.build_graph",
                    "--question", question,
                    "--dataset-path", dataset_path,
                    "--thread-id", thread_id,
                    "--email", email,
                    "--chat-model", model,
                    "--api-key", os.environ["OPENAI_API_KEY"] if "Default" in api_key else api_key,
                    "--base-url", os.environ["BASE_URL"] if "Default" in base_url else base_url,
                    "--code-model", code_model,
                ])
            
                # 将进程信息添加到进程管理器
                if not process_manager.add_process(process.pid, thread_id):
                    process.terminate()  # 如果添加失败，终止进程
                    st.error(f"Failed to start process. Maximum number of processes ({process_manager.MAX_PROCESSES}) reached.")
                    return
            
            time.sleep(5)
            config = open(os.path.join("outputs", thread_id, "config.json"), "r").read()
            config = json.loads(config)
            config = Config(**config)
            
            
            st.write(f"Thread ID: {thread_id}")
            st.warning(f"Job progress and results will be sent to {email}, please make sure the address is correct.")

            # 保存 config 到 session state
            st.session_state.config = config

            # 如果有旧的监控线程，停止它
            if st.session_state.monitor_thread:
                logger.info("Stopping old monitor thread")
                st.session_state.monitor_thread.stop()

            # 启动新的监控线程
            monitor_thread = WorkspaceMonitor(config.save_path, sidebar_container_empty)
            add_script_run_ctx(monitor_thread, get_script_run_ctx())
            monitor_thread.start()
            st.session_state.monitor_thread = monitor_thread

            st.success("Graph built successfully!")
            
            with st.empty():
                while True:
                    display_messages_from_file(config)
                    time.sleep(5)
                

        else:
            if not question:
                st.error("Please enter a question.")
            elif not dataset_path:
                st.error("Please enter a dataset path.")
            elif not len(email) > 5:
                st.error("Please enter an email.")


def resume_session(sidebar_container_empty):
    """Handle the resume session mode"""
    # 获取邮箱输入以过滤会话
    email_filter = st.text_input("Email", st.session_state.email)

    if len(email_filter) > 5:
        # 加载已保存的会话，根据邮箱过滤
        saved_sessions = load_saved_sessions(email_filter)
        
        if not saved_sessions:
            st.info("No saved sessions found. Start a new session first.")
        else:
            # 创建一个映射从显示文本到会话数据
            session_options = {
                f"{s.thread_id[:80]}{'...' if len(s.thread_id) > 80 else ''}": s 
                for s in saved_sessions
            }
            
            # 选择会话
            selected_session_key = st.selectbox(
                "Select a session to resume",
                list(session_options.keys()),
                help="Choose a previous session to continue"
            )
            
            if selected_session_key:
                config: Config = session_options[selected_session_key]
                
                # 显示选中的会话信息
                st.subheader("Session Information")
                st.write(f"**Thread ID:** {config.thread_id}")
                st.write(f"**Question:** {config.question}")
                st.write(f"**Dataset Path:** {config.dataset_path}")
                st.write(f"**Email:** {config.email}")
                st.write(f"**Path:** {config.save_path}")
                
                # Resume按钮
                if st.button("Resume Session"):
                    st.chat_message("human").write(
                        f"**Resuming Session**\n\n"
                        f"**Thread ID:** {config.thread_id}\n\n"
                        f"**Question:** {config.question}\n\n"
                        f"**Dataset Path:** {config.dataset_path}"
                    )
                    
                    # 重新加载配置
                    config_path = os.path.join(config.save_path, "config.json")
                    with open(config_path, 'r') as f:
                        config_dict = json.load(f)
                    config = Config(**config_dict)
                    
                    # 设置session state
                    st.session_state.config = config
                    
                    # 如果有旧的监控线程，停止它
                    if st.session_state.monitor_thread:
                        logger.info("Stopping old monitor thread")
                        st.session_state.monitor_thread.stop()

                    # 启动新的监控线程
                    monitor_thread = WorkspaceMonitor(config.save_path, sidebar_container_empty)
                    add_script_run_ctx(monitor_thread, get_script_run_ctx())
                    monitor_thread.start()
                    st.session_state.monitor_thread = monitor_thread
                    
                    with st.empty():
                        while True:
                            display_messages_from_file(config)
                            time.sleep(5)

    else:
        st.error("Please provide a email address (Length > 5).")


def main():
    
    st.title("OpenLens AI 📚🔍💡")
    st.subheader("Fully Autonomous Medical Research Agent")
    
    # 显示当前进程数量
    process_count = process_manager.get_process_count()
    st.caption(f"Current Running Jobs: {process_count}/{process_manager.MAX_PROCESSES}")
    
    st.write(" ")

    # 初始化 session state
    if "config" not in st.session_state:
        st.session_state.config = None
    if "monitor_thread" not in st.session_state:
        st.session_state.monitor_thread = None
    if "mode" not in st.session_state:
        st.session_state.mode = "Start New"
    if "email" not in st.session_state:
        st.session_state.email = ""

    # 创建侧边栏容器
    sidebar_container = st.sidebar.container()
    with sidebar_container:
        st.title("LLM Configuration")
        sidebar_container_api = st.container()
        st.title("Workspace")
        sidebar_container_empty = st.empty()
    
    with sidebar_container_api:
        base_url = st.text_input("API Base URL", value="Default (may be extremely slow)")
        api_key = st.text_input("API Key", value="Default (may be extremely slow)")
        model = st.text_input("Chat Model", value=os.environ.get("MODEL", ""))
        code_model = st.text_input("Code Model", value=os.environ.get("CODE_MODEL", ""))

    # 如果有正在运行的监控线程，但 config 已更改，则停止旧线程
    if (
        st.session_state.monitor_thread
        and st.session_state.config
        and hasattr(st.session_state.monitor_thread, "save_path")
        and st.session_state.monitor_thread.save_path != st.session_state.config.save_path
    ):
        logger.info("Stopping old monitor thread")

        st.session_state.monitor_thread.stop()
        st.session_state.monitor_thread = None

    # 如果没有运行中
    if not st.session_state.config:
        sidebar_container_empty.info("Run an agent to start monitoring workspace files.")

    # 添加模式选择
    mode = st.radio("Select Mode", ["Start New", "Resume"], horizontal=True, key="mode")
    
    if mode == "Start New":
        start_new_session(sidebar_container_empty, base_url, api_key, model, code_model)
    else:  # Resume mode
        resume_session(sidebar_container_empty)