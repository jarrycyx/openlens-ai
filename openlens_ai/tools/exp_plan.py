import sys, os
import subprocess
import traceback
import json
from typing import Optional, Type, Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self
from ..utils.config import Config

class PlanWriterToolInput(BaseModel):
    objective: str = Field(
        ...,
        description="The main objective of the experiment"
    )
    sub_tasks: List[str] = Field(
        ...,
        description="List of sub tasks to be performed in the experiment"
    )
    expected_result: str = Field(
        ...,
        description="Expected outcome of the experiment"
    )


class PlanWriterTool(BaseTool):
    name: str = "plan_writer_tool"
    description: str = "A tool that writes structured experimental plans to a fixed location."
    args_schema: Type[BaseModel] = PlanWriterToolInput
    config: Optional[dict] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    
    def _run(self, objective: str, sub_tasks: List[str], expected_result: str) -> str:
        """执行写入结构化实验计划的主要方法"""
        # 将结构化数据转换为字典
        plan_data = {
            "objective": objective,
            "sub_tasks": sub_tasks,
            "expected_result": expected_result
        }
        if len(sub_tasks) < 5:
            raise ValueError("Must have at least 5 subtasks.")
        for sub_task in sub_tasks:
            if len(sub_task) < 500:
                raise ValueError("Please provide a more detailed sub-task description.")
        
        workspace_dir = os.path.join(self.config.save_path, "workspace")
        # 写入JSON格式的计划文件
        with open(f"{workspace_dir}/plan.json", "w") as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
        plan_markdown = f"# Experiment Plan\n\nObjective: {objective}\n\nSub Tasks:\n"
        for i, task in enumerate(sub_tasks):
            plan_markdown += f"\n\n# SUBTASK{i+1:02d}\n {task}\n"
        plan_markdown += f"\nExpected Result: {expected_result}"
        with open(os.path.join(self.config.save_path, "plan.md"), "w") as f:
            f.write(plan_markdown)
            
        return f"Plan written successfully with objective: {objective}"


class PlanReaderToolInput(BaseModel):
    pass


class PlanReaderTool(BaseTool):
    name: str = "plan_reader_tool"
    description: str = "A tool that reads structured experimental plans from a fixed location."
    args_schema: Type[BaseModel] = PlanReaderToolInput
    config: Optional[dict] = None

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
    def _run(self) -> str:
        """读取结构化实验计划的主要方法"""
        try:
            workspace_dir = os.path.join(self.config.save_path, "workspace")
            with open(f"{workspace_dir}/plan.json", "r") as f:
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