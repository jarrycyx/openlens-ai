# Vector Search MCP Server
# This server provides MCP tools for vector search functionality
import os
import argparse
from typing import List, Dict, Optional, Annotated, Union
from pydantic import Field
from loguru import logger
from fastmcp import FastMCP
from langchain.schema import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from ...utils.config import Config
from ...chatbot import vector_search, perform_rerank, count_tokens_approximately

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
mcp = FastMCP("vector_search_server")


def search_files_by_vector(
    query: str,
    folders: List[str],
    file_extensions: List[str] = [".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"],
    token_cnt: int = 10000,
    max_results: int = 50
) -> List[Dict]:
    """Search for files using vector search based on a query.
    
    Args:
        query: Query string to search for relevant content
        folders: List of folders to search in
        file_extensions: List of file extensions to search in
        token_cnt: Maximum token count for the results
        max_results: Maximum number of results to return
    
    Returns:
        List of dictionaries containing search results
    """
    results = []
    
    # Collect all documents from the specified folders
    all_docs = []
    
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
                            content = f.read()
                            
                        # Create a document with the file content
                        doc = Document(page_content=content, metadata={"source": file_path})
                        all_docs.append(doc)
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or files with permission issues
                        continue
    
    if not all_docs:
        logger.warning("No documents found for vector search")
        return results
    
    # Get config for rerank model settings
    config = get_config()
    rerank_model = config.rerank.rerank_model
    rerank_api_key = config.rerank.rerank_api_key
    rerank_base_url = config.rerank.rerank_base_url
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
    all_splits = text_splitter.split_documents(all_docs)
    
    # Extract text content from documents
    all_docs_str = [doc.page_content for doc in all_splits]
    
    # Perform rerank using the existing function
    relevant_messages = perform_rerank(
        all_docs_str, 
        query, 
        token_cnt, 
        rerank_model, 
        rerank_api_key, 
        rerank_base_url
    )
    
    # Convert messages back to result format
    for message in relevant_messages:
        # Find the original document that contains this message
        for doc in all_splits:
            if message.content in doc.page_content:
                results.append({
                    "file_path": doc.metadata.get("source", "Unknown"),
                    "content": message.content,
                    "relevance_score": "High"  # We don't have direct access to scores
                })
                break
        
        # Limit results to avoid overwhelming output
        if len(results) >= max_results:
            break
    
    return results


@mcp.tool(
    name="vector_search",
    description="Search for files using vector search based on a query and return the most relevant chunks.",
)
def vector_search_tool(
    query: Annotated[str, Field(description="Query string to search for relevant content")],
    folders: Annotated[List[str], Field(description="List of folders to search in")],
    file_extensions: Annotated[List[str], Field(default=[".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"], description="List of file extensions to search in")],
    token_cnt: Annotated[int, Field(default=10000, description="Maximum token count for the results")],
    max_results: Annotated[int, Field(default=50, description="Maximum number of results to return")]
) -> List[Dict]:
    """Search for files using vector search based on a query.
    
    Args:
        query: Query string to search for relevant content
        folders: List of folders to search in
        file_extensions: List of file extensions to search in
        token_cnt: Maximum token count for the results
        max_results: Maximum number of results to return
    
    Returns:
        List of dictionaries containing search results
    """
    logger.info(f"Vector search: query='{query}', folders={folders}")
    return search_files_by_vector(
        query=query,
        folders=folders,
        file_extensions=file_extensions,
        token_cnt=token_cnt,
        max_results=max_results
    )


def run_server(config):
    """Run the vector search MCP server with the provided config.
    
    Args:
        config: Config object or path to the configuration file
    """
    if isinstance(config, Config):
        config = config
    else:
        config = Config.from_toml(config)
    set_config(config)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9079)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vector Search MCP Server")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to the configuration file")
    args = parser.parse_args()
    run_server(args.config)
