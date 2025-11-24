# VLM MCP Server
# This server provides MCP tools for VLM (Vision Language Model) functionality
import os
import sys
import base64
import traceback
import time
import argparse
from loguru import logger
from typing import List, Dict, Optional, Annotated, Union
from pydantic import Field
from loguru import logger
import fitz
from fastmcp import FastMCP

from ...utils.vision_feedback import get_vlm, get_vision_feedback, get_vision_classification, get_latex_vision_feedback, get_fig_base64, call_vlm_with_prompt
from ...utils.config import Config
from ...state import load_state


# Global config variable
_config = None


def set_config(config: Config):
    """Set the global config"""
    global _config
    _config = config


def get_config() -> Config:
    """Get the global config"""
    global _config
    if _config is None:
        raise ValueError("Config not initialized. Call set_config first.")
    return _config


# Initialize MCP server
mcp = FastMCP("vlm_server")

def analyze_image(image_base64: str, prompt: Optional[str] = None) -> str:
    """Analyze an image using VLM.
    
    Args:
        image_base64: Base64 encoded image
        prompt: Optional custom prompt for analysis (if not provided, uses default)
    
    Returns:
        VLM analysis result
    """
    try:
        config = get_config()
        return call_vlm_with_prompt(image_base64, config, prompt)
    except Exception as e:
        return f"Error analyzing image: {str(e)}\n{traceback.format_exc()}"


def classify_image(image_base64: str) -> str:
    """Classify an image using VLM.
    
    Args:
        image_base64: Base64 encoded image
    
    Returns:
        VLM classification result
    """
    try:
        config = get_config()
        return get_vision_classification(image_base64, config)
    except Exception as e:
        return f"Error classifying image: {str(e)}\n{traceback.format_exc()}"


def analyze_latex_image(image_base64: str) -> str:
    """Analyze a LaTeX image using VLM.
    
    Args:
        image_base64: Base64 encoded image
    
    Returns:
        VLM analysis result for LaTeX
    """
    try:
        config = get_config()
        return get_latex_vision_feedback(image_base64, config)
    except Exception as e:
        return f"Error analyzing LaTeX image: {str(e)}\n{traceback.format_exc()}"



@mcp.tool(
    name="analyze_pdf_vlm",
    description="Analyze a file (pdf) using VLM.",
)
def analyze_pdf_vlm(file_path: Annotated[str, Field(description="ABSOLUTE Path to the file (supports pdf)")], 
                     prompt: Annotated[str, Field(description="Analysis instruction for the file, i.e., 'Describe the figure in detail.', 'Does the result contain any error?'")],
                     pdf_page: Annotated[Union[int, str], Field(description="Page number of the PDF to analyze (starts from 1), set to \"merge\" to analyze all pages at once but with lower precision.")] = "merge",
                     security_risk: Annotated[str, Field(description="Security risk level for the file, i.e., 'Low', 'Medium', 'High'")] = "Low") -> str:
    """Analyze a file (image or PDF) using VLM.
    
    Args:
        file_path: Path to the file (supports png, jpg, jpeg, pdf)
        prompt: Optional custom prompt for analysis
    
    Returns:
        VLM analysis result
    """
    config = get_config()
    if file_path.startswith("/workspace"):
        file_path = file_path.replace("/workspace", os.path.join(config.save_path, "workspace"))
    
    logger.info(f"MCP analyze_image_vlm: Analyzing file: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if pdf_page != "merge":
        try:
            pdf_page = int(pdf_page)
        except ValueError:
            pass
    
    if ext in ['.pdf']:
        # Handle PDF file
        if isinstance(pdf_page, int):
            # Analyze specific page
            page_images = get_fig_base64([file_path])
            if pdf_page > 0 and pdf_page <= len(page_images):
                fig, fig_base64 = page_images[pdf_page - 1]
                page_prompt = f"Page {pdf_page}: {prompt}" if prompt else f"Analyze page {pdf_page} of the PDF."
                return analyze_image(fig_base64, page_prompt)
            else:
                return f"Error: Page number {pdf_page} is out of range. PDF has {len(page_images)} pages, page number starts from 1."
        elif pdf_page == "merge":
            # Merge all pages and analyze
            page_images = get_fig_base64([file_path], merge_pdf=True)
            if page_images:
                fig, fig_base64 = page_images[0]
                merge_prompt = f"Analyze the merged PDF pages. {prompt}" if prompt else "Analyze the merged PDF pages."
                return analyze_image(fig_base64, merge_prompt)
            else:
                return f"Error: Failed to merge PDF pages."
        else:
            return "Error: Invalid pdf_page value. Please provide a valid page number or 'merge'."
    else:
        return f"Error: Unsupported file format {ext}. Supported formats: pdf"


@mcp.tool(
    name="analyze_image_vlm",
    description="Analyze a file (png, jpg, jpeg) using VLM.",
)
def analyze_image_vlm(file_path: Annotated[str, Field(description="ABSOLUTE Path to the file (supports png, jpg, jpeg, pdf)")], 
                     prompt: Annotated[str, Field(description="Analysis instruction for the file, i.e., 'Describe the figure in detail.', 'Does the result contain any error?'")],
                     security_risk: Annotated[str, Field(description="Security risk level for the file, i.e., 'Low', 'Medium', 'High'")]) -> str:
    """Analyze a file (image or PDF) using VLM.
    
    Args:
        file_path: Path to the file (supports png, jpg, jpeg, pdf)
        prompt: Optional custom prompt for analysis
    
    Returns:
        VLM analysis result
    """
    config = get_config()
    if file_path.startswith("/workspace"):
        file_path = file_path.replace("/workspace", os.path.join(config.save_path, "workspace"))
    
    logger.info(f"MCP analyze_image_vlm: Analyzing file: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.png', '.jpg', '.jpeg']:
        # Handle PDF file
        page_images = get_fig_base64([file_path])
        if len(page_images) >= 1:
            fig, fig_base64 = page_images[0]
            # Single page PDF, analyze directly
            return analyze_image(fig_base64, prompt)
        else:
            return f"Reading {file_path} failed. Please check the file format."
    else:
        return f"Error: Unsupported file format {ext}. Supported formats: png, jpg, jpeg"


def run_server(config: Union[Config, str], port: int = 9077):
    """Run the VLM MCP server with the provided config.
    
    Args:
        config: Config object or path to the configuration file
        port: Port number to run the server on (default: 9077)
    """
    if isinstance(config, Config):
        config = config
    else:
        config = Config.from_toml(config)
    set_config(config)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    logger.info(f"VLM MCP server running on port {port}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VLM MCP Server")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to the configuration file")
    parser.add_argument("--port", type=int, default=9077,
                        help="Port number to run the server on (default: 9077)")
    args = parser.parse_args()
    run_server(args.config)
