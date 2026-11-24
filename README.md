# Invoice & PO Discrepancy Auditor

## Project goal
A prompt-engineering application that audits Purchase Orders (POs) against vendor invoices and flags quantity, unit-price, currency, line-item and payment-term discrepancies.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Input format
Use plain text with header fields and pipe-separated line items:
`ITEM | QTY | UNIT PRICE | CURRENCY`

## Prompt-engineering components
- Zero-shot baseline
- Role/persona prompting
- Explicit constraints and guardrails
- Few-shot example
- Delimited inputs
- Structured JSON output
- Deterministic validation layer

## Important
The current demo is runnable without an API key. The `final_prompt.txt` is designed to be connected to a multimodal LLM/API for PDF/image extraction. For production, add OCR/document parsing and an LLM call, then validate the JSON before posting results to an ERP/AP system.
