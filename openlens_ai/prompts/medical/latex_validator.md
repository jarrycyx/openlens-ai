
Verify if the manuscript is structured in the following order and meets length limits:  

**1. Abstract (≤ 300 words)**  
- **Content:** Research gap (1 sentence), Methodology (1 sentence), Key quantitative results, Significance (1 sentence)  
- **Format:** Impersonal passive voice, no citations  
- **Data Source:** Exact values from `/workspace/results/`

**2. Introduction (600-1200 words)**  
- **Structure:**  
  a. Hook (domain significance)  
  b. Literature gap (cite 3+ papers with `\cite`)  
  c. Problem statement  
  d. Hypothesis/Objectives  
  e. Experimental approach overview  
- **Requirement:** Include 1 key quantitative result as inline math from `/workspace/results/`
- **Reminder:** Make sure no figures or tables are included in introduction or the first page.

**3. Related Works (300-600 words)**  
- **Structure (in one subsection):**  
  a. Foundational studies (3+ seminal papers)  
  b. Methodological evolution (4+ citations, chronological)  
  c. Critical knowledge gaps (2+ unresolved challenges)  
  d. Positioning statement (how current work advances the field)  
- **Format:** Continuous text; all citations from `/workspace/literature_review.md`

**4. Methods (1000-2000 words)**  
- **Structure:**  
  a. Experimental Design (with `\ref` to figures)  
  b. Materials/Subjects (exact sample numbers)  
  c. Technical Procedures (chronological with parameters)  
  d. Measurement Protocols (instrument specs)  
  e. Analysis Methods (statistical tests + software versions)  
- **Requirements:**  
  - 3+ cross-references to figures/tables (figures are in /workspace/manuscript/figures/)
  - Equations in `equation` environment with `\label`  
- **Appendices (≤5 words):** Additional parameters/methods
- **Reminder:** Make sure all relevant figures/tables are included in the Methods section.

**5. Experiments (1000-2000 words)**  
- **Main Text:**  
  - Methodology (materials, procedure, statistical methods)  
  - Results (quantitative findings, tables/figures, comparisons)  
- **Appendices (1000-10000 words):**  
  - Experimental setup (equipment, environment, software, variables)    
- **Requirements:**  
  - 3+ cross-references to figures/tables (figures are in /workspace/manuscript/figures/)
- **Data Rules:** All metrics must match `/workspace/results/*.csv`
- **Reminder:** Make sure all relevant figures/tables are included in the Experiments section.

**6. Conclusion (300 words)**  
- **Structure:**  
  a. Summary of findings (hypothesis, key results, p-values)  
  b. Implications (theoretical/practical impact, limitations)  
  c. Future work (specific extensions)  
- **Format:** Cautious language; no new data

**7. References (10+ citations)**
- **Source:** All citations from `/workspace/literature_review.md` using BibTeX
- **Format:** BibTeX entries in `/workspace/manuscript/ref.bib`
- Consistent citation style throughout

**8. Appendix**
- **Content:** Any additional material that may be helpful for the reader, such as supplementary data, code, or figures
- **Reminder:** Make sure all relevant figures/tables are included in the Appendix section.

**If issues are found**, rewrite and fix any underlying issues, then re-compile the manuscript.

Reminders: 
- When adding figure references, make sure to FIRST CHECK the current workspace for existing figures. REFERENCE ALL EXISTING FIGURES (.png, .pdf, etc).  Description of the figures can be found in /workspace/manuscript/figures/xxx_description.txt
- DO NOT draw new figures when writing paper unless ABSOLUTELY NECESSARY.
- When fixing issues or writing improved version, edit the original files directly, do not write new files, i.e. DO NOT create files such as main_improved.tex, main_fixed.py because this may make the workspace messy and difficult to manage.
- Make sure the all texts are written in the specified language.

Availabel Figures:
{figures}