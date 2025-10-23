import os
import time
import json
from loguru import logger
import time
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from .config import Config

current_node = ""
last_message = None




tool_show_message = {
    "search_arxiv_tool": "Searching Arxiv for **{query}**",
    "read_arxiv_paper_tool": "Reading Arxiv Paper: **{paper_id}**",
    "search_medrxiv_tool": "Searching MedRxiv for **{query}**",
    "read_medrxiv_paper_tool": "Reading MedRxiv Paper: **{paper_id}**",
    "report_writer_tool": "Writing report to **{file_name}**",
    "openhands": "Writing/executing codes",
    "tavily_search": "Searching on the web for **{query}**",
}

def frontend_add_message(new_message: Union[ToolMessage, HumanMessage, AIMessage], config: Config):
    try:
        global current_node, last_message

        if new_message == last_message:
            last_message = new_message
            return

        last_message = new_message
        if isinstance(new_message.content, str) and new_message.content.strip():
            if isinstance(new_message, ToolMessage):
                role = "tool"
                title = ""
                content = tool_show_message.get(new_message.name, f"Calling {new_message.name}...")
                # 工具消息不保存
                return
            elif isinstance(new_message, HumanMessage):
                role = "user"
                title = "Agent"
                content = new_message.content
            elif isinstance(new_message, AIMessage):
                role = "assistant"
                title = config.llm.chat.model
                content = new_message.content
            else:
                role = "assistant"
                title = ""
                content = new_message.content

            # 保存消息数据而不是直接显示
            message_data = {"timestamp": datetime.now().isoformat(), "type": "message", "role": role, "title": title, "content": content}
            _save_message(config, message_data)
        else:
            logger.warning("Empty message content", new_message)
    except Exception as e:
        logger.warning(f"Error in frontend_add_message: {e}")


def frontend_add_tool_call(tool_name: str, tool_args: dict, config: Config):
    try:
        tool_message = tool_show_message.get(tool_name, "Calling {tool_name}...")
        tool_message = tool_message.format(tool_name=tool_name, **tool_args)

        # 保存工具调用数据
        message_data = {"timestamp": datetime.now().isoformat(), "type": "tool_call", "tool_name": tool_name, "content": tool_message}
        _save_message(config, message_data)
    except Exception as e:
        logger.warning(f"Error in frontend_add_tool_call: {e}")


def frontend_update_node(node_name: str, config: Config):
    try:
        global current_node
        current_node = node_name

        # 保存节点更新数据
        message_data = {"timestamp": datetime.now().isoformat(), "type": "node_update", "node_name": node_name, "content": f"Subgraph complete: {node_name}"}
        _save_message(config, message_data)
    except Exception as e:
        logger.warning(f"Error in frontend_update_node: {e}")



def frontend_add_file_msg(file_path, config: Optional[Config] = None, file_status="added"):
    try:
        filename = os.path.basename(file_path)

        # 如果提供了配置，则保存消息到缓存
        if config:
            message_data = {
                "timestamp": datetime.now().isoformat(),
                "type": f"file_content_{file_status}",
                "filename": filename,
                "content": file_path,
                "file_path": file_path,
            }
            _save_message(config, message_data)
    except Exception as e:
        logger.warning(f"Error in frontend_add_file_msg: {e}")



def _save_message(config: Config, message_data: dict):
    """保存消息到JSON文件，只保留最新的30条消息"""
        
    messages_file = _get_messages_file_path(config)
    message_file_all = messages_file.replace(".json", "_all.json")
    if not message_file_all:
        return

    # 读取现有消息
    messages = []
    if os.path.exists(message_file_all):
        try:
            with open(message_file_all, "r") as f:
                messages = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read messages file: {e}")
            messages = []

    # 添加新消息
    messages.append(message_data)

    # 去重
    messages = _message_remove_duplicates(messages)

    # 保存回文件
    try:
        with open(messages_file, "w") as f:
            # show_messages = messages[-30:] if len(messages) > 30 else messages
            show_messages = messages
            json.dump(show_messages, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save message to file: {e}")

    try:
        with open(message_file_all, "w") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save message to file: {e}")



def _get_messages_file_path(config: Config):
    """获取消息文件路径"""
    streamlit_dir = os.path.join(config.save_path, "streamlit")
    os.makedirs(streamlit_dir, exist_ok=True)
    return os.path.join(streamlit_dir, "messages.json")


def _message_remove_duplicates(messages: list):
    def to_string(msg):
        return msg["type"] + msg["content"]

    logger.debug(f"Removing duplicates from {len(messages)} messages")
    # 对整个list去除重复
    messages_no_dup = []
    for message in messages:
        if to_string(message) not in [to_string(m) for m in messages_no_dup]:
            messages_no_dup.append(message)
    logger.debug(f"Removed {len(messages) - len(messages_no_dup)} duplicates")
    messages = messages_no_dup
    return messages


