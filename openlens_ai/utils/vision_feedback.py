import os
import json
import math

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


def get_fig_base64(fig_file_list, merge_pdf=False):
    fig_base64_list = []
    for fig in fig_file_list:
        # If it's a PDF file, convert it to PNG first
        if fig.lower().endswith(".pdf"):
            try:
                pdf_document = fitz.open(fig)
                
                if merge_pdf:
                    # Merge all pages into a single image
                    # Calculate dimensions for the merged image in a grid layout
                    page_images = []
                    page_widths = []
                    page_heights = []
                    
                    # First pass: render all pages and collect dimensions
                    for page_num in range(len(pdf_document)):
                        page = pdf_document[page_num]
                        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                        pix = page.get_pixmap(matrix=mat)
                        page_images.append(pix)
                        page_widths.append(pix.width)
                        page_heights.append(pix.height)
                    
                    # Calculate grid layout to make the image more square
                    num_pages = len(page_images)
                    
                    # Calculate average page dimensions
                    avg_page_width = sum(page_widths) / len(page_widths)
                    avg_page_height = sum(page_heights) / len(page_heights)
                    aspect_ratio = avg_page_width / avg_page_height
                    
                    # Calculate optimal grid dimensions to minimize aspect ratio difference
                    best_cols = int(math.ceil(math.sqrt(num_pages * aspect_ratio)))
                    best_rows = int(math.ceil(num_pages / best_cols))
                    
                    # Try a few variations to find the most square layout
                    min_diff = float('inf')
                    for cols in range(max(1, best_cols - 2), best_cols + 3):
                        rows = int(math.ceil(num_pages / cols))
                        total_width = cols * max(page_widths)
                        total_height = rows * max(page_heights)
                        diff = abs(total_width - total_height) / max(total_width, total_height)
                        if diff < min_diff:
                            min_diff = diff
                            best_cols = cols
                            best_rows = rows
                    
                    cols = best_cols
                    rows = best_rows
                    
                    # Calculate max width and height for uniform grid cells
                    max_page_width = max(page_widths)
                    max_page_height = max(page_heights)
                    
                    # Calculate total dimensions for the merged image
                    total_width = cols * max_page_width
                    total_height = rows * max_page_height
                    
                    # Apply maximum resolution limit (4000 pixels)
                    max_resolution = 4000
                    if total_width > max_resolution or total_height > max_resolution:
                        # Calculate scaling factor to fit within max_resolution
                        scale_factor = min(max_resolution / total_width, max_resolution / total_height)
                        
                        # Scale down the total dimensions
                        total_width = int(total_width * scale_factor)
                        total_height = int(total_height * scale_factor)
                        
                        # Scale down the grid cell dimensions
                        max_page_width = int(max_page_width * scale_factor)
                        max_page_height = int(max_page_height * scale_factor)
                        
                        # Scale down each page image
                        for i in range(len(page_images)):
                            # Get the original page and render it with scaling
                            page = pdf_document[i]
                            scale_matrix = fitz.Matrix(2 * scale_factor, 2 * scale_factor)  # 2x zoom for quality, then scale
                            scaled_pix = page.get_pixmap(matrix=scale_matrix)
                            page_images[i] = scaled_pix
                    
                    # Create a new pixmap for the merged image
                    # First create a base pixmap from the first page
                    first_pix = page_images[0]
                    merged_pix = fitz.Pixmap(first_pix, total_width, total_height)
                    
                    # Create a single temporary document and page for all images
                    temp_doc = fitz.open()
                    temp_page = temp_doc.new_page(width=total_width, height=total_height)
                    
                    # Insert each page image to the temporary page in grid layout
                    for i, pix in enumerate(page_images):
                        # Calculate grid position
                        row = i // cols
                        col = i % cols
                        
                        # Calculate position in the grid
                        x_offset = col * max_page_width
                        y_offset = row * max_page_height
                        
                        # Center the page within its grid cell if needed
                        x_center_offset = (max_page_width - pix.width) // 2
                        y_center_offset = (max_page_height - pix.height) // 2
                        
                        # Insert the image at the calculated position
                        temp_page.insert_image(
                            fitz.Rect(
                                x_offset + x_center_offset, 
                                y_offset + y_center_offset, 
                                x_offset + x_center_offset + pix.width, 
                                y_offset + y_center_offset + pix.height
                            ), 
                            pixmap=pix
                        )
                        pix = None  # Free memory
                    
                    # Get the final merged pixmap from the temporary page
                    merged_pix = temp_page.get_pixmap()
                    temp_doc.close()
                    
                    # Convert merged image to base64
                    img_data = merged_pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                    save_tmp_path = f"{os.path.dirname(fig)}/.tmp_{os.path.basename(fig)}_merged.png"
                    with open(save_tmp_path, "wb") as f:
                        f.write(base64.b64decode(img_base64))
                    fig_base64_list.append((save_tmp_path, img_base64))
                    merged_pix = None  # Free memory
                else:
                    # Convert each page to PNG separately (original behavior)
                    for page_num in range(len(pdf_document)):
                        page = pdf_document[page_num]
                        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        img_base64 = base64.b64encode(img_data).decode("utf-8")
                        # Append page number to filename for identification
                        fig_base64_list.append((f"{os.path.dirname(fig)}/.tmp_{os.path.basename(fig)}_page_{page_num+1}.png", img_base64))
                
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