"""
多语言支持模块，提供中英文界面文本的查找表和切换功能
支持LLM自动翻译和缓存机制
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

# 语言查找表
TRANSLATIONS = {
    # 英文到中文的映射
    "en": {
        # 登录相关
        "log_in": "Log in",
        "email": "Email",
        "logout": "Log out",
        
        # 语言选项
        "chs": "Chinese",
        "eng": "English",
        
        # 项目相关
        "your_projects": "Your Projects",
        "new_project": "+ New project",
        "no_projects_yet": "No projects yet. Create your first project below.",
        "eicu-demo": "eICU Demo",
        "mimic-iv-icu": "MIMIC-IV ICU",
        
        # 进程相关
        "max_processes_reached": "Maximum number of processes ({max}) reached. Please wait for some processes to finish.",
        "failed_to_start_process": "Failed to start process, Maximum number of processes ({max}) reached. Can submit an issue on GitHub for help.",
        "creating_job": "Creating job...",
        "current_running_jobs": "Current Running Jobs: {current}/{max}",
        
        # 任务相关
        "question_label": "Question:",
        "dataset_path_label": "Dataset Path:",
        "thread_id": "Thread ID: {thread_id}",
        "job_progress_notification": "Job progress and results will be sent to {email}, please make sure the address is correct.",
        "graph_built_successfully": "Graph built successfully!",
        "job_not_running": "Task {thread_id} is not running.",
        "continue_task": "Continue Task",
        "task_resumed": "Task resumed successfully with PID: {pid}",
        "failed_to_resume_task": "Failed to resume task. Please try again.",
        "task_dir_not_found": "Task directory not found: {dir}",
        "task_running": "Task Running",
        "task_stopped": "Task Stopped",
        
        # 界面元素
        "refresh": "Refresh",
        "conversation_history": "Conversation History",
        "all_files": "All files",
        "github_link": "🌟 Star us on GitHub",
        
        # 应用标题和描述
        "app_title": "OpenLens AI: Fully Autonomous Research Agent for Health Informatics",
        "research_question": "Research Question",
        "dataset_source": "Dataset Source",
        "upload_dataset_files": "Upload Dataset Files",
        "upload_dataset_help": "Upload your dataset files",
        "files_uploaded_successfully": "Files uploaded successfully to: {path}",
        "start_research": "Start Research",
        "start_research_maintenance": "Start Research (under maintenance)", 
        "start_research_note": "Note: This will start a fully autonomous research process that may take significant time to complete.",
        "explore_use_cases": "Explore use cases",
        "loading_use_cases": "Loading use cases...",
        "click_to_use_experiment": "Click to use this experiment",
        "max_processes_reached": "The server is busy. New task will added to the waiting queue.",
        
        # 文件相关
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
        
        # 占位符文本
        "question_placeholder": "What is the prediction precision of AKI in ICU patients when dynamically predicting each day based on the past two days of historical data?",
    },
    
    "zh": {
        # 登录相关
        "log_in": "登录",
        "email": "邮箱",
        "logout": "登出",
        
        # 语言选项
        "chs": "中文",
        "eng": "英文",
        
        # 项目相关
        "your_projects": "您的项目",
        "new_project": "+ 新建项目",
        "no_projects_yet": "暂无项目。请在下方创建您的第一个项目。",
        "eicu-demo": "eICU Demo",
        "mimic-iv-icu": "MIMIC-IV ICU",
        
        # 进程相关
        "max_processes_reached": "已达到最大进程数 ({max})。请等待一些进程完成。",
        "failed_to_start_process": "启动进程失败，已达到最大进程数 ({max})，可在GitHub上提交issue反馈。",
        "creating_job": "正在创建任务...",
        "current_running_jobs": "当前运行任务: {current}/{max}",
        
        # 任务相关
        "question_label": "问题:",
        "dataset_path_label": "数据集路径:",
        "thread_id": "线程ID: {thread_id}",
        "job_progress_notification": "任务进度和结果将发送至 {email}，请确保地址正确。",
        "graph_built_successfully": "工作流构建成功!",
        "max_processes_reached": "服务器繁忙，新任务会进入等待队列。",
        "job_not_running": "任务 {thread_id} 未在运行。",
        "continue_task": "继续任务",
        "task_resumed": "任务已成功恢复，PID: {pid}",
        "failed_to_resume_task": "恢复任务失败，请重试。",
        "task_dir_not_found": "未找到任务目录: {dir}",
        "task_running": "任务运行中",
        "task_stopped": "任务已停止",
        
        # 界面元素
        "refresh": "刷新",
        "conversation_history": "对话历史",
        "all_files": "所有文件",
        "github_link": "🌟 在GitHub上Star我们",
        
        # 应用标题和描述
        "app_title": "OpenLens AI: 全自主医学科研智能体",
        "research_question": "研究问题",
        "dataset_source": "数据集来源",
        "upload_dataset_files": "上传数据集文件",
        "upload_dataset_help": "上传您的数据集文件",
        "files_uploaded_successfully": "文件已成功上传至: {path}",
        "start_research": "开始研究",
        "start_research_maintenance": "开始研究 (维护中)",
        "start_research_note": "注意：这将启动一个完全自主的研究过程，可能需要较长时间完成。",
        "explore_use_cases": "探索用例",
        "loading_use_cases": "正在加载用例...",
        "click_to_use_experiment": "点击使用此实验",
        
        # 文件相关
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
        
        # 占位符文本
        "question_placeholder": "在ICU患者中，基于过去两天的历史数据动态预测每一天，AKI的预测精度是多少？",
    }
}

# 翻译缓存文件路径
TRANSLATION_CACHE_FILE = os.path.join(os.path.dirname(__file__), "trans_cache.json")

def load_translation_cache() -> Dict[str, Any]:
    """加载翻译缓存"""
    try:
        if os.path.exists(TRANSLATION_CACHE_FILE):
            with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load translation cache: {e}")
    return {}

def save_translation_cache(cache: Dict[str, Any]) -> None:
    """保存翻译缓存"""
    try:
        with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save translation cache: {e}")

def get_cache_key(text: str, target_lang: str) -> str:
    """生成缓存键 - 直接使用原文作为键，更直观且便于调试"""
    return text

def load_llm_config() -> Dict[str, Any]:
    """从translation_llm.json加载LLM配置"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "translation_llm.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
    except Exception as e:
        logger.warning(f"Failed to load LLM config: {e}")
    return {}

# 全局变量，用于跟踪正在进行的翻译任务
_ongoing_translations = {}
_translation_lock = threading.Lock()

def translate_with_llm_async(text: str, target_lang: str, cache_key: str) -> None:
    """异步使用LLM进行翻译"""
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
        
        # 构建翻译提示
        lang_map = {"zh": "中文", "en": "English"}
        target_language = lang_map.get(target_lang, target_lang)
        
        prompt = f"""Please translate the following text to {target_language}.
Only return the translated text, no explanations or additional content.

Text to translate: {text}

Translation:"""
        
        # 调用LLM API
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
            
            # 保存到缓存
            cache = load_translation_cache()
            if target_lang not in cache:
                cache[target_lang] = {}
            cache[target_lang][cache_key] = translated_text
            save_translation_cache(cache)
            
            # 保存到内存中的翻译表
            if target_lang in TRANSLATIONS:
                # 查找对应的键
                for key, value in TRANSLATIONS["en"].items():
                    if value == text:
                        TRANSLATIONS[target_lang][key] = translated_text
                        break
            
            logger.info(f"Successfully translated '{text}' to {target_lang}")
        else:
            logger.warning(f"LLM API request failed: {response.status_code}, {response.text}")
            
    except Exception as e:
        logger.warning(f"Translation with LLM failed: {e}")
    finally:
        # 清理正在进行的翻译任务记录
        with _translation_lock:
            translation_id = f"{text}_{target_lang}"
            if translation_id in _ongoing_translations:
                del _ongoing_translations[translation_id]

def translate_with_llm(text: str, target_lang: str) -> Optional[str]:
    """使用LLM进行翻译（非阻塞版本）"""
    # 检查是否已经在进行中
    translation_id = f"{text}_{target_lang}"
    with _translation_lock:
        if translation_id in _ongoing_translations:
            return None  # 已在进行中，不重复启动
        
        # 标记为正在进行
        _ongoing_translations[translation_id] = True
    
    # 启动异步翻译
    cache_key = get_cache_key(text, target_lang)
    thread = threading.Thread(
        target=translate_with_llm_async,
        args=(text, target_lang, cache_key),
        daemon=True
    )
    thread.start()
    
    return None  # 立即返回None，表示翻译正在进行中

def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """
    获取指定语言的文本
    
    Args:
        key: 文本键名
        lang: 语言代码 ("en" 或 "zh")
        **kwargs: 格式化参数
    
    Returns:
        格式化后的文本
    """
    if lang not in TRANSLATIONS:
        lang = "en"
    
    # 如果在预定义翻译中找到
    if key in TRANSLATIONS[lang]:
        text = TRANSLATIONS[lang][key]
        
        # 如果提供了格式化参数，进行格式化
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                # 格式化失败时返回原始文本
                return text
        return text
    
    # 如果在英文版本中找到，但目标语言中没有，尝试自动翻译
    if key in TRANSLATIONS["en"]:
        english_text = TRANSLATIONS["en"][key]
        
        # 如果目标语言是英文，直接返回
        if lang == "en":
            return english_text
        
        # 加载缓存
        cache = load_translation_cache()
        
        # 确保缓存中有目标语言的条目
        if lang not in cache:
            cache[lang] = {}
        
        cache_key = get_cache_key(english_text, lang)
        
        # 检查缓存中是否有翻译
        if cache_key in cache[lang]:
            translated_text = cache[lang][cache_key]
            # 保存到内存中的翻译表
            TRANSLATIONS[lang][key] = translated_text
            # logger.info(f"Used cached translation for '{key}' in {lang}")
            
            # 如果提供了格式化参数，进行格式化
            if kwargs:
                try:
                    return translated_text.format(**kwargs)
                except (KeyError, ValueError):
                    return translated_text
            return translated_text
        
        # 使用LLM进行翻译（非阻塞）
        logger.info(f"Starting translation for '{key}' using LLM...")
        translated_text = translate_with_llm(english_text, lang)
        
        # 立即返回英文版本，翻译在后台进行
        logger.info(f"Translation started for '{key}', returning English version for now")
        
        # 如果提供了格式化参数，进行格式化
        if kwargs:
            try:
                return english_text.format(**kwargs)
            except (KeyError, ValueError):
                return english_text
        return english_text
    
    # 如果键名本身不在任何翻译表中，尝试直接翻译键名
    if lang != "en":
        # 加载缓存
        cache = load_translation_cache()
        
        # 确保缓存中有目标语言的条目
        if lang not in cache:
            cache[lang] = {}
        
        cache_key = get_cache_key(key, lang)
        
        # 检查缓存中是否有翻译
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
        
        # 使用LLM进行翻译（非阻塞）
        logger.info(f"Starting translation for key '{key}' using LLM...")
        translated_text = translate_with_llm(key, lang)
        
        # 立即返回原始键名，翻译在后台进行
        logger.info(f"Translation started for key '{key}', returning original for now")
        return key
    
    # 默认返回键名本身
    return key

def set_language(lang: str) -> None:
    """
    设置当前语言（可以保存到session state中）
    
    Args:
        lang: 语言代码 ("en" 或 "zh")
    """
    import streamlit as st
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if lang in ["en", "zh"]:
        st.session_state.language = lang

def get_current_language() -> str:
    """
    获取当前语言
    
    Returns:
        当前语言代码
    """
    import streamlit as st
    return st.session_state.get("language", "en")

def t(key: str, **kwargs) -> str:
    """
    便捷函数：获取当前语言的文本
    
    Args:
        key: 文本键名
        **kwargs: 格式化参数
    
    Returns:
        格式化后的文本
    """
    return get_text(key, get_current_language(), **kwargs)