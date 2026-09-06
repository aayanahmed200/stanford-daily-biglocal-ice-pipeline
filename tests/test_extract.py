"""
Tests for scripts/extract.py.

The text fixtures below are short excerpts of actual ICE press releases
(as previewed on the stanforddams/biglocal dataset page). ICE press
releases are U.S. government works and are not subject to copyright
(17 U.S.C. Sec. 105); they're used here, unmodified, purely to check the
extraction rules against real dataset text rather than invented examples.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from extract import (  # noqa: E402
    parse_html,
    extract_dateline,
    extract_people,
    extract_agencies,
    extract_money,
    extract_quantities,
    classify_action,
    extract_record,
)

PHOENIX_TEXT = (
    "PHOENIX, Ariz. \u2013 Two Mexican nationals who are targets of an ongoing "
    "U.S. Immigration and Customs Enforcement investigation appeared for their "
    "initial appearances Feb. 28, after they were secured from Mexico the "
    "previous day. Jose Bibiano Cabrera-Cabrera, 37 and Jesus Humberto "
    "Limon-Lopez, 43, were taken into U.S. custody."
)

TAMPA_TEXT = (
    "TAMPA, Fla. \u2014 A Trinidadian national, and international firearms "
    "trafficking organization ringleader, has been indicted with conspiracy "
    "to commit smuggling and conspiracy to traffic firearms following a "
    "Homeland Security Investigations (HSI) Tampa investigation. Shem Wayne "
    "Alexander, 35, of Port of Spain, Trinidad, faces charges."
)

FORT_MYERS_TEXT = (
    "FORT MYERS, Fla. \u2013 An investigation by U.S. Immigration and Customs "
    "Enforcement led to Tomas Juarez-Santos, 45, a four-time removed criminal "
    "illegal alien from Mexico with two prior convictions for illegal reentry "
    "after deportation, being sentenced March 11 to more than a year in "
    "federal prison for illegally reentering the United States."
)

MIAMI_MONEY_TEXT = (
    "NEW ORLEANS \u2014 announced the seizure of $39.5 million in counterfeit "
    "sports merchandise through Operation Team Player, alongside HSI and CBP."
)


def test_extract_dateline_phoenix():
    location, rest = extract_dateline(PHOENIX_TEXT)
    assert location == "PHOENIX, Ariz."
    assert rest.startswith("Two Mexican nationals")


def test_extract_dateline_tampa():
    location, _ = extract_dateline(TAMPA_TEXT)
    assert location == "TAMPA, Fla."


def test_extract_dateline_none_when_no_dash_lead():
    location, rest = extract_dateline("No dateline here at all, just prose.")
    assert location is None
    assert rest == "No dateline here at all, just prose."


def test_extract_dateline_ignores_update_prefix():
    # "UPDATE - ..." reads like a dateline (all-caps word, then a dash) but
    # isn't a location -- ICE uses it to flag a follow-up to an earlier
    # release.
    text = (
        "UPDATE - Suspect previously reported at large has been taken "
        "into custody."
    )
    location, rest = extract_dateline(text)
    assert location is None
    assert rest == text


def test_extract_people_two_names_phoenix():
    people = extract_people(PHOENIX_TEXT)
    names = {p["name"] for p in people}
    assert "Jose Bibiano Cabrera-Cabrera" in names
    assert "Jesus Humberto Limon-Lopez" in names
    ages = {p["name"]: p["age"] for p in people}
    assert ages["Jose Bibiano Cabrera-Cabrera"] == 37
    assert ages["Jesus Humberto Limon-Lopez"] == 43


def test_extract_people_with_origin_tampa():
    people = extract_people(TAMPA_TEXT)
    assert len(people) == 1
    assert people[0]["name"] == "Shem Wayne Alexander"
    assert people[0]["age"] == 35
    assert people[0]["origin"] == "Port of Spain, Trinidad"


def test_extract_people_no_false_positive_on_dateline_stopwords():
    # "FORT MYERS, Fla." precedes the sentence; make sure the location
    # itself is never mistaken for a person's name.
    people = extract_people(FORT_MYERS_TEXT)
    names = [p["name"] for p in people]
    assert "Fort Myers" not in names
    assert any(n == "Tomas Juarez-Santos" for n in names)


def test_extract_people_merges_duplicate_across_patterns():
    # First mention has no origin (matched by _PERSON_RE); a later mention of
    # the same person in the "a NN-year-old ... of Country" phrasing adds the
    # origin. The merged record should keep the origin, not drop it because
    # the name was already "seen" by the first pattern.
    text = (
        "Maria Elena Torres-Reyes, 29, was arrested Tuesday during a "
        "targeted enforcement operation. Officials confirmed Maria Elena "
        "Torres-Reyes, a 29-year-old national of Honduras, remains in "
        "custody pending removal proceedings."
    )
    people = extract_people(text)
    matches = [p for p in people if p["name"] == "Maria Elena Torres-Reyes"]
    assert len(matches) == 1
    assert matches[0]["origin"] == "Honduras"


def test_extract_record_sets_text_field_from_full_text():
    example = {
        "url": "https://www.ice.gov/news/releases/example",
        "title": "Example release",
        "full_text": FORT_MYERS_TEXT,
    }
    record = extract_record(dict(example))
    assert record["text"] == FORT_MYERS_TEXT


def test_extract_record_sets_text_field_from_html_when_no_full_text():
    # Simulates a future scrape that only has the html column (no full_text
    # at all). extract_record should still populate `text` from the parsed
    # HTML, so a downstream word-count filter keyed on `text` -- not
    # `full_text` -- doesn't drop the row.
    html = """
    <html><head><title>Sample Release | ICE</title></head><body>
    <article>
        <p>PHOENIX, Ariz. -- Sample lead paragraph with enough words to
        clear a minimum word-count filter for testing purposes here.</p>
        <p>Second paragraph with more detail about the operation.</p>
    </article>
    </body></html>
    """
    example = {"url": "https://www.ice.gov/news/releases/example-2", "html": html}
    record = extract_record(example)
    assert "full_text" not in record or not record.get("full_text")
    assert record["text"]
    assert len(record["text"].split()) > 0


def test_extract_record_handles_nan_html_from_left_merge():
    # Regression test: pipeline.py left-merges the default and html subsets
    # on `url`. A row with no match in the html subset gets `html = nan` (a
    # float), not None or "" -- `bool(float("nan"))` is True, so the old
    # `if example.get("html"):` guard treated it as real content and called
    # parse_html(nan), which crashed with a TypeError inside BeautifulSoup.
    example = {
        "url": "https://www.ice.gov/news/releases/unmatched-row",
        "title": "Some title",
        "topics": "Narcotics",
        "html": float("nan"),
    }
    record = extract_record(dict(example))  # must not raise
    assert record["text"] == ""
    assert record["extracted_people"] == []
    assert record["money_mentioned"] == []
    assert record["action_type"] == "other"


def test_extract_record_handles_nan_full_text():
    # Same NaN-truthiness bug, on the `full_text` fallback path: `nan or ""`
    # returns `nan` (not ""), because bool(nan) is True -- `text` then held
    # a float, and passing it into extract_dateline()/etc. crashed.
    example = {
        "url": "https://www.ice.gov/news/releases/no-text-row",
        "title": "Some title",
        "topics": "Narcotics",
        "full_text": float("nan"),
    }
    record = extract_record(dict(example))  # must not raise
    assert record["text"] == ""


def test_extract_record_handles_nan_topics():
    # classify_action()'s `if topics and ...` has the same bug: with
    # topics = nan, `"Detainee Death" in topics` raised a TypeError since a
    # float isn't iterable.
    example = {
        "url": "https://www.ice.gov/news/releases/no-topics-row",
        "title": "Some title",
        "topics": float("nan"),
        "full_text": FORT_MYERS_TEXT,
    }
    record = extract_record(dict(example))  # must not raise
    assert record["action_type"] == "sentencing"


def test_extract_agencies():
    agencies = extract_agencies(TAMPA_TEXT)
    assert "HSI" in agencies


def test_extract_money():
    assert extract_money(MIAMI_MONEY_TEXT) == ["$39.5 million"]


def test_extract_money_stops_at_word_boundary_after_suffix():
    # Regression test: the (million|billion|M|B) suffix alternation used to
    # have no trailing word boundary, so a dollar amount immediately
    # followed by a capitalized word starting with M or B had that word's
    # leading letter swallowed into the match, e.g. "$500 Monday" wrongly
    # matched as "$500 M" instead of stopping at "$500".
    cases = [
        ("The fine totaled $500 Monday morning after the hearing.", "$500"),
        ("Court records show a $2,000 Bond was posted for his release.", "$2,000"),
        ("He forfeited $1,000 Because he failed to appear as ordered.", "$1,000"),
        ("The judge set bail at $750 Both defendants were released.", "$750"),
    ]
    for text, expected in cases:
        assert extract_money(text) == [expected], text


def test_extract_quantities():
    text = "agents seized 89 kilograms of cocaine and 3 firearms during the raid"
    quantities = extract_quantities(text)
    units = {q["unit"] for q in quantities}
    assert "kilograms" in units
    assert "firearms" in units


def test_classify_action_sentencing():
    assert classify_action("Narcotics", FORT_MYERS_TEXT) == "sentencing"


def test_classify_action_death_by_topic():
    assert classify_action("Detainee Death Notifications", "some body text") == "death_in_custody"


def test_classify_action_indictment():
    assert classify_action("Financial Crimes", TAMPA_TEXT) == "indictment_or_charge"


def test_parse_html_strips_scripts_and_styles():
    html = """
    <html><head><title>Sample Release | ICE</title>
    <style>.hidden{display:none}</style>
    <script>trackPage();</script>
    </head><body>
    <nav>Home | News | Contact</nav>
    <article>
        <p>PHOENIX, Ariz. -- Sample lead paragraph.</p>
        <p>Second paragraph with more detail.</p>
    </article>
    <script>console.log('footer script')</script>
    </body></html>
    """
    parsed = parse_html(html)
    assert parsed["title"] == "Sample Release | ICE"
    assert "Sample lead paragraph" in parsed["text"]
    assert "trackPage" not in parsed["text"]
    assert parsed["paragraph_count"] == 2
    assert parsed["word_count"] > 0


def test_extract_record_end_to_end_from_full_text():
    example = {
        "url": "https://www.ice.gov/news/releases/example",
        "title": "Example release",
        "topics": "Narcotics",
        "date_normalized": "03/14/2025",
        "full_text": FORT_MYERS_TEXT,
        "location_full_text": "FORT MYERS, Fla.",
    }
    record = extract_record(dict(example))
    assert record["extracted_location"] == "FORT MYERS, Fla."
    assert record["action_type"] == "sentencing"
    assert record["person_count"] >= 1
    assert "ICE" in record["agencies_mentioned"]
