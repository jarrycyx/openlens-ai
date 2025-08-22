import os
import json
from typing import Annotated
from typing_extensions import TypedDict
import dotenv
from loguru import logger
import asyncio
import traceback
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
from langchain_core.messages.utils import count_tokens_approximately, get_buffer_string

from ..utils.frontend_utils import frontend_add_message, frontend_add_tool_call
from ..state import State
from ..utils.config import Config

dotenv.load_dotenv()


def route_tools(
    state,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """

    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


def route_by_tool_call(tool_name: str):
    """
    Creates a conditional edge function that checks if a specific tool was called.

    Args:
        tool_name: The name of the tool to check for

    Returns:
        A function that can be used in conditional_edge to route based on tool calls
    """

    def route_tool_check(state):
        """
        Route to END if the specified tool was called, otherwise return "RETURN_TO_LLM"
        """
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            # 如果来自工具的信息报错，或者最后一条不是工具信息，就直接返回llm
            if isinstance(messages[-1], ToolMessage):
                # if messages[-1].name == "tool_error":
                if "error" in messages[-1].status:
                    logger.warning(f"Tool error: {str(messages[-1])}")
                    return "RETURN_TO_LLM"
            else:
                logger.warning(f"Last message is not tool message: {str(messages[-1])}")
                return "RETURN_TO_LLM"

            if hasattr(messages[-1], "tool_calls") and len(messages[-1].tool_calls) > 0:
                ai_message = messages[-1]
            elif hasattr(messages[-2], "tool_calls") and len(messages[-2].tool_calls) > 0:
                ai_message = messages[-2]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")

        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            # Check if the specific tool was called
            for tool_call in ai_message.tool_calls:
                if tool_call.get("name") == tool_name:
                    logger.info(f"Tool call as expected: {tool_call}")
                    return END  # Tool was called, end the process
            return "RETURN_TO_LLM"  # Tool was not called, return to LLM
        return "RETURN_TO_LLM"  # No tool calls, return to LLM

    return route_tool_check


def route_by_file_existence(file_path: str):
    """
    Creates a conditional edge function that checks if a specific file exists in the workspace.

    Args:
        file_path: The path of the file to check for (relative to workspace)
        workspace: The workspace root directory path

    Returns:
        A function that can be used in conditional_edge to route based on file existence
    """

    def route_file_check(state):
        """
        Route to END if the specified file exists in workspace, otherwise return "no"
        """
        if os.path.exists(file_path):
            return "FILE_EXISTS"  # File exists, end the process
        return "FILE_NOT_FOUND"  # File does not exist, return to caller

    return route_file_check



def route_by_keywords(keywords: list):
    """
    Creates a conditional edge function that checks if any of the specified keywords are present in the last message.

    Args:
        keywords: A list of keywords to check for

    Returns:
        A function that can be used in conditional_edge to route based on keyword presence
    """

    def route_keyword_check(state: State):
        """
        Route to END if any of the specified keywords are present in the last message, otherwise return "no"
        """
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            return "NONE"  # Keyword not found, return to caller
        for keyword in keywords:
            if keyword in ai_message.content:
                logger.info(f"Keyword found: {keyword}")
                return keyword  # Keyword found, end the process

        return "NONE"  # Keyword not found, return to caller

    return route_keyword_check


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list, config: Config) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.config = config
        
        
    def save_tool_call(self, tool_message: ToolMessage):
        
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join(self.config.save_path, "tool_calls", f"{time_stamp}_{tool_message.name}.txt")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            f.write(get_buffer_string([tool_message]))

    def __call__(self, state: State):

        tool_call = {"name": "none"}
        try:
            if messages := state.get("messages", []):
                message = messages[-1]
            else:
                raise ValueError("No message found in input")
            outputs = []
            for tool_call in message.tool_calls:
                this_tool = self.tools_by_name[tool_call["name"]]
                frontend_add_tool_call(tool_call["name"], tool_call["args"])
                # 如果是异步函数，那就阻塞执行
                if asyncio.iscoroutine(this_tool):
                    logger.info(f"Waiting for async tool call: {tool_call}")
                    tool_result = asyncio.run(this_tool.invoke(tool_call["args"]))
                else:
                    logger.info(f"Tool call: {tool_call}")
                    tool_result = this_tool.invoke(tool_call["args"])
                
                logger.info(f"Tool result: {tool_result}")
                outputs.append(
                    ToolMessage(
                        content=json.dumps(tool_result),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                        status="success"
                    )
                )
                self.save_tool_call(outputs[-1])
                # frontend_add_message(outputs[-1])
                
            state["messages"] += outputs
            state["last_tool_call"] = tool_call["name"]
            return state
        except Exception as e:
            logger.warning(f"Error running tool: {e}")
            logger.warning(traceback.format_exc())
            # traceback.print_exc()
            state["messages"] += [
                    ToolMessage(
                        content=str(e),
                        name=tool_call["name"],
                        tool_call_id="",
                        status="error"
                    )
                ]
            self.save_tool_call(state["messages"][-1])
            frontend_add_message(state["messages"][-1])
            state["last_tool_call"] = tool_call["name"]
            return state
