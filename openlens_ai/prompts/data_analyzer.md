Explore and analyze all accessible data files in the /workspace/datasets directory to:

1. Exploration: List the /workspace/datasets directory (if exists) in a non-recursive manner and capture the output.
2. Data Identification: Based on the exploration, identify data files (CSV, JSON, XLSX, sqlite, zip, gz, sx, or TXT) and file codecs (UTF-8, GBK, etc.) that are likely to contain experimental data. 
3. Data Analysis: Write an analysis script in /workspace/data_analyze (e.g., in Python) that:
    - Reads the identified data files.
    - Identify the data structure and determines how to read them.
    - For each files in /workspace/datasets
      - If it is a standlone tabular files: print the first 10 rows and random 10 rows ; 
      - If it is a database connection configuration file: connect and list all tables, identify required tables for the research question, then print the first 10 rows and random 10 rows of required tables; 
      - If it is a document file: search for related infomation about how to load required data, print the matched content;
      - decompress the file start the analysis again if it is a compressed file; 
      - copy the file content as is to "data_show.md" if it is a document file;
    - Saves the results in "data_show.md".
4. Final Checking:
    - Make sure that the data files are accessible and readable.
    - Make sure no errors occur during the analysis.
    - Make sure that the results does support the following data analysis.

IMPORTANT: You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP. Make sure all scripts, tools, and data files are saved in /workspace/data_analyze. Do not train models, perform experiments, or generate LaTeX files in this task. You will have separate tasks for those steps.

Research Question:
{question}