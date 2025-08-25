

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

3. **Check for Data Integrity:**
   * Verify that the code does not generate simulated or mocked results in place of actual experimental data.
   * Ensure that no synthetic data or fabricated outcomes are present unless explicitly stated in the experimental setup. Note that some datasets may contain shifted years for confidentiality reasons, this does not mean the data is fabricated.
   * **If simulated data is found**, adjust the code to ensure only real data is used and rerun the experiment.
   * Ensure the intermediate results are not demo/minified versions or placeholders.

4. **Check for Abnormal Intermediate Results:**

   * Inspect intermediate results (e.g., partial outputs, metrics during the process) for abnormalities like all values being 100%, 0%, or other unrealistic patterns.
   * Investigate the root cause of such anomalies and ensure they do not stem from errors in data processing or model behavior.
   * **If abnormal results are found**, debug the process and fix any underlying issues, then rerun the code.


Experiment Plan:
{subplan}


IMPORTANT: You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP.