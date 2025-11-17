# VLM MCP Server

This MCP server provides tools for analyzing images and PDFs using Vision Language Models (VLM).

## Features

- Read and analyze image files (PNG, JPG, JPEG)
- Read and analyze PDF files (converts each page to image)
- Classify images using VLM
- Analyze LaTeX images
- Custom prompt support for specific analysis needs

## Setup

1. Install dependencies:
   ```bash
   pip install fastmcp loguru PyMuPDF langchain
   ```

2. Set environment variables:
   ```bash
   export VISION_MODEL="gpt-4-vision-preview"  # or your preferred vision model
   export VISION_BASE_URL="https://api.openai.com/v1"  # or your API endpoint
   export VISION_API_KEY="your-api-key"  # or set OPENAI_API_KEY
   export LANGUAGE="eng"  # or "chs" for Chinese
   export DOMAIN="general"  # or "medical" for medical domain
   export SAVE_PATH="./outputs"  # path to save outputs
   ```

3. Run the server:
   ```bash
   python -m openlens_ai.tools.vlm_mcp.server
   ```

## Using Custom Configuration

To use a custom configuration when running the server programmatically:

```python
from openlens_ai.tools.vlm_mcp.server import run_server
from openlens_ai.utils.config import Config

# Load your custom configuration
config = Config.from_toml("path/to/your/config.toml")

# Run the server with your custom configuration
run_server(config)
```

## Tools

### read_image_file

Read an image file and convert it to base64.

**Parameters:**
- `file_path` (string): Path to the image file (supports png, jpg, jpeg)

**Returns:**
- Base64 encoded string of the image

### read_pdf_file

Read a PDF file and convert each page to base64.

**Parameters:**
- `file_path` (string): Path to the PDF file

**Returns:**
- List of base64 encoded strings, one for each page

### analyze_image

Analyze an image using VLM.

**Parameters:**
- `image_base64` (string): Base64 encoded image
- `prompt` (optional string): Custom prompt for analysis (if not provided, uses default)

**Returns:**
- VLM analysis result

### classify_image

Classify an image using VLM.

**Parameters:**
- `image_base64` (string): Base64 encoded image

**Returns:**
- VLM classification result

### analyze_latex_image

Analyze a LaTeX image using VLM.

**Parameters:**
- `image_base64` (string): Base64 encoded image

**Returns:**
- VLM analysis result for LaTeX

### analyze_file

Analyze a file (image or PDF) using VLM.

**Parameters:**
- `file_path` (string): Path to the file (supports png, jpg, jpeg, pdf)
- `prompt` (optional string): Custom prompt for analysis

**Returns:**
- VLM analysis result

## Usage Examples

### Analyze an image file

```python
# First read the image file
image_base64 = read_image_file("path/to/image.png")

# Then analyze it
result = analyze_image(image_base64)
```

### Analyze a PDF file

```python
# Directly analyze the PDF file
result = analyze_file("path/to/document.pdf")
```

### Classify an image

```python
# First read the image file
image_base64 = read_image_file("path/to/image.png")

# Then classify it
classification = classify_image(image_base64)
```

### Analyze with custom prompt

```python
# Directly analyze with custom prompt
result = analyze_file("path/to/image.png", "Describe the main elements in this image.")
```

## Integration with MCP Clients

To use this server with an MCP client, add it to your client configuration:

```json
{
  "mcpServers": {
    "vlm": {
      "command": "python",
      "args": ["-m", "openlens_ai.tools.vlm_mcp.server"]
    }
  }
}
```

## Testing

A test script is provided to verify the server functionality through stdio communication:

### Quick Test

Run the following command to execute the test:

```bash
./run_test.sh
```

### Manual Test

1. Ensure all dependencies are installed
2. Set the PYTHONPATH environment variable
3. Run the test script

```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python openlens_ai/tools/vlm_mcp/test_server.py
```

### Test Script Functionality

The test script performs the following steps:

1. Starts the MCP server as a subprocess
2. Sends JSON-RPC requests via stdio
3. Receives and parses responses from stdout
4. Tests various server functionalities:
   - Server initialization
   - Tool listing
   - Image analysis

## Notes

- The server supports both image and PDF files
- PDF files are converted to images page by page
- Custom prompts can be provided for specific analysis needs
- The server uses the same VLM configuration as the main OpenLens AI application
- All analysis results are saved to the configured save path
- The test script creates temporary files during testing and cleans them up afterward
