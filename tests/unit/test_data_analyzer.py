import unittest
import os
from unittest.mock import patch, MagicMock

from openlens_ai.agents.data_analyzer import build_data_analyzer
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestDataAnalyzer(unittest.TestCase):
    """Test data_analyzer module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("data_analyzer")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_data_analyzer_main_function(self):
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        state["messages"] = []
        
        # Build graph
        graph = build_data_analyzer(config, file_manager)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("messages", final_state)
        self.assertIn("data_show", final_state)
        
        # Verify data analysis file was created
        data_show_path = os.path.join(self.test_path, "workspace", "data_analyze", "data_show.md")
        self.assertTrue(os.path.exists(data_show_path))


if __name__ == "__main__":
    unittest.main()