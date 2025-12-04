import sys, os
import subprocess
import traceback
import json
from typing import Optional, Type, Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self
from loguru import logger

class PlanWriterToolInput(BaseModel):
    objective: str = Field(
        ...,
        description="The main objective of the experiment"
    )
    sub_tasks: List[str] = Field(
        ...,
        description="List of sub tasks to be performed in the experiment, must be a LIST OF STRINGS, make sure each string is detailed enough (at least 500 characters), and there should be at least 3 sub tasks."
    )
    expected_result: str = Field(
        ...,
        description="Expected outcome of the experiment"
    )


class PlanWriterTool(BaseTool):
    name: str = "plan_writer_tool"
    description: str = "A tool that writes structured experimental plans to a fixed location."
    args_schema: Type[BaseModel] = PlanWriterToolInput
    save_path: str = ""
    min_sub_tasks: int = 3

    def __init__(self, save_path: str, min_sub_tasks: int = 3):
        super().__init__()
        self.save_path = save_path
        self.min_sub_tasks = max(min_sub_tasks, min_sub_tasks)
        logger.info(f"Minimum number of subtasks for the experiment plan: {self.min_sub_tasks}")
    
    def _run(self, objective: str, sub_tasks: List[str], expected_result: str) -> str:
        """执行写入结构化实验计划的主要方法"""
        # 将结构化数据转换为字典
        plan_data = {
            "objective": objective,
            "sub_tasks": sub_tasks,
            "expected_result": expected_result
        }
        if len(sub_tasks) < self.min_sub_tasks:
            raise ValueError(f"Must have at least 3 subtasks. If the question is complex, may increase to 4 or 5 subtasks. Due to the complexity of the question, must have at least {self.min_sub_tasks} subtasks.")
        for sub_task in sub_tasks:
            if len(sub_task) < 500:
                raise ValueError("Please provide a more detailed sub-task description. Remeber: Argument sub_tasks must be a LIST OF STRINGS, make sure each string is detailed enough (at least 500 characters), and there should be at least 3 sub tasks")
        
        # 写入JSON格式的计划文件
        with open(os.path.join(self.save_path, "plan.json"), "w") as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
        plan_markdown = f"# Experiment Plan\n\nObjective: {objective}\n\nSub Tasks:\n"
        for i, task in enumerate(sub_tasks):
            plan_markdown += f"\n\n# SUBTASK{i+1:02d}\n {task}\n"
        plan_markdown += f"\nExpected Result: {expected_result}"
        with open(os.path.join(self.save_path, "plan.md"), "w") as f:
            f.write(plan_markdown)
            
        return f"Plan written successfully with objective: {objective}"


class PlanReaderToolInput(BaseModel):
    pass


class PlanReaderTool(BaseTool):
    name: str = "plan_reader_tool"
    description: str = "A tool that reads structured experimental plans from a fixed location."
    args_schema: Type[BaseModel] = PlanReaderToolInput
    save_path: str = ""

    def __init__(self, save_path: str):
        super().__init__()
        self.save_path = save_path
        
    def _run(self) -> str:
        """读取结构化实验计划的主要方法"""
        try:
            with open(os.path.join(self.save_path, "plan.json"), "r") as f:
                plan_data = json.load(f)
            return plan_data
        except FileNotFoundError:
            return "ERROR: No experimental plan found. Please create a plan first."
        except Exception as e:
            return f"ERROR: Error reading experimental plan: {str(e)}"
        
        

def subtask_route_tools(
    state,
):
    """
    """
    
    if state["current_subtask_index"] <= len(state["plan"]["sub_tasks"]):
        return "NEXT_TASK"
    return END