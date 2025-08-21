Explore and analyze all accessible data files in the /workspace/datasets directory to:

1. Exploration: List the /workspace/datasets directory (if exists) in a non-recursive manner and capture the output.
2. Data Identification: Based on the exploration, identify data files (CSV, JSON, XLSX, sqlite, zip, gz, sx, or TXT) and file codecs (UTF-8, GBK, etc.) that are likely to contain experimental data. 
3. Data Analysis: Write an analysis script in /workspace/data_analyze (e.g., in Python) that:
    - Reads the identified data files.
    - Identify the data structure and determines how to read them.
    - For each files in /workspace/datasets, print the first 10 rows and random 10 rows if it is a standlone tabular files; Connect and print the first 10 rows and random 10 rows of each tables (if database) if it is a database connection configuration file; decompress the file start the analysis again if it is a compressed file.
    - Saves the results in "data_show.md".
4. Final Checking:
    - Make sure that the data files are accessible and readable.
    - Make sure no errors occur during the analysis.
    - Make sure that the results does support the following data analysis.

IMPORTANT: You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP. Make sure all scripts, tools, and data files are saved in /workspace/data_analyze.