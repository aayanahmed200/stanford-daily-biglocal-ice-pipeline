# Stanford Daily: Big Local News Extraction Pipeline

**Live:** [aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline](https://aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline/)

**Series:** [The Price of Prestige](https://aayanahmed200.github.io/stanford-daily-price-of-prestige/) · [PlasticList](https://aayanahmed200.github.io/stanford-daily-plasticlist-eda/) · [Blotter fiction](https://aayanahmed200.github.io/stanford-daily-blotter-fiction/)

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/) [![GitHub Actions](https://img.shields.io/badge/github%20actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)

A Python pipeline for extracting and validating structured information from 965 public press releases in the Big Local News ICE dataset.

## Overview

The pipeline works from raw HTML so the extraction process can also be applied to future releases. It turns narrative text into structured records for reporting workflows, then writes a validation report that says how much of the output is usable.

## How it was made

The pipeline reads the raw HTML bodies of the press releases rather than a pre-parsed export, so the same code can be pointed at a future release. `scripts/extract.py` holds the extractors — dateline locations, named people, agencies, money amounts, quantities and broad action categories — built from sentence patterns to find people and from text cues to separate action types where the dataset's own labels are too broad.

`scripts/validate.py` then checks schema conformance, field completeness, duplicate URLs, body length, ages and dates, and reports what failed instead of dropping records silently. `scripts/pipeline.py` runs both stages and writes the CSV and the report in one pass, which is how `notes/validation_report_sample.md` was produced. The project page is static HTML on the shared series stylesheet, published by a GitHub Actions workflow on every push to `main`.

## Highlights

- Extracts dateline locations, named people where stated, agencies, money amounts, quantities, and broad action categories.
- Uses sentence patterns to identify people and text cues to distinguish action types when dataset labels are broad.
- Validates schema, field completeness, duplicate URLs, body length, ages and dates, then reports what failed instead of dropping it silently.

## Repository contents

- `scripts/extract.py` — the field extractors.
- `scripts/validate.py` — schema, completeness and sanity checks.
- `scripts/pipeline.py` — runs extraction and validation end to end, writing the CSV and the report.
- `site/` — the published project page and the shared series stylesheet.
- `notes/dataset-notes.md`, `notes/validation_report_sample.md` — dataset notes and a five-row smoke-test report.
- `tests/` — extractor, validator and pipeline smoke tests.

## Notes and limitations

The pipeline uses extraction rules and validation checks; extracted fields are not guaranteed to be correct. Each record should be checked against the original press release before it is used in reporting or publication. The coverage figures on the project page come from a five-row smoke test, not the full 965-record run.

## License

MIT — see `LICENSE`.
