#!/usr/bin/env python3
"""
Example script demonstrating how to use the FileManager utility

cd /data/cyx/openlens-ai
python examples/file_manager_example.py
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import openlens_ai modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from openlens_ai.utils.config import Config
from openlens_ai.utils.file_manager import FileManager
from openlens_ai.state import load_state


def main():
    # Load configuration and state
    # You can replace "outputs/power_grid_fault_id" with your own experiment path
    config, state, last_subgraph = load_state("outputs/power_grid_fault_id")
    
    # Create file manager instance
    file_manager = FileManager(config)
    
    # Clean the repository
    print("Starting repository cleaning process...")
    result = file_manager.clean_repository()
    
    # Print results
    print(f"\nCleaning completed!")
    print(f"Deleted {len(result['deleted_files'])} files:")
    for file_info in result['deleted_files']:
        print(f"  - {file_info['path']}: {file_info['reason']}")
    
    print(f"\nFound {len(result['duplicate_pairs'])} duplicate pairs:")
    for pair in result['duplicate_pairs']:
        print(f"  - {pair['file1']} and {pair['file2']}")


if __name__ == "__main__":
    main()