# Stanford Daily: Big Local News Extraction Pipeline

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)

A Python pipeline that extracts and validates structured information from 965 public press releases in the Big Local News ICE dataset.

## Overview

The pipeline works from raw HTML so the extraction process can be applied to future releases as well as the supplied dataset. It turns narrative text into records that can be filtered and checked for reporting workflows.

## Highlights

- Extracts dateline locations, named people where stated, agencies, money amounts, quantities, and broad action categories.
- Uses sentence patterns to identify people and text cues to distinguish action types when dataset labels are broad.
- Validates schema, field completeness, duplicate URLs, body length, ages, and dates.

## Technology

Python 3, Hugging Face `datasets`, Beautiful Soup, lxml, pandas, and pytest.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
```

Run tests with `pytest tests/`.

## Notes and limitations

The extraction patterns are precision-first and can miss people described in other ways. The source has no time-of-day field, so dates are date-only. Extracted records are a starting point for analysis, not citable facts; check each field against the original release before reporting it. The source dataset is [`stanforddams/biglocal`](https://huggingface.co/datasets/stanforddams/biglocal) and remains subject to its own terms.

## License

MIT — see `LICENSE`.
