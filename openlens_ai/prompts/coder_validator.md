

**Review all saved results and processed data files in the workspace directory to:**

1. **Verify Code Functionality:**
   * Check if the existing code executes without errors across all relevant modules.
   * Ensure that the output matches expected values or patterns based on test cases or historical data.
   * **If issues are found**, modify the code to fix errors and rerun the necessary processes.

2. **Confirm Experiment Completion:**
   * Review all experiment logs and data to ensure that all planned tasks and experiments are fully completed.
   * Check if any experiment was prematurely stopped or had incomplete outputs (e.g., missing data, incomplete runs).
   * Validate that the results align with the objectives outlined in the experiment plan.
   * **If experiments are incomplete**, revise the code to handle missing data or unfinished experiments, and rerun.
   * Make sure the program ONLY SAVE ONE COPY of each figure and does not save different formats of the same figure.

3. **Check for Data Integrity:**
   * Ensure that no synthetic data, fabricated outcomes, or demo/minified versions of datasets are present unless explicitly stated in the experimental setup (make sure that actual sample/patient/row numbers used match the provided dataset). Note that some datasets may contain shifted years for confidentiality reasons, this does not mean the data is fabricated.
   * **If simulated data is found**, adjust the code to ensure only real data is used and rerun the experiment.

4. **Check for Abnormal Intermediate Results:**
   * Inspect intermediate results (e.g., partial outputs, metrics during the process) for abnormalities like all values being 100%, 0%, or other unrealistic patterns.
   * Investigate the root cause of such anomalies and ensure they do not stem from errors in data processing or model behavior.
   * **If abnormal results are found**, debug the process and fix any underlying issues, then rerun the code.

5. **Ensure Academic Rigor:**
   * **Prevent Data Leakage:** Confirm that training, validation, and testing datasets are strictly separated, with no overlap in samples, time windows, or features. Verify that test data is never used—directly or indirectly—for model training, feature engineering, or hyperparameter tuning.
   * **Validate Temporal Integrity:** For time-series or longitudinal data, ensure that no future information is used to predict past or present states (e.g., avoid “peeking ahead” into data that would not be available at the prediction time).
   * **Audit Feature Engineering:** Verify that derived or engineered features are created using only information available at the time of prediction, and not using aggregated statistics from the entire dataset.
   * **Check for Unrealistic Results:** If the model produces unreasonable results (e.g., AUROC<=0.5, AUROC>0.98, Accuracy>0.98, Accuracy=0), investigate the cause (e.g. data leakage) and fix the issue.


Experiment Plan:
{subplan}

Reminders: 
- You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP. 
- Data prepreration and model training may take a long time, DO NOT set a short timeout for the execution, also DO NOT force kill the process unless you are sure it is stuck.
- When writing any scripts related to data loading/processing, DO NOT try to load all data into memory at once, use batch processing or data streaming techniques to handle large datasets efficiently.
- When fixing issues or writing improved version, edit the original script directly, do not write new scripts, i.e. DO NOT create files such as train_improved.py, process_fixed.py because this may make the workspace messy and difficult to manage.
- Make sure ALL code, reports and results are in the designated directory (/workspace/subtask_XX).