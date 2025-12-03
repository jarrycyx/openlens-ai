

Reminders: 
- DO NOT mock or simulate results. Always generate real results using an actual workflow setup (e.g., scripts that can directly run with experimental/control group inputs to produce dependent variables).
- DO NOT execute commands like "ls -R", as it may cause you to exceed context length.
- When loading/extracting datasets, make sure to load as much data as possible, NEVER create demo/tiny/sample versions or placeholders and NEVER use maximum data limits (e.g. max_rows=1000, max-patients=10).
- You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP.
- Make sure each request to the tool is simple and specific. If the request is too complex, split it into multiple requests. When the tool responds, you can then generate the next request.
- Data prepreration and model training may take a long time, DO NOT set a short timeout for the execution, also DO NOT force kill the process unless you are sure it is stuck. You should log the progress and status of the process every a few minutes when it is running.
- When writing any scripts related to data loading/processing, DO NOT try to load all data into memory at once, use batch processing or data streaming techniques to handle large datasets efficiently.
- You are provided with the following important tools to enhance your understanding of the workspace:
  - `get_summary`: Get a summary of a file. Always prioritize this tool to get a summary of a file before you read the file content.
  - `analyze_file_vlm`: See the content of a figure, image, or pdf using vision language model. Always use this tool to see the content of a figure, image, or pdf before you try to edit the figure.