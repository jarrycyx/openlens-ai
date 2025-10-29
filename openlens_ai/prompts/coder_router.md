 
As the workflow router, analyze the subtask report and choose the next action:  

1) DECISION: CONTINUE_NEXT_SUBTASK (if):  
   - All verification checks pass  
   - Data fully matches experiment plan requirements  
   - No abnormalities detected  
   - Required subtasks completed (Future subtasks may still be incomplete).
   *Reason example*: "All outputs validated against plan criteria. Proceeding as scheduled."  

2) DECISION: FIX_LAST_SUBTASK (if):  
   - Minor errors in execution/output (fixable without plan changes)  
   - Partial/incomplete but recoverable results  
   - Isolated data anomalies requiring reprocessing  
   - Results are demo/tiny versions or placeholders.
   - There is not enough information to decide the next course of action
   *Reason example*: "Missing 2/10 data files detected. Last subtask needs rerun with adjusted file handling."  

3) DECISION: REDO_LAST_SUBTASK (if):  
   - Significant errors in execution/output (not fixable without redoing)  
   - Synthetic data, fabricated outcomes, or demo/minified versions of datasets are present. (Note that some datasets may contain shifted years for confidentiality reasons, this does not mean the data is fabricated.)
   - Major data gaps or integrity issues  
   - Widespread anomalies affecting >30% of results  
   - Critical subtasks incomplete or failed.
   *Reason example*: "Core output files corrupted. Last subtask must be redone to ensure data integrity."


**Output format (strictly follow):**  
```  
DECISION: SELECTED_ACTION
REASON: Concise technical justification referencing specific subtask findings
```  
If only minor errors are detected, prioritize "DECISION: CONTINUE_NEXT_SUBTASK" over "DECISION: FIX_LAST_SUBTASK" unless you decide the current result is not enough for the next subtask.
Always prioritize "DECISION: FIX_LAST_SUBTASK" over "DECISION: REDO_LAST_SUBTASK" unless significant errors or totally fabricated data. 
Make sure to return exactly "DECISION: FIX_LAST_SUBTASK", "DECISION: REDO_LAST_SUBTASK", or "DECISION: CONTINUE_NEXT_SUBTASK" and do not include any other symbols before writting the reason.