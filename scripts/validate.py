"""
Validation pass for extracted ICE press-release records.

Checks three separate things, deliberately kept apart so a failure in one
doesn't hide a failure in another:

  1. Schema      - required fields are present on every record
  2. Completeness - how often each extracted field is actually populated
  3. Sanity       - values that are present but implausible (bad ages,
                    duplicate URLs, unparseable dates, empty bodies)

`validate_dataframe()` returns a report dict; `usable_mask()` turns that
into a boolean filter you can apply before using the data downstream. This
mirrors the `validate()` step in the assignment's starter snippet, but
checks the extracted accountability fields, not just word/paragraph counts.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

REQUIRED_FIELDS = ["url", "title"]

# At least one of these should be populated for a record to be "usable" for
# the accountability-journalism use case (location + date of the action).
CORE_FIELDS = ["extracted_location", "date_normalized"]


def _pct(n: int, total: int) -> float:
    return round(100 * n / total, 1) if total else 0.0


def validate_dataframe(df: pd.DataFrame) -> dict:
    total = len(df)
    report: dict = {"total_records": total}

    # 1. Schema -----------------------------------------------------------
    missing_required = {
        field: int((df[field].isna() | (df[field] == "")).sum())
        for field in REQUIRED_FIELDS
        if field in df.columns
    }
    report["schema"] = {
        "required_fields_checked": REQUIRED_FIELDS,
        "missing_counts": missing_required,
        "passes": all(v == 0 for v in missing_required.values()),
    }

    # 2. Completeness -------------------------------------------------------
    completeness = {}
    for col in [
        "extracted_location", "date_normalized", "extracted_people",
        "agencies_mentioned", "action_type",
    ]:
        if col not in df.columns:
            continue
        if col in ("extracted_people", "agencies_mentioned"):
            filled = df[col].apply(lambda v: bool(v)).sum()
        else:
            filled = df[col].notna().sum()
        completeness[col] = {"filled": int(filled), "pct": _pct(filled, total)}
    report["completeness"] = completeness

    # 3. Sanity checks ------------------------------------------------------
    issues = {}

    dupes = df["url"].duplicated().sum() if "url" in df.columns else 0
    issues["duplicate_urls"] = int(dupes)

    # `text` (not `full_text`) is the canonical body field extract_record()
    # produces either way — HTML-derived when available, falling back to
    # full_text otherwise (see extract.py). Checking full_text directly here
    # both skips this check entirely on an HTML-only future scrape (no
    # full_text column at all) and can flag a row with a perfectly good
    # derived body just because its separate, unused full_text cell is NaN.
    empty_body = 0
    if "text" in df.columns:
        empty_body = (df["text"].fillna("").str.len() < 50).sum()
    issues["empty_or_near_empty_body"] = int(empty_body)

    bad_ages = 0
    if "extracted_people" in df.columns:
        def _bad_ages(people):
            if not isinstance(people, list):
                return 0  # NaN/None/missing -- nothing to flag
            return sum(1 for p in people if not (0 < p.get("age", -1) <= 110))
        bad_ages = df["extracted_people"].apply(_bad_ages).sum()
    issues["out_of_range_ages"] = int(bad_ages)

    bad_dates = 0
    if "date_normalized" in df.columns:
        def _bad_date(d):
            # A NaN float (a genuinely missing date, common with real
            # scraped data) is falsy but not a string, so `datetime.strptime`
            # would raise TypeError, not the ValueError this was built to
            # catch -- checking `isinstance(d, str)` first keeps missing
            # dates out of this check instead of crashing the pipeline.
            if not isinstance(d, str) or not d:
                return False
            try:
                datetime.strptime(d, "%m/%d/%Y")
                return False
            except ValueError:
                return True
        bad_dates = df["date_normalized"].apply(_bad_date).sum()
    issues["unparseable_dates"] = int(bad_dates)

    report["sanity_issues"] = issues

    # Overall usable-for-analysis count: has both a location and a date.
    if all(f in df.columns for f in CORE_FIELDS):
        usable = usable_mask(df).sum()
        report["usable_for_analysis"] = {
            "count": int(usable),
            "pct": _pct(usable, total),
        }

    return report


def usable_mask(df: pd.DataFrame) -> pd.Series:
    """Rows with at least a location and a normalized date, no duplicate URL."""
    mask = pd.Series(True, index=df.index)
    for field in CORE_FIELDS:
        if field in df.columns:
            mask &= df[field].notna() & (df[field] != "")
    if "url" in df.columns:
        mask &= ~df["url"].duplicated()
    return mask


def format_report(report: dict) -> str:
    """Render the report dict as a short Markdown summary."""
    lines = ["# Validation report", "", f"Total records: **{report['total_records']}**", ""]

    lines.append("## Schema")
    lines.append(f"- Passes: **{report['schema']['passes']}**")
    for field, count in report["schema"]["missing_counts"].items():
        lines.append(f"- Missing `{field}`: {count}")
    lines.append("")

    lines.append("## Completeness")
    for field, stats in report["completeness"].items():
        lines.append(f"- `{field}`: {stats['filled']} / {report['total_records']} ({stats['pct']}%)")
    lines.append("")

    lines.append("## Sanity issues")
    for issue, count in report["sanity_issues"].items():
        lines.append(f"- {issue.replace('_', ' ')}: {count}")
    lines.append("")

    if "usable_for_analysis" in report:
        u = report["usable_for_analysis"]
        lines.append(f"## Usable for analysis: {u['count']} / {report['total_records']} ({u['pct']}%)")

    return "\n".join(lines)
