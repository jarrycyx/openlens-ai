import os, sys

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
import zipfile
import io
import shutil
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

from .build_graph import build_graph, run_graph
from .utils.frontend_utils import WorkspaceMonitor, display_messages_from_file
from .utils.config import Config
from .state import load_state
from .utils.process_manager import process_manager

def load_saved_experiments():
    """Load saved experiments from exp/saved_exp directory"""
    preset_experiments = []
    saved_exp_root = "exp/saved_exp/eval_0915_old"
    
    if not os.path.exists(saved_exp_root):
        return []
    
    # 遍历所有子目录查找实验目录
    for root, dirs, files in os.walk(saved_exp_root):
        for dir_name in dirs:
            if dir_name.startswith("test_"):
                # 解析目录名获取dataset和question信息
                # 格式: test_{dataset}_{question}
                dir_path = os.path.join(root, dir_name)
                config_path = os.path.join(dir_path, "config.json")
                
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        
                        preset_experiments.append({
                            'question': config.get('question', ''),
                            'dataset_path': config.get('dataset_path', ''),
                            'dir_name': dir_name,
                            'path': dir_path,
                            'thread_id': config.get('thread_id', ''),
                            'email': config.get('email', '')
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load config from {config_path}: {e}")
    
    return preset_experiments

def load_saved_sessions(email_filter=None):
    """Load saved sessions from outputs directory, optionally filtered by email"""
    if not email_filter or len(email_filter) <= 5:
        return []
    
    sessions = []
    admin_email = os.environ.get("FRONTEND_ADMIN_EMAIL", "")
    if email_filter == admin_email:
        pattern = os.path.join("./outputs", f"*")
        email_filter = ""
    else:
        email_show = email_filter.replace("@", "_").replace(".", "_")
        pattern = os.path.join("./outputs", f"OL_*{email_show}*")
    filter_list = glob.glob(pattern)
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
    if os.path.exists(os.path.join("./outputs", email_filter)):
        filter_list.append(os.path.join("./outputs", email_filter))
        config_path = os.path.join("./outputs", email_filter, "config.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                config = Config(**config)
                logger.info(f"Exact match found for {email_filter}")
                sessions.append(config)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    return sorted(sessions, key=lambda x: x.thread_id, reverse=True)


def start_new_session(workspace_container, sidebar_usage_container, base_url, api_key, model, code_model, vision_model):
    """Handle the start new session mode"""
    
    # 添加预设问题选择
    preset_experiments = load_saved_experiments()
    
    use_preset = st.checkbox("Use preset research question and dataset", value=True)
    
    question = ""
    dataset_path = ""
    preset_selected = None
    
    if use_preset and preset_experiments:
        # 创建预设问题选项列表
        preset_options = [f"{exp['question']} | Dataset: {exp['dataset_path']}" for exp in preset_experiments]
        selected_preset = st.selectbox("Select a preset experiment", preset_options)
        
        # 根据选择的预设填充问题和数据集路径
        if selected_preset:
            selected_index = preset_options.index(selected_preset)
            preset_selected = preset_experiments[selected_index]
            question = preset_selected['question']
            dataset_path = preset_selected['dataset_path']
            
            # 显示预设的问题和数据集
            st.text_area("Research Question (preset)", question, height=150, key="preset_question", disabled=True)
            st.text_input("Dataset Path (preset)", dataset_path, disabled=True, key="preset_dataset")
            
            # 添加"Resume with Preset"按钮
            paper_path = os.path.join(preset_selected['path'], "workspace", "manuscript", "*main*.pdf")
            paper_path = glob.glob(paper_path)
            paper_path = paper_path[0] if paper_path else None
            
            if paper_path and os.path.exists(paper_path):
                with open(paper_path, "rb") as f:
                    pdf_buffer = f.read()
                btn = st.download_button("Resume with Preset", data=pdf_buffer, file_name="paper.pdf")
            else:
                btn = st.button("Resume with Preset", width="stretch")
            
            if btn:
                if preset_selected:
                    # 设置session state模拟从已保存会话恢复
                    config_dict = {
                        'save_path': preset_selected['path'],
                        'thread_id': preset_selected['thread_id'],
                        'question': preset_selected['question'],
                        'dataset_path': preset_selected['dataset_path'],
                        'email': preset_selected['email']
                    }
                    config = Config(**config_dict)
                    st.session_state.config = config
                    
                    # 如果有旧的监控线程，停止它
                    if st.session_state.monitor_thread:
                        logger.info("Stopping old monitor thread")
                        st.session_state.monitor_thread.stop()

                    # 启动新的监控线程
                    monitor_thread = WorkspaceMonitor(config, workspace_container, sidebar_usage_container)
                    add_script_run_ctx(monitor_thread, get_script_run_ctx())
                    monitor_thread.start()
                    st.session_state.monitor_thread = monitor_thread
                    
                    st.success(f"Resumed with preset: {question}")
                    
                    with st.empty():
                        while True:
                            display_messages_from_file(config)
                            time.sleep(5)
    else:
        # 输入字段
        question = st.text_area(
            "Research Question",
            "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
            height=150,
        )

        # Dataset selection with dropdown
        dataset_option = st.selectbox(
            "Dataset Source",
            # ["MIMIC-IV-ICU", "eICU-Demo", "PLAGH", "Upload My Own"],
            ["MIMIC-IV-ICU", "eICU-Demo", "Upload My Own"],
            help="Select a pre-existing dataset or upload your own data"
        )
        
        # Initialize dataset_path
        dataset_path = ""
        
        # Handle dataset selection
        if dataset_option == "MIMIC-IV-ICU":
            dataset_path = "datasets/mimic-iv-icu"
            st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_mimic")
        elif dataset_option == "eICU-Demo":
            dataset_path = "datasets/eicu-demo"
            st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_eicu")
        # elif dataset_option == "PLAGH":
        #     dataset_path = "datasets/301_pros"
        #     st.text_input("Dataset Path", dataset_path, disabled=True, key="dataset_path_plagh")
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

        btn1, btn2 = st.columns(2)
        btn1 = btn1.button("Run Agent", type="secondary")
        # btn2 = btn2.container(horizontal_alignment="right").button("Abort", type="primary")
        
        if btn1:
            if api_key and base_url:
                if question and dataset_path and (len(email) > 5):
                    # 检查进程数量是否已满
                    if process_manager.is_full():
                        st.error(f"Maximum number of processes ({process_manager.MAX_PROCESSES}) reached. Please wait for some processes to finish.")
                        return
                        
                    st.chat_message("human").write("**Question:** " + question + "\n\n**Dataset Path:** " + dataset_path)
                    
                    if not process_manager.is_full():
                        # 启动新进程运行任务
                        process = subprocess.Popen([
                            "python", "-m", "openlens_ai.build_graph",
                            "--question", question,
                            "--dataset-path", dataset_path,
                            "--thread-id", thread_id,
                            "--email", email,
                            "--chat-model", model,
                            "--api-key", os.environ["OPENAI_API_KEY"] if "Default" in api_key else api_key,
                            "--base-url", os.environ["BASE_URL"] if "Default" in base_url else base_url,
                            "--code-model", code_model,
                            "--vision-model", vision_model,
                        ])
                    
                        # 将进程信息添加到进程管理器
                        if not process_manager.add_process(process.pid, thread_id):
                            process.terminate()  # 如果添加失败，终止进程
                            st.error(f"Failed to start process. Maximum number of processes ({process_manager.MAX_PROCESSES}) reached.")
                            return
                    while True:
                        try:
                            time.sleep(5)
                            config = open(os.path.join("outputs", thread_id, "config.json"), "r").read()
                            config = json.loads(config)
                            config = Config(**config)
                            break
                        except Exception as e:
                            logger.error(f"Error loading config: {e}")
                            continue
                    
                    
                    st.write(f"Thread ID: {thread_id}")
                    st.warning(f"Job progress and results will be sent to {email}, please make sure the address is correct.")

                    # 保存 config 到 session state
                    st.session_state.config = config

                    # 如果有旧的监控线程，停止它
                    if st.session_state.monitor_thread:
                        logger.info("Stopping old monitor thread")
                        st.session_state.monitor_thread.stop()

                    # 启动新的监控线程
                    monitor_thread = WorkspaceMonitor(config, workspace_container, sidebar_usage_container)
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
            else:
                st.error("Please provide both API Key and Base URL. Recommended platform: https://www.siliconflow.cn/, https://cloud.infini-ai.com/, https://openrouter.ai/models")


def resume_session(workspace_container, sidebar_usage_container):
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
                s.thread_id: s 
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
                paper_path = os.path.join(config.save_path, "workspace", "manuscript", "*main*.pdf")
                paper_path = glob.glob(paper_path)
                paper_path = paper_path[0] if paper_path else None
                
                if paper_path and os.path.exists(paper_path):
                    with open(paper_path, "rb") as f:
                        pdf_buffer = f.read()
                    btn = st.download_button("Resume Session", data=pdf_buffer, file_name="paper.pdf", type="primary")
                else:
                    btn = st.button("Resume Session")
                
                if btn:
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
                    monitor_thread = WorkspaceMonitor(config, workspace_container, sidebar_usage_container)
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
    st.set_page_config(page_title="OpenLens AI", layout="wide")
    st.title("🫧 OpenLens AI")
    st.subheader("Fully Autonomous Research Agent for Health Infomatics")
    st.page_link("https://github.com/jarrycyx/openlens-ai", label="🌟 Star our project on GitHub")
    
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
    sidebar_container.title("LLM Configuration")
    sidebar_container_api = sidebar_container.container()
    sidebar_container.title("Token Usage")
    sidebar_usage_container = sidebar_container.empty()
    sidebar_container.title("Workspace")
    workspace_container = sidebar_container.empty()
    
    with sidebar_container_api:
        # 使用列布局使三个模型输入框并排放置
        col1, col2 = st.columns(2)
        
        # with col1:
        #     base_url = st.text_input("API Base URL", value="Default (slow)")
        # with col2:
        #     api_key = st.text_input("API Key", value="Default (slow)")
        
        with col1:
            base_url = st.text_input("API Base URL", value="", help="Recommended platform: https://www.siliconflow.cn/, https://cloud.infini-ai.com/, https://openrouter.ai/models, https://bigmodel.cn/", placeholder="Enter LLM Base URL")
        with col2:
            api_key = st.text_input("API Key", value="", placeholder="Enter LLM API key")
        
        # 将code_model和vision_model放在新的一行
        col3, col4, col5 = st.columns(3)
        with col3:
            model = st.text_input("Chat Model", value="glm-4.5-air")
        with col4:
            code_model = st.text_input("Code Model", value="glm-4.5-air")
        with col5:
            vision_model = st.text_input("Vision Model", value="glm-4.1v-9b-thinking", help="Please select a vision model (e.g. qwen3-vl, glm-4.5v, glm-4.1v-9b-thinking)")

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
        workspace_container.info("Run an agent to start monitoring workspace files.")

    # 添加模式选择
    mode = st.radio("Select Mode", ["Start New", "Resume"], horizontal=True, key="mode")
    
    
    if mode == "Start New":
        start_new_session(workspace_container, sidebar_usage_container, base_url, api_key, model, code_model, vision_model)
    else:  # Resume mode
        resume_session(workspace_container, sidebar_usage_container)