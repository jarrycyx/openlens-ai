
Verify if the manuscript is structured in the following order and meets page limits:  

**1. Abstract (≤ 0.5 page)**  
- **Content:** Research gap (1 sentence), Methodology (1 sentence), Key quantitative results, Significance (1 sentence)  
- **Format:** Impersonal passive voice, no citations  
- **Data Source:** Exact values from `/workspace/results/`

**2. Introduction (1–2 pages)**  
- **Structure:**  
  a. Hook (domain significance)  
  b. Literature gap (cite 3+ papers with `\cite`)  
  c. Problem statement  
  d. Hypothesis/Objectives  
  e. Experimental approach overview  
- **Requirement:** Include 1 key quantitative result as inline math from `/workspace/results/`

**3. Related Works (0.5–1 page)**  
- **Structure (in one subsection):**  
  a. Foundational studies (3+ seminal papers)  
  b. Methodological evolution (4+ citations, chronological)  
  c. Critical knowledge gaps (2+ unresolved challenges)  
  d. Positioning statement (how current work advances the field)  
- **Format:** Continuous text; all citations from `/workspace/literature_review.md`

**4. Methods (1–1.5 pages)**  
- **Structure:**  
  a. Experimental Design (with `\ref` to figures)  
  b. Materials/Subjects (exact sample numbers)  
  c. Technical Procedures (chronological with parameters)  
  d. Measurement Protocols (instrument specs)  
  e. Analysis Methods (statistical tests + software versions)  
- **Requirements:**  
  - 3+ cross-references to figures/tables  
  - Equations in `equation` environment with `\label`  
- **Appendices (≤5 pages):** Additional parameters/methods

**5. Experiments (2–3 pages)**  
- **Main Text:**  
  - Methodology (materials, procedure, statistical methods)  
  - Results (quantitative findings, tables/figures, comparisons)  
- **Appendices (≤3 pages):**  
  - Experimental setup (equipment, environment, software, variables)  
- **Data Rules:** All metrics must match `/workspace/results/*.csv`

**6. Conclusion (≤0.4 page)**  
- **Structure:**  
  a. Summary of findings (hypothesis, key results, p-values)  
  b. Implications (theoretical/practical impact, limitations)  
  c. Future work (specific extensions)  
- **Format:** Cautious language; no new data
