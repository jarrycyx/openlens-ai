---
name: latex_reminders
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- latex
- paper
---

Reminders: 
- When adding figure references, make sure to FIRST CHECK the current workspace for existing figures. Description of the figures can be found in /workspace/manuscript/figures/xxx_description.txt. INCLUDE ALL EXISTING FIGURES (.png, .pdf, etc) using the following format:
```
\begin{figure}[htbp]
\centering
\includegraphics[width=0.x\textwidth]{figures/figure_name.png}
\caption{Figure caption}
\label{fig:figure_name}
\end{figure}
```
and refer to them using \ref{fig:figure_name}

- DO NOT draw new figures when writing paper unless ABSOLUTELY NECESSARY.
- Make sure the paper is structures in the order and meets length limits:
  - 1. Abstract (≤ 300 words)  
  - 2. Introduction (600-1200 words)  
  - 3. Related Works (300-600 words)  
  - 4. Methods (1000-2000 words)  
  - 5. Experiments (1000-2000 words)  
  - 6. Conclusion (300 words)  
  - 7. References (10+ citations)
  - 8. Appendix
- When fixing issues or writing improved version, edit the original files directly, do not write new files, i.e. DO NOT create files such as main_improved.tex, main_fixed.tex, main_clean.tex, main_fixed.pdf, etc because this may make the workspace messy and difficult to manage.
- Only write latex files, reports and compile pdf in the designated directory (/workspace/manuscript), do not create files outside the directory (i.e., DO NOT CREATE ANY FILES directly in /workspace or its other subdirectories).
- NEVER DOWNLOAD texlive or any other version of texlive because it is already installed in the container, if pdflatex, xeletex, or latex is not found, execute ```export PATH=/usr/local/texlive/2025/bin/x86_64-linux/:$PATH```.