import unittest
import os
from unittest.mock import patch, MagicMock

from openlens_ai.agents.literature_reviewer import build_literature_review_subgraph
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestLiteratureReviewer(unittest.TestCase):
    """Test literature_reviewer module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("literature_reviewer")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_literature_reviewer_main_function(self):
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        state["messages"] = []
        
        # Build graph
        graph = build_literature_review_subgraph(config, file_manager)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("messages", final_state)
        self.assertIn("literature_report", final_state)
        
        # Verify literature review file was created
        literature_review_path = os.path.join(self.test_path, "workspace", "literature_review.md")
        self.assertTrue(os.path.exists(literature_review_path))


if __name__ == "__main__":
    unittest.main()