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


# Content summary cache database path
SUMMARY_CACHE_DB = os.path.join(os.path.dirname(__file__), "summary_cache.db")

# Maximum concurrent threads
MAX_CONCURRENT_SUMMARIES = 3

# Global variables for tracking ongoing summary tasks
_ongoing_summaries = {}
_summary_lock = threading.Lock()
_summary_semaphore = threading.Semaphore(MAX_CONCURRENT_SUMMARIES)


def init_summary_db():
    """Initialize summary cache database"""
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
        logger.warning(f"Failed to initialize summary cache database: {e}")


# Initialize database
init_summary_db()


def get_summary_from_db(cache_key: str) -> Optional[str]:
    """Get summary from database"""
    try:
        conn = sqlite3.connect(SUMMARY_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM summaries WHERE content_hash = ?", (cache_key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.warning(f"Failed to get summary from database: {e}")
        return None


def save_summary_to_db(cache_key: str, summary: str) -> None:
    """Save summary to database"""
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
            logger.warning(f"Failed to save summary to database: {e}, retrying {try_i}...")
            time.sleep(3)


def get_summary_cache_key(content: str, target_lang: str = "") -> str:
    """Generate summary cache key"""
    # return hashlib.md5(content.encode("utf-8")).hexdigest()
    # TODO: Too time consuming
    return target_lang + "|" + content[:100]


def summarize_with_llm_async(content: str, cache_key: str, max_len: int = 50, language: str = "Chinese") -> None:
    """Asynchronously summarize content using LLM"""
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

        if language.lower() == "chs" or language.lower() == "chinese":
            language = "Chinese"
        elif language.lower() == "eng" or language.lower() == "english":
            language = "English"
        
        # Build summary prompt
        prompt = f"""Please summarize the following processing progress in {language} in no more than {max_len} Chinese characters/English words. Only return the summarized progress content, no explanations or additional information needed.
Content: {content[:300]}
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

            # Ensure summary does not exceed specified length
            if len(summary) > max_len * 4:
                summary = summary[:max_len * 4] + "..." if len(summary) > max_len * 4 + 3 else summary[:max_len * 4]

            # Save to database
            save_summary_to_db(cache_key, summary)

            logger.info(f"Successfully summarized content, length: {len(summary)} characters")
        else:
            logger.warning(f"LLM API请求失败: {response.status_code}, {response.text}")

    except Exception as e:
        logger.warning(f"Failed to summarize content using LLM: {e}")
    finally:
        # Clean up ongoing summary task records
        with _summary_lock:
            if cache_key in _ongoing_summaries:
                del _ongoing_summaries[cache_key]


def summarize_content(content: str, max_len: int = 50, language: str = "Chinese") -> Optional[str]:
    """
    Summarize content using LLM (non-blocking version)

    Args:
        content: Content to be summarized
        max_len: Maximum length of the summary

    Returns:
        Optional[str]: Return summary if available in cache, otherwise return None indicating processing
    """
    # # Ensure database is initialized
    # init_summary_db()

    # Check if already in progress
    cache_key = get_summary_cache_key(content, language)
    with _summary_lock:
        if cache_key in _ongoing_summaries:
            return t("Processing...")  # 已在进行中，不重新开始

        # Mark as in progress
        _ongoing_summaries[cache_key] = True

    # Check database cache
    cached_summary = get_summary_from_db(cache_key)
    if cached_summary and (not "None" in str(cached_summary)):
        with _summary_lock:
            if cache_key in _ongoing_summaries:
                del _ongoing_summaries[cache_key]
        return cached_summary

    # Start asynchronous summary with semaphore control
    def run_with_semaphore():
        with _summary_semaphore:
            summarize_with_llm_async(content, cache_key, max_len, language)

    thread = threading.Thread(target=run_with_semaphore, daemon=True)
    thread.start()
    
    # with st.spinner(text=t("loading")):
    #     summarize_with_llm_async(content, cache_key, max_len, language)

    # return content[:(max_len * 4)]  # Immediately return None, indicating summary is in progress
    return t("Processing...")


def get_content_summary(content: str, max_length: int = 200, language: str = "Chinese") -> str:
    """
    Get content summary, prioritize LLM summary, use simple truncation if unavailable

    Args:
        content: Content to be summarized
        max_length: Maximum display length when LLM summary is unavailable

    Returns:
        str: Content summary
    """
    if not content or not content.strip():
        return "No content"

    if len(content) <= max_length * 4:
        return t(content)

    # Try to use LLM summary
    summary = summarize_content(content, max_len=max_length, language=language)
    return summary
