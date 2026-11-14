# Dataset Notes

Notes on `stanforddams/biglocal`, taken while building the extraction pipeline.

## Structure

The dataset ships two subsets that join on `url`:

- **default** — 965 rows, pre-parsed metadata: `title`, `subtitle`, `topics`, `date_raw`, `date_normalized`, `date_last_updated`, `location_full_text`, `city`, `state`, `full_text`, `image_urls`, `scraped_at`, plus two reserved-but-empty columns (`blurb_list`, `updated_date`).
- **html** — 965 rows, the raw HTML source page for each release, keyed by `url`.

Per the [dataset card](https://huggingface.co/datasets/stanforddams/biglocal), this is Project 1 of Big Local News's pitch for the Datathon for Social Good 2026. The brief asks for two things: a structured dataset of enforcement-action date/time/location plus identifying detail about the people named, and **a pipeline that can process press releases published in the future** — which is why this pipeline is built to run on the raw `html` subset (what a future scrape would actually produce), not just the already-parsed `full_text` column.

## What shaped the pipeline

- **The corpus is almost entirely 2025–2026** (956 of 965 records), so the extraction rules were checked against current-era ICE press-release phrasing, not the older wire-style releases.
- **Two distinct "name + age" phrasings recur throughout the corpus:**
  - `"Name, AGE[, of/from Origin]"` — e.g. *"Shem Wayne Alexander, 35, of Port of Spain, Trinidad, faces charges."*
  - `"Name, a AGE-year-old ... of/from Origin"` — e.g. *"Johnny Noviello, a 49-year-old citizen of Canada..."*

  Both are matched by `extract_people()` in `scripts/extract.py`; missing either one would silently drop a meaningful share of the named individuals the assignment is asking for.
- **The dateline (`CITY, ST — `) at the top of the body is a reliable, cheap signal** for location and is extracted separately from `location_full_text`/`city`/`state`, since a future scrape (raw HTML only, no pre-parsed columns) won't have those columns available.
- **`topics` is a useful shortcut for classification, but not sufficient on its own.** `Detainee Death Notifications` reliably means `death_in_custody`, but most other topics (`Narcotics`, `Enforcement and Removal`, `Financial Crimes`, ...) span multiple real action types (arrest vs. indictment vs. sentencing all show up under `Narcotics`). `classify_action()` checks `topics` first for the unambiguous cases, then falls back to text cues (`sentenced`, `indicted`/`charged`, `arrested`, a `Statement`-labeled release) for the rest.
- **No article's press-release text is reproduced beyond short excerpts used as test fixtures.** ICE press releases are U.S. government works and aren't subject to copyright (17 U.S.C. § 105), so this isn't a legal constraint on this specific dataset, but the pipeline and tests are still built to extract *structure* (names, ages, locations, dates, agencies), not to republish full release text.

## Known limitations of the extraction rules

- **Name/age regexes are precision-first, not exhaustive.** They catch the two dominant phrasings above but will miss releases that introduce a person a different way (e.g., a name given in one sentence and their age in a separate sentence later). `person_count == 0` on a release does not mean no one was named — see `notes/validation_report_sample.md` for how often this shows up in practice.
- **No time-of-day field exists in the source data.** `date_normalized` gives a date only; the pipeline does not currently extract time-of-day mentions (e.g., "at 1:36 p.m.") into a structured field, though they do appear in some release bodies (see the `canadian-national-ice-custody-passes-away` example in the smoke test).
- **`origin` extraction assumes the standard "of/from Country" construction** and will miss less direct phrasings (e.g., an origin implied only by a demonym like "Trinidadian" or "Mexican nationals" without a later "of/from Place").
- **Sex/gender is deliberately not extracted.** ICE releases don't state it as a discrete field, and inferring it from pronouns or naming conventions would introduce more error than the field is worth for this use case.

## Reproducing the pipeline

```bash
pip install -r requirements.txt
python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md
python -m pytest tests/
```

See `notes/validation_report_sample.md` for a report generated from a 5-row hand-picked sample (used to sanity-check the pipeline without requiring network access to Hugging Face); run `scripts/pipeline.py` for the real, full-dataset numbers.
