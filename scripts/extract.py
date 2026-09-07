"""
Structured extraction for stanforddams/biglocal (ICE press releases).

Turns each raw press-release page into the fields the Datathon brief asks
for: enforcement-action date/location, named individuals with age and
country of origin where the release states them, agencies involved, and a
rough action-type classification (arrest / indictment / sentencing /
death-in-custody / statement / other).

Two entry points:

    parse_html(html)        -> title, cleaned body text, basic HTML stats
    extract_record(example) -> full structured record, safe to use as a
                                `.map()` function over the HF dataset

Everything else is a focused helper so each extraction rule can be tested
and audited on its own; see tests/test_extract.py.
"""

from __future__ import annotations

import math
import re
from typing import Optional

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# NaN-safe "is this field actually missing?" check
# ---------------------------------------------------------------------------
#
# Rows processed here often come straight from a pandas DataFrame (see
# pipeline.py's left-merge of the default/html subsets): a column with no
# value for a given row shows up as a float `nan`, not `None` or `""`. Plain
# `if value:` / `if not value:` checks get this wrong because
# `bool(float("nan"))` is `True` in Python -- NaN slips through every plain
# truthiness guard as if it were valid, present content, and then crashes
# whatever downstream code tries to treat it as a string. Use this helper
# instead of bare truthiness anywhere a field might be NaN.


def _is_missing(value: object) -> bool:
    """True for None, NaN, and other falsy values (e.g. "", [])."""
    if isinstance(value, float) and math.isnan(value):
        return True
    return not value


# ---------------------------------------------------------------------------
# HTML -> text  (extends the starter snippet from the assignment brief)
# ---------------------------------------------------------------------------

def parse_html(html: str) -> dict:
    """Strip an ICE press-release page down to title + body text + basic stats."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else None

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if p]  # drop empty <p> tags
    full_text = " ".join(paragraphs)

    return {
        "title": title,
        "text": full_text,
        "word_count": len(full_text.split()),
        "paragraph_count": len(paragraphs),
        "link_count": len(soup.find_all("a")),
        "image_count": len(soup.find_all("img")),
    }


# ---------------------------------------------------------------------------
# Dateline: "CITY, ST — " or "CITY —" at the start of the body text
# ---------------------------------------------------------------------------

# ICE datelines are ALL-CAPS city (optionally ", St." / ", Country"), then an
# em dash, en dash, or hyphen before the story starts.
_DATELINE_RE = re.compile(
    r"^\s*([A-Z][A-Za-z.'\-]*(?:\s[A-Z][A-Za-z.'\-]*)*(?:,\s*[A-Za-z.]+(?:\s[A-Za-z.]+)*)?)\s*[—–-]\s*"
)

# Words ICE sometimes leads a release with that look like a dateline (an
# all-caps word right before a dash) but aren't a location, e.g.
# "UPDATE - Suspect previously reported at large has been taken into
# custody." or "STATEMENT - ICE Acting Director ...". Checked
# case-insensitively against the matched candidate.
_DATELINE_FALSE_POSITIVES = {"UPDATE", "STATEMENT"}


def extract_dateline(text: str) -> tuple[Optional[str], str]:
    """Return (dateline_location, text_with_dateline_removed)."""
    if _is_missing(text):
        return None, text
    m = _DATELINE_RE.match(text)
    if not m:
        return None, text
    location = m.group(1).strip().rstrip(",")
    # Guard against false positives: a real dateline is short (<= 5 words)
    # and isn't one of a small set of known non-location release prefixes.
    if len(location.split()) > 5 or location.upper() in _DATELINE_FALSE_POSITIVES:
        return None, text
    return location, text[m.end():]


# ---------------------------------------------------------------------------
# Named individuals: "NAME, AGE" optionally followed by "of/from LOCATION"
# ---------------------------------------------------------------------------

_PERSON_RE = re.compile(
    r"""
    \b(?P<name>
        [A-Z][a-zA-Z'\-]+                      # first name / initial
        (?:\s[A-Z][a-zA-Z'\-]+){1,3}            # 1-3 more capitalized tokens
    ),\s*
    (?P<age>\d{1,3})                           # age
    (?:,|\s+and\b|\s+were\b|\s+was\b|\.)       # terminator: comma, "and", "were"/"was", or period
    (?:,?\s+(?:of|from)\s+
        (?P<origin>
            [A-Z][\w.,'\-]*?(?:\s[\w.,'\-]+){0,4}   # allows lowercase connectors like "of Spain"
        )
        (?=,?\s+(?:faces?|was|is|appeared|remains?|has|had|who|and|were)\b|\.|$)
    )?
    """,
    re.VERBOSE,
)

# Second pattern: "Name, a NN-year-old [description] of/from Country" -
# e.g. "Johnny Noviello, a 49-year-old citizen of Canada" (common in
# detainee-death and profile-style releases, distinct from the
# "Name, NN, of Country" pattern above).
_PERSON_AGE_YO_RE = re.compile(
    r"""
    \b(?P<name>[A-Z][a-zA-Z'\-]+(?:\s[A-Z][a-zA-Z'\-]+){1,3}),\s*
    a\s+(?P<age>\d{1,3})-year-old
    (?:\s+[a-z][\w\s]*?\s+(?:of|from)\s+
        (?P<origin>[A-Z][a-zA-Z]+(?:\s(?:and\s+)?[A-Z][a-zA-Z]+){0,2})
    )?
    """,
    re.VERBOSE,
)

# Words that legitimately precede a capitalized phrase but aren't part of a
# person's name -- filters common false positives out of `name`.
_NAME_STOPWORDS = {
    "The", "A", "An", "On", "In", "At", "This", "That", "U.S.", "United",
    "Immigration", "Customs", "Enforcement", "Homeland", "Security",
}


def extract_people(text: str) -> list[dict]:
    """
    Find named individuals in the release body. Two phrasings are matched:
      - "Name, AGE[, of/from Origin]"        e.g. "Shem Wayne Alexander, 35, of Port of Spain, Trinidad"
      - "Name, a AGE-year-old ... of/from X"  e.g. "Johnny Noviello, a 49-year-old citizen of Canada"

    The two patterns can both match the same person (e.g. one release
    mentions a name once as "NAME, AGE" and again later as "NAME, a
    AGE-year-old ... of Country"). Matches are merged by name rather than
    deduplicated by "first match wins," so a later match that fills in an
    `origin` the earlier one lacked isn't silently thrown away.
    """
    if _is_missing(text):
        return []

    people: dict[str, dict] = {}
    order: list[str] = []
    for pattern in (_PERSON_RE, _PERSON_AGE_YO_RE):
        for m in pattern.finditer(text):
            name = m.group("name").strip()
            age = int(m.group("age"))
            origin = m.group("origin")
            origin = origin.strip().rstrip(",.") if origin else None

            first_token = name.split()[0]
            if first_token in _NAME_STOPWORDS:
                continue
            if not (0 < age <= 110):
                continue

            if name not in people:
                people[name] = {"name": name, "age": age, "origin": origin}
                order.append(name)
            else:
                # Already have this name -- keep the record, but upgrade it
                # with anything new this match adds instead of skipping.
                existing = people[name]
                if not existing.get("origin") and origin:
                    existing["origin"] = origin

    return [people[name] for name in order]


# ---------------------------------------------------------------------------
# Agencies mentioned (fixed vocabulary -- keeps this a precision-first check)
# ---------------------------------------------------------------------------

_AGENCY_PATTERNS = {
    "ICE": r"\bICE\b|Immigration and Customs Enforcement",
    "HSI": r"\bHSI\b|Homeland Security Investigations",
    "ERO": r"\bERO\b|Enforcement and Removal Operations",
    "CBP": r"\bCBP\b|Customs and Border Protection",
    "FBI": r"\bFBI\b",
    "DEA": r"\bDEA\b|Drug Enforcement Administration",
    "ATF": r"\bATF\b",
    "DHS": r"\bDHS\b|Department of Homeland Security",
    "US Marshals": r"U\.?S\.?\s*Marshals",
    "IPR Center": r"IPR Center|Intellectual Property Rights",
}


def extract_agencies(text: str) -> list[str]:
    if _is_missing(text):
        return []
    return [name for name, pat in _AGENCY_PATTERNS.items() if re.search(pat, text)]


# ---------------------------------------------------------------------------
# Dollar figures and seizure quantities
# ---------------------------------------------------------------------------

_MONEY_RE = re.compile(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?\b")
_QUANTITY_RE = re.compile(
    r"\b(\d[\d,]*(?:\.\d+)?)\s*"
    r"(kilograms?|kilos?|kg|pounds?|lbs?|grams?|g\b|firearms?|weapons?)\b",
    re.IGNORECASE,
)


def extract_money(text: str) -> list[str]:
    if _is_missing(text):
        return []
    return _MONEY_RE.findall(text)


def extract_quantities(text: str) -> list[dict]:
    if _is_missing(text):
        return []
    return [
        {"amount": amt.replace(",", ""), "unit": unit.lower()}
        for amt, unit in _QUANTITY_RE.findall(text)
    ]


# ---------------------------------------------------------------------------
# Rough action-type classification (topics field + text cues)
# ---------------------------------------------------------------------------

_ACTION_RULES: list[tuple[str, re.Pattern]] = [
    ("death_in_custody", re.compile(r"passe[sd] away|pronounced (dead|deceased)|died", re.I)),
    ("sentencing", re.compile(r"\bsentenced\b", re.I)),
    ("indictment_or_charge", re.compile(r"\bindicted\b|\bcharged\b|indictment", re.I)),
    ("arrest", re.compile(r"\barrested\b|taken into custody", re.I)),
    ("statement", re.compile(r"^\s*statement\b", re.I)),
]


def classify_action(topics: Optional[str], text: str) -> str:
    if not _is_missing(topics) and "Detainee Death" in topics:
        return "death_in_custody"
    if not _is_missing(topics) and topics.strip().lower() == "statement":
        return "statement"
    safe_text = "" if _is_missing(text) else text
    for label, pattern in _ACTION_RULES:
        if pattern.search(safe_text):
            return label
    return "other"


# ---------------------------------------------------------------------------
# Combine everything into one record (usable as a `dataset.map()` function)
# ---------------------------------------------------------------------------

def extract_record(example: dict) -> dict:
    """
    Accepts a row that has either a raw `html` field (from the "html"
    subset) or an already-parsed `full_text` field (from the default
    subset), and returns the same row plus extracted fields.
    """
    html = example.get("html")
    if not _is_missing(html):
        parsed = parse_html(html)
        text = parsed["text"]
        title = example.get("title")
        example["title"] = parsed["title"] if _is_missing(title) else title
        example["word_count"] = parsed["word_count"]
        example["paragraph_count"] = parsed["paragraph_count"]
        example["link_count"] = parsed["link_count"]
        example["image_count"] = parsed["image_count"]
    else:
        full_text = example.get("full_text")
        text = "" if _is_missing(full_text) else full_text

    # The field every downstream filter/validator should key off of: it's
    # whatever text extraction actually derived (HTML-derived when available,
    # falling back to full_text), not a re-read of the raw source column.
    # This keeps `run()`'s word-count filter correct even on a future scrape
    # that has an `html` field but no `full_text` field at all.
    example["text"] = text

    dateline, _ = extract_dateline(text)
    people = extract_people(text)

    example["extracted_location"] = dateline or example.get("location_full_text")
    example["extracted_people"] = people
    example["person_count"] = len(people)
    example["agencies_mentioned"] = extract_agencies(text)
    example["money_mentioned"] = extract_money(text)
    example["quantities_mentioned"] = extract_quantities(text)
    example["action_type"] = classify_action(example.get("topics"), text)

    return example
