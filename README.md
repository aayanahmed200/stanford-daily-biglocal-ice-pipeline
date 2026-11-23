# Stanford Daily: Big Local News Extraction Pipeline

**Project page:** [aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline](https://aayanahmed200.github.io/stanford-daily-biglocal-ice-pipeline/)

**Series:** [The Price of Prestige](https://aayanahmed200.github.io/stanford-daily-price-of-prestige/) · [PlasticList](https://aayanahmed200.github.io/stanford-daily-plasticlist-eda/) · [Blotter fiction](https://aayanahmed200.github.io/stanford-daily-blotter-fiction/)

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)

A Python pipeline for extracting and validating structured information from 965 public press releases in the Big Local News ICE dataset.

## Overview

The pipeline works from raw HTML so the extraction process can also be applied to future releases. It turns narrative text into structured records for reporting workflows, then writes a validation report that says how much of the output is usable.

## Highlights

- Extracts dateline locations, named people where stated, agencies, money amounts, quantities, and broad action categories.
- Uses sentence patterns to identify people and text cues to distinguish action types when dataset labels are broad.
- Validates schema, field completeness, duplicate URLs, body length, ages and dates, then reports what failed instead of dropping it silently.

## Repository contents

- `scripts/extract.py` - the field extractors.
- `scripts/validate.py` - schema, completeness and sanity checks.
- `scripts/pipeline.py` - runs extraction and validation end to end, writing the CSV and the report.
- `site/` - the published project page and the shared series stylesheet.
- `notes/dataset-notes.md`, `notes/validation_report_sample.md` - dataset notes and a five-row smoke-test report.
- `tests/` - extractor, validator and pipeline smoke tests.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
```

Run tests with:

```bash
pytest tests/
```

## Notes and limitations

The pipeline uses extraction rules and validation checks; extracted fields are not guaranteed to be correct. Check each record against the original press release before using it in reporting or publication. The coverage figures on the project page come from a five-row smoke test, not the full 965-record run.

## License

MIT - see `LICENSE`.
