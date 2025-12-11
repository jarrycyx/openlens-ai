import unittest
import os
from unittest.mock import patch, MagicMock
import shutil

from openlens_ai.agents.supervisor import build_supervisor
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestSupervisor(unittest.TestCase):
    """Test supervisor module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("supervisor")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_supervisor_main_function(self):
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        state["plan"] = {}
        os.remove(os.path.join(self.test_path, "plan.json"))
        os.remove(os.path.join(self.test_path, "plan.md"))
        
        # Build graph
        graph = build_supervisor(config, file_manager)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("messages", final_state)
        self.assertIn("plan", final_state)


if __name__ == "__main__":
    unittest.main()