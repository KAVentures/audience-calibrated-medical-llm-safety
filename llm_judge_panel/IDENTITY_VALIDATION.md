# Frozen-panel identity validation

The four-judge dataset has 1,200 primary responses plus 120 blinded repeats per
judge. The frozen `blinding_key_do_not_share_with_judges.csv` is the sole
authoritative list of expected opaque IDs and response/occurrence assignments.

`04_validate_merge_judge_results.py` now fails before writing analysis-ready
CSV files if a judge's effective parsed results contain an absent, duplicated,
unexpected, or schema-invalid expected ID, or if primary/repeat coverage differs
from the frozen key. The audit records counts of each failure category. See
`tests/test_panel_identity.py` for negative tests.

The archived 2026-07-18 validation report already records 1,320 unique and
valid records for each judge (5,280 total, 4,800 primary). The new gate is
defensive and does not itself establish that any previously released count or
statistical result was incorrect. Existing rows have not been rejudged.
