# File Search MCP Tools

This directory contains two MCP (Model Context Protocol) tools for file searching:

1. **Keyword Search Server** - Searches for keywords in files
2. **Vector Search Server** - Uses vector search to find relevant content based on a query

## Features

### Keyword Search Server
- Searches for exact keywords in files within specified folders
- Supports multiple file extensions
- Returns context lines around matches
- Configurable maximum number of results

### Vector Search Server
- Uses vector search to find relevant content based on a query
- Leverages the existing `perform_rerank` function from the chatbot module
- Supports multiple file extensions
- Configurable token count and maximum number of results

## Usage

### Running Individual Servers

To run the keyword search server:
```bash
python keyword_search_server.py --config path/to/config.toml
```

To run the vector search server:
```bash
python vector_search_server.py --config path/to/config.toml
```

### Running Both Servers

To run both servers at once:
```bash
python run_servers.py --config path/to/config.toml
```

The servers will start on the following ports:
- Keyword Search Server: 9078
- Vector Search Server: 9079

## MCP Tools

### Keyword Search Tool

```python
keyword_search(
    keyword="example",
    folders=["/path/to/folder1", "/path/to/folder2"],
    file_extensions=[".py", ".md"],
    context_lines=3,
    max_results=50
)
```

Parameters:
- `keyword`: Keyword to search for in files
- `folders`: List of folders to search in
- `file_extensions`: List of file extensions to search in (default: [".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"])
- `context_lines`: Number of lines to include before and after the matched line (default: 3)
- `max_results`: Maximum number of results to return (default: 50)

### Vector Search Tool

```python
vector_search(
    query="How to implement a function",
    folders=["/path/to/folder1", "/path/to/folder2"],
    file_extensions=[".py", ".md"],
    token_cnt=10000,
    max_results=50
)
```

Parameters:
- `query`: Query string to search for relevant content
- `folders`: List of folders to search in
- `file_extensions`: List of file extensions to search in (default: [".txt", ".md", ".py", ".js", ".ts", ".java", ".cpp", ".h"])
- `token_cnt`: Maximum token count for the results (default: 10000)
- `max_results`: Maximum number of results to return (default: 50)

## Dependencies

- FastMCP
- LangChain
- Pydantic
- Loguru
- OpenLens AI utilities

## Configuration

The servers require a configuration file with the following structure:

```toml
[rerank]
rerank_model = "your-rerank-model"
rerank_api_key = "your-api-key"
rerank_base_url = "https://your-rerank-api.com/"
```

## Implementation Details

The vector search server leverages the existing `perform_rerank` function from the chatbot module, which:
1. Splits documents into chunks
2. Sends them to a rerank API
3. Returns the most relevant chunks based on the query

The keyword search server uses regular expressions to find exact matches of the keyword in files, providing context around each match.
