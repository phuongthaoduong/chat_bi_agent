# ChatBI Evaluation Pack

This folder contains small deterministic datasets for checking whether ChatBI answers correctly.

Files:
- `sales_basic.csv`: single-table sales data for totals, filters, grouping, top-N, and trend questions
- `inventory_status.csv`: inventory data for stock, low-stock, and zero-stock checks
- `receivables_aging.csv`: overdue receivables data for finance-style questions
- `expected_answers.md`: ground-truth questions and answers

Recommended usage:
1. Upload one CSV at a time and ask the listed questions.
2. Compare ChatBI's answer against `expected_answers.md`.
3. Treat mismatched numbers, wrong ranking, missing filters, or unsupported causal claims as failures.

Notes:
- Dates use ISO format for easier parsing.
- Numeric values are kept small enough to verify by hand.
- These datasets are intentionally simple; they are for correctness testing, not stress testing.
