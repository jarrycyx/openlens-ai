import os
import streamlit as st
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
import time
from loguru import logger
import time
from threading import Thread
import hashlib
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx, add_script_run_ctx
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
import streamlit_scrollable_textbox as stx
import glob
import json
import traceback
from .config import Config


tool_show_message = {
    "search_arxiv_tool": "Searching Arxiv for **\"{query}\"**",
    "read_arxiv_paper_tool": "Reading Arxiv Paper: **{paper_id}**",
    "search_medrxiv_tool": "Searching MedRxiv for **\"{query}\"**",
    "read_medrxiv_paper_tool": "Reading MedRxiv Paper: **{paper_id}**",
    "report_writer_tool": "Writing report to **\"{file_name}\"**",
    "openhands": "Writing/executing codes",
    "tavily_search": "Searching on the web for **\"{query}\"**"
}

is_in_streamlit = os.environ.get("STREAMLIT_RUNNING", "False")
logger.info(f"is_in_streamlit: {is_in_streamlit}")
current_node = ""
last_message = None

def _get_messages_file_path(config: Config):
    """获取消息文件路径"""
    streamlit_dir = os.path.join(config.save_path, "streamlit")
    os.makedirs(streamlit_dir, exist_ok=True)
    return os.path.join(streamlit_dir, "messages.json")

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
            with open(message_file_all, 'r') as f:
                messages = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read messages file: {e}")
            messages = []
    
    # 添加新消息
    messages.append(message_data)
    
    # 保存回文件
    try:
        with open(messages_file, 'w') as f:
            show_messages = messages[-30:] if len(messages) > 30 else messages
            json.dump(show_messages, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save message to file: {e}")
        
    try:
        with open(message_file_all, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save message to file: {e}")

def frontend_add_message(new_message: Union[ToolMessage, HumanMessage, AIMessage], config: Config):
    if not config:
        return
    
    global current_node, last_message
    
    if new_message == last_message:
        last_message = new_message
        return
    
    last_message = new_message
    if new_message.content.strip():
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
            title = os.environ.get("MODEL", "")
            content = new_message.content
        else:
            role = "assistant"
            title = ""
            content = new_message.content
        
        # 保存消息数据而不是直接显示
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "message",
            "role": role,
            "title": title,
            "content": content
        }
        _save_message(config, message_data)
    else:
        logger.warning("Empty message content", new_message)
        
def frontend_add_tool_call(tool_name: str, tool_args: dict, config: Config):
    if not config:
        return
    
    tool_message = tool_show_message.get(tool_name, "Calling {tool_name}...")
    tool_message = tool_message.format(tool_name=tool_name, **tool_args)
    
    # 保存工具调用数据
    message_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "tool_call",
        "tool_name": tool_name,
        "content": tool_message
    }
    _save_message(config, message_data)

def frontend_update_node(node_name: str, config: Config):
    if not config:
        return
    global current_node
    current_node = node_name
    
    # 保存节点更新数据
    message_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "node_update",
        "node_name": node_name,
        "content": f"Subgraph complete: {node_name}"
    }
    _save_message(config, message_data)

@st.fragment
def display_messages_from_file(config: Config):
    with st.container():
        """从文件中读取并显示最新的消息"""
        if not is_in_streamlit == "True":
            return
        
        messages_file = _get_messages_file_path(config)
        if not messages_file or not os.path.exists(messages_file):
            return
        
        try:
            with open(messages_file, 'r') as f:
                messages = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read messages file: {e}")
            return
        
        logger.debug(f"Loaded {len(messages)} messages from {messages_file}")
        # 显示消息
        for msg in messages:
            if msg["type"] == "message":
                role = msg["role"]
                title = msg["title"]
                content = msg["content"]
                
                with st.chat_message(role, avatar="🔍" if role=="user" else None):
                    if title:
                        st.write(f"**{title}**")
                    if len(content) > 300:
                        with st.container(height=150):
                            st.write(content)
                    else:
                        st.write(content)
            elif msg["type"] == "tool_call":
                st.chat_message("tool").write(msg["content"])
            elif msg["type"] == "node_update":
                st.info(msg["content"])




def show_scrollable(content, file_name, height=200):
    if file_name.endswith(".md"):
        component = st.write
    elif file_name.endswith(".txt"):
        component = st.text
    elif file_name.endswith(".py"):
        component = st.code
    elif file_name.endswith(".json"):
        component = st.json
    else:
        component = st.text
        
    with st.container(height=height):
        component(content)
def show_file_in_msg(file_path):
    
    filename = os.path.basename(file_path)
    try:
        file_content = open(file_path, "r").read()
    except:
        file_content = "Read file failed"
    with st.chat_message("assistant", avatar="📁"):
        st.write(f"**{filename}**")
        show_scrollable(file_content, filename, height=200)
@st.fragment
def show_file_in_dialog(rel_file_path):
    filename = os.path.basename(rel_file_path)
    print(filename)
    if st.button(rel_file_path, key=f"btn_{rel_file_path}"):
        print("!!!!!!!!!!")
        # @st.dialog(f"View File: {filename}", on_dismiss="ignore")
        # def view_file(text: str):
        #     show_scrollable(text, filename, height=800)
        
        # file_content = open(os.path.join(self.workspace_path, rel_file_path), "r").read()
        # view_file(file_content)


class WorkspaceMonitor(Thread):
    def __init__(self, save_path, sidebar_container):
        super().__init__()
        self.save_path = save_path
        self.sidebar_container = sidebar_container
        self.daemon = True  # 设置为守护线程，确保主程序结束时线程也结束
        self._stop_event = False
        self.workspace_path = os.path.join(self.save_path, "workspace")

    def stop(self):
        self._stop_event = True

    def refresh_file(self):
        if not os.path.exists(self.workspace_path):
            # 使用 Streamlit 的线程上下文安全方式显示信息
            self.sidebar_container.info("Workspace directory does not exist yet.")
        else:
            # 使用 glob.glob 递归获取所有文件
            pattern = os.path.join(self.workspace_path, "**", "*")
            all_files = glob.glob(pattern, recursive=True)
            # 过滤出文件（而不是目录），并计算相对于workspace_path的路径
            current_files = set()
            current_fils_hash = {}
            for f in all_files:
                if os.path.isfile(f):  # 只保留文件，排除目录
                    rel_path = os.path.relpath(f, self.workspace_path)
                    if not os.path.basename(rel_path).startswith("."):
                        current_files.add(rel_path)
                        current_fils_hash[rel_path] = hashlib.md5(open(f, 'rb').read()).hexdigest()
            
            
            new_files = current_files - self.previous_files
            update_files = [f for f in current_files if ((f in self.previous_files) and (current_fils_hash[f] != self.previous_files_hash[f]))]
            # 显示新文件通知，如果删除了文件也刷新
            new_files = list(new_files)[:3]
            update_files = update_files[:3]
            if new_files or update_files or (self.previous_files - current_files):
                # logger.debug(f"Checking workspace directory: " + str(current_files))
                logger.debug(f"New files found: {new_files}")
                logger.debug(f"Updated files found: {update_files}")
                # 每次都要覆盖掉上次的文件列表
                self.sidebar_container.empty()

                for file in new_files:
                    if file.endswith(".pyc"):
                        continue
                    st.success(f"File added: {file}")
                    show_file_in_msg(os.path.join(self.workspace_path, file))
                
                for file in update_files:
                    if file.endswith(".pyc"):
                        continue
                    st.success(f"File updated: {file}")
                    show_file_in_msg(os.path.join(self.workspace_path, file))

                with self.sidebar_container.container():
                    # 显示文件列表
                    if current_files:
                        # 创建一个按钮，点击后设置要查看的文件
                        for file in sorted(current_files):
                            st.write(f"- {file}")
                            # show_file_in_dialog(file)
                    else:
                        st.info("No files in workspace yet.")

                self.previous_files = current_files
                self.previous_files_hash = current_fils_hash
    
    
    def run(self):
        """在子线程中监控 workspace 目录并显示文件列表"""
        self.previous_files = set()
        self.previous_files_hash = {}

        for _ in range(120):
            if self._stop_event:
                break
            try:
                self.refresh_file()
                # 每2秒检查一次
                time.sleep(5)
            except Exception as e:
                # 避免线程因异常而终止
                logger.warning(f"Error in file watcher: {e}")
                logger.warning(traceback.format_exc())
                time.sleep(5)
                continue

