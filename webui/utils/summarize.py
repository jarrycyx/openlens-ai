import os
import streamlit as st
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
import time
from loguru import logger
import time
import hashlib
import streamlit as st
import json
import requests
import threading
import sqlite3
import numpy as np

from .translations import t, load_llm_config


# 内容概括缓存数据库路径
SUMMARY_CACHE_DB = os.path.join(os.path.dirname(__file__), "summary_cache.db")

# 最大并发线程数
MAX_CONCURRENT_SUMMARIES = 3

# 全局变量用于跟踪正在进行的概括任务
_ongoing_summaries = {}
_summary_lock = threading.Lock()
_summary_semaphore = threading.Semaphore(MAX_CONCURRENT_SUMMARIES)


def init_summary_db():
    """初始化概括缓存数据库"""
    try:
        conn = sqlite3.connect(SUMMARY_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                content_hash TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"初始化概括缓存数据库失败: {e}")


# 初始化数据库
init_summary_db()


def get_summary_from_db(cache_key: str) -> Optional[str]:
    """从数据库中获取概括"""
    try:
        conn = sqlite3.connect(SUMMARY_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM summaries WHERE content_hash = ?", (cache_key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.warning(f"从数据库获取概括失败: {e}")
        return None


def save_summary_to_db(cache_key: str, summary: str) -> None:
    """将概括保存到数据库"""
    for try_i in range(3):
        try:
            time.sleep(np.random.uniform(0, 0.3))
            conn = sqlite3.connect(SUMMARY_CACHE_DB, timeout=30)
            cursor = conn.cursor()
            cursor.execute('PRAGMA journal_mode = WAL')
            result = cursor.fetchone()
            # logger.info(f"WAL: {result[0]}")  # 应该输出 'wal'
            cursor.execute(
                """
                INSERT OR REPLACE INTO summaries (content_hash, summary, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (cache_key, summary),
            )
            conn.commit()
            conn.close()
            return
        except Exception as e:
            logger.warning(f"保存概括到数据库失败: {e}, 重试中{try_i}...")
            time.sleep(3)


def get_summary_cache_key(content: str, target_lang: str = "") -> str:
    """生成概括缓存键"""
    # return hashlib.md5(content.encode("utf-8")).hexdigest()
    # TODO: Too time consuming
    return target_lang + "|" + content[:100]


def summarize_with_llm_async(content: str, cache_key: str, max_len: int = 50, language: str = "中文") -> None:
    """使用LLM异步概括内容"""
    try:
        llm_config = load_llm_config()
        if not llm_config:
            logger.warning("未找到LLM配置")
            return

        model = llm_config.get("model", "")
        base_url = llm_config.get("base_url", "")
        api_key = llm_config.get("api_key", "")

        if not all([model, base_url, api_key]):
            logger.warning("LLM配置不完整")
            return

        if language.lower() == "chs" or language.lower() == "chinese":
            language = "中文"
        elif language.lower() == "eng" or language.lower() == "english":
            language = "英文"
        
        # 构建概括提示
        prompt = f"""请用不超过{max_len}个中文字/英文词的{language}概括以下处理进度的核心要点，只返回概括的进度内容，不需要解释或额外信息。
内容: {content[:300]}
/no_think"""

        # 调用LLM API
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 100,
        }

        response = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            summary = (
                summary.replace("\n", " ").replace("*", " ").replace("<think>", "").replace("</think>", "").strip()
            )

            # 确保概括不超过指定字数
            if len(summary) > max_len * 4:
                summary = summary[:max_len * 4] + "..." if len(summary) > max_len * 4 + 3 else summary[:max_len * 4]

            # 保存到数据库
            save_summary_to_db(cache_key, summary)

            logger.info(f"成功概括内容，长度: {len(summary)}字")
        else:
            logger.warning(f"LLM API请求失败: {response.status_code}, {response.text}")

    except Exception as e:
        logger.warning(f"使用LLM概括内容失败: {e}")
    finally:
        # 清理正在进行的概括任务记录
        with _summary_lock:
            if cache_key in _ongoing_summaries:
                del _ongoing_summaries[cache_key]


def summarize_content(content: str, max_len: int = 50, language: str = "中文") -> Optional[str]:
    """
    使用LLM概括内容（非阻塞版本）

    Args:
        content: 需要概括的内容
        max_len: 概括的最大长度

    Returns:
        Optional[str]: 如果缓存中有概括则返回，否则返回None表示正在处理
    """
    # # 确保数据库已初始化
    # init_summary_db()

    # 检查是否已在进行中
    cache_key = get_summary_cache_key(content, language)
    with _summary_lock:
        if cache_key in _ongoing_summaries:
            return t("Processing...")  # 已在进行中，不重新开始

        # 标记为进行中
        _ongoing_summaries[cache_key] = True

    # 检查数据库缓存
    cached_summary = get_summary_from_db(cache_key)
    if cached_summary and (not "None" in str(cached_summary)):
        with _summary_lock:
            if cache_key in _ongoing_summaries:
                del _ongoing_summaries[cache_key]
        return cached_summary

    # 启动异步概括，使用信号量控制并发数
    def run_with_semaphore():
        with _summary_semaphore:
            summarize_with_llm_async(content, cache_key, max_len, language)

    thread = threading.Thread(target=run_with_semaphore, daemon=True)
    thread.start()
    
    # with st.spinner(text=t("loading")):
    #     summarize_with_llm_async(content, cache_key, max_len, language)

    # return content[:(max_len * 4)]  # 立即返回None，表示概括正在进行中
    return t("Processing...")


def get_content_summary(content: str, max_length: int = 200, language: str = "中文") -> str:
    """
    获取内容概括，优先使用LLM概括，如果不可用则使用简单截断

    Args:
        content: 需要概括的内容
        max_length: 当LLM概括不可用时的最大显示长度

    Returns:
        str: 内容概括
    """
    if not content or not content.strip():
        return "无内容"

    if len(content) <= max_length * 4:
        return t(content)

    # 尝试使用LLM概括
    summary = summarize_content(content, max_len=max_length, language=language)
    return summary
