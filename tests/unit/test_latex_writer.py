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

    @patch('openlens_ai.agents.latex_writer.init_chat_model')
    @patch('openlens_ai.agents.latex_writer.run_openhands_prompt')
    @patch('openlens_ai.agents.latex_writer.chatbot_with_context_manager')
    def test_latex_writer_main_function(self, mock_chatbot, mock_openhands, mock_init_chat):
        """Test main function logic (simulate if __name__ == "__main__" part)"""
        # Mock LLM
        mock_llm = MagicMock()
        mock_init_chat.return_value = mock_llm
        
        # Mock OpenHands response
        mock_openhands.return_value = "Successfully created LaTeX document"
        
        # Mock chatbot
        mock_chatbot_instance = MagicMock()
        mock_chatbot_instance.return_value = {}
        mock_chatbot.return_value = mock_chatbot_instance
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        
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