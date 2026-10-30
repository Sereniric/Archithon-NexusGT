# PS01 — Explainable Application Privacy and Permission Analyzer

This directory contains the Step 1 project foundation for the privacy and permission analyzer.

## Requirements

- Python
- Streamlit
- defusedxml
- pandas
- pytest

## Run

From the repository root, run:

```bash
streamlit run PS01/frontend/app.py
```

## Tests

```bash
pytest PS01/backend/tests
```

PS01 is fully implemented through Step 7. It provides a safe Android manifest permission extractor, deterministic permission explanations, privacy-policy topic extraction with supporting excerpts, permission-to-policy comparison, optional application-purpose analysis, and a downloadable evidence-linked Markdown report. Unknown permissions remain unknown; the report and interface do not claim actual runtime behavior, maliciousness, safety, or risk.

## Generate a report

1. Run the application from the repository root:

```bash
streamlit run PS01/frontend/app.py
```

2. Upload an Android manifest and optionally upload or paste a privacy policy.
3. Analyze the policy and provide an application name/purpose if desired.
4. Select **Generate report**, then use **Download report (.md)**.
