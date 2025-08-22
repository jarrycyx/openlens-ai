import sys, os
import subprocess
import traceback
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from langchain_core.tools import BaseTool
from ..utils.config import Config

class ReportWriterToolInput(BaseModel):
    data_report: str = Field(
        ...,
        description="Data report with markdown formatting."
    )
    file_name: str = Field(
        ...,
        description="The name of the file to write to. May not be used if the file name is fixed in advance."
    )


class ReportWriterTool(BaseTool):
    name: str = "report_writer_tool"
    description: str = "A tool that writes reports to a fixed locations."
    args_schema: Type[BaseModel] = ReportWriterToolInput
    config: Optional[dict] = None
    file_name: Optional[str] = ""

    def __init__(self, config: Config, file_name: str=""):
        super().__init__()
        self.config = config
        self.file_name = file_name
    def _run(self, data_report: str, file_name: str) -> str:
        """执行OpenHands操作的主要方法"""
        if self.file_name:
            file_name = self.file_name
        
        workspace_dir = os.path.join(self.config.save_path, "workspace")
        with open(os.path.join(workspace_dir, file_name), "w") as f:
            f.write(data_report)
        return data_report

class ReportReaderToolInput(BaseModel):
    file_name: str = Field(
        "data_report.md",
        description="The name of the file to read from. May not be used if the file name is fixed in advance."
    )


class ReportReaderTool(BaseTool):
    name: str = "data_report_reader_tool"
    description: str = "A tool that reads reports from a fixed location."
    args_schema: Type[BaseModel] = ReportReaderToolInput
    config: Optional[dict] = None
    file_name: str = ""

    def __init__(self, config: Config, file_name: str=""):
        super().__init__()
        self.config = config
        self.file_name = file_name
        
    def _run(self, file_name: str) -> str:
        """读取实验计划的主要方法"""
        if self.file_name:
            file_name = self.file_name
        try:
            workspace_dir = os.path.join(self.config.save_path, "workspace")
            with open(os.path.join(workspace_dir, file_name), "r") as f:
                data_report = f.read()
            return data_report
        except FileNotFoundError:
            return "No data report found. Please create a data report first."
        except Exception as e:
            return f"Error reading data report: {str(e)}"