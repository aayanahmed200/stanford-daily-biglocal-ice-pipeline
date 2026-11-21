# Big Local News ICE Extraction Pipeline

A Python pipeline that extracts structured fields from ICE-related press-release records in the Hugging Face `stanforddams/biglocal` dataset and checks the resulting records for consistency.

## Overview

The pipeline loads the dataset's metadata and HTML subsets, joins them by URL, extracts fields from each release and writes a CSV or JSONL file. It also produces a validation report. The extracted fields include locations, people and organisations when stated, quantities, monetary amounts and broad action categories.

## Repository contents

- `scripts/pipeline.py` — loads the source dataset, runs extraction and writes results.
- `scripts/extract.py` — extracts structured fields from release content.
- `scripts/validate.py` — checks extracted records and formats the validation report.
- `data/` — destination for generated output; the source dataset is fetched when the pipeline runs.
- `notes/` — destination for the generated validation report.
- `tests/` — tests for extraction and validation.

## Technology

Python, Hugging Face `datasets`, pandas, Beautiful Soup, lxml and pytest. The source records are loaded from Hugging Face, so the pipeline needs an internet connection.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
```

Run the tests with:

```bash
pytest tests/
```

The script also accepts `--min-word-count` to change the minimum body-text length used when retaining records.

## Scope and limitations

Extraction is rule-based and some fields may be missing, ambiguous or incorrectly identified. The validation report checks structure and consistency; it does not establish that every extracted value is correct. Verify records against the original press release before using them in reporting or publication. The dataset is fetched from its upstream source at run time and may change.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
