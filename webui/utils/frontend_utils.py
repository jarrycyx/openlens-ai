import os
import streamlit as st
from typing import Optional, Type, Dict, Any, Union
from datetime import datetime
import time
from loguru import logger
import time
import random
import hashlib
import streamlit as st
import glob
import json
import traceback
from pypdf import PdfReader
from PIL import Image
from datetime import datetime

from openlens_ai.utils.file_utils import collect_files, collect_token_usage
from openlens_ai.utils.frontend_messages import _get_messages_file_path, _message_remove_duplicates
from openlens_ai.utils.config import Config

from .translations import t, load_llm_config
from .summarize import get_content_summary, get_summary_cache_key, summarize_content, summarize_with_llm_async




pdf_file_ext = [".pdf"]
image_file_ext = [".png", ".jpg", ".jpeg", ".gif", ".svg"]
text_file_ext = [".md", ".txt"]
code_file_ext = [".py"]
all_view_ext = pdf_file_ext + image_file_ext + text_file_ext + code_file_ext

def display_single_file(config: Config, file_path: str):
    rel_path = os.path.relpath(file_path, config.save_path)
    # Try to read file content
    if rel_path.endswith(tuple(image_file_ext)):
        st.image(file_path)
    elif rel_path.endswith(tuple(pdf_file_ext)):
        # pdf_viewer(file_path)
        st.pdf(file_path, height=1200, key=f"pdf_{file_path}")
    elif rel_path.endswith(tuple(text_file_ext + code_file_ext)):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Limit the display content length
        if len(content) > 20000:
            content = content[:20000] + "\n\n" + t("content_truncated")

        if rel_path.endswith(".md"):
            st.markdown(content)
        else:
            st.code(content, language=rel_path.split(".")[-1] if "." in rel_path else None)
    else:
        pass

    # Provide download button
    with open(file_path, "rb") as f:
        file_data = f.read()

    st.download_button(label=f"⬇️ {t('download')}", data=file_data, file_name=rel_path, key=f"download_{rel_path}_{random.randint(1000, 9999)}")

def get_paper_path(config: Config):
    if os.path.exists(os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")):
        return os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")
    else:
        pdf_path_list = glob.glob(os.path.join(config.save_path, "workspace", "manuscript", "*.pdf"))
        if pdf_path_list:
            return pdf_path_list[0]
        else:
            return None

def check_file(file_path: str):
    """Check if the file is valid and readable
    
    Args:
        file_path: File path
        
    Returns:
        bool: Whether the file is valid and readable
    """
    # First check if the file exists
        
    # Try to read file content
    try:
        assert os.path.exists(file_path), f"File {file_path} does not exist"
        assert os.path.getsize(file_path) > 0, f"File {file_path} is empty"
        if file_path.endswith(tuple(image_file_ext)):
            # Try to parse the image
            with Image.open(file_path) as img:
                img.verify()  # 验证图像完整性
            return True
        elif file_path.endswith(tuple(pdf_file_ext)):
            # Try to parse the PDF
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                # Check if the PDF has pages
                assert len(reader.pages) > 0, f"PDF {file_path} has no pages"
                return True
        elif file_path.endswith(tuple(text_file_ext + code_file_ext)):
            # Try to read text/code files
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Check if the file has content
            assert content.strip(), f"File {file_path} is empty after stripping"
            return True
        else:
            # Unsupported file type
            raise ValueError(f"Unsupported file type: {file_path}")
    except Exception as e:
        logger.debug(f"Failed to check file {file_path}: {e}")
        return False


def get_latest_files(config: Config, max_files: int = 10):
    workspace_path = os.path.join(config.save_path, "workspace")
    pdf_path = get_paper_path(config)

    if not os.path.exists(workspace_path):
        # st.info(t("no_files_generated_yet"))
        return []

    # Get all files and sort by modification time
    all_files = {}
    for root, dirs, files in os.walk(workspace_path):
        for file in files:
            file_path = os.path.join(root, file)
            if (file.startswith(".")) or (file.endswith(".pyc")):
                continue
            if ((pdf_path) and (os.path.basename(file_path) == os.path.basename(pdf_path))):
                continue
            if not check_file(file_path):
                continue
                        
            rel_path = os.path.relpath(file_path, workspace_path)
            try:
                all_files[file_path] = (file_path, rel_path, os.path.getmtime(file_path))
            except Exception as e:
                logger.warning(f"Failed to get mtime for {file_path}: {e}")
                    
    if not all_files:
        # st.info(t("no_files_generated_yet"))
        return []

    
    all_files = list(all_files.values())
    # Sort by modification time, take the latest files
    all_files = sorted(all_files, key=lambda x: x[2], reverse=True)
    all_files = [x for x in all_files if x[1].endswith(tuple(all_view_ext))]
    if pdf_path:
        all_files.insert(0, (pdf_path, os.path.relpath(pdf_path, workspace_path), os.path.getmtime(pdf_path)))

    latest_files = all_files[:max_files]  # Display the latest 10 files

    return latest_files

def display_multiple_file_preview(config: Config):
    """Display preview of the latest generated file content"""
    latest_files = get_latest_files(config)

    ############ Display multiple files
    for i, (file_path, rel_path, _) in enumerate(latest_files):
        try:
            expand = i == 0

            with st.expander(t("file_preview", rel_path=rel_path), expanded=expand):
                display_single_file(config, file_path)
        except Exception as e:
            st.error(t("error_reading_file", rel_path=rel_path, error=e))


def display_messages_from_file(config: Config):
    # Read and display the latest messages from the file

    question = t(config.question)
    dataset_path = config.dataset_path
    language = t(config.llm.language)
    st.chat_message("human").write(f"**{t('question_label')}** " + question + f"\n\n**{t('dataset_path_label')}** " + dataset_path + f"\n\n**{t('language')}** " + language)
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
    # Display messages
    for msg in messages:
        if msg["type"] == "message":
            role = "ai"
            title = ""
            content = msg["content"]
            time_str = msg.get("timestamp", "")
            try:
                timestamp_int = datetime.fromisoformat(time_str).timestamp()
                time_str = datetime.fromtimestamp(timestamp_int).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Failed to parse timestamp: {time_str}: {e}")
                time_str = ""
            
            content_search_lower = content[:100].lower().replace("\n", " ")
            if "search" in content_search_lower:
                avatar = "🌐"
                title = t("Searching")
            elif "latex" in content_search_lower or "manuscript" in content_search_lower or "paper" in content_search_lower:
                avatar = "📑"
                title = t("Writing")
            elif "coding" in content_search_lower:
                avatar = "👩‍💻"
                title = t("Coding")
            elif "decision" in content_search_lower:
                if "polish" in content_search_lower:
                    avatar = "🧐"
                    title = t("Polishing the paper")
                if "fix_last_subtask" in content_search_lower:
                    avatar = "🔧"
                    title = t("Fixing the code")
                elif "continue" in content_search_lower:
                    avatar = "✅"
                else:
                    avatar = "🤔"
            # elif "subtask" in content_search_lower:
            #     avatar = "📝"
            else:
                # print("Not sure what to show: ", content_search_lower)
                avatar = "🫧"
                # title = "OpenLens AI"

            with st.chat_message(role, avatar=avatar):
                if title and (title != "Agent"):
                    with st.container(horizontal=True, width="content"):
                        st.write(f"**{title.strip()}**")
                        st.caption(time_str)
                content_summary = get_content_summary(content, max_length=50, language=config.llm.language)
                st.write(content_summary)
                # if len(content) > 2000:
                #     with st.container(height=300):
                #         st.write(content)
                #     # content = content[:300] + "\n\n" + t("content_truncated")
                #     # st.write(content)
                # else:
                #     st.write(content)
        elif msg["type"] == "tool_call":
            st.chat_message("tool").write(t(msg["content"]))
        elif msg["type"] == "node_update":
            # st.info(msg["content"])
            st.divider()
        elif "file_content" in msg["type"]:
            pass



def show_scrollable(content, file_name, height=200):
    content = content[:10000]  # Limit content length to prevent it from being too large

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



@st.cache_data(ttl=600)
def get_zip(config: Config):
    collect_files(config)
    with open(os.path.join(config.save_path, "compressed", "all_files.zip"), "rb") as f:
        zip_buffer = f.read()
    return zip_buffer

@st.cache_data(ttl=600)
def get_pdf(config: Config):
    pdf_path = os.path.join(config.save_path, "workspace", "manuscript", "main.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    logger.warning(f"No PDF found for {config.save_path}")
    return None

@st.cache_data(ttl=600)
def get_plan(config: Config):
    plan_path = os.path.join(config.save_path, "plan.md")
    if os.path.exists(plan_path):
        with open(plan_path, "r") as f:
            plan_str = f.read()
        return plan_str
    logger.warning(f"No plan found for {config.save_path}")
    return None

def download_workspace_button(config):

    zip_buffer = get_zip(config)
    pdf_buffer = get_pdf(config)
    plan_str = get_plan(config)

    st.download_button(
        label=f"📥 {t('download_workspace')}",
        data=zip_buffer,
        file_name=f"workspace_{os.path.basename(config.save_path)}.zip",
        mime="application/zip",
    )
    if pdf_buffer:
        st.download_button(label=f"📑 {t('download_paper')}",
                           data=pdf_buffer,
                           mime="application/pdf",
                           file_name="main.pdf")

    if plan_str:
        st.download_button(label=f"✍️ {t('download_plan')}",
                           data=plan_str,
                           mime="text/markdown",
                           file_name="plan.md")



def show_workspace(config):

    save_path = config.save_path
    workspace_path = os.path.join(save_path, "workspace")
    # Use glob.glob to recursively get all files
    pattern = os.path.join(workspace_path, "**", "*")
    all_files = glob.glob(pattern, recursive=True)
    # Filter out files (not directories) and calculate the path relative to workspace_path
    current_files = set()
    current_fils_hash = {}
    for f in all_files:
        if os.path.isfile(f):  # 只保留文件，排除目录
            rel_path = os.path.relpath(f, workspace_path)
            if not os.path.basename(rel_path).startswith("."):
                current_files.add(f)
                current_fils_hash[f] = hashlib.md5(open(f, "rb").read()).hexdigest()

    # extra files are files outside the workspace that may need to be displayed, so they are paths relative to save_path
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
        st.success(t("click_download_workspace"))
        st.write(f"**{t('file_list')}**")
        with st.container(horizontal=True):
            # Display file list
            if current_files:
                # Create a button that sets the file to view after clicking
                for file_path in sorted(current_files):
                    try:
                        file_name = os.path.basename(file_path)
                        rel_path = os.path.relpath(file_path, workspace_path)
                        st.caption(t("file_list_item", rel_path=rel_path))
                    except Exception as e:
                        logger.error(f"Error previewing file {file_path}: {e}")
                    # show_file_in_dialog(file)
            else:
                st.info(t("no_files_in_workspace"))
