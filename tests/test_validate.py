"""
Tests for scripts/validate.py.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import validate_dataframe, usable_mask  # noqa: E402


def test_missing_required_counts_nan_and_empty_string_separately():
    # 2 rows with a NaN title, 2 different rows with an empty-string title,
    # 1 row with a real title -> 4 total rows missing a required field.
    # (Regression test: an earlier version used `isna().sum() | (== "").sum()`,
    # a bitwise OR of two counts, which silently undercounted this case.)
    df = pd.DataFrame({
        "url": ["u1", "u2", "u3", "u4", "u5"],
        "title": [None, None, "", "", "Real Title"],
    })
    report = validate_dataframe(df)
    assert report["schema"]["missing_counts"]["title"] == 4
    assert report["schema"]["passes"] is False


def test_schema_passes_when_required_fields_fully_populated():
    df = pd.DataFrame({
        "url": ["u1", "u2"],
        "title": ["Title A", "Title B"],
    })
    report = validate_dataframe(df)
    assert report["schema"]["missing_counts"] == {"url": 0, "title": 0}
    assert report["schema"]["passes"] is True


def test_usable_mask_requires_location_date_and_unique_url():
    df = pd.DataFrame({
        "url": ["u1", "u1", "u2", "u3"],  # u1 is a duplicate
        "extracted_location": ["Tampa, FL", "Tampa, FL", None, "Miami, FL"],
        "date_normalized": ["06/25/2025", "06/25/2025", "06/25/2025", ""],
    })
    mask = usable_mask(df)
    # row 0: usable | row 1: duplicate url -> excluded | row 2: no location -> excluded
    # row 3: empty date -> excluded
    assert mask.tolist() == [True, False, False, False]
