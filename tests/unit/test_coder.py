import unittest
import os
from unittest.mock import patch, MagicMock

from openlens_ai.agents.coder import build_coder
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestCoder(unittest.TestCase):
    """Test coder module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("coder")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_coder_main_function(self):

        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        state["messages"] = []
        state["plan"] = {
            "objective": "What are the temporal patterns of the data?",
            "sub_tasks": [
                "Task 1: Create a subtask for task 1"
            ],
            "expected_result": "Expected result",
        }
        config.workflow.max_subtask_redo = 1
        config.workflow.max_latex_polish_round = 1

        # Build graph
        graph = build_coder(config, file_manager)

        # Execute graph
        final_state = graph.invoke(state)

        # Verify state updates
        self.assertIn("messages", final_state)

        # Verify subtask directory was created
        subtask_path = os.path.join(self.test_path, "workspace", "hello.sh")
        self.assertTrue(os.path.exists(subtask_path))


if __name__ == "__main__":
    unittest.main()
