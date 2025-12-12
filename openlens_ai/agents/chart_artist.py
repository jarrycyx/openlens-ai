import os
import json
import base64
import subprocess
import tempfile
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from PIL import Image
import io
from loguru import logger
import traceback

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool

from ..tools.tool_utils import (
    BasicToolNode,
    route_tools,
    route_by_tool_call,
)
from ..state import State
from ..chatbot import chatbot_with_context_manager
from ..state import load_state, track_node_call
from ..utils.config import Config
from ..utils.vision_feedback import get_fig_base64, call_vlm_with_prompt

from file1agent.file_manager import FileManager


# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, "domain") and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()


# Tool input schemas
class ImageDescriptionToolInput(BaseModel):
    image_path: str = Field(..., description="Path to the input image to be described")


class HTMLGenerationToolInput(BaseModel):
    image_description: str = Field(..., description="Detailed description of the image to recreate as HTML")


class HTMLToPNGToolInput(BaseModel):
    html_content: str = Field(..., description="HTML content to convert to PNG")


class ImageComparisonToolInput(BaseModel):
    original_image_path: str = Field(..., description="Path to the original image")
    generated_image_path: str = Field(..., description="Path to the generated PNG image")


class ImageMergeToolInput(BaseModel):
    original_image_path: str = Field(..., description="Path to the original image")
    generated_image_path: str = Field(..., description="Path to the generated PNG image")


class HTMLUpdateToolInput(BaseModel):
    current_html: str = Field(..., description="Current HTML content to be updated")
    comparison_feedback: str = Field(..., description="Feedback from image comparison")


# Tool classes for chart artist workflow
class ImageDescriptionTool(BaseTool):
    """Tool for generating detailed description of an input image using VLM"""
    name: str = "image_description_tool"
    description: str = "Generate detailed description of an input image using Vision Language Model"
    args_schema: Type[BaseModel] = ImageDescriptionToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, image_path: str) -> str:
        """Generate detailed description of the input image"""
        try:
            # Get base64 of the image
            fig_base64_list = get_fig_base64([image_path])
            if not fig_base64_list:
                return f"Error: Could not process image at {image_path}"
            
            image_base64 = fig_base64_list[0][1]
            
            # Create prompt for detailed description
            prompt = """Please analyze this image in detail and provide a comprehensive description including:
1. The type of diagram/chart/image (flowchart, graph, table, etc.)
2. All visible elements, text, labels, and their relationships
3. The structure and layout of the diagram
4. Any patterns, trends, or key information conveyed
5. Colors, shapes, and visual styling
6. Any technical details that would be important for recreating this diagram

Please be very detailed and specific, as this description will be used to recreate a similar diagram in HTML."""
            
            # Call VLM with the image and prompt
            description = call_vlm_with_prompt(image_base64, self.config, prompt)
            return description
            
        except Exception as e:
            logger.error(f"Error in ImageDescriptionTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating image description: {str(e)}"


class HTMLGenerationTool(BaseTool):
    """Tool for generating HTML flowchart based on image description"""
    name: str = "html_generation_tool"
    description: str = "Generate HTML flowchart based on image description"
    args_schema: Type[BaseModel] = HTMLGenerationToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, image_description: str) -> str:
        """Generate HTML flowchart based on image description"""
        try:
            # Initialize LLM
            llm = init_chat_model(
                self.config.llm.chat.model,
                base_url=self.config.llm.chat.base_url,
                model_provider="openai",
                openai_api_key=self.config.llm.chat.api_key,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}},
            )
            
            # Create prompt for HTML generation
            prompt = f"""Based on the following detailed image description, please create a complete HTML file that recreates the diagram as a flowchart using HTML, CSS, and possibly JavaScript.

Image Description:
{image_description}

Requirements:
1. Create a self-contained HTML file with inline CSS and JavaScript
2. Use modern HTML5 and CSS3 features
3. Make the flowchart responsive and visually appealing
4. Use appropriate colors, shapes, and styling to match the original diagram
5. Include all text, labels, and connections from the original
6. Ensure the layout is clear and easy to follow
7. Use libraries like Mermaid.js or similar if appropriate for flowchart creation
8. The HTML should be complete and ready to render in a browser

Please return only the complete HTML code without any additional explanations."""
            
            # Call LLM to generate HTML
            response = llm.invoke([HumanMessage(content=prompt)])
            html_content = response.content
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error in HTMLGenerationTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating HTML: {str(e)}"


class HTMLToPNGTool(BaseTool):
    """Tool for converting HTML to PNG image"""
    name: str = "html_to_png_tool"
    description: str = "Convert HTML content to PNG image"
    args_schema: Type[BaseModel] = HTMLToPNGToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, html_content: str) -> str:
        """Convert HTML content to PNG image"""
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name
            
            # Create output path for PNG
            output_dir = os.path.join(self.config.save_path, "workspace", "chart_artist")
            os.makedirs(output_dir, exist_ok=True)
            png_path = os.path.join(output_dir, "generated_flowchart.png")
            
            # Use wkhtmltoimage or similar tool to convert HTML to PNG
            # Try multiple methods
            success = False
            
            # Method 1: Try wkhtmltoimage
            try:
                cmd = ["wkhtmltoimage", "--format", "png", "--width", "1200", html_path, png_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(png_path):
                    success = True
                    logger.info("HTML to PNG conversion successful using wkhtmltoimage")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"wkhtmltoimage failed: {e}")
            
            # Method 2: Try puppeteer with Node.js
            if not success:
                try:
                    # Create a Node.js script for conversion
                    js_script = f"""
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {{
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setViewport({{ width: 1200, height: 800 }});
    await page.setContent(`{html_content.replace('`', '\\`')}`);
    await page.screenshot({{ path: '{png_path}', fullPage: true }});
    await browser.close();
}})();
"""
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                        f.write(js_script)
                        js_path = f.name
                    
                    cmd = ["node", js_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 and os.path.exists(png_path):
                        success = True
                        logger.info("HTML to PNG conversion successful using puppeteer")
                    
                    # Clean up JS file
                    os.unlink(js_path)
                    
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    logger.warning(f"Puppeteer conversion failed: {e}")
            
            # Method 3: Try using Selenium with Chrome/Chromium
            if not success:
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--window-size=1200,800")
                    
                    driver = webdriver.Chrome(options=chrome_options)
                    driver.get(f"file://{html_path}")
                    driver.save_screenshot(png_path)
                    driver.quit()
                    
                    if os.path.exists(png_path):
                        success = True
                        logger.info("HTML to PNG conversion successful using Selenium")
                        
                except Exception as e:
                    logger.warning(f"Selenium conversion failed: {e}")
            
            # Clean up temporary HTML file
            os.unlink(html_path)
            
            if success and os.path.exists(png_path):
                return png_path
            else:
                return f"Error: Could not convert HTML to PNG. All conversion methods failed."
                
        except Exception as e:
            logger.error(f"Error in HTMLToPNGTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error converting HTML to PNG: {str(e)}"


class ImageComparisonTool(BaseTool):
    """Tool for comparing original image with generated HTML PNG"""
    name: str = "image_comparison_tool"
    description: str = "Compare original image with generated HTML PNG and provide feedback"
    args_schema: Type[BaseModel] = ImageComparisonToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, original_image_path: str, generated_image_path: str) -> str:
        """Compare original image with generated HTML PNG"""
        try:
            # Get base64 of both images
            original_base64_list = get_fig_base64([original_image_path])
            generated_base64_list = get_fig_base64([generated_image_path])
            
            if not original_base64_list or not generated_base64_list:
                return "Error: Could not process one or both images for comparison"
            
            original_base64 = original_base64_list[0][1]
            generated_base64 = generated_base64_list[0][1]
            
            # Initialize VLM
            from ..utils.vision_feedback import get_vlm
            vlm = get_vlm(self.config)
            
            # Create prompt for comparison
            prompt = """Please compare these two images side by side and provide a detailed analysis:

Left image: Original diagram
Right image: Generated HTML flowchart

Please analyze:
1. Overall structure and layout similarities/differences
2. Missing or extra elements in the generated version
3. Text and label accuracy
4. Visual styling differences (colors, shapes, sizes)
5. Connection and flow accuracy
6. Specific suggestions for improving the HTML version to better match the original

Please be very specific and provide actionable feedback for improving the HTML flowchart."""
            
            # Create message with both images
            message = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{original_base64}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{generated_base64}"}},
                    ],
                }
            ]
            
            # Call VLM for comparison
            response = vlm.invoke(message)
            comparison_result = response.content
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error in ImageComparisonTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error comparing images: {str(e)}"


class ImageMergeTool(BaseTool):
    """Tool for merging original image and generated HTML PNG side by side"""
    name: str = "image_merge_tool"
    description: str = "Merge original image and generated HTML PNG side by side"
    args_schema: Type[BaseModel] = ImageMergeToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, original_image_path: str, generated_image_path: str) -> str:
        """Merge original image and generated HTML PNG side by side"""
        try:
            # Open both images
            original_img = Image.open(original_image_path)
            generated_img = Image.open(generated_image_path)
            
            # Get dimensions
            orig_width, orig_height = original_img.size
            gen_width, gen_height = generated_img.size
            
            # Determine the maximum height to resize both images to the same height
            max_height = max(orig_height, gen_height)
            
            # Resize images to have the same height
            orig_resized = original_img.resize((int(orig_width * max_height / orig_height), max_height), Image.LANCZOS)
            gen_resized = generated_img.resize((int(gen_width * max_height / gen_height), max_height), Image.LANCZOS)
            
            # Create a new image with width equal to sum of both resized images
            merged_width = orig_resized.width + gen_resized.width
            merged_img = Image.new('RGB', (merged_width, max_height), color='white')
            
            # Paste the original image on the left
            merged_img.paste(orig_resized, (0, 0))
            
            # Paste the generated image on the right
            merged_img.paste(gen_resized, (orig_resized.width, 0))
            
            # Save the merged image
            output_dir = os.path.join(self.config.save_path, "workspace", "chart_artist")
            os.makedirs(output_dir, exist_ok=True)
            merged_image_path = os.path.join(output_dir, "comparison_merged.png")
            merged_img.save(merged_image_path)
            
            logger.info(f"Images merged successfully: {merged_image_path}")
            return merged_image_path
            
        except Exception as e:
            logger.error(f"Error in ImageMergeTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error merging images: {str(e)}"


class HTMLUpdateTool(BaseTool):
    """Tool for updating HTML based on comparison feedback"""
    name: str = "html_update_tool"
    description: str = "Update HTML based on comparison feedback"
    args_schema: Type[BaseModel] = HTMLUpdateToolInput
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, current_html: str, comparison_feedback: str) -> str:
        """Update HTML based on comparison feedback"""
        try:
            # Initialize LLM
            llm = init_chat_model(
                self.config.llm.chat.model,
                base_url=self.config.llm.chat.base_url,
                model_provider="openai",
                openai_api_key=self.config.llm.chat.api_key,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}},
            )
            
            # Create prompt for HTML update
            prompt = f"""Please update the following HTML flowchart based on the comparison feedback provided:

Current HTML:
{current_html}

Comparison Feedback:
{comparison_feedback}

Please:
1. Address all the issues mentioned in the feedback
2. Improve the HTML to better match the original diagram
3. Fix any missing elements, text, or styling issues
4. Ensure the flowchart structure is accurate
5. Maintain the self-contained HTML format with inline CSS and JavaScript
6. Return only the complete updated HTML code without any additional explanations"""
            
            # Call LLM to update HTML
            response = llm.invoke([HumanMessage(content=prompt)])
            updated_html = response.content
            
            return updated_html
            
        except Exception as e:
            logger.error(f"Error in HTMLUpdateTool: {e}")
            logger.error(traceback.format_exc())
            return f"Error updating HTML: {str(e)}"


def build_chart_artist(config: Config, file_manager: FileManager) -> StateGraph:
    """Build the chart artist workflow graph"""
    
    # Load prompts
    chart_artist_prompt = load_prompt_file(config, "chart_artist.md")
    
    # Initialize LLM
    llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    
    # Initialize tools
    image_description_tool = ImageDescriptionTool(config)
    html_generation_tool = HTMLGenerationTool(config)
    html_to_png_tool = HTMLToPNGTool(config)
    image_comparison_tool = ImageComparisonTool(config)
    image_merge_tool = ImageMergeTool(config)
    html_update_tool = HTMLUpdateTool(config)
    
    tools = [
        image_description_tool,
        html_generation_tool,
        html_to_png_tool,
        image_comparison_tool,
        image_merge_tool,
        html_update_tool,
    ]
    
    llm_with_tools = llm.bind_tools(tools)
    
    @track_node_call("chart_artist")
    def initialize_chart_artist(state: State):
        """Initialize the chart artist workflow"""
        # Create output directory
        output_dir = os.path.join(state["save_path"], "workspace", "chart_artist")
        os.makedirs(output_dir, exist_ok=True)
        
        # Set initial state
        state["chart_artist_iteration"] = 0
        state["max_iterations"] = 3  # Maximum number of refinement iterations
        
        logger.info("Chart artist workflow initialized")
        return state
    
    @track_node_call("chart_artist")
    def describe_input_image(state: State):
        """Generate detailed description of the input image"""
        # Get the input image path from state or use a default
        if "input_image_path" not in state:
            # Use a default test image from workspace
            workspace_path = os.path.join(state["save_path"], "workspace")
            possible_images = [
                os.path.join(workspace_path, "subtask_01", "fig", "analysis_plots.jpg"),
                os.path.join(workspace_path, "subtask_01", "fig", "data_histogram.png"),
                os.path.join(workspace_path, "subtask_02", "fig", "analysis_plots.jpg"),
            ]
            
            # Find the first existing image
            for img_path in possible_images:
                if os.path.exists(img_path):
                    state["input_image_path"] = img_path
                    break
            else:
                return state  # No image found
        
        # Call the image description tool
        description_result = image_description_tool._run(state["input_image_path"])
        state["image_description"] = description_result
        
        logger.info(f"Generated image description: {description_result[:200]}...")
        return state
    
    @track_node_call("chart_artist")
    def generate_html_flowchart(state: State):
        """Generate HTML flowchart based on image description"""
        if "image_description" not in state:
            logger.error("No image description available")
            return state
        
        # Call the HTML generation tool
        html_result = html_generation_tool._run(state["image_description"])
        state["current_html"] = html_result
        
        # Save HTML to file
        output_dir = os.path.join(state["save_path"], "workspace", "chart_artist")
        html_path = os.path.join(output_dir, "flowchart.html")
        with open(html_path, "w") as f:
            f.write(html_result)
        
        logger.info(f"Generated HTML flowchart: {html_path}")
        return state
    
    @track_node_call("chart_artist")
    def convert_html_to_png(state: State):
        """Convert HTML to PNG"""
        if "current_html" not in state:
            logger.error("No HTML content available")
            return state
        
        # Call the HTML to PNG tool
        png_result = html_to_png_tool._run(state["current_html"])
        
        if png_result.startswith("Error:"):
            logger.error(f"HTML to PNG conversion failed: {png_result}")
            state["html_to_png_error"] = png_result
        else:
            state["generated_png_path"] = png_result
            logger.info(f"HTML converted to PNG: {png_result}")
        
        return state
    
    @track_node_call("chart_artist")
    def merge_images(state: State):
        """Merge original and generated images side by side"""
        if "input_image_path" not in state or "generated_png_path" not in state:
            logger.error("Missing image paths for merging")
            return state
        
        # Call the image merge tool
        merge_result = image_merge_tool._run(state["input_image_path"], state["generated_png_path"])
        
        if merge_result.startswith("Error:"):
            logger.error(f"Image merging failed: {merge_result}")
            state["image_merge_error"] = merge_result
        else:
            state["merged_image_path"] = merge_result
            logger.info(f"Images merged: {merge_result}")
        
        return state
    
    @track_node_call("chart_artist")
    def compare_images(state: State):
        """Compare original and generated images"""
        if "input_image_path" not in state or "generated_png_path" not in state:
            logger.error("Missing image paths for comparison")
            return state
        
        # Call the image comparison tool
        comparison_result = image_comparison_tool._run(state["input_image_path"], state["generated_png_path"])
        state["comparison_feedback"] = comparison_result
        
        logger.info(f"Image comparison completed: {comparison_result[:200]}...")
        return state
    
    @track_node_call("chart_artist")
    def update_html_based_on_feedback(state: State):
        """Update HTML based on comparison feedback"""
        if "current_html" not in state or "comparison_feedback" not in state:
            logger.error("Missing HTML or feedback for update")
            return state
        
        # Call the HTML update tool
        updated_html_result = html_update_tool._run(state["current_html"], state["comparison_feedback"])
        state["current_html"] = updated_html_result
        
        # Update iteration counter
        state["chart_artist_iteration"] += 1
        
        # Save updated HTML to file
        output_dir = os.path.join(state["save_path"], "workspace", "chart_artist")
        html_path = os.path.join(output_dir, f"flowchart_v{state['chart_artist_iteration']}.html")
        with open(html_path, "w") as f:
            f.write(updated_html_result)
        
        logger.info(f"Updated HTML flowchart (iteration {state['chart_artist_iteration']}): {html_path}")
        return state
    
    @track_node_call("chart_artist")
    def chart_artist_chatbot(state: State):
        """Chatbot for final processing and user interaction"""
        # Prepare context for the chatbot
        context = {
            "image_description": state.get("image_description", ""),
            "comparison_feedback": state.get("comparison_feedback", ""),
            "merged_image_path": state.get("merged_image_path", ""),
            "current_html": state.get("current_html", ""),
            "chart_artist_iteration": state.get("chart_artist_iteration", 0),
        }
        
        # Add context to the prompt
        formatted_prompt = chart_artist_prompt.format(**context)
        
        # Create chatbot with context
        this_chatbot = chatbot_with_context_manager(
            config, llm_with_tools, formatted_prompt, calling_subgraph="chart_artist"
        )
        state = this_chatbot(state)
        return state
    
    # Build the graph
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("initialize", initialize_chart_artist)
    graph_builder.add_node("describe_image", describe_input_image)
    graph_builder.add_node("generate_html", generate_html_flowchart)
    graph_builder.add_node("convert_to_png", convert_html_to_png)
    graph_builder.add_node("merge_images", merge_images)
    graph_builder.add_node("compare_images", compare_images)
    graph_builder.add_node("update_html", update_html_based_on_feedback)
    graph_builder.add_node("chart_artist_chatbot", chart_artist_chatbot)
    graph_builder.add_node("tools", BasicToolNode(tools, config))
    
    # Add edges
    graph_builder.add_edge(START, "initialize")
    graph_builder.add_edge("initialize", "describe_image")
    graph_builder.add_edge("describe_image", "generate_html")
    graph_builder.add_edge("generate_html", "convert_to_png")
    graph_builder.add_edge("convert_to_png", "merge_images")
    graph_builder.add_edge("merge_images", "compare_images")
    
    # Conditional edge: either update HTML (if more iterations needed) or go to chatbot
    def should_continue_iteration(state: State):
        """Determine if we should continue iterating or finish"""
        if state.get("chart_artist_iteration", 0) >= state.get("max_iterations", 3):
            return "chatbot"
        else:
            return "update_html"
    
    graph_builder.add_conditional_edges(
        "compare_images",
        should_continue_iteration,
        {"update_html": "update_html", "chatbot": "chart_artist_chatbot"}
    )
    
    graph_builder.add_edge("update_html", "convert_to_png")
    graph_builder.add_edge("chart_artist_chatbot", "tools")
    
    # Route based on tool calls
    graph_builder.add_conditional_edges(
        "tools",
        route_tools,
        {"tools": "chart_artist_chatbot", END: END}
    )
    
    # Compile the graph
    graph = graph_builder.compile()
    
    return graph


if __name__ == "__main__":
    # Test's chart artist with a sample image
    try:
        config, state, last_subgraph, file_manager = load_state("outputs/test_chart_artist")
    except:
        # If the state doesn't exist, create a minimal one
        from ..utils.config import Config
        config = Config.from_toml("tests/test_proj/config.toml")
        config.save_path = "outputs/test_chart_artist"
        os.makedirs(config.save_path, exist_ok=True)
        
        # Initialize state
        state = {
            "question": "Test chart artist workflow",
            "messages": [],
            "thread_id": "test_chart_artist",
            "save_path": config.save_path,
        }
        
        # Create a basic file manager
        from file1agent.file_manager import FileManager
        file_manager = FileManager(
            analyze_dir=os.path.join(config.save_path, "workspace"),
            config={
                "llm": {
                    "chat": dict(config.llm.chat),
                    "vision": dict(config.llm.vision),
                },
                "rerank": dict(config.rerank),
                "inclusion": {
                    "mode": "whitelist"
                }
            },
            realloc_log=False,
            backup_path=os.path.join(config.save_path, "backup", "deleted"),
            file_relationships_save_path=os.path.join(config.save_path, ".f1a_cache", "file_relationships.json"),
            summary_cache_path=os.path.join(config.save_path, ".f1a_cache", "file_summary_cache.json"),
        )
    
    # Set a test image path from workspace
    workspace_path = "tests/test_proj/workspace"
    possible_test_images = [
        os.path.join(workspace_path, "subtask_01", "fig", "analysis_plots.jpg"),
        os.path.join(workspace_path, "subtask_01", "fig", "data_histogram.png"),
        os.path.join(workspace_path, "subtask_02", "fig", "analysis_plots.jpg"),
        os.path.join(workspace_path, "subtask_02", "fig", "data_histogram.png"),
    ]
    
    # Find the first existing image
    test_image = None
    for img_path in possible_test_images:
        if os.path.exists(img_path):
            test_image = img_path
            break
    
    if test_image:
        state["input_image_path"] = test_image
        logger.info(f"Using test image: {test_image}")
        
        # Copy the test image to our workspace
        import shutil
        dest_dir = os.path.join(config.save_path, "workspace")
        os.makedirs(dest_dir, exist_ok=True)
        dest_image = os.path.join(dest_dir, os.path.basename(test_image))
        shutil.copy2(test_image, dest_image)
        state["input_image_path"] = dest_image  # Update to use the copied image
        logger.info(f"Copied test image to: {dest_image}")
    else:
        logger.error(f"No test image found in workspace. Checked paths: {possible_test_images}")
        # Create a simple test image for demonstration
        try:
            from PIL import Image, ImageDraw
            import numpy as np
            
            # Create a simple flowchart image
            width, height = 600, 400
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw simple flowchart elements
            # Box 1
            draw.rectangle([50, 50, 200, 100], outline='black', fill='lightblue')
            draw.text((100, 70), "Start", fill='black')
            
            # Box 2
            draw.rectangle([225, 50, 375, 100], outline='black', fill='lightgreen')
            draw.text((275, 70), "Process", fill='black')
            
            # Box 3
            draw.rectangle([400, 50, 550, 100], outline='black', fill='lightyellow')
            draw.text((450, 70), "End", fill='black')
            
            # Arrows
            draw.line([200, 75, 225, 75], fill='black', width=2)
            draw.line([375, 75, 400, 75], fill='black', width=2)
            
            # Save the test image
            dest_dir = os.path.join(config.save_path, "workspace")
            os.makedirs(dest_dir, exist_ok=True)
            test_image = os.path.join(dest_dir, "simple_flowchart.png")
            img.save(test_image)
            state["input_image_path"] = test_image
            logger.info(f"Created a simple test flowchart image: {test_image}")
        except Exception as e:
            logger.error(f"Failed to create test image: {e}")
            logger.error(traceback.format_exc())
    
    # Build and run's chart artist graph
    try:
        graph = build_chart_artist(config, file_manager)
        result = graph.invoke(state)
        logger.info("Chart artist workflow completed")
        
        # Print results summary
        print("\n=== Chart Artist Workflow Results ===")
        if "image_description" in result:
            print(f"Image Description: {result['image_description'][:200]}...")
        if "current_html" in result:
            print(f"Generated HTML saved to: {os.path.join(config.save_path, 'workspace', 'chart_artist', 'flowchart.html')}")
        if "generated_png_path" in result:
            print(f"Generated PNG: {result['generated_png_path']}")
        if "merged_image_path" in result:
            print(f"Merged comparison image: {result['merged_image_path']}")
        if "comparison_feedback" in result:
            print(f"Comparison Feedback: {result['comparison_feedback'][:200]}...")
        
    except Exception as e:
        logger.error(f"Error running chart artist workflow: {e}")
        logger.error(traceback.format_exc())
if __name__ == "__main__":
    # Test the chart artist with a sample image
    config, state, last_subgraph, file_manager = load_state("outputs/test_chart_artist")
    
    # Set a test image path
    workspace_path = os.path.join(config.save_path, "workspace")
    test_image = os.path.join(workspace_path, "Gemini_Generated_Image_7fm2lz7fm2lz7fm2.png")
    if os.path.exists(test_image):
        state["input_image_path"] = test_image
        logger.info(f"Using test image: {test_image}")
    else:
        logger.warning(f"Test image not found: {test_image}")
    
    # Build and run the chart artist graph
    graph = build_chart_artist(config, file_manager)
    result = graph.invoke(state)
    
    logger.info("Chart artist workflow completed")