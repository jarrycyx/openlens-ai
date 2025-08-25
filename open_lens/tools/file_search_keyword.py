"""File keyword search tool for LangGraph agents."""
import os
import re
from typing import List, Dict, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class FileSearchInput(BaseModel):
    """Input arguments for searching keywords in files"""
    keyword: str = Field(..., description="Keyword to search for in files")
    file_extensions: List[str] = Field(default=[".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"], 
                                      description="List of file extensions to search in")
    context_lines: int = Field(default=3, description="Number of lines to include before and after the matched line")


class FileSearchTool(BaseTool):
    """Tool for searching keywords in files within specified folders"""
    name: str = "file_search_tool"
    description: str = "Search for a keyword in files within specified folders and return the matching chunks with context"
    args_schema: Type[BaseModel] = FileSearchInput
    
    # Predefined folders to search in
    folders: List[str] = []
    
    def __init__(self, folders: List[str], file_extensions: List[str] = [".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folders = folders
        self.file_extensions = file_extensions

    def _run(self, keyword: str, context_lines: int = 10) -> List[Dict]:
        """Execute file search synchronously"""
        results = []
        
        # Compile regex pattern for efficient matching
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        for folder in self.folders:
            if not os.path.exists(folder):
                continue
                
            for root, _, files in os.walk(folder):
                for file in files:
                    # Check if file has one of the specified extensions
                    if any(file.endswith(ext) for ext in self.file_extensions):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                        except (UnicodeDecodeError, PermissionError):
                            # Skip binary files or files with permission issues
                            continue
                        
                        # Search for keyword in file
                        for i, line in enumerate(lines):
                            if pattern.search(line):
                                # Extract context around the match
                                start_line = max(0, i - context_lines)
                                end_line = min(len(lines), i + context_lines + 1)
                                
                                context = ''.join(lines[start_line:end_line])
                                
                                results.append({
                                    "file_path": file_path,
                                    "line_number": i + 1,
                                    "matched_line": line.strip(),
                                    "context": context
                                })
                                
                                # Limit results to avoid overwhelming output
                                if len(results) >= 50:
                                    return results
        
        return results
