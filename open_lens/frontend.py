import os

os.environ["STREAMLIT_RUNNING"] = "True"

import streamlit as st
from datetime import datetime
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from loguru import logger
import random
import re

from .build_graph import build_graph, run_graph
from .utils.file_utils import prepare_file_config
from .utils.frontend_utils import WorkspaceMonitor


def main():
    
    st.title("OpenLens AI 📚🔍💡")
    st.subheader("Fully Autonomous Medical Research Agent")
    st.write(" ")

    # 初始化 session state
    if "save_path" not in st.session_state:
        st.session_state.save_path = None
    if "monitor_thread" not in st.session_state:
        st.session_state.monitor_thread = None

    # 创建侧边栏容器
    sidebar_container = st.sidebar.container()
    with sidebar_container:
        st.title("LLM Configuration")
        sidebar_container_api = st.container()
        st.title("Workspace")
        sidebar_container_empty = st.empty()
    
    with sidebar_container_api:
        base_url = st.text_input("API Base URL", value=os.environ.get("BASE_URL", ""))
        api_key = st.text_input("API Key", value=os.environ.get("OPENAI_API_KEY", ""))
        model = st.text_input("Chat Model", value=os.environ.get("MODEL", ""))
        code_model = st.text_input("Code Model", value=os.environ.get("CODE_MODEL", ""))

    # 如果有正在运行的监控线程，但 save_path 已更改，则停止旧线程
    if (
        st.session_state.monitor_thread
        and st.session_state.save_path
        and hasattr(st.session_state.monitor_thread, "save_path")
        and st.session_state.monitor_thread.save_path != st.session_state.save_path
    ):

        st.session_state.monitor_thread.stop()
        st.session_state.monitor_thread = None

    # 如果没有运行中
    if not st.session_state.save_path:
        sidebar_container_empty.info("Run an agent to start monitoring workspace files.")

    # 输入字段
    question = st.text_area(
        "Research Question",
        "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
        height=150,
    )

    # Dataset selection with dropdown
    dataset_option = st.selectbox(
        "Dataset Source",
        ["MIMIC-IV", "eICU", "Upload My Own"],
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
            str(random.randint(1000, 9999))

    btn1, btn2 = st.columns(2)
    btn1 = btn1.button("Run Agent", type="secondary")
    btn2 = btn2.container(horizontal_alignment="right").button("Abort", type="primary")
    
    if btn2:
        st.rerun()
    
    if btn1:
        if question and dataset_path and model and base_url and api_key and email:
            if model != os.environ.get("MODEL", ""):
                os.environ["MODEL"] = model
            if api_key != os.environ.get("OPENAI_API_KEY", ""):
                os.environ["OPENAI_API_KEY"] = api_key
            if base_url != os.environ.get("BASE_URL", ""):
                os.environ["BASE_URL"] = base_url
            if code_model != os.environ.get("CODE_MODEL", ""):
                os.environ["CODE_MODEL"] = code_model
            
            st.chat_message("human").write("**Question:** " + question + "\n\n**Dataset Path:** " + dataset_path)
            # 准备配置
            init_state, config, save_path = prepare_file_config(thread_id, question, dataset_path, email)
            
            st.write(f"Thread ID: {thread_id}")
            st.warning(f"Job progress and results will be sent to {email}, please make sure the address is correct.")

            # 保存 save_path 到 session state
            st.session_state.save_path = save_path

            # 如果有旧的监控线程，停止它
            if st.session_state.monitor_thread:
                st.session_state.monitor_thread.stop()

            # 启动新的监控线程
            monitor_thread = WorkspaceMonitor(save_path, sidebar_container_empty)
            add_script_run_ctx(monitor_thread, get_script_run_ctx())
            monitor_thread.start()
            st.session_state.monitor_thread = monitor_thread

            # 构建图
            with st.spinner("Building graph..."):
                graph = build_graph(config, None)

            st.success("Graph built successfully!")

            run_graph(config, graph, save_path, init_state)

        else:
            if not question:
                st.error("Please enter a question.")
            elif not dataset_path:
                st.error("Please enter a dataset path.")
            elif not email:
                st.error("Please enter an email.")
