import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from .config import Config
from .vision_feedback import get_fig_base64, get_vision_classification


class FileSummary:
    """
    File inspection and summarization tool for checking file modification times and generating file trees with one-sentence summaries for each file.
    """
    
    def __init__(self, config: Config, root_dir: str = None):
        """
        Initialize the file inspection and summarization tool
        
        Args:
            config: Configuration object
            root_dir: Root directory to check, defaults to config.save_path
        """
        self.config = config
            
        self.file_cache_path = os.path.join(config.save_path, "file_summary_cache.json")
        self.file_cache = self._load_cache()
        
        # Initialize the large language model
        self.concluder_llm = init_chat_model(
            config.llm.chat.model,
            base_url=config.llm.chat.base_url,
            model_provider="openai",
            openai_api_key=config.llm.chat.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
    
    def _load_cache(self) -> Dict:
        """
        Load file cache
        
        Returns:
            File cache dictionary
        """
        if os.path.exists(self.file_cache_path):
            try:
                with open(self.file_cache_path, 'r', encoding='utf-8') as f:
                    file_summary_cache = json.load(f)
                    logger.debug(f"File summary cache loaded with {len(file_summary_cache)} entries: {str(file_summary_cache)}")
                    return file_summary_cache
            except Exception as e:
                logger.warning(f"Failed to load file summary cache: {e}")
        return {}
    
    def _save_cache(self):
        """
        Save file cache
        """
        try:
            cache_dir = os.path.dirname(self.file_cache_path)
            if cache_dir:  # Ensure directory path is not empty
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.file_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save file cache: {e}")
    
    def _get_file_mtime(self, file_path: str) -> float:
        """
        Get file modification time
        
        Args:
            file_path: File path
            
        Returns:
            File modification timestamp
        """
        try:
            return os.path.getmtime(file_path)
        except Exception as e:
            logger.warning(f"Failed to get file modification time {file_path}: {e}")
            return 0
    
    def _is_file_updated(self, file_path: str) -> bool:
        """
        Check if file has been updated
        
        Args:
            file_path: File path
            
        Returns:
            True if file is new or has been updated, otherwise False
        """
        abs_path = os.path.abspath(file_path)
        current_mtime = self._get_file_mtime(abs_path)
        
        # Check if file modification time has been updated
        cached_mtime = self.file_cache.get(abs_path, {}).get("mtime", 0)
        logger.debug(f"Check file {abs_path}, current mtime: {current_mtime}, cached mtime: {cached_mtime}")
        return current_mtime > cached_mtime
    
    def _read_file_content(self, file_path: str, max_size: int = 5000) -> str:
        """
        Read file content
        
        Args:
            file_path: File path
            max_size: Maximum number of bytes to read
            
        Returns:
            File content as string
        """
        try:
            # Check file extension to handle image and PDF files
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.png', '.jpg', '.jpeg', '.pdf']:
                for try_i in range(3):
                    try:
                        # 获取base64编码
                        base64_list = get_fig_base64([file_path])
                        if base64_list and len(base64_list) > 0:
                            # 获取第一个base64编码
                            base64_content = base64_list[0][1]
                            # 使用视觉模型进行分类和总结
                            summary = get_vision_classification(base64_content, self.config)
                            if summary:
                                return summary
                    except Exception as e:
                        logger.warning(f"Failed to process {file_ext} file {file_path}: {e}")
                return f"Failed to process {file_ext} file"
            
            # Try to read as text file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_size)
                    return content
            except UnicodeDecodeError:
                # If UTF-8 decoding fails, try other encodings
                try:
                    with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                        content = f.read(max_size)
                        return content
                except UnicodeDecodeError:
                    # If still fails, it's a binary file
                    logger.warning(f"{file_path} is a binary file, skipping")
                    return ""
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return f"Cannot read file: {str(e)}"
    
    def _summarize_file(self, file_path: str) -> str:
        """
        Use large language model to generate a one-sentence summary of the file
        
        Args:
            file_path: File path
            
        Returns:
            One-sentence summary of the file (no more than 200 characters)
        """
        for try_i in range(3):
            try:
                # Read file content, ensuring correct handling
                content = self._read_file_content(file_path)
                if not content:
                    return "Cannot read file content"
                
                # Check if this is a summary for an image or PDF file (already processed by vision model)
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in ['.png', '.jpg', '.jpeg', '.pdf']:
                    # For image and PDF files, _read_file_content already returns the vision model summary
                    return content
                
                # Limit content length to avoid excessive size
                if len(content) > 2000:
                    content = content[:2000] + "...[Content truncated]"
                
                file_name = os.path.basename(file_path)
                
                # Build a more detailed prompt including file path information
                prompt = f"Please summarize in one sentence (no more than 500 characters) the main function and content of the following file '{file_name}':\n\nFile Path: {file_path}\n\nFile Content:\n{content}\n\nSummary:"
                
                logger.debug(f"Summarizing file {file_path}...")
            
                # Wrap the prompt with HumanMessage
                message = HumanMessage(content=prompt)
                response = self.concluder_llm.invoke([message])
                summary = response.content.strip()
                    
                logger.info(f"Summary for {file_path}: {summary}")
                
                # Ensure summary does not exceed 500 characters
                if len(summary) > 500:
                    summary = summary[:500] + "..."
                    
                return summary
            except Exception as e:
                logger.warning(f"Failed to summarize file {file_path}: {e}")
        return f"Summary failed after {try_i} attempts"
    
    def _update_file_cache(self, file_path: str, summary: str):
        """
        Update file cache
        
        Args:
            file_path: File path
            summary: File summary
        """
        abs_path = os.path.abspath(file_path)
        self.file_cache[abs_path] = {
            "mtime": self._get_file_mtime(abs_path),
            "summary": summary
        }
    
    def _generate_file_tree(self, directory: str, prefix: str = "", is_last: bool = True, 
                           file_tree: List[str] = None, summaries: Dict[str, str] = None) -> Tuple[List[str], Dict[str, str]]:
        """
        Generate file tree and file summaries
        
        Args:
            directory: Directory path
            prefix: Prefix string
            is_last: Whether this is the last item
            file_tree: File tree list
            summaries: File summary dictionary
            
        Returns:
            Tuple of file tree list and file summary dictionary
        """
        if file_tree is None:
            file_tree = []
        if summaries is None:
            summaries = {}
            
        # Get all items in the directory, sorted by name
        items = sorted(os.listdir(directory))
        
        # Filter out hidden files and specific directories
        exclude_dirs = ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.vscode', '.idea']
        exclude_files = ['.DS_Store', 'Thumbs.db']
        
        items = [item for item in items if not item.startswith('.') and item not in exclude_dirs + exclude_files]
        
        for i, item in enumerate(items):
            item_path = os.path.join(directory, item)
            is_last_item = i == len(items) - 1
            
            # Add current item to file tree
            connector = "└── " if is_last_item else "├── "
            file_tree.append(f"{prefix}{connector}{item}")
            
            # If it's a file, check if summary needs to be updated
            if os.path.isfile(item_path):
                if self._is_file_updated(item_path):
                    summary = self._summarize_file(item_path)
                    self._update_file_cache(item_path, summary)
                else:
                    # Get summary from cache
                    abs_path = os.path.abspath(item_path)
                    summary = self.file_cache.get(abs_path, {}).get("summary", "")
                
                if summary:
                    # Use file tree line as key to ensure uniqueness
                    file_tree_line = f"{prefix}{connector}{item}"
                    summaries[file_tree_line] = summary
            
            # If it's a directory, process recursively
            elif os.path.isdir(item_path):
                extension = "    " if is_last_item else "│   "
                self._generate_file_tree(
                    item_path, 
                    prefix + extension, 
                    is_last_item, 
                    file_tree, 
                    summaries
                )
        
        return file_tree, summaries
    
    def get_file_tree_with_summaries(self) -> str:
        """
        Get file tree and one-sentence summary for each file
        
        Args:
            directory: Directory path
        
        Returns:
            String representation of file tree with one-sentence summaries for each file
        """
        
        # Generate file tree and summaries
        file_tree_workspace, summaries_workspace = self._generate_file_tree(os.path.join(self.config.save_path, "workspace"))
        file_tree_dataset, summaries_dataset = self._generate_file_tree(self.config.dataset_path)
        file_tree = file_tree_workspace + file_tree_dataset
        summaries = {**summaries_workspace, **summaries_dataset}
        
        
        # Save cache
        self._save_cache()
        
        # Build result string
        result = [f"File tree: {self.config.save_path}"]
        result.extend(file_tree)
        result.append("\nFile summaries:")
        
        # Add summaries in file tree order
        for line in file_tree:
            # 直接使用文件树行作为键查找总结
            if line in summaries:
                # Extract file name
                file_name = line.split("└── ")[-1].split("├── ")[-1].strip()
                # Add indentation to match file tree structure
                indent = line[:len(line) - len(file_name)]
                result.append(f"{indent}{file_name}: {summaries[line]}")
        
        return "\n".join(result)


# Example usage
if __name__ == "__main__":
    from .config import Config
    from ..state import load_state
    
    config, state, last_subgraph = load_state("outputs/pred_aki_dy_mimic_icu_csv")
    
    # Create file inspection and summarization tool
    file_summary = FileSummary(config)
    
    # Get file tree and summaries
    result = file_summary.get_file_tree_with_summaries()
    print(result)