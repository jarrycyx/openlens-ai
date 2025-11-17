#!/bin/bash

# Test script for VLM MCP Server
# This script sets up the environment and runs the test

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "$(dirname "$DIR")"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Running VLM MCP Server test..."
echo "Project root: $(pwd)"
echo "Test script: $DIR/test_server.py"

# Run the test
python "$DIR/test_server.py"

# Exit with the test's exit code
exit $?
