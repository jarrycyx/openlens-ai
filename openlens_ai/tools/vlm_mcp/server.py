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

from ...utils.vision_feedback import get_vlm, get_vision_feedback, get_vision_classification, get_latex_vision_feedback, get_fig_base64
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
        
        # If custom prompt is provided, use it with the default vision feedback function
        if prompt:
            # Create a custom prompt by modifying the default one
            vlm = get_vlm(config)
            
            from langchain_core.messages import HumanMessage
            logger.info(f"MCP analyze_image: prompt is {prompt}")
            # Try both formatters
            for formatter in [
                lambda p, img: HumanMessage(content=[
                    {"type": "text", "text": p},
                    {"type": "image_url", "image_url": {"url": img}}
                ]),
                lambda p, img: HumanMessage(content=[
                    {"type": "text", "text": p},
                    {"type": "image", "source_type": "base64", "data": img, "mime_type": "image/jpeg"}
                ])
            ]:
                try:
                    message = formatter(prompt, image_base64)
                    response = vlm.invoke([message])
                    return response.content
                except Exception as e:
                    logger.warning(f"Error with formatter: {e}")
                    continue
            
            return "Error: Failed to process image with VLM"
        else:
            # Use the default vision feedback function
            return get_vision_feedback(image_base64, config)
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
    name="analyze_file_vlm",
    description="Analyze a file (image or PDF) using VLM.",
)
def analyze_file_vlm(file_path: Annotated[str, Field(description="ABSOLUTE Path to the file (supports png, jpg, jpeg, pdf)")], 
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
    
    logger.info(f"MCP analyze_file_vlm: Analyzing file: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.png', '.jpg', '.jpeg', '.pdf']:
        # Handle PDF file
        page_images = get_fig_base64([file_path])
        if len(page_images) == 1:
            fig, fig_base64 = page_images[0]
            # Single page PDF, analyze directly
            return analyze_image(fig_base64, prompt)
        
        # Analyze each page and combine results
        results = []
        for i, (fig, fig_base64) in enumerate(page_images):
            page_prompt = f"Analyze page {i+1} of the PDF."
            if prompt:
                page_prompt = f"Page {i+1}: {prompt}"
            
            result = analyze_image(fig_base64, page_prompt)
            results.append(f"--- Page {i+1} ---\n{result}")
        
        return "\n\n".join(results)
    else:
        return f"Error: Unsupported file format {ext}. Supported formats: png, jpg, jpeg, pdf"


def run_server(config: Union[Config, str]):
    """Run the VLM MCP server with the provided config.
    
    Args:
        config: Config object or path to the configuration file
    """
    if isinstance(config, Config):
        config = config
    else:
        config = Config.from_toml(config)
    set_config(config)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9077)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VLM MCP Server")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to the configuration file")
    args = parser.parse_args()
    run_server(args.config)
