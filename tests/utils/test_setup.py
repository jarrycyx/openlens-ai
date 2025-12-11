import os
import shutil
import toml
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

def setup_test_environment(test_name: str) -> Tuple[str, str]:
    """
    Copy test project and modify configuration files to prepare environment for unit tests
    
    Args:
        test_name: Test name, will be used to generate unique folder name
        
    Returns:
        Tuple[str, str]: (new test project path, new config file path)
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = f"{test_name}_unit_test_{timestamp}"
    
    # Source and target paths
    source_proj_path = Path("tests/test_proj")
    if os.path.exists(Path("outputs/tests")):
        shutil.rmtree(Path("outputs/tests"))
        
    target_proj_path = Path("outputs/tests") / unique_id
    
    
    
    # Create target directory
    target_proj_path.mkdir(parents=True, exist_ok=True)
    
    # Copy entire test project
    shutil.copytree(source_proj_path, target_proj_path, dirs_exist_ok=True)
    
    # Modify configuration file
    config_path = target_proj_path / "config.toml"
    
    # Read configuration file
    with open(config_path, 'r') as f:
        config_data = toml.load(f)
    
    # Modify configuration
    config_data['save_path'] = str(target_proj_path)
    config_data['thread_id'] = unique_id
    config_data['question'] = f"Unit test for {test_name}"
    
    # Add unit test markers
    if 'workflow' not in config_data:
        config_data['workflow'] = {}
    config_data['workflow']['e2e_test'] = True
    config_data['workflow']['enable_literature_review'] = False
    config_data['workflow']['enable_latex_writer'] = False
    config_data['workflow']['enable_artifact_publisher'] = False
    
    # Write back to configuration file
    with open(config_path, 'w') as f:
        toml.dump(config_data, f)
    
    # Also update latest_state.json with correct paths
    latest_state_path = target_proj_path / "latest_state.json"
    if latest_state_path.exists():
        with open(latest_state_path, 'r') as f:
            state_data = json.load(f)
            state_data["save_path"] = str(target_proj_path)
            state_data["thread_id"] = unique_id
        with open(latest_state_path, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    print(f"Test environment setup: {target_proj_path}")
    print(f"Configuration file updated: {config_path}")
    
    return str(target_proj_path), str(config_path)

def cleanup_test_environment(test_path: str):
    """
    Clean up test environment
    
    Args:
        test_path: Test project path
    """
    try:
        shutil.rmtree(test_path)
        print(f"Test environment cleaned up: {test_path}")
    except Exception as e:
        print(f"Failed to clean up test environment: {e}")

if __name__ == "__main__":
    # Test utility script
    test_path, config_path = setup_test_environment("example_test")
    print(f"Test path: {test_path}")
    print(f"Config path: {config_path}")
    
    # Optionally clean up
    # cleanup_test_environment(test_path)