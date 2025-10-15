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
from typing import List, Dict, Any, Optional

logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

from .build_graph import build_graph, run_graph
from .utils.frontend_utils import WorkspaceMonitor, display_messages_from_file, frontend_add_message, display_file_preview
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


def load_user_projects(email: str) -> List[Dict[str, Any]]:
    """加载用户专属项目列表"""
    if not email:
        return []
    
    
    projects = []
    # 根据用户ID查找项目
    admin_email = os.environ.get("FRONTEND_ADMIN_EMAIL", "")
    
    if email == admin_email:
        pattern = os.path.join("./outputs", f"*")
    else:
        email_show = email.replace("@", "_").replace(".", "_")
        pattern = os.path.join("./outputs", f"OL_*{email_show}*")
    
    for path in glob.glob(pattern):
        if os.path.isdir(path):
            config_path = os.path.join(path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    projects.append({
                        "thread_id": config_data.get("thread_id", ""),
                        "title": config_data.get("question", "Untitled Project")[:50] + ("..." if len(config_data.get("question", "")) > 50 else ""),
                        "question": config_data.get("question", ""),
                        "dataset": config_data.get("dataset_path", ""),
                        "path": path,
                        "created_at": os.path.getctime(path),
                        "last_modified": os.path.getmtime(path)
                    })
                except Exception as e:
                    logger.warning(f"Failed to load project from {path}: {e}")
    
    # 按最后修改时间排序
    return sorted(projects, key=lambda x: x["last_modified"], reverse=True)


def build_sidebar():
    with st.sidebar:
        # 登录/登出功能
        if not st.user.is_logged_in:
            st.button("Log in", on_click=st.login)
            # st.stop()  # 未登录时停止执行
        else:
            user_info = st.user.to_dict()
            col1, col2 = st.columns([4,1])
            with st.popover(f"😀 {user_info.get('email', 'Unknown')}"):
                st.write(f"Email: {user_info.get('email', 'Unknown')}")
                if hasattr(st.user, 'sub'):
                    st.write(f"Sub: {st.user.sub}")
                st.button("🚶‍♂️‍➡ Log out", on_click=st.logout, width="content", type="tertiary")
        
        # 用户专属项目列表（移到侧边栏底部）
        st.subheader("📁 Your Projects")
        if st.user.is_logged_in:
            user_id = st.user.sub if hasattr(st.user, 'sub') else st.user.email
            st.session_state.email = st.user.email
            user_projects = load_user_projects(st.session_state.email)
            
            if user_projects:
                for project in user_projects:
                    project_title = project["title"]
                    project_key = f"project_{project['thread_id']}"
                    
                    if st.button(project_title, key=project_key, width="stretch", type="tertiary"):
                        # 加载项目配置
                        config_path = os.path.join(project["path"], "config.json")
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                        
                        config = Config(**config_data)
                        st.session_state.config = config
                        
                        # 如果有旧的监控线程，停止它
                        if st.session_state.monitor_thread:
                            st.session_state.monitor_thread.stop()
                        
                        
                        st.rerun()
            else:
                st.info("No projects yet. Create your first project below.")

        # 新建项目按钮
        if st.button("\+ New project", width="stretch"):
            st.session_state.config = None
            st.rerun()



def start_job(question, dataset_path, email):
    if question and dataset_path and (len(email) > 5):
        # 生成线程ID
        question_show = re.sub(r'[^\w]', '_', question.strip())
        thread_id = "OL_" + datetime.now().strftime("%Y%m%d%H%M%S") + \
            f"_{question_show[:15]}" + f"_{question_show[-15:]}" + \
                "_" + email.replace("@", "_").replace(".", "_") + "_" + \
                str(random.randint(1000, 9999))
                
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
                "--chat-model", os.environ.get("MODEL", ""),
                "--api-key", os.environ.get("OPENAI_API_KEY", ""),
                "--base-url", os.environ.get("BASE_URL", ""),
                "--code-model", os.environ.get("CODE_MODEL", ""),
                "--vision-model", os.environ.get("VISION_MODEL", ""),
            ])
        
            # 将进程信息添加到进程管理器
            if not process_manager.add_process(process.pid, thread_id):
                process.terminate()  # 如果添加失败，终止进程
                st.error(f"Failed to start process. Maximum number of processes ({process_manager.MAX_PROCESSES}) reached.")
                return
        
        with st.status("Creating job...") as status:
            while True:
                try:
                    time.sleep(5)
                    config = open(os.path.join("outputs", thread_id, "config.json"), "r").read()
                    config = json.loads(config)
                    config = Config(**config)
                    st.session_state.config = config
                    st.rerun()
                    break
                except Exception as e:
                    logger.error(f"Error loading config: {e}")
                    continue
        

def watch_job(config):
    thread_id = config.thread_id
    email = config.email
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
    

def main():
    # 设置页面配置
    st.set_page_config(page_title="OpenLens AI", layout="wide", initial_sidebar_state="expanded")
    
    # 初始化session state
    if "config" not in st.session_state:
        st.session_state.config = None
    if "monitor_thread" not in st.session_state:
        st.session_state.monitor_thread = None
    if "question_input" not in st.session_state:
        st.session_state.question_input = ""
    if "dataset_selected" not in st.session_state:
        st.session_state.dataset_selected = "MIMIC-IV-ICU"
    
    # 侧边栏设计
    build_sidebar()
          
    # 如果有当前项目，显示项目界面
    if st.session_state.config:
        config = st.session_state.config
        
        # 分割为左右两栏
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📄 Latest Files")
            with st.container(height=800):
                display_file_preview(config)
        
        with col2:
            st.subheader("💬 Conversation History")
            with st.container(height=800):
                display_messages_from_file(config)
    else:
          
        # 主界面设计
        st.title("🫧 OpenLens AI")
        st.subheader("Fully Autonomous Research Agent for Health Informatics")
        
        # 显示当前进程数量
        process_count = process_manager.get_process_count()
        st.caption(f"Current Running Jobs: {process_count}/{process_manager.MAX_PROCESSES}")
        
        
        # 主要输入框
        question = st.text_area(
            "Research Question",
            value=st.session_state.question_input,
            height=150,
            placeholder="What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
            key="question_input_main"
        )
        
        # 如果用户输入了问题，隐藏Use Cases
        show_use_cases = not question.strip()
        
        # 数据集选择/上传功能区
        dataset_option = st.selectbox(
            "Dataset Source",
            ["MIMIC-IV-ICU", "eICU-Demo", "Upload My Own"],
            index=["MIMIC-IV-ICU", "eICU-Demo", "Upload My Own"].index(st.session_state.dataset_selected),
            key="dataset_select"
        )
        
        st.session_state.dataset_selected = dataset_option
        
        dataset_path = ""
        
        # 处理数据集选择
        if dataset_option == "MIMIC-IV-ICU":
            dataset_path = "datasets/mimic-iv-icu"
            # st.text_input("Dataset Path", dataset_path, disabled=True)
        elif dataset_option == "eICU-Demo":
            dataset_path = "datasets/eicu-demo"
            # st.text_input("Dataset Path", dataset_path, disabled=True)
        elif dataset_option == "Upload My Own":
            st.info("Please upload your dataset files below. They will be saved to ./datasets/user_upload/")
            uploaded_files = st.file_uploader(
                "Upload Dataset Files", 
                accept_multiple_files=True,
                type=["csv", "txt", "json", "parquet", "xls", "xlsx"],
                help="Upload your dataset files"
            )
            
            # 创建用户上传目录
            user_upload_dir = "datasets/user_upload"
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # 处理文件上传
            if uploaded_files:
                # 创建带时间戳的子目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                upload_subdir = os.path.join(user_upload_dir, f"upload_{timestamp}_{random.randint(1000, 9999):04d}")
                os.makedirs(upload_subdir, exist_ok=True)
                
                # 保存上传的文件
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(upload_subdir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                dataset_path = upload_subdir
                st.success(f"Files uploaded successfully to: {upload_subdir}")
                st.text_input("Dataset Path", dataset_path, disabled=True)
            else:
                st.warning("Please upload at least one file for your dataset")
                dataset_path = None
        
        # 提交按钮
        submit_col1, submit_col2 = st.columns([1, 3])
        
        with submit_col1:
            submit_button = st.button("🚀 Start Research", width="stretch")
            
        with submit_col2:
            st.caption("Note: This will start a fully autonomous research process that may take significant time to complete.")
            
        # 处理提交
        if submit_button:
            start_job(question, dataset_path, st.session_state.email)
            
            
            
        # Use Cases选项卡（仅在没有输入问题时显示）
        if show_use_cases:
            st.subheader("Explore use cases")
            
            # 加载保存的实验
            saved_experiments = load_saved_experiments()
            saved_experiments = random.sample(saved_experiments, min(6, len(saved_experiments)))
            
            # 创建三列用于卡片式展示（添加一列用于Resume Session）
            col1, col2 = st.columns(2)
            
            
            if saved_experiments:
                for i, exp in enumerate(saved_experiments):
                    # 从dir_name解析出dataset和更友好的标题
                    dir_name = exp.get('dir_name', '')
                    
                    # 选择列（跳过第一列，因为已经被Resume Session占用）
                    if i % 2 == 0:
                        col = col1
                    else:
                        col = col2
                    
                    with col:
                        # 创建卡片式按钮
                        if st.button(
                            exp.get('question', 'No question specified'),
                            key=f"use_case_{i}",
                            help="Click to use this experiment",
                            width="stretch"
                        ):
                            st.session_state.config = exp.get('config', {})
            
            
            
        

