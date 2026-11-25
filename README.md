# Big Local News ICE Data Extraction Pipeline

> A Python pipeline that extracts and validates structured records from the Stanford Daily Tech Practicum's Big Local News ICE press-release dataset.

**Live project page:** [aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline](https://aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline/)

**Stanford Daily series:** [The Price of Prestige](https://aayanahmed200.github.io/stanford-daily-price-of-prestige/) · [PlasticList EDA](https://aayanahmed200.github.io/stanford-daily-plasticlist-eda/) · [Blotter Fiction](https://aayanahmed200.github.io/stanford-daily-blotter-fiction/)

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/) [![Pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/) [![GitHub Actions](https://img.shields.io/badge/github%20actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)

## Overview

The pipeline processes the public `stanforddams/biglocal` dataset, which contains ICE-related press-release records. It extracts structured fields from release text and HTML, including dateline locations, named people where stated, agencies, money amounts, quantities, and broad action categories. A validation stage checks the resulting records and produces a report describing missing or suspicious fields.

The project page documents the pipeline and its validation approach; it is not a claim that all extracted fields are fully verified.

## Highlights

- Loads the dataset's pre-parsed and HTML subsets and joins records by URL.
- Extracts locations, people, agencies, amounts, quantities, and action categories.
- Validates schema conformance, field completeness, duplicate URLs, body length, ages, and dates.
- Writes a structured CSV or JSONL output plus a Markdown validation report.
- Includes tests for extraction, validation, and end-to-end pipeline behaviour.

## Implementation

The extraction rules are in `scripts/extract.py`, validation is in `scripts/validate.py`, and `scripts/pipeline.py` runs both stages. The pipeline uses Hugging Face `datasets` to load the public dataset, Beautiful Soup and lxml to work with HTML, and pandas to assemble and write records.

The project page is static HTML in `site/` and is published to GitHub Pages by GitHub Actions when changes are pushed to `main`.

## Repository structure

- `scripts/extract.py` — field extraction rules.
- `scripts/validate.py` — schema, completeness, and sanity checks.
- `scripts/pipeline.py` — end-to-end loading, extraction, validation, and export.
- `data/` — location for generated structured output.
- `notes/` — source-dataset notes and validation-report examples.
- `tests/` — extractor, validator, and pipeline tests.
- `site/` — published project page and shared series stylesheet.
- `requirements.txt` — Python dependencies.

## Run locally

Install dependencies and run the pipeline from the repository root:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
```

The script downloads the dataset from Hugging Face, so a network connection is required. Use `--out`, `--report`, and `--min-word-count` to change the output paths or minimum body length.

## Status and limitations

The extraction logic uses rules and text cues, so extracted values are candidates for review rather than verified facts. Records should be checked against their original press releases before use in reporting or publication. The coverage figures shown on the project page are based on a five-row smoke-test report, not a completed full-dataset validation run.

## License

MIT. See [LICENSE](LICENSE).
