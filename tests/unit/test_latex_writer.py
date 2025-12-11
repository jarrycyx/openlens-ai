import unittest
import os
from unittest.mock import patch, MagicMock

from openlens_ai.agents.latex_writer import build_latex_writer
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestLatexWriter(unittest.TestCase):
    """Test latex_writer module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("latex_writer")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_latex_writer_main_function(self):
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        
        config.workflow.max_subtask_redo = 1
        config.workflow.max_latex_polish_round = 1
        
        # Build graph
        graph = build_latex_writer(config, file_manager)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("messages", final_state)
        
        # Verify manuscript directory was created
        manuscript_path = os.path.join(self.test_path, "workspace", "manuscript")
        self.assertTrue(os.path.exists(manuscript_path))


if __name__ == "__main__":
    unittest.main()