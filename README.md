# Stanford Daily: Big Local News Extraction Pipeline

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)

A Python pipeline that extracts and validates structured information from 965 public press releases in the Big Local News ICE dataset.

## Overview

The pipeline works from raw HTML so the extraction process can be applied to future releases as well as the supplied dataset. It turns narrative text into structured records for reporting workflows; check extracted fields against the original release before publication.

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


## License

MIT — see `LICENSE`.
