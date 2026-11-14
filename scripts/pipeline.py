"""
End-to-end pipeline: load stanforddams/biglocal -> extract -> validate -> save.

    python scripts/pipeline.py --out data/extracted.csv --report notes/validation_report.md

Requires: datasets, beautifulsoup4, lxml, pandas
    pip install -r requirements.txt

Loads both dataset subsets and joins them on `url`:
  - default subset: pre-parsed metadata + full_text
  - html subset:     raw HTML (used to (re)derive text/title if full_text is missing,
                      and to keep the pipeline runnable against future scrapes that
                      only have raw HTML)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from extract import extract_record
from validate import validate_dataframe, format_report, usable_mask


def load_and_join() -> pd.DataFrame:
    from datasets import load_dataset

    default = load_dataset("stanforddams/biglocal", split="train")
    html = load_dataset("stanforddams/biglocal", "html", split="train")

    df_default = default.to_pandas()
    df_html = html.to_pandas()[["url", "html"]]

    return df_default.merge(df_html, on="url", how="left")


def run(out_path: str, report_path: str, min_word_count: int = 50) -> pd.DataFrame:
    df = load_and_join()

    records = [extract_record(row.to_dict()) for _, row in df.iterrows()]
    out_df = pd.DataFrame(records)

    # Filter on `text` (what extraction actually used: HTML-derived body
    # when available, full_text otherwise) rather than `full_text` directly.
    # On a future scrape with only an `html` field and no `full_text` at
    # all, this keeps rows that extract_record successfully parsed instead
    # of dropping every one of them for having an empty full_text column.
    out_df = out_df[out_df["text"].fillna("").str.split().apply(len) >= min_word_count]

    report = validate_dataframe(out_df)

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(format_report(report))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if out_path.endswith(".jsonl"):
        with open(out_path, "w") as f:
            for rec in out_df.to_dict(orient="records"):
                f.write(json.dumps(rec, default=str) + "\n")
    else:
        out_df.to_csv(out_path, index=False)

    usable = usable_mask(out_df).sum()
    print(f"Extracted {len(out_df)} records ({usable} usable for analysis).")
    print(f"Saved data to {out_path}, report to {report_path}")

    return out_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/extracted.csv")
    parser.add_argument("--report", default="notes/validation_report.md")
    parser.add_argument("--min-word-count", type=int, default=50)
    args = parser.parse_args()
    run(args.out, args.report, args.min_word_count)
