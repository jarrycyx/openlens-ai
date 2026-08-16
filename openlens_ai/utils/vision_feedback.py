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
from PIL import Image
import io
import cairosvg
try:
    from langchain_core.load.dump import dumps
except ImportError:
    from langchain.load.dump import dumps
from .llm_provider import build_chat_model, build_multimodal_message
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from ..utils.config import Config, get_lang_prompt
from ..state import load_state


def compress_image(img_data, max_size=4000):
    """
    Compress image to ensure width and height do not exceed max_size
    
    Args:
        img_data: Image binary data
        max_size: Maximum width and height size, default is 4000
        
    Returns:
        Compressed image binary data
    """
    try:
        # Convert binary data to PIL Image object
        img = Image.open(io.BytesIO(img_data))
        
        # Check if compression is needed
        if img.width <= max_size and img.height <= max_size:
            return img_data
            
        # Calculate scaling ratio
        width_ratio = max_size / img.width
        height_ratio = max_size / img.height
        ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        # Compress image
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert compressed image to binary data
        img_byte_arr = io.BytesIO()
        img_resized.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
    except Exception as e:
        logger.warning(f"Error compressing image: {e}")
        return img_data


def get_vlm(config: Config):
    return build_chat_model(
        config.llm.vision,
        enable_thinking=True,
        max_tokens=config.context.max_context_token_cnt,
    )


def collect_fig_files(config: Config, fig_files_extensions: list = [".png", ".jpg", ".jpeg", ".pdf"], base_dir=None):
    fig_file_list = []
    if base_dir is None:
        base_dir = os.path.join(config.save_path, "workspace")
    for ext in fig_files_extensions:
        fig_file_list.extend(glob.glob(os.path.join(base_dir, "**", f"*{ext}"), recursive=True))
    logger.info(f"Found {len(fig_file_list)} results files: {fig_file_list}")
    return fig_file_list




def convert_pdf_to_merged_image(pdf_file: str):
    """
    Convert all pages of a PDF file into a single merged image in a grid layout.
    
    Args:
        pdf_file: Path to the PDF file
        
    Returns:
        Tuple of (save_tmp_path, img_base64) or (None, None) if error
    """
    try:
        pdf_document = fitz.open(pdf_file)
        
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
        # 压缩图片，确保长宽不超过4000像素
        compressed_img_data = compress_image(img_data, max_size=4000)
        img_base64 = base64.b64encode(compressed_img_data).decode("utf-8")
        
        try:
            if "workspace" in pdf_file:
                save_path = pdf_file.split("workspace")[0]
                save_tmp_path = os.path.join(save_path, "backup", "tmp", f"{os.path.basename(pdf_file)}_merged.png")
            else:
                save_tmp_path = os.path.join(os.path.dirname(pdf_file), f".tmp_{os.path.basename(pdf_file)}_merged.png")
            os.makedirs(os.path.dirname(save_tmp_path), exist_ok=True)
            with open(save_tmp_path, "wb") as f:
                f.write(compressed_img_data)
        except Exception as e:
            error_msg = f"Error saving merged PDF image: {e}"
            logger.warning(error_msg)
            logger.error(traceback.format_exc())
        
        merged_pix = None  # Free memory
        pdf_document.close()
        return save_tmp_path, img_base64
    except Exception as e:
        logger.warning(f"Error converting PDF {pdf_file} to merged PNG: {e}")
        logger.warning(traceback.format_exc())
        return None, None


def convert_pdf_to_separate_images(pdf_file: str):
    """
    Convert each page of a PDF file into separate PNG images.
    
    Args:
        pdf_file: Path to the PDF file
        
    Returns:
        Tuple of (save_tmp_path, img_base64) for the first page or (None, None) if error
    """
    try:
        pdf_document = fitz.open(pdf_file)
        name_list, base64_list = [], []
        
        # Convert each page to PNG separately
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            # Append page number to filename for identification
            
            try:
                # 压缩图片，确保长宽不超过4000像素
                img_data = base64.b64decode(img_base64)
                compressed_img_data = compress_image(img_data, max_size=4000)
                compressed_img_base64 = base64.b64encode(compressed_img_data).decode("utf-8")
                
                if "workspace" in pdf_file:
                    save_path = pdf_file.split("workspace")[0]
                    save_tmp_path = os.path.join(save_path, "backup", "tmp", f"{os.path.basename(pdf_file)}_page_{page_num+1}.png")
                else:
                    save_tmp_path = os.path.join(os.path.dirname(pdf_file), f".tmp_{os.path.basename(pdf_file)}_page_{page_num+1}.png")
                os.makedirs(os.path.dirname(save_tmp_path), exist_ok=True)
                with open(save_tmp_path, "wb") as f:
                    f.write(compressed_img_data)
            except Exception as e:
                error_msg = f"Error saving separate PDF page image: {e}"
                logger.warning(error_msg)
                logger.error(traceback.format_exc())
            
            name_list.append(save_tmp_path)
            base64_list.append(compressed_img_base64)
        
        pdf_document.close()
        
        return name_list, base64_list
        
    except Exception as e:
        logger.warning(f"Error converting PDF {pdf_file} to separate PNGs: {e}")
        logger.warning(traceback.format_exc())
        return None, None


def convert_svg_to_png(svg_file: str) -> str:
    if "workspace" in svg_file:
        save_path = svg_file.split("workspace")[0]
        save_tmp_path = os.path.join(save_path, "backup", "tmp", f"{os.path.basename(svg_file)}.png")
    else:
        save_tmp_path = os.path.join(os.path.dirname(svg_file), f".tmp_{os.path.basename(svg_file)}.png")
    cairosvg.svg2png(url=svg_file, write_to=save_tmp_path, output_width=2000, output_height=1000)
    return save_tmp_path

def get_fig_base64(fig_file_list, merge_pdf=False):
    fig_base64_list = []
    for fig in fig_file_list:
        if not os.path.exists(fig):
            continue
        # If it's a PDF file, convert it to PNG first
        if fig.lower().endswith(".pdf"):
            if merge_pdf:
                name, img_base64 = convert_pdf_to_merged_image(fig)
                if name is None:
                    continue
                fig_base64_list.append((name, img_base64))
            else:
                name_list, img_base64_list = convert_pdf_to_separate_images(fig)
                if name_list is None:
                    continue
                fig_base64_list.extend(zip(name_list, img_base64_list))
        if fig.lower().endswith(".svg"):
            png_path = convert_svg_to_png(fig)
            with open(png_path, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                fig_base64_list.append((fig, img_base64))
        else:
            with open(fig, "rb") as f:
                img_data = f.read()
                # 压缩图片，确保长宽不超过4000像素
                compressed_img_data = compress_image(img_data, max_size=4000)
                img_base64 = base64.b64encode(compressed_img_data).decode("utf-8")
                fig_base64_list.append((fig, img_base64))
    return fig_base64_list


def save_llm_call(messages: list, config: Config):
    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_path = os.path.join(config.save_path, "llm_calls", f"{time_stamp}.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "w") as f:
        f.write(dumps(messages, indent=4, ensure_ascii=False))




def call_vlm_with_prompt(
    config: Config,
    media: str,
    prompt: str,
    media_type: str = "image",
) -> str:
    """
    Generic VLM calling function for handling image-related requests

    Args:
        media: Media URL, data URI, or base64-encoded image data
        config: Configuration object
        prompt: Prompt text
        media_type: Input modality, either ``image`` or ``video``

    Returns:
        VLM response content
    """

    vlm = get_vlm(config)

    error_msg = ""
    for try_i in range(3):
        try:
            media_message = build_multimodal_message(
                config.llm.vision.provider,
                config.llm.vision.model,
                prompt,
                media,
                media_type,
            )
            vlm_response = vlm.invoke(media_message)
            save_llm_call(media_message + [vlm_response], config)
            logger.debug(f"Vision response: {vlm_response.content}")
            return vlm_response.content
        except Exception as e:
            error_msg = f"Error when calling llm: {e}"
            logger.warning(f"Error when calling llm: {e}")
            logger.warning(traceback.format_exc())
            logger.warning("Retrying...")
            time.sleep(5)
    return error_msg


def call_video_vlm_with_prompt(config: Config, video_url: str, prompt: str) -> str:
    """Call a video-capable vision model with a remote video URL."""
    return call_vlm_with_prompt(config, video_url, prompt, media_type="video")


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
    return call_vlm_with_prompt(config, image_base64, prompt)


def get_latex_vision_feedback(image_base64: str, config: Config) -> str:
    """
    Get LaTeX image feedback
    """
    prompt = _load_prompt(config, "vision_latex_feedback.md")
    return call_vlm_with_prompt(config, image_base64, prompt)


def get_vision_classification(image_base64: str, config: Config) -> str:
    """
    Get image classification
    """
    prompt = _load_prompt(config, "vision_classify.md")
    return call_vlm_with_prompt(config, image_base64, prompt)


if __name__ == "__main__":

    config, state, last_subgraph, file_manager = load_state("outputs/power_grid_fault_id")

    test_image = "outputs/mlebench-0-denoising-dirty-documents/workspace/subtask_01/figures/sample_image_pairs.png"
    image_base64 = get_fig_base64([test_image])[0][1]
    vlm_response = get_vision_feedback(image_base64, config)
    logger.info(vlm_response)

    test_pdf = "outputs/power_grid_fault_id/workspace/manuscript/main.pdf"
    pdf_base64 = get_fig_base64([test_pdf])[0][1]
    vlm_response = get_latex_vision_feedback(pdf_base64, config)
    logger.info(vlm_response)
