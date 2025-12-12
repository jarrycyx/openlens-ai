import unittest
import os
import sys
import asyncio
import multiprocessing
import time
import glob
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from openlens_ai.tools.openhands_mcp.server import run_server, set_config
from openlens_ai.state import load_state
from tests.utils.test_setup import setup_test_environment
import toml

try:
    from fastmcp import Client
except ImportError:
    Client = None


class TestMCPServerIntegration(unittest.TestCase):
    """Test MCP server integration with actual client connections"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and start MCP server"""
            
        cls.test_path, cls.config_path = setup_test_environment("mcp_server_integration")
        
        # Load config
        config, state, last_subgraph, file_manager = load_state(cls.test_path)
        cls.config = config
        
        # Find test files in test_proj
        cls.test_files = cls._find_test_files(cls.test_path)
        
        # Get available port
        from openlens_ai.tools.openhands_adaptor import get_available_port
        cls.port = get_available_port(9077)
        
        # Start MCP server in a separate process
        cls.server_process = multiprocessing.Process(
            target=run_server, 
            args=(config, cls.port)
        )
        cls.server_process.start()
        
        # Wait for server to start
        time.sleep(5)
        
        # Initialize client
        cls.client_url = f"http://localhost:{cls.port}/mcp"
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment and stop MCP server"""
        if hasattr(cls, 'server_process') and cls.server_process.is_alive():
            cls.server_process.terminate()
            cls.server_process.join(timeout=5)
            if cls.server_process.is_alive():
                cls.server_process.kill()
                cls.server_process.join()

    @staticmethod
    def _find_test_files(test_path):
        """Find test files (PDF, PNG, JPG) in the test project"""
        test_files = {
            'pdf': [],
            'png': [],
            'jpg': [],
            'jpeg': []
        }
        
        workspace_path = os.path.join(test_path, "workspace")
        
        # Use glob.glob to find files by extension
        for ext in test_files.keys():
            pattern = os.path.join(workspace_path, "**", f"*.{ext}")
            test_files[ext] = glob.glob(pattern, recursive=True)
        
        return test_files

    async def _test_mcp_connection(self):
        """Test MCP server connection"""
        async with Client(self.client_url) as client:
            # Test server connection
            await client.ping()
            return True

    def test_mcp_server_connection(self):
        """Test MCP server connection"""
        async def run_test():
            return await self._test_mcp_connection()
        
        result = asyncio.run(run_test())
        self.assertTrue(result, "Failed to connect to MCP server")

    async def _test_list_tools(self):
        """Test listing available tools"""
        async with Client(self.client_url) as client:
            # List available tools
            tools = await client.list_tools()
            return tools

    def test_list_tools(self):
        """Test listing available tools"""
        async def run_test():
            return await self._test_list_tools()
        
        tools = asyncio.run(run_test())
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Check for expected tools
        tool_names = [tool.name for tool in tools]
        expected_tools = ['analyze_image_vlm', 'analyze_pdf_vlm', 'get_summary']
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names, f"Expected tool {tool_name} not found")

    async def _test_analyze_pdf_vlm(self, pdf_path, pdf_page="1"):
        """Test analyze_pdf_vlm tool"""
        async with Client(self.client_url) as client:
            # Test analyze_pdf_vlm tool
            result = await client.call_tool("analyze_pdf_vlm", {
                "file_path": pdf_path,
                "prompt": "Describe the content of this PDF page.",
                "pdf_page": pdf_page,
                "security_risk": "Low"
            })
            return result

    def test_analyze_pdf_vlm(self):
        """Test analyze_pdf_vlm tool with PDF files from test_proj"""
        
        async def run_test(pdf_path):
            return await self._test_analyze_pdf_vlm(pdf_path)
        
        # Test with the first PDF file
        pdf_file = self.test_files['pdf'][0]
        result = asyncio.run(run_test(pdf_file))
        
        # Verify the result
        self.assertTrue(not result.is_error)
        self.assertGreater(len(result.content), 0)
        self.assertGreater(len(result.content[0].text), 10)

    async def _test_analyze_pdf_vlm_merge(self, pdf_path):
        """Test analyze_pdf_vlm tool with merge option"""
        async with Client(self.client_url) as client:
            # Test analyze_pdf_vlm tool with merge option
            result = await client.call_tool("analyze_pdf_vlm", {
                "file_path": pdf_path,
                "prompt": "Summarize the content of this PDF document.",
                "pdf_page": "merge",
                "security_risk": "Low"
            })
            return result

    def test_analyze_pdf_vlm_merge(self):
        """Test analyze_pdf_vlm tool with merge option"""
        
        async def run_test(pdf_path):
            return await self._test_analyze_pdf_vlm_merge(pdf_path)
        
        # Test with the first PDF file
        pdf_file = self.test_files['pdf'][0]
        result = asyncio.run(run_test(pdf_file))
        
        # Verify the result
        self.assertTrue(not result.is_error)
        self.assertGreater(len(result.content), 0)
        self.assertGreater(len(result.content[0].text), 10)

    async def _test_analyze_image_vlm(self, image_path):
        """Test analyze_image_vlm tool"""
        async with Client(self.client_url) as client:
            # Test analyze_image_vlm tool
            result = await client.call_tool("analyze_image_vlm", {
                "file_path": image_path,
                "prompt": "Describe this image in detail.",
                "security_risk": "Low"
            })
            return result

    def test_analyze_image_vlm(self):
        """Test analyze_image_vlm tool with image files from test_proj"""
        # Combine png and jpg/jpeg files
        image_files = self.test_files['png'] + self.test_files['jpg'] + self.test_files['jpeg']
        
        async def run_test(image_path):
            return await self._test_analyze_image_vlm(image_path)
        
        # Test with the first image file
        image_file = image_files[0]
        result = asyncio.run(run_test(image_file))
        
        # Verify the result
        self.assertTrue(not result.is_error)
        self.assertGreater(len(result.content), 0)
        self.assertGreater(len(result.content[0].text), 10)

    async def _test_get_summary(self, file_path):
        """Test get_summary tool"""
        async with Client(self.client_url) as client:
            # Test get_summary tool
            result = await client.call_tool("get_summary", {
                "file_path": file_path
            })
            return result

    def test_get_summary(self):
        """Test get_summary tool with text files from test_proj"""
        # Find text files using glob
        workspace_path = os.path.join(self.test_path, "workspace")
        text_extensions = ['.md', '.txt', '.py', '.csv']
        text_files = []
        
        for ext in text_extensions:
            pattern = os.path.join(workspace_path, "**", f"*{ext}")
            text_files.extend(glob.glob(pattern, recursive=True))
        
        async def run_test(file_path):
            return await self._test_get_summary(file_path)
        
        # Test with the first text file
        text_file = text_files[0]
        result = asyncio.run(run_test(text_file))
        
        # Verify the result
        self.assertTrue(not result.is_error)
        self.assertGreater(len(result.content), 0)
        self.assertGreater(len(result.content[0].text), 10)

    async def _test_error_handling(self):
        """Test error handling with invalid file path"""
        async with Client(self.client_url) as client:
            # Test with invalid file path
            result = await client.call_tool("analyze_image_vlm", {
                "file_path": "/path/to/nonexistent/file.png",
                "prompt": "Describe this image.",
                "security_risk": "Low"
            })
            return result

    def test_error_handling(self):
        """Test error handling with invalid file path"""
        async def run_test():
            return await self._test_error_handling()
        
        result = asyncio.run(run_test())
        
        # Verify the result
        self.assertTrue(not result.is_error)


if __name__ == "__main__":
    unittest.main()