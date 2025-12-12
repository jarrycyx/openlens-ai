import unittest
import os
import sys
import multiprocessing
import time
from unittest.mock import patch, MagicMock, Mock

from openlens_ai.tools.openhands_adaptor import OpenHandsTool, run_openhands_prompt, get_available_port
from openlens_ai.tools.openhands_mcp.server import run_server, set_config, get_config
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment
import toml


class TestOpenhandsAdaptor(unittest.TestCase):
    """Test openhands_adaptor module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("openhands_adaptor")
        
        # Modify config to set e2e_test to False as required
        with open(self.config_path, 'r') as f:
            config_data = toml.load(f)
        config_data['workflow']['e2e_test'] = False
        with open(self.config_path, 'w') as f:
            toml.dump(config_data, f)

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_get_available_port(self):
        """Test get_available_port function"""
        port = get_available_port(9077)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 9077)
        self.assertLessEqual(port, 9177)  # Maximum 100 attempts


    def test_run_openhands_prompt(self):
        """Test run_openhands_prompt function"""
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        
        # Create a test prompt that requires testing all MCP tools
        test_prompt = """
        Please test all available MCP tools by performing the following tasks:
        
        1. Use analyze_image_vlm to analyze an image file in the workspace
        2. Use analyze_pdf_vlm to analyze a PDF file in the workspace
        3. Use get_summary to get the summary of a file in the workspace
        
        Make sure to call all three MCP tools and verify they work correctly.
        """
        
        # Call the function
        result = run_openhands_prompt(test_prompt, config, file_manager=file_manager)
        
        # Verify the result
        # self.assertEqual(result, "Test result")


if __name__ == "__main__":
    unittest.main()