# Invoice & PO Discrepancy Auditor — Evaluation Package

Files:
- evaluation_30_cases.json — 30 test cases
- prompt_versions.txt — four prompt versions required for the PBL
- ground_truth_results.csv — expected field-level labels
- run_evaluation.py — evaluates the deterministic audit engine
- evaluation_category_summary.csv — test-case distribution

Run:
1. Copy these files into your project folder.
2. Open PowerShell in that folder.
3. Run: py run_evaluation.py

Important:
The 30-case evaluation measures the document-comparison engine. Do not invent LLM accuracy numbers.
Because the local Llama 3.2 1B model takes about 29 seconds even for a tiny request on this machine, running all 30 cases through four LLM prompts would be unnecessarily slow. For the report, use the deterministic 30-case evaluation for correctness and use the four prompt versions to document iterative prompt engineering. If actual LLM prompt accuracy is required, run a smaller controlled LLM subset and report the real measurements.
