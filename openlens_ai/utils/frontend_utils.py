import os
import streamlit as st
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
import time
from loguru import logger
import time
import random
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
from streamlit_pdf_viewer import pdf_viewer

from .file_utils import prepare_file_config, collect_files, collect_token_usage
from .config import Config


tool_show_message = {
    "search_arxiv_tool": "Searching Arxiv for **{query}**",
    "read_arxiv_paper_tool": "Reading Arxiv Paper: **{paper_id}**",
    "search_medrxiv_tool": "Searching MedRxiv for **{query}**",
    "read_medrxiv_paper_tool": "Reading MedRxiv Paper: **{paper_id}**",
    "report_writer_tool": "Writing report to **{file_name}**",
    "openhands": "Writing/executing codes",
    "tavily_search": "Searching on the web for **{query}**",
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
        message_data = {"timestamp": datetime.now().isoformat(), "type": "message", "role": role, "title": title, "content": content}
        _save_message(config, message_data)
    else:
        logger.warning("Empty message content", new_message)


def frontend_add_tool_call(tool_name: str, tool_args: dict, config: Config):
    if not config:
        return

    tool_message = tool_show_message.get(tool_name, "Calling {tool_name}...")
    tool_message = tool_message.format(tool_name=tool_name, **tool_args)

    # 保存工具调用数据
    message_data = {"timestamp": datetime.now().isoformat(), "type": "tool_call", "tool_name": tool_name, "content": tool_message}
    _save_message(config, message_data)


def frontend_update_node(node_name: str, config: Config):
    if not config:
        return
    global current_node
    current_node = node_name

    # 保存节点更新数据
    message_data = {"timestamp": datetime.now().isoformat(), "type": "node_update", "node_name": node_name, "content": f"Subgraph complete: {node_name}"}
    _save_message(config, message_data)


pdf_file_ext = [".pdf"]
image_file_ext = [".png", ".jpg", ".jpeg", ".gif", ".svg"]
text_file_ext = [".md", ".txt"]
code_file_ext = [".py"]
all_view_ext = pdf_file_ext + image_file_ext + text_file_ext + code_file_ext

def display_single_file(config: Config, file_path: str):
    rel_path = os.path.relpath(file_path, config.save_path)
    # 尝试读取文件内容
    if rel_path.endswith(tuple(image_file_ext)):
        st.image(file_path)
    elif rel_path.endswith(tuple(pdf_file_ext)):
        # pdf_viewer(file_path)
        st.pdf(file_path, height=1200, key=f"pdf_{file_path}")
    elif rel_path.endswith(tuple(text_file_ext + code_file_ext)):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # 限制显示内容长度
        if len(content) > 4000:
            content = content[:4000] + "\n\n... (content truncated)"

        if rel_path.endswith(".md"):
            st.markdown(content)
        else:
            st.code(content, language=rel_path.split(".")[-1] if "." in rel_path else None)
    else:
        pass

    # 提供下载按钮
    with open(file_path, "rb") as f:
        file_data = f.read()

    st.download_button(label="⬇️ Download", data=file_data, file_name=rel_path, key=f"download_{rel_path}_{random.randint(1000, 9999)}")

def get_paper_path(config: Config):
    if os.path.exists(os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")):
        return os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")
    else:
        pdf_path_list = glob.glob(os.path.join(config.save_path, "workspace", "manuscript", "*.pdf"))
        if pdf_path_list:
            return pdf_path_list[0]
        else:
            return None

def get_latest_files(config: Config):
    workspace_path = os.path.join(config.save_path, "workspace")

    if not os.path.exists(workspace_path):
        st.info("No files generated yet.")
        return

    # 获取所有文件并按修改时间排序
    all_files = []
    for root, dirs, files in os.walk(workspace_path):
        for file in files:
            if not file.startswith(".") and not file.endswith(".pyc"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                all_files.append((file_path, rel_path, os.path.getmtime(file_path)))

    if not all_files:
        st.info("No files generated yet.")
        return
    
    # 按修改时间排序，取最新的几个文件
    all_files.sort(key=lambda x: x[2], reverse=True)
    all_files = [x for x in all_files if x[1].endswith(tuple(all_view_ext))]
    pdf_path = get_paper_path(config)
    print(pdf_path)
    if pdf_path:
        all_files.insert(0, (pdf_path, os.path.relpath(pdf_path, workspace_path), os.path.getmtime(pdf_path)))
    
    latest_files = all_files[:10]  # 显示最新的5个文件

    return latest_files

def display_multiple_file_preview(config: Config):
    """显示最新生成的文件内容预览"""
    latest_files = get_latest_files(config)

    ############ 显示多个文件
    for i, (file_path, rel_path, _) in enumerate(latest_files):
        try:
            expand = i == 0

            with st.expander(f"📄 {rel_path}", expanded=expand):
                display_single_file(config, file_path)
        except Exception as e:
            st.error(f"Error reading file {rel_path}: {e}")


def display_messages_from_file(config: Config):
    # 从文件中读取并显示最新的消息
    if is_in_streamlit != "True":
        return

    messages_file = _get_messages_file_path(config)
    if not messages_file or not os.path.exists(messages_file):
        return

    try:
        with open(messages_file, "r") as f:
            messages = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read messages file: {e}")
        return

    messages = _message_remove_duplicates(messages)
    # logger.debug(f"Loaded {len(messages)} messages from {messages_file}")
    # 显示消息
    for msg in messages:
        if msg["type"] == "message":
            role = msg["role"]
            title = msg["title"]
            content = msg["content"]

            with st.chat_message(role, avatar="🔍" if role == "user" else None):
                if title:
                    st.write(f"**{title}**")
                if len(content) > 300:
                    # with st.container(height=150):
                    #     st.write(content)
                    content = content[:300] + "\n\n... (content truncated)"
                    st.write(content)
                else:
                    st.write(content)
        elif msg["type"] == "tool_call":
            st.chat_message("tool").write(msg["content"])
        elif msg["type"] == "node_update":
            st.info(msg["content"])
        elif "file_content" in msg["type"]:
            pass
                    


def show_scrollable(content, file_name, height=200):
    content = content[:10000]  # 限制内容长度，防止过大

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


def frontend_add_file_msg(file_path, config: Optional[Config] = None, file_status="added"):

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


@st.cache_data
def get_zip(config: Config):
    collect_files(config)
    with open(os.path.join(config.save_path, "compressed", "all_files.zip"), "rb") as f:
        zip_buffer = f.read()
    return zip_buffer

@st.cache_data
def get_pdf(config: Config):
    pdf_path = os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    return None

@st.cache_data
def get_plan(config: Config):
    plan_path = os.path.join(config.save_path, "plan.md")
    if os.path.exists(plan_path):
        with open(plan_path, "r") as f:
            plan_str = f.read()
        return plan_str
    return None

def download_workspace_button(config):
   
    zip_buffer = get_zip(config)
    pdf_buffer = get_pdf(config)
    plan_str = get_plan(config)
    
    st.download_button(
        label="📥 Download Workspace",
        data=zip_buffer,
        file_name=f"workspace_{os.path.basename(config.save_path)}.zip",
        mime="application/zip",
    )
    if pdf_buffer:
        st.download_button(label="📑 Download Paper", 
                           data=pdf_buffer, 
                           mime="application/pdf",
                           file_name="main.pdf")

    if plan_str:
        st.download_button(label="✍️ Download Plan", 
                           data=plan_str, 
                           mime="text/markdown",
                           file_name="plan.md")



def show_workspace(config):
    
    save_path = config.save_path
    workspace_path = os.path.join(save_path, "workspace")
    # 使用 glob.glob 递归获取所有文件
    pattern = os.path.join(workspace_path, "**", "*")
    all_files = glob.glob(pattern, recursive=True)
    # 过滤出文件（而不是目录），并计算相对于workspace_path的路径
    current_files = set()
    current_fils_hash = {}
    for f in all_files:
        if os.path.isfile(f):  # 只保留文件，排除目录
            rel_path = os.path.relpath(f, workspace_path)
            if not os.path.basename(rel_path).startswith("."):
                current_files.add(f)
                current_fils_hash[f] = hashlib.md5(open(f, "rb").read()).hexdigest()

    # extra files是workspace外面的可能需要展示的文件，所以是相对于save_path的路径
    extra_files = ["overall_graph_image.png"]
    for extra_f in extra_files:
        if os.path.exists(os.path.join(save_path, extra_f)):
            fp = os.path.join(save_path, extra_f)
            current_files.add(fp)
            current_fils_hash[fp] = hashlib.md5(open(fp, "rb").read()).hexdigest()
    
    with st.container(horizontal=False):
        with st.container(horizontal=True):
            download_workspace_button(config)
        
        # with st.popover("See file list"):
        st.success(f"Click **📥 Download Workspace** button to download all files.")
        st.write("**File List:**")
        with st.container(horizontal=True):
            # 显示文件列表
            if current_files:
                # 创建一个按钮，点击后设置要查看的文件
                for file_path in sorted(current_files):
                    try:
                        file_name = os.path.basename(file_path)
                        rel_path = os.path.relpath(file_path, workspace_path)
                        st.caption(f"- {rel_path}")
                    except Exception as e:
                        logger.error(f"Error previewing file {file_path}: {e}")
                    # show_file_in_dialog(file)
            else:
                st.info("No files in workspace yet.")
