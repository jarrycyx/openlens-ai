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

# Language lookup table
TRANSLATIONS = {
    # English to Chinese mapping
    "eng": {
        # Login related
        "log_in": "Log in",
        "email": "Email",
        "logout": "Log out",
        'points': "Points",
        
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
        
        # Task related
        "question_label": "Question:",
        "dataset_path_label": "Dataset Path:",
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
        
        # UI elements
        "refresh": "Refresh",
        "conversation_history": "Conversation History",
        "all_files": "All files",
        "github_link": "🌟 Star us on GitHub",
        
        # Application title and description
        "app_title": "OpenLens AI: Fully Autonomous Multimodal Agent for Health Informatics Research",
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
        "question_placeholder": "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
        
        # Note
        "note": "Note: OpenLens AI is not responsible for any errors or omissions in the results. Please verify the results independently. The research results are for informational purposes only and should not be used as a substitute for direct submission.",
    },
    
    "chs": {
        # Login related
        "log_in": "登录",
        "email": "邮箱",
        "logout": "登出",
        'points': "积分",
        
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
        
        # Task related
        "question_label": "问题:",
        "dataset_path_label": "数据集路径:",
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
        "confirm_submission_warning": "⚠️ 确认提交研究问题？\n完成基础调研后将**自动暂停**，等待您确认。\n全部研究过程会需要相当长的时间（从几小时到一两天），进度会通过邮件 {email} 通知您。",
        "confirm": "确认",
        "missing_fields": "请填写研究问题，数据集，并确保注册邮箱可用。",
        
        # UI elements
        "refresh": "刷新",
        "conversation_history": "对话历史",
        "all_files": "所有文件",
        "github_link": "🌟 在GitHub上Star我们",
        
        # Application title and description
        "app_title": "OpenLens AI: 全自主多模态医学科研智能体",
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
        "question_placeholder": "在ICU患者中，基于过去两天的历史数据动态预测每一天，AKI的预测精度是多少？",
        
        # Note
        "note": "注意：OpenLens AI 不承担任何因使用其结果而导致的错误或遗漏。请独立验证结果。研究结果仅供参考，不应直接用于学术投稿。",
    }
}

# Translation cache file path
TRANSLATION_CACHE_FILE = os.path.join(os.path.dirname(__file__), "trans_cache.json")

def load_translation_cache() -> Dict[str, Any]:
    """Load translation cache"""
    try:
        if os.path.exists(TRANSLATION_CACHE_FILE):
            with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load translation cache: {e}")
    return {}

def save_translation_cache(cache: Dict[str, Any]) -> None:
    """Save translation cache"""
    try:
        with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save translation cache: {e}")

def get_cache_key(text: str, target_lang: str) -> str:
    """Generate cache key - use original text as key directly, more intuitive and easier to debug"""
    return text

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
        lang_map = {"chs": "中文", "eng": "English"}
        target_language = lang_map.get(target_lang, target_lang)
        
        prompt = f"""Please translate the following text to {target_language}.
Only return the translated text, no explanations or additional content.

Text to translate: {text}

Translation:"""
        
        # Call LLM API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()
            
            # Save to cache
            cache = load_translation_cache()
            if target_lang not in cache:
                cache[target_lang] = {}
            cache[target_lang][cache_key] = translated_text
            save_translation_cache(cache)
            
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
    
    # Start asynchronous translation
    cache_key = get_cache_key(text, target_lang)
    thread = threading.Thread(
        target=translate_with_llm_async,
        args=(text, target_lang, cache_key),
        daemon=True
    )
    thread.start()
    
    return None  # Immediately return None, indicating translation is in progress

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
        
        # Load cache
        cache = load_translation_cache()
        
        # Ensure cache has entries for target language
        if lang not in cache:
            cache[lang] = {}
        
        cache_key = get_cache_key(english_text, lang)
        
        # Check if translation exists in cache
        if cache_key in cache[lang]:
            translated_text = cache[lang][cache_key]
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
        
        # 如果提供了格式化参数，进行格式化
        if kwargs:
            try:
                return english_text.format(**kwargs)
            except (KeyError, ValueError):
                return english_text
        return english_text
    
    # If key name itself is not in any translation table, try translating the key name directly
    if lang != "eng":
        # Load cache
        cache = load_translation_cache()
        
        # Ensure cache has entries for target language
        if lang not in cache:
            cache[lang] = {}
        
        cache_key = get_cache_key(key, lang)
        
        # Check if translation exists in cache
        if cache_key in cache[lang]:
            translated_text = cache[lang][cache_key]
            # logger.info(f"Used cached translation for key '{key}' in {lang}")
            
            # 如果提供了格式化参数，进行格式化
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
    import streamlit as st
    if "language" not in st.session_state:
        st.session_state.language = "chs"
    
    if lang in ["eng", "chs"]:
        st.session_state.language = lang

def get_current_language() -> str:
    """
    Get current language
    
    Returns:
        Current language code
    """
    import streamlit as st
    return st.session_state.get("language", "eng")

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