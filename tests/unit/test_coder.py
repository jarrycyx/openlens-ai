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

    @patch('openlens_ai.agents.coder.init_chat_model')
    @patch('openlens_ai.agents.coder.run_openhands_prompt')
    @patch('openlens_ai.agents.coder.chatbot_with_context_manager')
    def test_coder_main_function(self, mock_chatbot, mock_openhands, mock_init_chat):
        """Test main function logic (simulate if __name__ == "__main__" part)"""
        # Mock LLM
        mock_llm = MagicMock()
        mock_init_chat.return_value = mock_llm
        
        # Mock OpenHands response
        mock_openhands.return_value = "Successfully created Python script"
        
        # Mock chatbot
        mock_chatbot_instance = MagicMock()
        mock_chatbot_instance.return_value = {}
        mock_chatbot.return_value = mock_chatbot_instance
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        
        # Build graph
        graph = build_coder(config, file_manager)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("messages", final_state)
        
        # Verify subtask directory was created
        subtask_path = os.path.join(self.test_path, "workspace", "subtask_01")
        self.assertTrue(os.path.exists(subtask_path))


if __name__ == "__main__":
    unittest.main()