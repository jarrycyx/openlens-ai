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
import cairosvg
import numpy as np

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
from ..utils.vision_feedback import get_fig_base64, call_vlm_with_prompt, convert_svg_to_png
from ..tools.openhands_adaptor import run_openhands_prompt

from file1agent.file_manager import FileManager

# Prompt templates for the chart artist workflow
DIRECT_SVG_GENERATION_PROMPT = """Please analyze this image and create a complete SVG code that recreates the diagram directly.

Requirements:
1. Create a complete SVG code that recreates the diagram shown in the image
2. The SVG should include all elements, text, labels, and connections from the original image
3. Use appropriate colors to match the original diagram
4. Ensure the layout is clear and easy to follow
5. The SVG should be well-structured and properly formatted
6. Include proper dimensions and viewBox for the SVG
7. The SVG should be complete and ready to use

Please return only the complete SVG code without any additional explanations and without markdown elements like ```svg``` or ``````.
"""


FIX_SVG_PROMPT = """
Please analyze this SVG code and fix the issues.
Previous Feedback:
{feedback}

Please address these issues in your new SVG generation by adjusting locations, colors, shapes, sizes, and connections.
Please return only the complete SVG code without any additional explanations and without markdown elements like ```svg``` or ``````.
Never return SVG examples, just fix and return the complete SVG code.
"""

IMAGE_COMPARISON_PROMPT = """Please compare these two images side by side and provide a detailed analysis:

Left image: Original diagram
Right image: Generated SVG diagram

Please analyze the following to provide a detailed steps to improve the SVG diagram to better match the original diagram.
1. Overall structure and layout similarities/differences
2. Missing or extra elements in the generated version
3. Text and label accuracy
4. Visual styling differences (colors, shapes, sizes)
5. Connection and flow accuracy
6. Specific suggestions for improving the SVG version to better match the original

Response example:
1. Change the size of the box surronding the text "Data Science" from 100x100 to 150x150.
2. Delete the right angle arrow pointing to the "Data Science" text and convert to a corner arrow.

Please be very specific and provide actionable feedback for improving the SVG diagram.
"""

SVG_UPDATE_PROMPT = """Please analyze the original image and the comparison feedback provided, then create an updated SVG code that addresses all the issues mentioned in the feedback.

Comparison Feedback:
{comparison_feedback}

Please:
1. Address all the issues mentioned in the feedback
2. Create an improved SVG that better matches the original diagram
3. Fix any missing elements, text, or styling issues
4. Ensure the SVG structure is accurate
5. The SVG should be complete and ready to use
6. Return only the complete updated SVG code without any additional explanations and without markdown elements like ```svg``` or ``````.
"""


# Function to load prompts based on domain configuration
def load_prompt_file(config: Config, filename: str) -> str:
    """Load a prompt file from the appropriate domain directory."""
    domain_dir = config.domain if hasattr(config, "domain") and config.domain else "general"
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", domain_dir, filename)
    with open(prompt_path) as f:
        return f.read()


def get_svg_path(config: Config) -> str:
    """Get the path to the SVG file."""
    return os.path.join(config.save_path, "workspace", "chart_artist", "chart_artist_output.svg")


def get_llm_feedback(config: Config, prompt: str) -> str:
    
    # Initialize LLM
    llm = init_chat_model(
        config.llm.chat.model,
        base_url=config.llm.chat.base_url,
        model_provider="openai",
        openai_api_key=config.llm.chat.api_key,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    aimessage = llm.invoke([HumanMessage(content=prompt)])
    return aimessage.content

# Simple functions for chart artist workflow (replacing tool classes)
def generate_svg_from_image(config: Config, image_path: str, feedback: str = "", current_svg: str = "") -> str:
    """Generate SVG code directly from input image"""
    # Get base64 of the image
    fig_base64_list = get_fig_base64([image_path])
    if not fig_base64_list:
        return f"Error: Could not process image at {image_path}"
    image_base64 = fig_base64_list[0][1]


    def update_with_llm(all_feedback: str):
        prompt = FIX_SVG_PROMPT.format(feedback=all_feedback)
        logger.info(f"Calling LLM with prompt: {prompt}")
        svg_code = get_llm_feedback(config, prompt)
        svg_code = svg_code.strip().replace("```svg", "").replace("```", "")
        return svg_code

    def update_with_vlm(all_feedback: str):
        prompt = FIX_SVG_PROMPT.format(feedback=all_feedback)                
        # with open(get_svg_path(config), "w", encoding="utf-8") as f:
        #     f.write(svg_code)
        # run_openhands_prompt(prompt, config, add_file_summary=False)
        with open(get_svg_path(config), "r", encoding="utf-8") as f:
            svg_code = f.read()
        svg_code = call_vlm_with_prompt(config, image_base64, prompt)
        return svg_code
        
    
    try:
        # If svg does not exists, re-generate
        if not current_svg:
            prompt = DIRECT_SVG_GENERATION_PROMPT
            # Call VLM with the image and direct SVG generation prompt
            svg_code = call_vlm_with_prompt(config, image_base64, prompt)
            svg_code = svg_code.strip().replace("```svg", "").replace("```", "")
        else:
            svg_code = current_svg

        if svg_code:

            for try_idx in range(5):
                logger.info(f"Trying to generate PNG from SVG (try {try_idx+1})")

                try:
                    png_path = convert_svg_to_png(get_svg_path(config))
                    state["generated_png_path"] = png_path
                    if feedback:
                        # no error and feedback exists, use feedback from last node
                        svg_code = update_with_vlm(feedback)
                        feedback = ""
                    else:
                        # no error and no feedback, return svg directly
                        return svg_code
                except Exception as e:
                    logger.warning(f"Error converting SVG to PNG: {e}")
                    svg_code = update_with_llm(str(e))


        return svg_code

    except Exception as e:
        logger.error(f"Error in generate_svg_from_image: {e}")
        logger.error(traceback.format_exc())
        return f"Error generating SVG directly from image: {str(e)}"


# # Simple functions for chart artist workflow (replacing tool classes)
# def generate_svg_from_plan(config: Config, plan: str, feedback: str = "", current_svg: str = "") -> str:
#     """Generate SVG code directly from input image"""
#     try:

#         # Initialize LLM
#         llm = init_chat_model(
#             config.llm.chat.model,
#             base_url=config.llm.chat.base_url,
#             model_provider="openai",
#             openai_api_key=config.llm.chat.api_key,
#             extra_body={"chat_template_kwargs": {"enable_thinking": True}},
#         )
#         # If svg does not exists, re-generate
#         if (not current_svg):
#             # Get base64 of the image
#             desc_prompt = f"""
# I need to generate a diagram for the following plan:
# {plan}
# Please generate a detailed description for the diagram, including all included elements, their relationships, their locations, and any special considerations.
# """
#             image_desc = llm.invoke([HumanMessage(content=desc_prompt)])
#             generate_prompt = image_desc.content + DIRECT_SVG_GENERATION_PROMPT
#             svg_code = llm.invoke([HumanMessage(content=generate_prompt)])
#             svg_code = svg_code.content.strip().replace("```svg", "").replace("```", "")
#         else:
#             svg_code = current_svg

#         if svg_code:

#             with open(get_svg_path(config), "w", encoding="utf-8") as f:
#                 f.write(svg_code)

#             all_feedback = feedback
#             try:
#                 png_path = convert_svg_to_png(get_svg_path(config))
#                 state["generated_png_path"] = png_path
#             except Exception as e:
#                 logger.warning(f"Error converting SVG to PNG: {e}")
#                 all_feedback += str(e)

#             if all_feedback:
#                 prompt = FIX_SVG_PROMPT.format(feedback=all_feedback)
#                 run_openhands_prompt(prompt, config, add_file_summary=False)

#         with open(get_svg_path(config), "r", encoding="utf-8") as f:
#             svg_code = f.read()

#         return svg_code

#     except Exception as e:
#         logger.error(f"Error in generate_svg_from_image: {e}")
#         logger.error(traceback.format_exc())
#         return f"Error generating SVG directly from image: {str(e)}"


def compare_images(config: Config, merged_image_path: str) -> str:
    """Compare original image with generated SVG PNG"""
    try:
        # Get base64 of both images
        merged_base64_list = get_fig_base64([merged_image_path])
        merged_base64 = merged_base64_list[0][1]

        # Call VLM with the image and prompt
        comparison_result = call_vlm_with_prompt(config, merged_base64, IMAGE_COMPARISON_PROMPT)

        return comparison_result

    except Exception as e:
        logger.error(f"Error in compare_images: {e}")
        logger.error(traceback.format_exc())
        return f"Error comparing images: {str(e)}"


def merge_images(config: Config, original_image_path: str, generated_image_path: str) -> str:
    """Merge original image and generated SVG PNG side by side"""
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
        merged_img = Image.new("RGB", (merged_width, max_height), color="white")

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


def build_chart_artist(config: Config, file_manager: FileManager) -> StateGraph:
    """Build the chart artist workflow graph"""

    @track_node_call("chart_artist")
    def initialize_chart_artist(state: State) -> State:
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
    def generate_svg_node(state: State) -> State:
        """Generate SVG code directly from input image"""

        # Call the direct SVG generation function with error feedback
        svg_result = generate_svg_from_image(config, state["input_image_path"], "", state.get("current_svg", ""))
        # svg_result = generate_svg_from_plan(config, str(state["plan"]), state.get("svg_conversion_error", ""), state.get("current_svg", ""))

        # Save SVG code to file
        svg_path = get_svg_path(config)
        state["current_svg"] = svg_result
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_result)

        logger.info(f"Generated SVG code directly from image: {svg_path}")
        return state

    @track_node_call("chart_artist")
    def merge_images_node(state: State) -> State:
        """Merge original and generated images side by side"""

        try:
            png_path = convert_svg_to_png(get_svg_path(config))
            # Call the image merge function
            merge_result = merge_images(config, state["input_image_path"], png_path)
        except Exception as e:
            logger.warning(f"Error converting SVG to PNG for merging: {e}")
            merge_result = f"Error converting SVG to PNG for merging: {str(e)}"

        if merge_result.startswith("Error:"):
            logger.error(f"Image merging failed: {merge_result}")
        else:
            state["merged_image_path"] = merge_result
            logger.info(f"Images merged: {merge_result}")

        return state

    @track_node_call("chart_artist")
    def compare_images_node(state: State) -> State:
        """Compare original and generated images"""
        logger.debug("Comparing images")
        if "input_image_path" not in state or "generated_png_path" not in state:
            logger.error("Missing image paths for comparison")
            return state

        # Call the image comparison function with merged image
        if "merged_image_path" not in state:
            logger.error("No merged image available for comparison")
            return state

        comparison_result = compare_images(config, state["merged_image_path"])
        state["comparison_feedback"] = comparison_result

        logger.info(f"Image comparison completed: {comparison_result[:200]}...")
        return state

    @track_node_call("chart_artist")
    def update_svg_based_on_feedback_node(state: State) -> State:
        """Update SVG code based on original image and comparison feedback using VLM"""
        if "input_image_path" not in state or "comparison_feedback" not in state:
            logger.error("Missing input image path or feedback for update")
            return state

        # Call the SVG update function with original image and feedback
        updated_svg_result = generate_svg_from_image(
            config, state["input_image_path"], state.get("comparison_feedback", ""), state.get("current_svg", "")
        )
        state["current_svg"] = updated_svg_result

        # Update iteration counter
        state["chart_artist_iteration"] += 1

        # Save updated SVG code to file
        svg_path = get_svg_path(config)
        bak_svg_path = svg_path.replace(".svg", f"_bak_{state['chart_artist_iteration']}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(updated_svg_result)
        with open(bak_svg_path, "w", encoding="utf-8") as f:
            f.write(updated_svg_result)

        logger.info(f"Updated SVG code (iteration {state['chart_artist_iteration']}): {svg_path}")
        return state

    # Build the graph
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("initialize", initialize_chart_artist)
    graph_builder.add_node("generate_svg", generate_svg_node)
    graph_builder.add_node("merge_images", merge_images_node)
    graph_builder.add_node("compare_images", compare_images_node)
    graph_builder.add_node("update_svg", update_svg_based_on_feedback_node)

    # Add edges
    graph_builder.add_edge(START, "initialize")
    graph_builder.add_edge("initialize", "generate_svg")
    graph_builder.add_edge("generate_svg", "merge_images")
    graph_builder.add_edge("merge_images", "compare_images")

    # Conditional edge: either update SVG (if more iterations needed) or go to chatbot
    def should_continue_iteration(state: State):
        """Determine if we should continue iterating or finish"""
        if state.get("chart_artist_iteration", 0) >= 10:
            return "end"
        else:
            return "update_svg"

    graph_builder.add_conditional_edges(
        "compare_images", should_continue_iteration, {"update_svg": "update_svg", "end": END}
    )

    graph_builder.add_edge("update_svg", "merge_images")

    # Compile the graph
    graph = graph_builder.compile()

    return graph


if __name__ == "__main__":
    # Test's chart artist with a sample image
    config, state, last_subgraph, file_manager = load_state("outputs/test_chart_artist")
    config.workflow.e2e_test = False
    state["resume_node_call_stack"] = []
    state["node_call_stack"] = []
    state["current_svg"] = ""

    # Find the first existing image
    test_image = "outputs/test_chart_artist/workspace/flowchart.png"
    state["input_image_path"] = test_image
    logger.info(f"Using test image: {test_image}")

    # Build and run's chart artist graph
    try:
        graph = build_chart_artist(config, file_manager)

        try:
            graph_image = graph.get_graph(xray=True).draw_mermaid_png()
        except Exception as e:
            error_info = traceback.format_exc()
            logger.info(f"Failed to build mermaid graph: {e}")
            graph_image = graph.get_graph(xray=True).draw_png()
        # Save
        with open(os.path.join(config.save_path, "chart_graph_image.png"), "wb") as f:
            f.write(graph_image)

        result = graph.invoke(state, {"recursion_limit": 100})
        logger.info("Chart artist workflow completed")

        # Print results summary
        print("\n=== Chart Artist Workflow Results ===")
        if "current_svg" in result:
            print(f"Generated SVG code saved to: {get_svg_path(config)}")
        if "generated_png_path" in result:
            print(f"Generated PNG: {result['generated_png_path']}")
        if "merged_image_path" in result:
            print(f"Merged comparison image: {result['merged_image_path']}")
        if "comparison_feedback" in result:
            print(f"Comparison Feedback: {result['comparison_feedback'][:200]}...")

    except Exception as e:
        logger.error(f"Error running chart artist workflow: {e}")
        logger.error(traceback.format_exc())
