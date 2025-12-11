import unittest
import os
from unittest.mock import patch, MagicMock

from openlens_ai.agents.artifact_publisher import build_artifact_publisher
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment


class TestArtifactPublisher(unittest.TestCase):
    """Test artifact_publisher module functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("artifact_publisher")

    def tearDown(self):
        """Clean up test environment"""
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    @patch('openlens_ai.agents.artifact_publisher._run_git_command')
    @patch('openlens_ai.agents.artifact_publisher._auto_create_github_repo_if_needed')
    def test_artifact_publisher_main_function(self, mock_repo, mock_git):
        """Test main function logic (simulate if __name__ == "__main__" part)"""
        # Mock GitHub repository creation
        mock_repo.return_value = "https://github.com/test/repo.git"
        
        # Use load_state like in the original main function
        config, state, last_subgraph, file_manager = load_state(self.test_path)
        
        # Build graph
        graph = build_artifact_publisher(config)
        
        # Execute graph
        final_state = graph.invoke(state)
        
        # Verify state updates
        self.assertIn("artifact_manifest_path", final_state)
        self.assertIn("artifact_code_stats", final_state)
        self.assertIn("artifact_ok_to_publish", final_state)
        
        # Verify artifact manifest file was created
        manifest_path = final_state.get("artifact_manifest_path")
        if manifest_path:
            self.assertTrue(os.path.exists(manifest_path))


if __name__ == "__main__":
    unittest.main()