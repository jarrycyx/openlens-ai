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
- When adding figure references, make sure to FIRST CHECK the current workspace for existing figures. INCLUDE ALL EXISTING FIGURES (.png, .pdf, etc) using the following format:
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