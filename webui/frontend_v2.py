"""
此模块为 OpenLens AI 前端的核心模块，负责实现用户界面和交互逻辑，
包括用户登录、项目管理、任务启动和监控等功能。
"""
import os
import sys
from datetime import datetime
import random
import re
import json
import glob
import subprocess
import time
import toml
from typing import List, Dict, Any, Optional

from loguru import logger
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from openlens_ai.utils.config import Config


from .utils.frontend_utils import show_workspace, display_messages_from_file, get_zip, display_multiple_file_preview, display_single_file, get_latest_files
from .utils.process_manager import process_manager
from .utils.translations import t, set_language, get_current_language

logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])
config = Config.from_toml("config.toml")

@st.cache_data()
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

                try:
                    # TODO: remove config.json because it is not used anymore
                    if os.path.exists(os.path.join(dir_path, "config.json")):
                        with open(config_path, "r") as f:
                            config = json.load(f)
                    elif os.path.exists(os.path.join(dir_path, "config.toml")):
                        with open(os.path.join(dir_path, "config.toml"), "r") as f:
                            config = toml.load(f)
                    else:
                        raise FileNotFoundError("No config.json or config.toml found in experiment directory")

                    preset_experiments.append(
                        {
                            "question": config.get("question", ""),
                            "dataset": config.get("dataset_path", ""),
                            "dir_name": dir_name,
                            "path": dir_path,
                            "thread_id": config.get("thread_id", ""),
                            "email": config.get("email", ""),
                            "language": config.get("llm", {}).get("language", "eng"),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
                    continue

    return preset_experiments


def load_user_projects(email: str) -> List[Dict[str, Any]]:
    """加载用户专属项目列表"""
    if not email:
        return []

    projects = []
    # 根据用户ID查找项目
    admin_email = config.frontend.frontend_admin_email

    if email == admin_email:
        pattern = os.path.join("./outputs", "*")
    else:
        email_show = email.replace("@", "_").replace(".", "_")
        pattern = os.path.join("./outputs", f"OL_*{email_show}*")

    for path in glob.glob(pattern):
        if os.path.isdir(path):
            try:
                # TODO: Remove config.json because it is not used anymore
                if os.path.exists(os.path.join(path, "config.json")):
                    with open(config_path, "r") as f:
                        config_data = json.load(f)
                elif os.path.exists(os.path.join(path, "config.toml")):
                    with open(os.path.join(path, "config.toml"), "r") as f:
                        config_data = toml.load(f)
                else:
                    raise FileNotFoundError("No config.json or config.toml found in project directory")
            except Exception as e:
                logger.debug(f"Failed to load project from {path}: {e}")
                continue
            
            # 用户创建的项目，question不需要翻译
            question =  config_data.get("question", "Untitled Project")
            
            chinese_char_cnt = len(re.findall(r"[\u4e00-\u9fa5]", question))
            chinese_ratio = chinese_char_cnt / len(question) if len(question) > 0 else 0
            title_truncate_len = 30 if chinese_ratio > 0.5 else 100
            projects.append(
                {
                    "thread_id": config_data.get("thread_id", ""),
                    "language": config_data.get("llm", {}).get("language", "eng"),
                    "title": question[:title_truncate_len] + ("..." if len(question) > title_truncate_len else ""),
                    "question": config_data.get("question", ""),
                    "dataset": config_data.get("dataset_path", ""),
                    "path": path,
                    "created_at": os.path.getctime(path),
                    "last_modified": os.path.getmtime(path),
                }
            )
    # 按最后修改时间排序
    return sorted(projects, key=lambda x: x["last_modified"], reverse=True)


def build_sidebar():
    with st.sidebar:
        # 登录/登出功能
        if not st.user.is_logged_in:
            # 未登录时显示登录按钮和语言切换按钮
            col1, col2 = st.columns([2, 1])
            with col1:
                st.button(f"🚶‍♂️‍➡ {t('log_in')}", help=t('log_in'), width="stretch", on_click=st.login)
            with col2:
                current_lang = get_current_language()
                lang_button_text = "🌐 中" if current_lang == "eng" else "🌐 En"
                with st.popover(lang_button_text, width="stretch"):
                    st.write("**选择语言 / Select Language**")
                    if st.button("🇨🇳 中文", key="lang_zh_logout"):
                        set_language("chs")
                        st.rerun()
                    if st.button("🇺🇸 English", key="lang_en_logout"):
                        set_language("eng")
                        st.rerun()
            # st.stop()  # 未登录时停止执行
        else:
            # 已登录时显示用户信息和语言切换按钮
            user_info = st.user.to_dict()
            col1, col2 = st.columns([3, 1])
            with col1:
                with st.popover(f"😀 {user_info.get('email', 'Unknown')}", width="stretch"):
                    st.write(f"{t('email')}: {user_info.get('email', 'Unknown')}")
                    if hasattr(st.user, "sub"):
                        st.write(f"Sub: {st.user.sub}")
                    st.button(f"🚶‍♂️‍➡ {t('logout')}", on_click=st.logout, width="content", type="tertiary")
            with col2:
                current_lang = get_current_language()
                lang_button_text = "🌐 中" if current_lang == "chs" else "🌐 En"
                with st.popover(lang_button_text, width="content"):
                    st.write("**选择语言 / Select Language**")
                    with st.container(horizontal=True):
                        if st.button("🇨🇳 中文", key="lang_zh"):
                            set_language("chs")
                            st.rerun()
                        if st.button("🇺🇸 English", key="lang_en"):
                            set_language("eng")
                            st.rerun()

        st.divider()
        # 用户专属项目列表（移到侧边栏底部）
        st.subheader(f"📁 {t('your_projects')}")
        # 新建项目按钮
        if st.button(f"&nbsp; 🚀&nbsp; {t('new_project')}", help=t("new_project"), width="stretch"):
            st.session_state.config = None
            st.rerun()
        if st.user.is_logged_in:
            user_id = st.user.sub if hasattr(st.user, "sub") else st.user.email
            st.session_state.email = st.user.email
            user_projects = load_user_projects(st.session_state.email)

            if user_projects:
                for project in user_projects:
                    project_title = project["title"]
                    project_language = t(project["language"])
                    project_key = f"project_{project['thread_id']}"
                    dataset_name = t(project["dataset"].split("/")[-1] if project["dataset"] else "Unknown dataset")

                    if st.button(f"**{project_language}** | {project_title} | *{dataset_name}*", key=project_key, width="stretch", type="tertiary"):
                        # 加载项目配置
                        try:
                            if os.path.exists(os.path.join(project["path"], "config.json")):
                                with open(config_path, "r") as f:
                                    config_data = json.load(f)
                            elif os.path.exists(os.path.join(project["path"], "config.toml")):
                                with open(os.path.join(project["path"], "config.toml"), "r") as f:
                                    config_data = toml.load(f)
                            else:
                                raise FileNotFoundError("No config.json or config.toml found in project directory")
                        except Exception as e:
                            logger.warning(f"Failed to load config from {project['path']}: {e}")
                            continue

                        config = Config(**config_data)
                        st.session_state.config = config

                        # 如果有旧的监控线程，停止它
                        if st.session_state.monitor_thread:
                            st.session_state.monitor_thread.stop()

                        st.rerun()
            else:
                st.info(t("no_projects_yet"))
        else:
            st.info(t("no_projects_yet"))

        st.divider()
        st.link_button(t("github_link"), url="https://github.com/jarrycyx/openlens-ai", type="secondary", width="stretch")


def start_job(question, dataset_path, email, language="chs"):
    if question and dataset_path and (len(email) > 5):
        # 获取配置
        
        # 生成线程ID
        question_show = re.sub(r"[^\w]", "_", question.strip())
        thread_id = (
            "OL_"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + f"_{question_show[:15]}"
            + f"_{question_show[-15:]}"
            + "_"
            + email.replace("@", "_").replace(".", "_")
            + "_"
            + str(random.randint(1000, 9999))
        )

        # 检查进程数量是否已满
        if process_manager.is_full():
            st.error(t("failed_to_start_process", max=process_manager.MAX_PROCESSES))
            return

        if not process_manager.is_full():
            # 将语言选择映射到main.py期望的值
            language_code = "chs" if language == "中文" else "eng"
            
            # 启动新进程运行任务
            process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "openlens_ai.main",
                    "--question", question,
                    "--dataset-path", dataset_path,
                    "--thread-id", thread_id,
                    "--notify-email", email,
                    "--language", language_code,
                    "--interrupt-after-subgraph", "literature_reviewer"
                ]
            )

            # 将进程信息添加到进程管理器
            if not process_manager.add_process(process.pid, thread_id):
                process.terminate()  # 如果添加失败，终止进程
                st.error(t("failed_to_start_process", max=process_manager.MAX_PROCESSES))
                return

        with st.spinner(t("creating_job")):
            error_cnt = 0
            while True:
                try:
                    time.sleep(10)                   
                    dir_path = os.path.join("outputs", thread_id)
                    # TODO: remove config.json because it is not used anymore
                    if os.path.exists(os.path.join(dir_path, "config.json")):
                        with open(config_path, "r") as f:
                            config = json.load(f)
                    elif os.path.exists(os.path.join(dir_path, "config.toml")):
                        with open(os.path.join(dir_path, "config.toml"), "r") as f:
                            config = toml.load(f)
                    else:
                        raise FileNotFoundError("No config.json or config.toml found in experiment directory")
                    
                    config = Config(**config)
                    st.session_state.config = config
                    st.rerun()
                    break
                except Exception as e:
                    error_cnt += 1
                    if error_cnt > 5:
                        st.error(t("failed_to_start_process", max=process_manager.MAX_PROCESSES))
                        return
                    logger.error(f"Error loading config: {e}")
                    continue


def watch_job(config):
    thread_id = config.thread_id
    email = config.notify_email
    st.caption(t("thread_id", thread_id=thread_id))
    
    # 检查任务PID是否存在
    processes = process_manager.get_process_list()
    task_process = None
    for process in processes:
        if process.get('thread_id') == thread_id:
            task_process = process
            break
    
    # 如果任务PID不存在，显示警告信息
    if not task_process:
        st.warning(t("job_not_running", thread_id=thread_id))
        
        # 获取任务目录路径
        task_dir = os.path.join("outputs", thread_id)
        
        if not os.path.exists(task_dir):
            st.error(t("task_dir_not_found", dir=task_dir))
    else:
        st.warning(t("job_progress_notification", email=email))

    # 保存 config 到 session state
    st.session_state.config = config

    # 如果有旧的监控线程，停止它
    if st.session_state.monitor_thread:
        logger.info("Stopping old monitor thread")
        st.session_state.monitor_thread.stop()

    st.success(t("graph_built_successfully"))
    display_messages_from_file(config)


def main():
    # 设置页面配置
    # 初始化session state
    if "config" not in st.session_state:
        st.session_state.config = None
    if "monitor_thread" not in st.session_state:
        st.session_state.monitor_thread = None
    if "preview_file" not in st.session_state:
        st.session_state.preview_file = None
    if "question_input" not in st.session_state:
        st.session_state.question_input = ""
    if "dataset_selected" not in st.session_state:
        st.session_state.dataset_selected = "MIMIC-IV-ICU"
    # 初始化语言设置
    if "language" not in st.session_state:
        st.session_state.language = "chs"
    # 初始化语言选择
    if "language_selected" not in st.session_state:
        st.session_state.language_selected = "中文"
    st.markdown(
    """
    <style>
    /* Target all Streamlit buttons */
    div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important; /* Ensures content starts from the left */
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }                    
    .stAppHeader {
        background-color: rgba(255, 255, 255, 0.0);  /* Transparent background */
        visibility: visible;  /* Ensure the header is visible */
    }
    .main {overflow: hidden}
    </style>
    """,
        unsafe_allow_html=True,
    )
    
    
    # 如果有当前项目，显示项目界面
    if st.session_state.config:
        
        st.set_page_config(
            page_title="OpenLens AI",
            layout="wide",
            initial_sidebar_state="collapsed",
            page_icon="static/logo.png",
            menu_items={
                "About": "https://github.com/OpenLens-AI/OpenLens-AI",
            },
        )
        # 侧边栏设计
        build_sidebar()
        config = st.session_state.config
        
        with st.container(horizontal=True):
            
            # 检查任务PID是否存在并显示任务状态
            processes = process_manager.get_process_list()
            task_process = None
            for process in processes:
                if process.get('thread_id') == config.thread_id:
                    task_process = process
                    break
            
            chinese_char_cnt = len(re.findall(r"[\u4e00-\u9fa5]", config.question))
            chinese_ratio = chinese_char_cnt / len(config.question) if len(config.question) > 0 else 0
            question_truncate_len = 30 if chinese_ratio > 0.5 else 100
            question_show = config.question[:question_truncate_len] + ("..." if len(config.question) > question_truncate_len else "")
            
            if task_process:
                st.markdown(f"🙋 **{t('question_label')}** {t(question_show)} | 🟢 {t('task_running')}")
                
                # 如果任务正在运行，显示强制中断按钮
                if st.button(f"⏹️ {t('force_interrupt')}", key=f"interrupt_{config.thread_id}"):
                    try:
                        # 调用进程管理器的中断方法
                        if process_manager.interrupt_process(config.thread_id):
                            st.success(t("task_interrupted"))
                            st.rerun()
                        else:
                            st.error(t("failed_to_interrupt_task"))
                    except Exception as e:
                        logger.error(f"Failed to interrupt task: {e}")
                        st.error(t("failed_to_interrupt_task"))
            else:
                st.markdown(f"🙋 **{t('question_label')}** {t(question_show)} | 🔴 {t('task_stopped')}")
                
                # 如果任务未运行，显示继续任务按钮
                task_dir = os.path.join("outputs", config.thread_id)
                if os.path.exists(task_dir):
                    if st.button(f"▶️ {t('continue_task')}", key=f"continue_{config.thread_id}"):
                        # 调用resume-from接口
                        try:
                            # 启动新进程继续任务
                            process = subprocess.Popen(
                                [
                                    "python",
                                    "-m",
                                    "openlens_ai.main",
                                    "--resume-dir", task_dir,
                                ]
                            )
                            
                            # 将进程信息添加到进程管理器
                            if process_manager.add_process(process.pid, config.thread_id):
                                st.success(t("task_resumed", pid=process.pid))
                                st.rerun()
                            else:
                                process.terminate()  # 如果添加失败，终止进程
                                st.error(t("failed_to_resume_task"))
                        except Exception as e:
                            logger.error(f"Failed to resume task: {e}")
                            st.error(t("failed_to_resume_task"))
            
            st.button(f"🔄 {t('refresh')}", type="secondary", key="refresh_button")

        latest_files = get_latest_files(config)
        logger.debug(f"Latest files: {[f[0] for f in latest_files]}")
        if latest_files:
            latest_file_path, _, _ = latest_files[0]
            file_path = st.session_state.preview_file if st.session_state.preview_file else latest_file_path
            # 分割为左右两栏
            
            # st.divider()
            
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write(f"💬 **{t('conversation_history')}**")
                with st.container(height=900, border=False):
                    watch_job(config)
                    
            with col2:
                tab_names = [f"**{t('all_files')}**"]
                tab_names += [os.path.basename(fp) for fp, _, _ in latest_files]
                tab_list = st.tabs(tab_names, default=tab_names[1])
                for i, (latest_file_path, _, _) in enumerate(latest_files):
                    with tab_list[i+1]:
                        with st.container(height=900, border=False):
                            display_single_file(config, latest_file_path)
                with tab_list[0]:
                    with st.container(height=900, border=False):
                        show_workspace(config)

        else:
            watch_job(config)

    else:

        st.set_page_config(
            page_title="OpenLens AI",
            layout="wide",
            initial_sidebar_state="expanded",
            page_icon="static/logo.png",
            menu_items={
                "About": "https://github.com/OpenLens-AI/OpenLens-AI",
            },
        )
        # 侧边栏设计
        build_sidebar()

        # 主界面设计
        # st.title("🫧 OpenLens AI")
        st.subheader(f"🫧 {t('app_title')}")

        # 显示当前进程数量
        process_count = process_manager.get_process_count()
        st.caption(t("current_running_jobs", current=process_count, max=process_manager.MAX_PROCESSES))
        # if process_count >= process_manager.MAX_PROCESSES:
        #     st.warning(t("max_processes_reached"))

        # 主要输入框
        question = st.text_area(
            t("research_question"),
            value=st.session_state.question_input,
            height=150,
            placeholder=t("question_placeholder"),
            key="question_input_main",
        )

        # 如果用户输入了问题，隐藏Use Cases
        show_use_cases = not question.strip()

        # 数据集选择/上传功能区
        col1, col2 = st.columns([2, 1])
        
        with col1:
            dataset_option = st.selectbox(
                t("dataset_source"),
                ["MIMIC-IV-ICU", "eICU-Demo", "Upload My Own"],
                index=["MIMIC-IV-ICU", "eICU-Demo", "Upload My Own"].index(st.session_state.dataset_selected),
                key="dataset_select",
            )
            st.session_state.dataset_selected = dataset_option
        
        with col2:
            # 语言选择框
            language_option = st.selectbox(
                t("language"),
                ["中文", "English"],
                index=["中文", "English"].index(st.session_state.get("language_selected", "中文")),
                key="language_select",
            )
            st.session_state.language_selected = language_option

        dataset_path = ""

        # 处理数据集选择
        if dataset_option == "MIMIC-IV-ICU":
            dataset_path = "datasets/mimic-iv-icu"
            # st.text_input("Dataset Path", dataset_path, disabled=True)
        elif dataset_option == "eICU-Demo":
            dataset_path = "datasets/eicu-demo"
            # st.text_input("Dataset Path", dataset_path, disabled=True)
        elif dataset_option == "Upload My Own":
            # st.info("Please upload your dataset files below. They will be saved to ./datasets/user_upload/")
            uploaded_files = st.file_uploader(
                t("upload_dataset_files"), accept_multiple_files=True, type=["csv", "txt", "json", "parquet", "xls", "xlsx"], help=t("upload_dataset_help")
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
                st.success(t("files_uploaded_successfully", path=upload_subdir))
                st.text_input(t("dataset_path_label"), dataset_path, disabled=True)
            else:
                st.warning("Please upload at least one file for your dataset")
                dataset_path = None


        with st.container(horizontal=True):
            # submit_button = st.button(f"🚀 **{t('start_research')}**", help=t("start_research"), type="secondary")
            submit_button = st.button(f"🚀 {t('start_research_maintenance')}", type="secondary", disabled=True)

            st.caption(t("start_research_note"))

        
        # 处理提交
        if submit_button:
            if st.user.is_logged_in:
                start_job(question, dataset_path, st.session_state.email, st.session_state.language_selected)
            else:
                st.login()

        # Use Cases选项卡（仅在没有输入问题时显示）
        if show_use_cases:
            st.subheader(t("explore_use_cases"))

            # 加载保存的实验
            with st.spinner(t("loading_use_cases")):
                saved_experiments = load_saved_experiments()
                # saved_experiments = random.sample(saved_experiments, min(6, len(saved_experiments)))
                saved_experiments = saved_experiments[:12]

            # 创建三列用于卡片式展示（添加一列用于Resume Session）
            col1, col2 = st.columns(2)

            if saved_experiments:
                for i, exp in enumerate(saved_experiments):
                    # 从dir_name解析出dataset和更友好的标题

                    # 选择列（跳过第一列，因为已经被Resume Session占用）
                    if i % 2 == 0:
                        col = col1
                    else:
                        col = col2

                    with col:
                        # 创建卡片式按钮
                        # 样例的问题名称需要翻译，提供更好的用户体验
                        question = t(exp.get("question", "No question specified"))
                        dataset = t(exp.get("dataset", "Unknown dataset").split("/")[-1])
                        language = t(exp.get("language", "eng"))
                        if st.button(f"**{language}** | {question} | *{dataset}*", key=f"use_case_{i}", help=t("click_to_use_experiment"), width="stretch"):
                            config_path = os.path.join(exp["path"], "config.json")
                            with open(config_path, "r") as f:
                                config_data = json.load(f)

                            config = Config(**config_data)
                            config.save_path = exp["path"] # 确保保存路径与实验路径一致
                            st.session_state.config = config
                            logger.info(f"Loaded config for experiment: {exp.get('question', 'No question specified')}")
                            st.rerun()
    
    st.caption(t("note"))
