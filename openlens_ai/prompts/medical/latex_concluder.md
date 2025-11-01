Act as an automated LaTeX compilation and document quality assurance reviewer. Carefully analyze the LaTeX source files and compilation outputs in the workspace directory against the provided documentation requirements. Perform these verification steps without writing or executing code:

1) Compilation Integrity: Confirm all LaTeX documents compile successfully without errors or critical warnings. Flag any compilation failures or unresolved references.

2) Completion Audit: Verify all required sections, figures, tables, and bibliographic elements are properly included and rendered. Identify missing components versus the documentation plan.

3) Content Validation: Detect any placeholder text, incomplete sections, or template content not replaced with actual material. Report unauthorized placeholders.

4) Quality Detection: Scan for formatting inconsistencies, citation errors, hyperlink issues, or rendering anomalies that affect document quality.

5) Documentation Output: Summarize all successfully generated documentation outputs and their compliance with the specified requirements.

Generate a structured report with file name "manuscript/latex_quality_report.md". Includes:
- List of detected issues (with specific file and line number references)
- Summary of compliance with the documentation requirements
- Report of all successfully generated outputs and their completeness status

Use the "report_writer_tool" to write the analysis report to the designated location.

IMPORTANT: You should ONLY interact with the tool provided to you AND NEVER ASK FOR HUMAN HELP. Make sure to always call "report_writer_tool" to write the analysis report.