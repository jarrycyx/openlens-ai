# Keyword Search MCP Server
# This server provides MCP tools for keyword search functionality
import os
import re
import argparse
from typing import List, Dict, Optional, Annotated
from pydantic import Field
from loguru import logger
from fastmcp import FastMCP

from ...utils.config import Config

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
mcp = FastMCP("keyword_search_server")


def search_files_by_keyword(
    keyword: str,
    folders: List[str],
    file_extensions: List[str] = [".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"],
    context_lines: int = 3,
    max_results: int = 50
) -> List[Dict]:
    """Search for a keyword in files within specified folders.
    
    Args:
        keyword: Keyword to search for in files
        folders: List of folders to search in
        file_extensions: List of file extensions to search in
        context_lines: Number of lines to include before and after the matched line
        max_results: Maximum number of results to return
    
    Returns:
        List of dictionaries containing search results
    """
    results = []
    
    # Compile regex pattern for efficient matching
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    
    for folder in folders:
        if not os.path.exists(folder):
            logger.warning(f"Folder does not exist: {folder}")
            continue
            
        for root, _, files in os.walk(folder):
            for file in files:
                # Check if file has one of the specified extensions
                if any(file.endswith(ext) for ext in file_extensions):
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
                            if len(results) >= max_results:
                                return results
    
    return results


@mcp.tool(
    name="keyword_search",
    description="Search for a keyword in files within specified folders and return the matching chunks with context.",
)
def keyword_search(
    keyword: Annotated[str, Field(description="Keyword to search for in files")],
    folders: Annotated[List[str], Field(description="List of folders to search in")],
    file_extensions: Annotated[List[str], Field(default=[".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"], description="List of file extensions to search in")],
    context_lines: Annotated[int, Field(default=3, description="Number of lines to include before and after the matched line")],
    max_results: Annotated[int, Field(default=50, description="Maximum number of results to return")]
) -> List[Dict]:
    """Search for a keyword in files within specified folders.
    
    Args:
        keyword: Keyword to search for in files
        folders: List of folders to search in
        file_extensions: List of file extensions to search in
        context_lines: Number of lines to include before and after the matched line
        max_results: Maximum number of results to return
    
    Returns:
        List of dictionaries containing search results
    """
    logger.info(f"Keyword search: keyword='{keyword}', folders={folders}")
    return search_files_by_keyword(
        keyword=keyword,
        folders=folders,
        file_extensions=file_extensions,
        context_lines=context_lines,
        max_results=max_results
    )


def run_server(config):
    """Run the keyword search MCP server with the provided config.
    
    Args:
        config: Config object or path to the configuration file
    """
    if isinstance(config, Config):
        config = config
    else:
        config = Config.from_toml(config)
    set_config(config)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9078)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyword Search MCP Server")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to the configuration file")
    args = parser.parse_args()
    run_server(args.config)
