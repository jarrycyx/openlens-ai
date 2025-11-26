import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from loguru import logger
import tqdm
import numpy as np
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from .config import Config
from .file_summary import FileSummary
from .embedding import perform_rerank
from ..state import load_state

class FileManager:
    """
    File management tool for detecting duplicate files and simulated data files.
    Uses file summaries to identify potential duplicates and LLM to verify.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the file management tool
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.file_summary = FileSummary(config)
        self.file_summary.get_file_tree_with_summaries()
        
        # Initialize the large language model for detailed comparison
        self.comparison_llm = init_chat_model(
            config.llm.chat.model,
            base_url=config.llm.chat.base_url,
            model_provider="openai",
            openai_api_key=config.llm.chat.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
        
        # Initialize the large language model for simulated data detection
        self.detection_llm = init_chat_model(
            config.llm.chat.model,
            base_url=config.llm.chat.base_url,
            model_provider="openai",
            openai_api_key=config.llm.chat.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
        
        # Track deleted files
        self.deleted_files = []
        
        # Track duplicate file pairs
        self.duplicate_pairs = []
    
    def _read_file_content(self, file_path: str, max_size: int = 10000) -> str:
        """
        Read file content for detailed comparison
        
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
                # For image and PDF files, we'll use the summary from FileSummary
                return f"Image/PDF file: {self.file_summary.file_cache[file_path]}"
            
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
                    return f"Binary file: {file_path}"
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return f"Cannot read file: {str(e)}"
    
    def _compare_files_with_llm(self, file1_path: str, file2_path: str) -> bool:
        """
        Use LLM to compare two files and determine if they are duplicates
        
        Args:
            file1_path: Path to the first file
            file2_path: Path to the second file
            
        Returns:
            True if files are duplicates, False otherwise
        """
        try:
            # Read file contents
            content1 = self._read_file_content(file1_path)
            content2 = self._read_file_content(file2_path)
            
            file1_name = os.path.basename(file1_path)
            file2_name = os.path.basename(file2_path)
            
            # Build comparison prompt
            prompt = f"""
Please compare the following two files and determine if they are duplicates or implement different versions of the same functionality (e.g., one is the improved/optimized version of the other).

File 1: {file1_name}
Path: {file1_path}
Content:
{content1}

File 2: {file2_name}
Path: {file2_path}
Content:
{content2}

Please respond with concise reasons (less than 100 words) and then "Yes" if the files are duplicates or implement different versions of the same functionality, or "No" if they are different.

Example:
Reason: File 2 is the improved version of File 1, with additional features and optimizations.
Result: Yes
"""
            
            # Wrap the prompt with HumanMessage
            message = HumanMessage(content=prompt)
            response = self.comparison_llm.invoke([message])
            result = response.content.strip().upper()
            
            logger.debug(f"LLM comparison result for {file1_name} and {file2_name}: {result}")
            
            return (("Yes" in result) or ("YES" in result))
        except Exception as e:
            logger.warning(f"Failed to compare files {file1_path} and {file2_path}: {e}")
            return False
    
    def _detect_simulated_data(self, file_path: str) -> bool:
        """
        Use LLM to detect if a file contains simulated or fake data
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file contains simulated/fake data, False otherwise
        """
        try:
            # Read file content
            content = self._read_file_content(file_path)
            
            file_name = os.path.basename(file_path)
            
            # Build detection prompt
            prompt = f"""
Please analyze the following file and determine if it contains simulated, fake, or mock data.

File: {file_name}
Path: {file_path}
Content:
{content}

Please respond with concise reasons (less than 100 words) and then "Yes" if the file contains simulated, fake, mock data, or "No" if it contains real data.

Example:
Reason: The line "data = np.random.rand(100, 100)" generates random data for testing purposes.
Result: Yes
"""
            
            # Wrap the prompt with HumanMessage
            message = HumanMessage(content=prompt)
            response = self.detection_llm.invoke([message])
            result = response.content.strip().upper()
            
            logger.debug(f"Simulated data detection result for {file_name}: {result}")
            
            return (("Yes" in result) or ("YES" in result))
        except Exception as e:
            logger.warning(f"Failed to detect simulated data in {file_path}: {e}")
            return False
    
    def _delete_file(self, file_path: str, reason: str):
        """
        Move a file to backup directory with timestamp and record the reason
        
        Args:
            file_path: Path to the file to delete
            reason: Reason for deletion
        """
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(self.config.save_path, "backup", "deleted")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Get file name and extension
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1]
            base_name = os.path.splitext(file_name)[0]
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create new file name with timestamp
            new_file_name = f"{timestamp}_{base_name}{file_ext}"
            new_file_path = os.path.join(backup_dir, new_file_name)
            
            # Move file to backup directory
            os.rename(file_path, new_file_path)
            
            self.deleted_files.append({
                "path": file_path,
                "backup_path": new_file_path,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Moved file {os.path.relpath(file_path, self.config.save_path)} to {os.path.relpath(new_file_path, self.config.save_path)}: {reason}")
        except Exception as e:
            logger.warning(f"Failed to move file {file_path}: {e}")
    
    def _get_file_summaries(self) -> Dict[str, str]:
        """
        Get file summaries from FileSummary for code files only
        
        Returns:
            Dictionary mapping file paths to their summaries
        """
        # Get file tree with summaries
        self.file_summary.get_file_tree_with_summaries()
        result = self.file_summary.file_cache
        
        summaries = {}
        for path in result:
            summaries[path] = result[path]["summary"]
        
        return summaries
    
    def _find_duplicates_with_reranker(self, summaries: Dict[str, str]) -> List[Tuple[str, str]]:
        """
        Use reranker to find potential duplicate files based on summaries
        Only compares files within the same subdirectory
        
        Args:
            summaries: Dictionary mapping file paths to their summaries
            
        Returns:
            List of tuples containing paths to potential duplicate files
        """
        file_paths = list(summaries.keys())
        
        # For each file, compare it with all other files in the same subdirectory using reranker
        for i, file_path in enumerate(file_paths):
            confirmed_duplicates = []
            
            if not (os.path.abspath(os.path.join(self.config.save_path, "workspace")) in os.path.abspath(file_path)):
                continue
            
            if not os.path.exists(file_path):
                continue
            
            # Do not compare markdown files because they are usually reports
            if ".md" in file_path:
                continue
                
            # Get the parent directory of the current file
            current_dir = os.path.dirname(file_path)
            
            # Create a list of all other files in the same subdirectory
            other_files = []
            for path in file_paths:
                if (os.path.dirname(path) == current_dir) and (path != file_path) and (os.path.splitext(path)[1] == os.path.splitext(file_path)[1]):
                    other_files.append(path)
            other_summaries = [summaries[path] for path in other_files]
            logger.info(f"Comparing {os.path.relpath(file_path, self.config.save_path)} with {len(other_files)} other files in the same subdirectory")
            logger.debug(f"Comparing {os.path.relpath(file_path, self.config.save_path)} with {[os.path.relpath(path, self.config.save_path) for path in other_files]}")
            
            if not other_summaries:
                continue
            
            # Directly call rerank API to get relevance scores
            query = summaries[file_path]
            if len(query) > 2000:
                logger.warning(f"Query is too long, truncating to 2000 characters: {query[:2000]}")
                query = query[:2000]
            
            # Create payload for rerank API
            payload = {
                "model": self.config.rerank.rerank_model, 
                "query": query, 
                "documents": other_summaries, 
                "return_raw_scores": True
            }
            
            # Make API request
            api_key = self.config.rerank.rerank_api_key
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            url = self.config.rerank.rerank_base_url + "rerank"
            
            try:
                response = requests.post(url, json=payload, headers=headers)
                results = response.json()["results"]
                all_rerank_scores = [result["relevance_score"] for result in results]
                
                max_score = max(all_rerank_scores)
                min_score = min(all_rerank_scores)
                avg_score = sum(all_rerank_scores) / len(all_rerank_scores)
                med_score = np.median(all_rerank_scores)
                above_05 = sum(1 for score in all_rerank_scores if score > 0.5)
                above_08 = sum(1 for score in all_rerank_scores if score > 0.8)
                logger.info(
                    f"All rerank scores max: {max_score:.3f}, min: {min_score:.3f}, avg: {avg_score:.3f}, median: {med_score:.3f}, num_files: {len(all_rerank_scores)}, #>0.5: {above_05}, #>0.8: {above_08}"
                )
                
                # Process results and filter by relevance score > threshold
                for result in results:
                    relevance_score = result["relevance_score"]
                    if relevance_score > self.config.rerank.file_duplicate_threshold:
                    # if relevance_score > 0.8:
                        # Get the index of the matching document
                        doc_index = result["index"]
                        other_file_path = other_files[doc_index]
                        logger.debug(f"Found potential duplicate pair: {file_path} and {other_file_path} with score {relevance_score:.3f}, summary1: {summaries[file_path][:200]}, summary2: {summaries[other_file_path][:200]}")
                        
                        if os.path.exists(other_file_path):
                            # Use LLM to verify if they are actually duplicates
                            if self._compare_files_with_llm(file_path, other_file_path):
                                logger.info(f"LLM confirmed duplicate pair: {file_path} and {other_file_path} with score {relevance_score:.3f}")
                                confirmed_duplicates.append((file_path, other_file_path))
        
            except Exception as e:
                logger.warning(f"Error calling rerank API: {e}")
                continue
            
            logger.info(f"Found {len(confirmed_duplicates)} confirmed duplicate pairs")
            
            # Remove older duplicates
            self._remove_older_duplicates(confirmed_duplicates)
            
        
    def _remove_older_duplicates(self, duplicates: List[Tuple[str, str]]):
        """
        Remove the older file from each duplicate pair
        
        Args:
            duplicates: List of tuples containing paths to duplicate files
        """
        for file1, file2 in duplicates:
            try:
                # Get modification times
                mtime1 = os.path.getmtime(file1)
                mtime2 = os.path.getmtime(file2)
                
                # Remove the older file
                if mtime1 < mtime2:
                    self._delete_file(file1, "Older duplicate")
                else:
                    self._delete_file(file2, "Older duplicate")
            except Exception as e:
                logger.warning(f"Failed to compare modification times for {file1} and {file2}: {e}")
    
    def _find_and_remove_simulated_data_files(self, summaries: Dict[str, str]):
        """
        Find and remove code files containing simulated or fake data
        
        Args:
            summaries: Dictionary mapping file paths to their summaries
        """
        # Filter for code files only: py, sh, c, cpp, r
        code_extensions = {'.py', '.sh', '.c', '.cpp', '.r'}
        
        for file_path in summaries.keys():
            # Skip if file has already been deleted
            if not os.path.exists(file_path):
                continue
            
            # Get file extension
            _, ext = os.path.splitext(file_path)
            
            # Check if it's a code file
            if ext.lower() not in code_extensions:
                continue
                
            # Check if the file contains simulated data
            if self._detect_simulated_data(file_path):
                self._delete_file(file_path, "Contains simulated/fake data")
    
    def clean_repository(self):
        """
        Main method to clean the repository by removing duplicates and simulated data files
        
        Returns:
            Dictionary with information about deleted files and duplicate pairs
        """
        logger.info("Starting repository cleaning process")
        
        # Get file summaries
        summaries = self._get_file_summaries()
        logger.info(f"Found {len(summaries)} files to analyze")
        
        # Find and remove simulated data files
        self._find_and_remove_simulated_data_files(summaries)
        
        # Find potential duplicates using reranker
        duplicates = self._find_duplicates_with_reranker(summaries)
        
        logger.info("Repository cleaning process completed")
        
        return {
            "deleted_files": self.deleted_files,
            "duplicate_pairs": self.duplicate_pairs
        }


# Example usage
if __name__ == "__main__":
    from ..state import load_state
    
    config, state, last_subgraph = load_state("outputs/pred_aki_trend_eicu_demo_20251125181239")
    
    # Create file manager
    file_manager = FileManager(config)
    
    # Clean the repository
    result = file_manager.clean_repository()
    print(f"Deleted {len(result['deleted_files'])} files")
    print(f"Found {len(result['duplicate_pairs'])} duplicate pairs")
