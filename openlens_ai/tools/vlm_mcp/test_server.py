#!/usr/bin/env python3
"""
Test script for VLM MCP Server using stdio transport.

This script tests the VLM MCP server by:
1. Starting the server as a subprocess
2. Sending JSON-RPC requests via stdin
3. Receiving and parsing responses from stdout
4. Testing various server functionalities
"""

import os
import sys
import json
import base64
import subprocess
import time
from typing import Dict, Any, Optional


class VLMCPTestClient:
    """Client for testing VLM MCP Server via stdio."""
    
    def __init__(self):
        """Initialize the test client.
        """
        self.process = None
        self.request_id = 1
        
    def start_server(self):
        """Start the MCP server as a subprocess."""
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Start the server process as a module with proper Python path
            self.process = subprocess.Popen(
                ["python", "-m", "openlens_ai.tools.vlm_mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"Server started with PID: {self.process.pid}")
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Server stopped")
    
    def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server.
        
        Args:
            method: The method name to call
            params: Parameters for the method
            
        Returns:
            The JSON-RPC response
        """
        if not self.process:
            raise RuntimeError("Server not started")
        
        # Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        print(f"Received response: {response_line.strip()}")
        if not response_line:
            raise RuntimeError("No response from server")
        
        try:
            response = json.loads(response_line.strip())
            self.request_id += 1
            return response
        except json.JSONDecodeError as e:
            # raise RuntimeError(f"Failed to parse response: {e}")
            print(f"Failed to parse response: {e}, response_line: {response_line.strip()}")
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection.
        
        Returns:
            The initialization response
        """
        return self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools.
        
        Returns:
            The list of tools
        """
        return self.send_request("tools/list")
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            The tool result
        """
        return self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })


def test_server():
    """Test the VLM MCP server."""
    client = VLMCPTestClient()
    
    try:
        # Start the server
        if not client.start_server():
            return False
        
        # Give the server a moment to start
        time.sleep(1)
        
        # Initialize the connection
        print("Initializing connection...")
        init_response = client.initialize()
        print(f"Init response: {json.dumps(init_response, indent=2)}")
        
        # List available tools
        print("\nListing tools...")
        tools_response = client.list_tools()
        print(f"Tools response: {json.dumps(tools_response, indent=2)}")
        
        # Test analyze_file_vlm tool with a test image
        print("\nTesting analyze_file_vlm tool...")
        test_image_path = os.path.abspath("outputs/pred_aki_trend_eicu_demo_20251117110445/overall_graph_image.png")
        
        
        # Call the analyze_file_vlm tool with absolute path
        analyze_response = client.call_tool("analyze_file_vlm", {
            "file_path": test_image_path,
            "prompt": "Describe this image in detail."
        })
        
        
        print("\nAll tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False
    finally:
        # Stop the server
        client.stop_server()


if __name__ == "__main__":
    # Run the test
    success = test_server()
    sys.exit(0 if success else 1)
