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
# from html2image import Html2Image  # 不再需要 HTML 相关导入

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from ..tools.tool_utils import (
    route_by_tool_call,
)
from ..state import State
from ..chatbot import chatbot_with_context_manager
from ..state import load_state, track_node_call
from ..utils.config import Config
from ..utils.vision_feedback import get_fig_base64, call_vlm_with_prompt
from ..tools.openhands_adaptor import run_openhands_prompt

from file1agent.file_manager import FileManager

# Prompt templates for the chart artist workflow
IMAGE_DESCRIPTION_PROMPT = """Please analyze this image in detail and provide a comprehensive description including:
1. The type of diagram/chart/image (flowchart, graph, table, etc.)
2. All visible elements, text, labels, and their relationships
3. The structure and layout of the diagram
4. Any patterns, trends, or key information conveyed
5. Colors, shapes, and visual styling
6. Any technical details that would be important for recreating this diagram

Please be very detailed and specific, as this description will be used to recreate a similar diagram in PowerPoint using python-pptx."""

PYTHON_PPT_GENERATION_PROMPT = """Based on the following detailed image description, please create a complete Python script that uses the python-pptx library to recreate the diagram as a PowerPoint slide.

Image Description:
{image_description}

Requirements:
1. Create a complete Python script that uses python-pptx library
2. The script should create a new PowerPoint presentation with one slide
3. Use appropriate shapes, text boxes, and styling to match the original diagram
4. Include all text, labels, and connections from the original
5. Use appropriate colors to match the original diagram
6. Ensure the layout is clear and easy to follow
7. The script should save the PowerPoint file as '/workspace/chart_artist_output.pptx'
8. The script should be complete and ready to run

Please return only the complete Python code without any additional explanations and without markdown elements like ```python``` or ``````.
"""

IMAGE_COMPARISON_PROMPT = """Please compare these two images side by side and provide a detailed analysis:

Left image: Original diagram
Right image: Generated PowerPoint slide

Please analyze:
1. Overall structure and layout similarities/differences
2. Missing or extra elements in the generated version
3. Text and label accuracy
4. Visual styling differences (colors, shapes, sizes)
5. Connection and flow accuracy
6. Specific suggestions for improving the PowerPoint version to better match the original

Please be very specific and provide actionable feedback for improving the PowerPoint slide."""

PYTHON_PPT_UPDATE_PROMPT = """Please update the following Python script based on the comparison feedback provided:

Current Python Script:
{current_python}

Comparison Feedback:
{comparison_feedback}

Please:
1. Address all the issues mentioned in the feedback
2. Improve the Python script to better match the original diagram
3. Fix any missing elements, text, or styling issues
4. Ensure the PowerPoint structure is accurate
5. Maintain the complete Python script format
6. Return only the complete updated Python code without any additional explanations"""


# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, "domain") and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()


# Simple functions for chart artist workflow (replacing tool classes)
def describe_image(config: Config, image_path: str) -> str:
    """Generate detailed description of the input image"""
    try:
        # Get base64 of the image
        fig_base64_list = get_fig_base64([image_path])
        if not fig_base64_list:
            return f"Error: Could not process image at {image_path}"
        
        image_base64 = fig_base64_list[0][1]
        
        # Call VLM with the image and prompt
        description = call_vlm_with_prompt(config, image_base64, IMAGE_DESCRIPTION_PROMPT)
        return description
        
    except Exception as e:
        logger.error(f"Error in describe_image: {e}")
        logger.error(traceback.format_exc())
        return f"Error generating image description: {str(e)}"


def generate_python_ppt_code(config: Config, image_description: str) -> str:
    """Generate Python code for PPT creation based on image description"""
    try:
        # Initialize LLM
        llm = init_chat_model(
            config.llm.chat.model,
            base_url=config.llm.chat.base_url,
            model_provider="openai",
            openai_api_key=config.llm.chat.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
        
        # Create prompt for Python PPT generation
        prompt = PYTHON_PPT_GENERATION_PROMPT.format(image_description=image_description)
        
        # Call LLM to generate Python code
        response = llm.invoke([HumanMessage(content=prompt)])
        python_code = response.content
        python_code = python_code.strip().replace("```python", "").replace("```", "")
        
        return python_code
        
    except Exception as e:
        logger.error(f"Error in generate_python_ppt_code: {e}")
        logger.error(traceback.format_exc())
        return f"Error generating Python code: {str(e)}"


def execute_python_ppt_code(config: Config, python_code: str, file_manager: FileManager) -> str:
    """Execute Python code to generate PPT using OpenHands"""
    try:
        # Create output directory
        output_dir = os.path.join(config.save_path, "workspace", "chart_artist")
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare the prompt for OpenHands
        prompt = f"""
Please execute the following Python code to create a PowerPoint presentation:

{python_code}

After executing the code, please convert the PowerPoint slide to a PNG image and save it as '/workspace/chart_artist_output.png'.
You can use any method to convert PPT to PNG, such as using the python-pptx library with additional conversion tools or other appropriate methods.

Please ensure both the PPT file and PNG image are saved in the workspace directory.
"""
        
        # Execute the code using OpenHands
        result = run_openhands_prompt(prompt, config, file_manager=file_manager)
        
        # Check if the PPT was generated
        ppt_path = os.path.join(config.save_path, "workspace", "chart_artist_output.pptx")
        png_path = os.path.join(config.save_path, "workspace", "chart_artist_output.png")
        
        if os.path.exists(ppt_path):
            logger.info(f"PPT generated successfully: {ppt_path}")
            if os.path.exists(png_path):
                logger.info(f"PNG generated successfully: {png_path}")
                return png_path
            else:
                logger.warning(f"PPT generated but PNG conversion failed: {ppt_path}")
                return f"PPT generated but PNG conversion failed: {ppt_path}"
        else:
            logger.error(f"PPT generation failed. OpenHands result: {result}")
            return f"PPT generation failed. Check OpenHands logs for details."
        
    except Exception as e:
        logger.error(f"Error in execute_python_ppt_code: {e}")
        logger.error(traceback.format_exc())
        return f"Error executing Python code: {str(e)}"


def compare_images(config: Config, merged_image_path: str) -> str:
    """Compare original image with generated HTML PNG"""
    try:
        # Get base64 of both images
        merged_base64_list = get_fig_base64([merged_image_path])
        merged_base64 = merged_base64_list[0][1]
        
        # Initialize VLM
        from ..utils.vision_feedback import call_vlm_with_prompt
        
        # Call VLM with the image and prompt
        comparison_result = call_vlm_with_prompt(config, merged_base64, IMAGE_COMPARISON_PROMPT)
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"Error in compare_images: {e}")
        logger.error(traceback.format_exc())
        return f"Error comparing images: {str(e)}"


def merge_images(config: Config, original_image_path: str, generated_image_path: str) -> str:
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
        
        # Create a new image with width equal to the sum of both resized images
        merged_width = orig_resized.width + gen_resized.width
        merged_img = Image.new('RGB', (merged_width, max_height), color='white')
        
        # Paste the original image on the left
        merged_img.paste(orig_resized, (0, 0))
        
        # Paste the generated image on the right
        merged_img.paste(gen_resized, (orig_resized.width, 0))
        
        # Save the merged image
        output_dir = os.path.join(config.save_path, "workspace", "chart_artist")
        os.makedirs(output_dir, exist_ok=True)
        merged_image_path = os.path.join(output_dir, "comparison_merged.png")
        merged_img.save(merged_image_path)
        
        logger.info(f"Images merged successfully: {merged_image_path}")
        return merged_image_path
        
    except Exception as e:
        logger.error(f"Error in merge_images: {e}")
        logger.error(traceback.format_exc())
        return f"Error merging images: {str(e)}"


def update_python_ppt_based_on_feedback(config: Config, current_python: str, comparison_feedback: str) -> str:
    """Update Python PPT code based on comparison feedback"""
    try:
        # Initialize LLM
        llm = init_chat_model(
            config.llm.chat.model,
            base_url=config.llm.chat.base_url,
            model_provider="openai",
            openai_api_key=config.llm.chat.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
        
        # Create prompt for Python PPT update
        prompt = PYTHON_PPT_UPDATE_PROMPT.format(current_python=current_python, comparison_feedback=comparison_feedback)
        
        # Call LLM to update Python code
        response = llm.invoke([HumanMessage(content=prompt)])
        updated_python = response.content
        
        return updated_python
        
    except Exception as e:
        logger.error(f"Error in update_python_ppt_based_on_feedback: {e}")
        logger.error(traceback.format_exc())
        return f"Error updating Python code: {str(e)}"


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
    
    # 工具已重构为简单函数，无需初始化
    
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
        
        # Call the image description function
        description_result = describe_image(config, state["input_image_path"])
        state["image_description"] = description_result
        
        logger.info(f"Generated image description: {description_result[:200]}...")
        return state
    
    @track_node_call("chart_artist")
    def generate_python_ppt_node(state: State):
        """Generate Python PPT code based on image description"""
        if "image_description" not in state:
            logger.error("No image description available")
            return state
        
        # Call the Python PPT generation function
        python_result = generate_python_ppt_code(config, state["image_description"])
        
        # Save Python code to file
        output_dir = os.path.join(state["save_path"], "workspace", "chart_artist")
        python_path = os.path.join(output_dir, "chart_generator.py")
        state["current_python"] = python_path
        with open(python_path, "w") as f:
            f.write(python_result)
        
        logger.info(f"Generated Python PPT code: {python_path}")
        return state
    
    @track_node_call("chart_artist")
    def execute_python_ppt_node(state: State):
        """Execute Python PPT code using OpenHands"""
        if "current_python" not in state:
            logger.error("No Python code available")
            return state
        
        # Call the Python PPT execution function
        python_path_in_docker = state["current_python"].split("workspace")[1]
        python_path_in_docker = os.path.join("/workspace", python_path_in_docker)
        png_result = execute_python_ppt_code(config, python_path_in_docker, file_manager)
        
        if png_result.startswith("Error:") or "failed" in png_result.lower():
            logger.error(f"Python PPT execution failed: {png_result}")
            state["python_ppt_error"] = png_result
        else:
            state["generated_png_path"] = png_result
            logger.info(f"Python PPT executed successfully: {png_result}")
        
        return state
    
    @track_node_call("chart_artist")
    def merge_images_node(state: State):
        """Merge original and generated images side by side"""
        if "input_image_path" not in state or "generated_png_path" not in state:
            logger.error("Missing image paths for merging")
            return state
        
        # Call the image merge function
        merge_result = merge_images(config, state["input_image_path"], state["generated_png_path"])
        
        if merge_result.startswith("Error:"):
            logger.error(f"Image merging failed: {merge_result}")
            state["image_merge_error"] = merge_result
        else:
            state["merged_image_path"] = merge_result
            logger.info(f"Images merged: {merge_result}")
        
        return state
    
    @track_node_call("chart_artist")
    def compare_images_node(state: State):
        """Compare original and generated images"""
        if "input_image_path" not in state or "generated_png_path" not in state:
            logger.error("Missing image paths for comparison")
            return state
        
        # Call the image comparison function with merged image (comparing merged image with itself for quality assessment)
        if "merged_image_path" not in state:
            logger.error("No merged image available for comparison")
            return state
            
        comparison_result = compare_images(config, state["merged_image_path"])
        state["comparison_feedback"] = comparison_result
        
        logger.info(f"Image comparison completed: {comparison_result[:200]}...")
        return state
    
    @track_node_call("chart_artist")
    def update_python_ppt_based_on_feedback_node(state: State):
        """Update Python PPT code based on comparison feedback"""
        if "current_python" not in state or "comparison_feedback" not in state:
            logger.error("Missing Python code or feedback for update")
            return state
        
        # Call the Python PPT update function
        updated_python_result = update_python_ppt_based_on_feedback(config, state["current_python"], state["comparison_feedback"])
        state["current_python"] = updated_python_result
        
        # Update iteration counter
        state["chart_artist_iteration"] += 1
        
        # Save updated Python code to file
        output_dir = os.path.join(state["save_path"], "workspace", "chart_artist")
        python_path = os.path.join(output_dir, f"chart_generator_v{state['chart_artist_iteration']}.py")
        with open(python_path, "w") as f:
            f.write(updated_python_result)
        
        logger.info(f"Updated Python PPT code (iteration {state['chart_artist_iteration']}): {python_path}")
        return state
    
    @track_node_call("chart_artist")
    def chart_artist_chatbot(state: State):
        """Chatbot for final processing and user interaction"""
        # Prepare context for the chatbot
        context = {
            "image_description": state.get("image_description", ""),
            "comparison_feedback": state.get("comparison_feedback", ""),
            "merged_image_path": state.get("merged_image_path", ""),
            "current_python": state.get("current_python", ""),
            "chart_artist_iteration": state.get("chart_artist_iteration", 0),
        }
        
        # Add context to the prompt
        formatted_prompt = chart_artist_prompt.format(**context)
        
        # Create a simple message with the final results
        final_message = f"""
Chart Artist workflow completed!

## Workflow Summary
- Iteration count: {context['chart_artist_iteration']}
- Final Python code saved to: {os.path.join(config.save_path, "workspace", "chart_artist", "chart_generator.py")}
- Generated PPT file: {os.path.join(config.save_path, "workspace", "chart_artist_output.pptx")}
- Generated PNG image: {state.get("generated_png_path", "Not generated")}
- Merged comparison image: {context['merged_image_path']}

## Final Results
Based on the analysis of the input image and multiple iterative optimizations, a PowerPoint version of the flowchart has been generated. The Python script uses python-pptx library to create a professional-looking presentation that matches the original image.

## File Locations
- Python code: {os.path.join(config.save_path, "workspace", "chart_artist", "chart_generator.py")}
- PPT file: {os.path.join(config.save_path, "workspace", "chart_artist_output.pptx")}
- PNG image: {state.get("generated_png_path", "Not generated")}
- Comparison image: {context['merged_image_path']}
"""
        
        # Add the final message to the state
        state["messages"].append(HumanMessage(content=final_message))
        
        return state
    
    # Build the graph
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("initialize", initialize_chart_artist)
    graph_builder.add_node("describe_image", describe_input_image)
    graph_builder.add_node("generate_python", generate_python_ppt_node)
    graph_builder.add_node("execute_python", execute_python_ppt_node)
    graph_builder.add_node("merge_images", merge_images_node)
    graph_builder.add_node("compare_images", compare_images_node)
    graph_builder.add_node("update_python", update_python_ppt_based_on_feedback_node)
    graph_builder.add_node("chart_artist_chatbot", chart_artist_chatbot)
    
    # Add edges
    graph_builder.add_edge(START, "initialize")
    graph_builder.add_edge("initialize", "describe_image")
    graph_builder.add_edge("describe_image", "generate_python")
    graph_builder.add_edge("generate_python", "execute_python")
    graph_builder.add_edge("execute_python", "merge_images")
    graph_builder.add_edge("merge_images", "compare_images")
    
    # Conditional edge: either update Python (if more iterations needed) or go to chatbot
    def should_continue_iteration(state: State):
        """Determine if we should continue iterating or finish"""
        if state.get("chart_artist_iteration", 0) >= state.get("max_iterations", 3):
            return "chatbot"
        else:
            return "update_python"
    
    graph_builder.add_conditional_edges(
        "compare_images",
        should_continue_iteration,
        {"update_python": "update_python", "chatbot": "chart_artist_chatbot"}
    )
    
    graph_builder.add_edge("update_python", "execute_python")
    # chart_artist_chatbot不再需要调用工具，直接结束
    graph_builder.add_edge("chart_artist_chatbot", END)
    
    # Compile the graph
    graph = graph_builder.compile()
    
    return graph


if __name__ == "__main__":
    # Test's chart artist with a sample image
    config, state, last_subgraph, file_manager = load_state("outputs/test_chart_artist")
    config.workflow.e2e_test = False
    state["resume_node_call_stack"] = []
    
    # Find the first existing image
    test_image = "outputs/test_chart_artist/workspace/flowchart.png"
    state["input_image_path"] = test_image
    logger.info(f"Using test image: {test_image}")
    
    # Build and run's chart artist graph
    try:
        graph = build_chart_artist(config, file_manager)
        result = graph.invoke(state)
        logger.info("Chart artist workflow completed")
        
        # Print results summary
        print("\n=== Chart Artist Workflow Results ===")
        if "image_description" in result:
            print(f"Image Description: {result['image_description'][:200]}...")
        if "current_python" in result:
            print(f"Generated Python code saved to: {os.path.join(config.save_path, 'workspace', 'chart_artist', 'chart_generator.py')}")
        if "generated_png_path" in result:
            print(f"Generated PNG: {result['generated_png_path']}")
        if "merged_image_path" in result:
            print(f"Merged comparison image: {result['merged_image_path']}")
        if "comparison_feedback" in result:
            print(f"Comparison Feedback: {result['comparison_feedback'][:200]}...")
        
    except Exception as e:
        logger.error(f"Error running chart artist workflow: {e}")
        logger.error(traceback.format_exc())