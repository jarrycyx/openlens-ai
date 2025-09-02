import os
import json
import dotenv
import traceback
import time
from loguru import logger
import glob
import base64
import fitz

from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from ..utils.config import Config

dotenv.load_dotenv()



with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "vision_feedback.md")) as f:
    vision_feedback_prompt = f.read()


with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "vision_classify.md")) as f:
    vision_classify_prompt = f.read()
    
    
vlm = init_chat_model(
    os.environ.get("VISION_MODEL", "deepseek-chat"),
    base_url=os.environ.get("BASE_URL", ""),
    model_provider="openai",
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
def collect_fig_files(config: Config, fig_files_extensions: list = [".png", ".jpg", ".jpeg", ".pdf", ".svg"], base_dir=None):
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
        if fig.lower().endswith('.pdf'):
            try:
                pdf_document = fitz.open(fig)
                # Convert each page to PNG
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    # Append page number to filename for identification
                    fig_base64_list.append((f"{fig}_page_{page_num+1}.png", img_base64))
                pdf_document.close()
            except ImportError:
                logger.error("PyMuPDF (fitz) is not installed. Cannot convert PDF to PNG.")
                # If conversion fails, try to read PDF as is
                with open(fig, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    fig_base64_list.append((fig, img_base64))
            except Exception as e:
                logger.error(f"Error converting PDF {fig} to PNG: {e}")
                # If conversion fails, try to read PDF as is
                with open(fig, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    fig_base64_list.append((fig, img_base64))
        else:
            with open(fig, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                fig_base64_list.append((fig, img_base64))
    return fig_base64_list


def get_vision_feedback(image_base64: str, config: Config) -> str:
    for try_i in range(10):
        try:
            # Call VLM to evaluate the image
            image_feedback_message = HumanMessage(content=[
                {
                    "type": "text",
                    "text": vision_feedback_prompt
                },
                {
                    "type": "image",
                    "source_type": "base64",
                    "data": image_base64,
                    "mime_type": "image/jpeg",
                },
            ])
            
            vlm_response = vlm.invoke([image_feedback_message])
            logger.info(f"Vision feedback: {vlm_response.content}")
            return vlm_response.content
        except Exception as e:
            logger.warning(f"Error when calling llm: {e}")
            logger.warning(traceback.format_exc())
            logger.warning("Retrying...")
            time.sleep(5)


def get_vision_classification(image_base64: str, config: Config) -> str:
    # Call VLM to classify the image
    for try_i in range(10):
        try:
            image_classification_message = HumanMessage(content=[
                {
                    "type": "text",
                    "text": vision_classify_prompt
                },
                {
                    "type": "image",
                    "source_type": "base64",
                    "data": image_base64,
                    "mime_type": "image/jpeg",
                }
            ])
            vlm_response = vlm.invoke([image_classification_message])
            logger.info(f"Vision classification: {vlm_response.content}")
            return vlm_response.content
        except Exception as e:
            logger.warning(f"Error when calling llm: {e}")
            logger.warning(traceback.format_exc())
            logger.warning("Retrying...")
            time.sleep(5)