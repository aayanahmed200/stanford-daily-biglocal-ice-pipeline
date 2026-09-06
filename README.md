# Stanford Daily: Big Local News ICE Extraction Pipeline

[![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Hugging Face](https://img.shields.io/badge/hugging%20face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)

A data extraction and validation pipeline for [`stanforddams/biglocal`](https://huggingface.co/datasets/stanforddams/biglocal), 965 press releases published by U.S. Immigration and Customs Enforcement (ICE), curated by [Big Local News](https://biglocalnews.org/) at Stanford University for the Datathon for Social Good 2026. Built for a data journalism assignment at the Stanford Daily.

Pipeline: [`scripts/pipeline.py`](scripts/pipeline.py) · Extraction rules: [`scripts/extract.py`](scripts/extract.py) · Validation: [`scripts/validate.py`](scripts/validate.py)

## Why this exists

Big Local News's brief for this dataset asks for two deliverables: a structured record of the date, time, and location of each enforcement action described in a press release, with as much identifying detail about the people named as the release states — and a pipeline that can keep extracting that structure from press releases published in the future, not just the 965 already scraped. That second requirement is why this pipeline runs on the dataset's raw `html` subset (what a future scrape actually looks like) rather than only the pre-parsed `full_text` column, and why every extraction rule is tested against real release text before being trusted.

Big Local News gathers and structures data like this so that local newsrooms can do accountability reporting without needing their own data specialists. This is exactly that kind of work at a smaller scale: ICE names people, ages, nationalities, and case outcomes in its own releases, but only in narrative prose — this pipeline turns that prose back into structured fields a reporter can filter, count, and cross-reference.

## The data

The dataset ships two joinable subsets: a **default** subset with 965 rows of pre-parsed metadata (`title`, `topics`, `date_normalized`, `city`/`state`, `full_text`, ...), and an **html** subset with the raw source HTML for each release. Full field list and coverage stats are on the [dataset card](https://huggingface.co/datasets/stanforddams/biglocal).

Two things shaped the extraction rules more than anything else:

- **Individuals are introduced in one of two recurring phrasings** — `"Name, AGE, of/from Origin"` (e.g. *"Shem Wayne Alexander, 35, of Port of Spain, Trinidad"*) or `"Name, a AGE-year-old ... of/from Origin"` (e.g. *"Johnny Noviello, a 49-year-old citizen of Canada"*). Missing either one silently drops a meaningful share of named individuals, so `extract_people()` checks for both.
- **`topics` alone isn't a reliable action-type label.** It reliably flags detainee deaths (`Detainee Death Notifications`), but categories like `Narcotics` or `Enforcement and Removal` span arrests, indictments, and sentencings alike — so classification falls back to text cues (`sentenced`, `indicted`/`charged`, `arrested`) when `topics` doesn't resolve it.

Full notes on dataset structure, extraction decisions, and known limitations: [`notes/dataset-notes.md`](notes/dataset-notes.md).

## What the pipeline extracts

For each press release:

| Field | Source |
|---|---|
| `extracted_location` | Dateline at the top of the body text (`CITY, ST —`) |
| `extracted_people` | Named individuals with age and stated origin, where the release includes them |
| `agencies_mentioned` | ICE, HSI, ERO, CBP, FBI, DEA, ATF, DHS, and other named federal/local partners |
| `money_mentioned` | Dollar figures (seizures, fraud amounts, fines) |
| `quantities_mentioned` | Drug/firearm quantities with units |
| `action_type` | Rough classification: arrest, indictment/charge, sentencing, death in custody, statement, other |

`date_normalized`, `city`, and `state` pass through from the dataset's own parsed metadata when available.

## Validation

`scripts/validate.py` checks three things separately so one kind of failure doesn't mask another: **schema** (required fields present), **completeness** (how often each extracted field is actually populated), and **sanity** (duplicate URLs, near-empty bodies, out-of-range ages, unparseable dates). It flags a record "usable for analysis" only if it has both a location and a normalized date and isn't a duplicate. [`tests/test_validate.py`](tests/test_validate.py) covers all three checks directly.

The extraction rules are tested against real dataset excerpts (not invented examples) in [`tests/test_extract.py`](tests/test_extract.py) — 17 tests covering datelines, both person-naming patterns, agency/money/quantity extraction, action classification, and HTML parsing, all passing. [`tests/test_pipeline_smoke.py`](tests/test_pipeline_smoke.py) runs the full extract → validate flow end-to-end on a small hand-picked sample, including a deliberately malformed row, to confirm the pipeline degrades gracefully instead of crashing on bad data. A sample report from that smoke test is in [`notes/validation_report_sample.md`](notes/validation_report_sample.md); it understates real coverage because the sample rows use the dataset's truncated preview text, not full release bodies.

## Tech stack

- Python 3
- [`datasets`](https://pypi.org/project/datasets/) (Hugging Face, dataset loading)
- `beautifulsoup4` + `lxml` (HTML parsing)
- `pandas` (dataframes, CSV/JSONL output)
- `pytest` for the extraction, validation, and pipeline tests

## Project structure

- `scripts/extract.py` — HTML parsing and structured entity extraction rules
- `scripts/validate.py` — schema, completeness, and sanity-check validation
- `scripts/pipeline.py` — CLI entrypoint: load dataset → extract → validate → save
- `tests/test_extract.py` — unit tests against real dataset excerpts
- `tests/test_validate.py` — unit tests for the schema/completeness/sanity checks
- `tests/test_pipeline_smoke.py` — small end-to-end integration test
- `notes/dataset-notes.md` — dataset structure, extraction decisions, and known limitations
- `notes/validation_report_sample.md` — sample validation report
- `LICENSE`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
```

Run the tests with `pytest tests/`.

## Limitations

This is a class data-extraction exercise, not a finished accountability-journalism product. The name/age/origin regexes are precision-first and tuned to the two dominant phrasings in this corpus — they will miss releases that introduce people differently, and `person_count == 0` does not mean no one was named in the release. There's no time-of-day field in the source data, so extracted dates are date-only. See `notes/dataset-notes.md` for the full list, and treat every extracted field as a starting point for reporting, not a citable fact, without checking it against the original release.

## Contributors

- [@timofeywheat-wq](https://github.com/timofeywheat-wq)

## License

MIT — see [LICENSE](LICENSE). The underlying dataset is
[`stanforddams/biglocal`](https://huggingface.co/datasets/stanforddams/biglocal) on
Hugging Face; see its own license/terms for reuse of the raw data.
