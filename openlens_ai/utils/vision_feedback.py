import os
import json

import traceback
import time
from loguru import logger
import glob
import base64
import fitz
from datetime import datetime

from langchain.load.dump import dumps
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from ..utils.config import Config, get_lang_prompt
from ..state import load_state


def get_vlm(config: Config):
    return init_chat_model(
        config.llm.vision.model,
        base_url=config.llm.vision.base_url,
        model_provider="openai",
        openai_api_key=config.llm.vision.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )


def collect_fig_files(config: Config, fig_files_extensions: list = [".png", ".jpg", ".jpeg", ".pdf"], base_dir=None):
    fig_file_list = []
    if base_dir is None:
        base_dir = os.path.join(config.save_path, "workspace")
    for ext in fig_files_extensions:
        fig_file_list.extend(glob.glob(os.path.join(base_dir, "**", f"*{ext}"), recursive=True))
    logger.info(f"Found {len(fig_file_list)} results files: {fig_file_list}")
    return fig_file_list


def get_fig_base64(fig_file_list):
    fig_base64_list = []
    for fig in fig_file_list:
        # If it's a PDF file, convert it to PNG first
        if fig.lower().endswith(".pdf"):
            try:
                pdf_document = fitz.open(fig)
                # Convert each page to PNG
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    # Append page number to filename for identification
                    fig_base64_list.append((f"{fig}_page_{page_num+1}.png", img_base64))
                pdf_document.close()
            except ImportError:
                logger.error("PyMuPDF (fitz) is not installed. Cannot convert PDF to PNG.")
                # If conversion fails, try to read PDF as is
                with open(fig, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    fig_base64_list.append((fig, img_base64))
            except Exception as e:
                logger.error(f"Error converting PDF {fig} to PNG: {e}")
                # If conversion fails, try to read PDF as is
                with open(fig, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    fig_base64_list.append((fig, img_base64))
        else:
            with open(fig, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                fig_base64_list.append((fig, img_base64))
    return fig_base64_list


def save_llm_call(messages: list, config: Config):
    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_path = os.path.join(config.save_path, "llm_calls", f"{time_stamp}.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "w") as f:
        f.write(dumps(messages, indent=4, ensure_ascii=False))


def call_vlm_with_prompt(image_base64: str, config: Config, prompt: str) -> str:
    """
    Generic VLM calling function for handling image-related requests

    Args:
        image_base64: Base64 encoded image data
        config: Configuration object
        prompt: Prompt text

    Returns:
        VLM response content
    """

    def formatter_a(prompt, image_base64):
        logger.info(f"Using formatter A")
        # https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8#%E5%9B%BE%E7%89%87
        # https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions#vlm
        image_feedback_message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64,}},
            ]
        )
        return image_feedback_message

    def formatter_b(prompt, image_base64):
        logger.info(f"Using formatter B")
        image_feedback_message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image", "source_type": "base64", "data": image_base64, "mime_type": "image/jpeg"},
            ]
        )
        return image_feedback_message

    vlm = get_vlm(config)

    # Select formatter to use
    formatters = [formatter_a, formatter_b]

    for try_i in range(10):
        for this_formatter in formatters:
            try:
                # Call VLM to evaluate the image
                image_message = this_formatter(prompt, image_base64)

                vlm_response = vlm.invoke([image_message])
                save_llm_call([image_message, vlm_response], config)
                logger.info(f"Vision response: {vlm_response.content}")
                return vlm_response.content
            except Exception as e:
                logger.warning(f"Error when calling llm: {e}")
                logger.warning(traceback.format_exc())
                logger.warning("Retrying...")
                time.sleep(5)


def _load_prompt(config: Config, prompt_filename: str) -> str:
    """
    Load prompt text

    Args:
        config: Configuration object
        prompt_filename: Prompt file name

    Returns:
        Prompt text
    """
    # Load prompt based on domain configuration
    domain = getattr(config, "domain", "general")
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain, prompt_filename)
    with open(prompt_path, "r") as f:
        prompt = f.read() + get_lang_prompt(config.llm.language)
    return prompt


def get_vision_feedback(image_base64: str, config: Config) -> str:
    """
    Get image feedback
    """
    prompt = _load_prompt(config, "vision_feedback.md")
    return call_vlm_with_prompt(image_base64, config, prompt)


def get_latex_vision_feedback(image_base64: str, config: Config) -> str:
    """
    Get LaTeX image feedback
    """
    prompt = _load_prompt(config, "vision_latex_feedback.md")
    return call_vlm_with_prompt(image_base64, config, prompt)


def get_vision_classification(image_base64: str, config: Config) -> str:
    """
    Get image classification
    """
    prompt = _load_prompt(config, "vision_classify.md")
    return call_vlm_with_prompt(image_base64, config, prompt)


if __name__ == "__main__":

    config, state, last_subgraph = load_state("outputs/power_grid_fault_id")

    test_image = "outputs/power_grid_fault_id/workspace/subtask_01/processed_data/figures/domain_distribution_improved.png"
    image_base64 = get_fig_base64([test_image])[0][1]
    vlm_response = get_vision_feedback(image_base64, config)
    logger.info(vlm_response)

    test_pdf = "outputs/power_grid_fault_id/workspace/manuscript/main.pdf"
    pdf_base64 = get_fig_base64([test_pdf])[0][1]
    vlm_response = get_latex_vision_feedback(pdf_base64, config)
    logger.info(vlm_response)