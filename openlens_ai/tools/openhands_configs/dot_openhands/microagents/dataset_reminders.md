---
name: dataset_reminders
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- dataset
- data
- preprocess
- process
---

Reminders: 
- DO NOT mock or simulate results. Always generate real results using an actual workflow setup.
- When loading/extracting datasets, make sure to load as much data as possible, NEVER create demo/tiny/sample versions or placeholders and NEVER use maximum data limits (e.g. max_rows=1000, max-patients=10).
- Data prepreration and model training may take a long time, DO NOT set a short timeout for the execution, also DO NOT force kill the process unless you are sure it is stuck.
- When writing any scripts related to data loading/processing, DO NOT try to load all data into memory at once, use batch processing or iterations combining multiprocessing/multithreading, i.e., precessing one patient/sample/record at a time and save this one patient/sample/record to disk.