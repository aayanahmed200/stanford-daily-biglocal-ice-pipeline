# Validation report

Total records: **5**

## Schema
- Passes: **True**
- Missing `url`: 0
- Missing `title`: 0

## Completeness
- `extracted_location`: 4 / 5 (80.0%)
- `date_normalized`: 5 / 5 (100.0%)
- `extracted_people`: 3 / 5 (60.0%)
- `agencies_mentioned`: 4 / 5 (80.0%)
- `action_type`: 5 / 5 (100.0%)

## Sanity issues
- duplicate urls: 0
- empty or near empty body: 1
- out of range ages: 0
- unparseable dates: 1

## Usable for analysis: 4 / 5 (80.0%)

---
*This report was generated from a 5-row smoke-test sample (see `tests/test_pipeline_smoke.py`), not the full 965-row dataset. Run `scripts/pipeline.py` for a full report.*
