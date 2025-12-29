"""
Multilingual support module, providing lookup tables and switching functionality for Chinese and English interface text
Supports LLM automatic translation and caching mechanism
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
import toml
from loguru import logger
import requests
import threading
import time
import sqlite3
import streamlit as st
import numpy as np

# Language lookup table
TRANSLATIONS = {
    # English to Chinese mapping
    "eng": {
        # Login related
        "log_in": "Log in",
        "email": "Email",
        "logout": "Log out",
        "points": "Points",
        # Language options
        "chs": "Chinese",
        "eng": "English",
        # Project related
        "your_projects": "Your Projects",
        "new_project": "+ New project",
        "no_projects_yet": "No projects yet. Create your first project below.",
        "eicu-demo": "eICU Demo",
        "mimic-iv-icu": "MIMIC-IV ICU",
        # Process related
        "failed_to_start_process": "Failed to start the process. There are currently {n_processes} running processes in the system, of which {n_user_processes} belong to this user. The maximum allowed number of processes is {max_processes} system-wide and {max_user_processes} per user.",
        "creating_job": "Creating job...",
        "current_running_jobs": "Running jobs: {n_processes}/{max_processes}, user jobs: {n_user_processes}/{max_user_processes}",
        "failed_to_resume_task": "Failed to resume the task. The system is currently running {n_processes} processes in total, including {n_user_processes} processes owned by this user. The maximum allowed limits are {max_processes} processes system-wide and {max_user_processes} processes per user.",
        "Writing": "Writing",
        "Coding": "Coding",
        "Fixing the code": "Fixing the code",
        "Polishing the paper": "Polishing the paper",
        "Searching": "Searching",
        "loading": "Loading",
        # Task related
        "question_label": "Question:",
        "dataset_path_label": "Dataset Path:",
        "paper_language": "Paper language:",
        "language": "Language:",
        "thread_id": "Thread ID: {thread_id}",
        "job_progress_notification": "Job progress and results will be sent to {email}, please make sure the address is correct.",
        "graph_built_successfully": "Graph built successfully!",
        "job_not_running": "Task {thread_id} is not running.",
        "continue_task": "Continue Task",
        "task_resumed": "Task resumed successfully with PID: {pid}",
        "task_dir_not_found": "Task directory not found: {dir}",
        "start_research": "🚀 **Start Research**",
        "start_research_maintenance": "🚀 **Start Research (under maintenance)**",
        "task_running": "Task Running",
        "task_stopped": "Task Stopped",
        "force_interrupt": "Force Interrupt",
        "task_interrupted": "Task interrupted successfully",
        "failed_to_interrupt_task": "Failed to interrupt task. Please try again.",
        "confirm_submission": "Confirm Submission",
        "confirm_submission_warning": "⚠️ Sure to submit this research question? \nAfter the initial research, the process will **pause** to allow you to review and continue. \nAll research processes will take quite a long time (from several hours to a few days), and progress will be notified via email {email}.",
        "confirm": "Confirm",
        "missing_fields": "Please fill in question, dataset path and make sure the email address is correct.",
        "question_hint": "Enter a **complete scientific research question**, and ensure that the provided data are sufficient to support investigation of that question. \n\nFor example:\n\n- How can neural networks be used to predict acute kidney injury?\n\nNot recommended:\n\n- Please analyze the data I provided **(this is not a research question)**\n\n- Continue the research based on the previous results **(the question is incomplete)**",
        # UI elements
        "refresh": "Refresh",
        "conversation_history": "Conversation History",
        "all_files": "All files",
        "github_link": "🌟 Star us on GitHub",
        "pdf_viewer_tip": "⚠️ May take some time to load the PDF, download to view the full version.",
        "got_it": "Got it",
        "show_guide": "🙋 User Guide",
        # Application title and description
        "app_title": "OpenLens AI: A Fully Autonomous Multimodal Research Agent",
        "research_question": "Research Question",
        "dataset_source": "Dataset Source",
        "upload_dataset_files": "Upload Dataset Files",
        "upload_dataset_help": "Upload your dataset files",
        "files_uploaded_successfully": "Files uploaded successfully to: {path}",
        "explore_use_cases": "Explore use cases",
        "loading_use_cases": "Loading use cases...",
        "click_to_use_experiment": "Click to use this experiment",
        "max_processes_reached": "The server is busy. New task will added to the waiting queue.",
        # File related
        "content_truncated": "... (content truncated)",
        "download": "Download",
        "no_files_generated_yet": "No files generated yet.",
        "file_preview": "📄 {rel_path}",
        "error_reading_file": "Error reading file {rel_path}: {error}",
        "download_workspace": "Download Workspace",
        "download_paper": "Download Paper",
        "download_plan": "Download Plan",
        "click_download_workspace": "Click **📥 Download Workspace** button to download all files.",
        "file_list": "File List:",
        "file_list_item": "- {rel_path}",
        "no_files_in_workspace": "No files in workspace yet.",
        # Placeholder text
        "question_placeholder": "Input a complete scientific question or research target, make sure the provided data can support the research.",
        # Note
        "note": "Note: OpenLens AI is not responsible for any errors or omissions in the results. Please verify the results independently. The research results are for informational purposes only and should not be used as a substitute for direct submission.",
        "before_use_title": "🚀 OpenLens AI: Must-Read Guide",
        "before_use": """
Welcome to **OpenLens AI**! This is a fully autonomous multimodal research agent designed for **Medicine, Machine Learning (ML), Statistics**, and various **data-driven projects**, with special optimization for **AI + Medicine** scenarios.

### 🎯 What Can We Do?

> **Core Definition:** OpenLens AI can autonomously complete any **application-oriented research** that a human can perform on a computer **based on data and programming**.

* ✅ **Recommended Fields:** Medical Informatics, Clinical Data Analysis, Bioinformatics, Machine Learning Applications, Statistical Modeling, etc.
* 😐 **Not Recommended:** Theoretical Physics, Mathematical Derivations, etc. (While supported, performance may not meet expectations).



### 💡 How to Start High-Quality Research

**1. Prepare Data 📂**

Upload your dataset (supports `.csv`, `.xlsx`, etc.) or specify built-in medical databases (e.g., MIMIC-IV-ICU).
 
‼️ **Ensure the data is capable of supporting the research you intend to conduct.**

**2. Ask a Good Question (Crucial!) ❓**

Please input a **complete scientific question**.

* ✅ **Good Question:** "How can machine learning models be used to predict early mortality in sepsis patients based on MIMIC-IV data?"
* ❌ **Bad Question:** "Analyze this data for me" (Too vague), "Continue the previous research" (Missing context).



### ⚠️ Process & Important Notes

* **⏸️ Auto-Pause Mechanism:** After clicking "Start Research," the system will **automatically pause** after completing the initial survey to await your confirmation. Please note, **execution continues only after your confirmation**.
* **⏳ Time Estimation:** The process simulates human research—including literature review, coding, debugging, and writing—and typically takes **several hours to one or two days**.
* **📧 Notifications:** Since you don't need to monitor the screen, please ensure your **registered email** is correct. Progress updates and the final paper/code will be sent to you via email.



### 🛡️ Disclaimer

> Results generated by OpenLens AI are for reference only; we assume no responsibility for errors or omissions. Please **independently verify** code and conclusions. Do not use directly for clinical decisions or academic submission.



🌟 Find this useful? Star us on [GitHub](https://github.com/jarrycyx/openlens-ai)!
        """
    },
    "chs": {
        # Login related
        "log_in": "登录",
        "email": "邮箱",
        "logout": "登出",
        "points": "积分",
        # Language options
        "chs": "中文",
        "eng": "英文",
        # Project related
        "your_projects": "您的项目",
        "new_project": "➕ 新建项目",
        "no_projects_yet": "暂无项目。请在下方创建您的第一个项目。",
        "eicu-demo": "eICU Demo",
        "mimic-iv-icu": "MIMIC-IV ICU",
        # Process related
        "failed_to_start_process": "启动进程失败，当前系统中共有 {n_processes} 个正在运行的进程，最大 {max_processes} 个。其中该用户占用 {n_user_processes} 个，最大 {max_user_processes} 个。",
        "creating_job": "正在创建任务...",
        "current_running_jobs": "当前运行任务: {n_processes}/{max_processes}，当前用户任务: {n_user_processes}/{max_user_processes}",
        "failed_to_resume_task": "任务恢复失败，当前系统中共有 {n_processes} 个正在运行的进程，最大 {max_processes} 个。其中该用户占用 {n_user_processes} 个，最大 {max_user_processes} 个。",        
        "Writing": "正在写作",
        "Coding": "正在编程",
        "Fixing the code": "正在修改程序",
        "Polishing the paper": "正在润色论文",
        "Searching": "正在搜索",
        "loading": "处理中",
        # Task related
        "question_label": "问题:",
        "dataset_path_label": "数据集路径:",
        "paper_language": "论文语言:",
        "language": "语言:",
        "thread_id": "线程ID: {thread_id}",
        "job_progress_notification": "任务进度和结果将发送至 {email}，请确保地址正确。",
        "graph_built_successfully": "工作流构建成功!",
        "max_processes_reached": "服务器繁忙，新任务会进入等待队列。",
        "job_not_running": "任务 {thread_id} 未在运行。",
        "start_research": "🚀 **开始研究**",
        "start_research_maintenance": "🚀 **开始研究 (维护中)**",
        "continue_task": "继续任务",
        "task_resumed": "任务已成功恢复，PID: {pid}",
        "task_dir_not_found": "未找到任务目录: {dir}",
        "task_running": "任务运行中",
        "task_stopped": "任务已停止",
        "force_interrupt": "强制中断",
        "task_interrupted": "任务已成功中断",
        "failed_to_interrupt_task": "中断任务失败，请重试。",
        "confirm_submission": "确认提交",
        "confirm_submission_warning": "⚠️ 确认提交研究问题？\n\n完成基础调研后将**自动暂停**，等待您确认。\n\n全部研究过程会需要相当长的时间（从几小时到一两天），进度会通过邮件 {email} 通知您。",
        "confirm": "确认",
        "missing_fields": "请填写研究问题，数据集，并确保注册邮箱可用。",
        "question_hint": "输入一个**完整的科学问题或者目标**，并保证提供的数据能支持该问题的研究。\n\n例如：\n\n- 如何用神经网络预测急性肾损伤\n\n不建议输入：\n\n- 请分析我提供的数据 **（不是一个问题或者目标）**\n\n- 基于刚才的结果继续进行研究 **（不完整）**",
        # UI elements
        "refresh": "刷新",
        "conversation_history": "对话历史",
        "all_files": "所有文件",
        "github_link": "🌟 在GitHub上Star我们",
        "pdf_viewer_tip": "⚠️ 加载PDF可能会耗时较长，点击\"下载论文\"查看完整版本。",
        "got_it": "确认",
        "show_guide": "🙋 使用帮助",
        # Application title and description
        "app_title": "OpenLens AI: 全自主多模态科研智能体",
        "research_question": "研究问题",
        "dataset_source": "数据集来源",
        "upload_dataset_files": "上传数据集文件",
        "upload_dataset_help": "上传您的数据集文件",
        "files_uploaded_successfully": "文件已成功上传至: {path}",
        "explore_use_cases": "探索用例",
        "loading_use_cases": "正在加载用例...",
        "click_to_use_experiment": "点击使用此实验",
        # File related
        "content_truncated": "... (内容已截断)",
        "download": "下载",
        "no_files_generated_yet": "尚未生成文件。",
        "file_preview": "📄 {rel_path}",
        "error_reading_file": "读取文件 {rel_path} 时出错: {error}",
        "download_workspace": "下载工作区",
        "download_paper": "下载论文",
        "download_plan": "下载计划",
        "click_download_workspace": "点击 **📥 下载工作区** 按钮下载所有文件。",
        "file_list": "文件列表:",
        "file_list_item": "- {rel_path}",
        "no_files_in_workspace": "工作区中尚无文件。",
        # Placeholder text
        "question_placeholder": "输入一个完整的科学问题或者目标，并保证提供的数据能支持该问题的研究。",
        # Note
        "note": "注意：OpenLens AI 不承担任何因使用其结果而导致的错误或遗漏。请独立验证结果。研究结果仅供参考，不应直接用于学术投稿。",
        "before_use_title": "🚀 OpenLens AI 用前必读",
        "before_use": """
欢迎使用 **OpenLens AI**！这是一个专为 **医学、机器学习 (ML)、统计学** 及各类 **数据驱动项目** 设计的全自主多模态科研智能体，并针对 **AI + 医学** 场景进行了特别优化。

### 🎯 我们能做什么？

> **核心定义：** 只要是人类可以**基于数据和编程**在电脑上完成的**偏向应用型研究**，OpenLens AI 都可以自主完成。

* ✅ **推荐领域：** 医疗信息学、临床医学数据分析、生物信息学、机器学习应用、统计建模等。
* 😐 **非推荐领域：** 理论物理、数学推导等（虽然支持尝试，但效果可能不如预期）。



### 💡 如何开始高质量研究

**1. 准备数据 📂**

上传您的数据集（支持 `.csv`, `.xlsx` 等），或指定系统内置的医学数据库（如 MIMIC-IV-ICU）。

‼️**确保数据能够支持您需要进行的研究。**

**2. 提出好问题 (关键！) ❓**

请输入一个**完整的科学问题**。

* ✅ **好问题：** “如何利用机器学习模型基于 MIMIC-IV 数据预测脓毒症患者的早期死亡率？”
* ❌ **坏问题：** “帮我分析一下数据”（太模糊）、“继续刚才的研究”（信息缺失）。



### ⚠️ 流程与注意事项

* **⏸️ 自动暂停机制：** 点击“开始研究”后，系统在完成基础调研后会**自动暂停**，等待您确认。请留意，**确认后才会继续执行**。
* **⏳ 耗时预警：** 全流程模拟人类科研，包含查阅文献、写代码、调试和写作，通常需要 **数小时至一两天**。
* **📧 结果通知：** 既然不需要您盯着屏幕，请确保**注册邮箱**正确，进度和最终的论文/代码将通过邮件通知您。



### 🛡️ 免责声明

> OpenLens AI 生成的结果仅供参考，不承担因错误或遗漏导致的责任。请务必**独立验证**代码与结论，切勿直接用于临床决策或直接投稿。



🌟 觉得好用？ 欢迎在 [GitHub](https://github.com/jarrycyx/openlens-ai) 上 Star 我们！
        """
    },
}

# Translation cache database path
TRANSLATION_CACHE_DB = os.path.join(os.path.dirname(__file__), "trans_cache.db")

# Maximum concurrent threads
MAX_CONCURRENT_TRANSLATIONS = 3


def init_translation_db():
    """Initialize translation cache database"""
    try:
        conn = sqlite3.connect(TRANSLATION_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(text_hash, target_lang)
            )
        """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to initialize translation cache database: {e}")


def get_translation_from_db(text_hash: str, target_lang: str) -> Optional[str]:
    """Get translation from database"""
    try:
        conn = sqlite3.connect(TRANSLATION_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT translated_text FROM translations WHERE text_hash = ? AND target_lang = ?", (text_hash, target_lang)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.warning(f"Failed to get translation from database: {e}")
        return None


def save_translation_to_db(text_hash: str, target_lang: str, translated_text: str) -> None:
    """Save translation to database"""
    for try_i in range(3):
        try:
            time.sleep(np.random.uniform(0, 0.3))
            conn = sqlite3.connect(TRANSLATION_CACHE_DB, timeout=30)
            cursor = conn.cursor()
            cursor.execute('PRAGMA journal_mode = WAL')
            result = cursor.fetchone()
            # logger.info(f"WAL: {result[0]}")  # 应该输出 'wal'
            cursor.execute(
                """
                INSERT OR REPLACE INTO translations (text_hash, target_lang, translated_text, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (text_hash, target_lang, translated_text),
            )
            conn.commit()
            conn.close()
            return
        except Exception as e:
            logger.warning(f"Failed to save translation to database: {e}, retrying {try_i}...")
            time.sleep(3)


# Initialize database
init_translation_db()


def get_cache_key(text: str, target_lang: str = "") -> str:
    """Generate cache key - use text hash for database storage"""
    # return hashlib.md5(f"{text}_{target_lang}".encode("utf-8")).hexdigest()
    # TODO: Too time consuming
    return target_lang + "|" + text[:100]


def load_llm_config() -> Dict[str, Any]:
    """Load LLM configuration from translation_llm.json"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "translation_llm.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
    except Exception as e:
        logger.warning(f"Failed to load LLM config: {e}")
    return {}


# Global variables for tracking ongoing translation tasks
_ongoing_translations = {}
_translation_lock = threading.Lock()
_translation_semaphore = threading.Semaphore(MAX_CONCURRENT_TRANSLATIONS)


def translate_with_llm_async(text: str, target_lang: str, cache_key: str) -> None:
    """Asynchronously translate using LLM"""
    try:
        llm_config = load_llm_config()
        if not llm_config:
            logger.warning("No LLM configuration found")
            return

        model = llm_config.get("model", "")
        base_url = llm_config.get("base_url", "")
        api_key = llm_config.get("api_key", "")

        if not all([model, base_url, api_key]):
            logger.warning("Incomplete LLM configuration")
            return

        # Build translation prompt
        lang_map = {"chs": "Chinese", "eng": "English"}
        target_language = lang_map.get(target_lang, target_lang)

        prompt = f"""Please translate the following text to {target_language}.
Only return the translated text, no explanations or additional content.
Note: the word "polish" means improve the words (“润色”).

Text to translate: {text[:1000]}

Translation:/no_think"""

        # Call LLM API
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500,
        }

        response = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()
            translated_text = (
                translated_text.replace("\n", " ")
                .replace("*", "")
                .replace("<think>", "")
                .replace("</think>", "")
                .strip()
            )

            # Save to database
            save_translation_to_db(cache_key, target_lang, translated_text)

            # Save to in-memory translation table
            if target_lang in TRANSLATIONS:
                # Find the corresponding key
                for key, value in TRANSLATIONS["eng"].items():
                    if value == text:
                        TRANSLATIONS[target_lang][key] = translated_text
                        break

            logger.info(f"Successfully translated '{text}' to {target_lang}")
        else:
            logger.warning(f"LLM API request failed: {response.status_code}, {response.text}")

    except Exception as e:
        logger.warning(f"Translation with LLM failed: {e}")
    finally:
        # Clean up ongoing translation task records
        with _translation_lock:
            translation_id = f"{text}_{target_lang}"
            if translation_id in _ongoing_translations:
                del _ongoing_translations[translation_id]


def translate_with_llm(text: str, target_lang: str) -> Optional[str]:
    """Translate using LLM (non-blocking version)"""
    # Check if already in progress
    translation_id = f"{text}_{target_lang}"
    with _translation_lock:
        if translation_id in _ongoing_translations:
            return None  # Already in progress, don't start again

        # Mark as in progress
        _ongoing_translations[translation_id] = True

    # Start asynchronous translation with semaphore control
    cache_key = get_cache_key(text, target_lang)

    def run_with_semaphore():
        with _translation_semaphore:
            translate_with_llm_async(text, target_lang, cache_key)

    thread = threading.Thread(target=run_with_semaphore, daemon=True)
    thread.start()
    
    # with st.spinner(text=t("loading")):
    #     translate_with_llm_async(text, target_lang, cache_key)

    return text  # Immediately return None, indicating translation is in progress


def get_text(key: str, lang: str = "eng", **kwargs) -> str:
    """
    Get text in the specified language

    Args:
        key: Text key name
        lang: Language code ("eng" or "chs")
        **kwargs: Formatting parameters

    Returns:
        Formatted text
    """
    if lang not in TRANSLATIONS:
        lang = "eng"

    # If found in predefined translations
    if key in TRANSLATIONS[lang]:
        text = TRANSLATIONS[lang][key]

        # If formatting parameters are provided, format the text
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                # Return original text if formatting fails
                return text
        return text

    # If found in English version but not in target language, try automatic translation
    if key in TRANSLATIONS["eng"]:
        english_text = TRANSLATIONS["eng"][key]

        # If target language is English, return directly
        if lang == "eng":
            return english_text

        # Check database cache
        cache_key = get_cache_key(english_text, lang)

        # Check if translation exists in database
        translated_text = get_translation_from_db(cache_key, lang)
        if translated_text:
            # Save to in-memory translation table
            TRANSLATIONS[lang][key] = translated_text
            # logger.info(f"Used cached translation for '{key}' in {lang}")

            # If formatting parameters are provided, format the text
            if kwargs:
                try:
                    return translated_text.format(**kwargs)
                except (KeyError, ValueError):
                    return translated_text
            return translated_text

        # Use LLM for translation (non-blocking)
        logger.info(f"Starting translation for '{key}' using LLM...")
        translated_text = translate_with_llm(english_text, lang)

        # Immediately return English version, translation happens in background
        logger.info(f"Translation started for '{key}', returning English version for now")

        # If formatting parameters are provided, format the text
        if kwargs:
            try:
                return english_text.format(**kwargs)
            except (KeyError, ValueError):
                return english_text
        return english_text

    # If key name itself is not in any translation table, try translating the key name directly
    if lang != "eng":
        # Check database cache
        cache_key = get_cache_key(key, lang)

        # Check if translation exists in database
        translated_text = get_translation_from_db(cache_key, lang)
        if translated_text:
            # logger.info(f"Used cached translation for key '{key}' in {lang}")

            # If formatting parameters are provided, format the text
            if kwargs:
                try:
                    return translated_text.format(**kwargs)
                except (KeyError, ValueError):
                    return translated_text
            return translated_text

        # Use LLM for translation (non-blocking)
        logger.info(f"Starting translation for key '{key}' using LLM...")
        translated_text = translate_with_llm(key, lang)

        # Immediately return original key name, translation happens in background
        logger.info(f"Translation started for key '{key}', returning original for now")
        return key

    # Default to return the key name itself
    return key


def set_language(lang: str) -> None:
    """
    Set current language (can be saved to session state)

    Args:
        lang: Language code ("eng" or "chs")
    """

    if "ui_language" not in st.session_state:
        st.session_state.ui_language = "chs"

    if lang in ["eng", "chs"]:
        # logger.info(f"Set language to {lang}")
        st.session_state.ui_language = lang


def get_current_language() -> str:
    """
    Get current language

    Returns:
        Current language code
    """
    current_lang = st.session_state.get("ui_language", "chs")
    # logger.info(f"Get current language: {current_lang}")

    return current_lang


def t(key: str, **kwargs) -> str:
    """
    Convenience function: get text in current language

    Args:
        key: Text key name
        **kwargs: Formatting parameters

    Returns:
        Formatted text
    """
    return get_text(key, get_current_language(), **kwargs)
