# File Search MCP Servers Runner
# This script runs both keyword search and vector search MCP servers
import os
import sys
import argparse
import threading
import time
from loguru import logger

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openlens_ai.utils.config import Config
from keyword_search_server import run_server as run_keyword_server
from vector_search_server import run_server as run_vector_server


def run_servers(config_path):
    """Run both keyword search and vector search MCP servers.
    
    Args:
        config_path: Path to the configuration file
    """
    config = Config.from_toml(config_path)
    
    # Start keyword search server in a separate thread
    keyword_thread = threading.Thread(
        target=run_keyword_server,
        args=(config,),
        daemon=True
    )
    keyword_thread.start()
    logger.info("Keyword search MCP server started on port 9078")
    
    # Start vector search server in a separate thread
    vector_thread = threading.Thread(
        target=run_vector_server,
        args=(config,),
        daemon=True
    )
    vector_thread.start()
    logger.info("Vector search MCP server started on port 9079")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Search MCP Servers")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to the configuration file")
    args = parser.parse_args()
    run_servers(args.config)
