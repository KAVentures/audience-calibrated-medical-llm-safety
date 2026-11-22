"""Fail-closed identity and occurrence audit for the frozen blinded judge panel.

Pure standard-library code so identity checks can be regression-tested without
replaying provider calls or rebuilding manuscript outputs.
"""
from collections import Counter


def check_blinding_key(rows):
    """Validate the 1,200 primary + 120 blinded repeat identities."""
    ids = [row["opaque_id"] for row in rows]
    if len(ids) != 1320 or len(set(ids)) != 1320:
        raise ValueError("blinding key must contain 1320 distinct opaque IDs")
    occurrences = Counter(row["occurrence"] for row in rows)
    if occurrences != {"1": 1200, "2": 120}:
        raise ValueError(f"unexpected occurrence distribution: {occurrences}")
    primary = Counter(row["response_id"] for row in rows if row["occurrence"] == "1")
    repeats = Counter(row["response_id"] for row in rows if row["occurrence"] == "2")
    if (len(primary) != 1200 or any(n != 1 for n in primary.values())
            or len(repeats) != 120 or any(n != 1 for n in repeats.values())
            or not set(repeats).issubset(primary)):
        raise ValueError("blinding key violates unique-primary/one-repeat design")
    return {row["opaque_id"]: row for row in rows}


def audit_judge_identities(blind, parsed_ids, valid_ids):
    """Report missing, duplicate, unexpected, and occurrence-level coverage.

    Counts alone are not sufficient: 1319 expected IDs plus a duplicate can
    incorrectly masquerade as 1320 successful responses.
    """
    expected = set(blind)
    parsed = Counter(parsed_ids)
    valid = Counter(valid_ids)
    duplicate_ids = sum(n - 1 for n in parsed.values() if n > 1)
    missing_ids = len(expected - set(valid))
    unexpected_ids = len(set(parsed) - expected)
    duplicate_valid_ids = sum(n - 1 for n in valid.values() if n > 1)
    valid_occurrence = Counter(blind[key]["occurrence"] for key in valid if key in blind
                               for _ in range(valid[key]))
    is_complete = (
        len(parsed_ids) == len(expected) == len(valid_ids)
        and duplicate_ids == 0 and duplicate_valid_ids == 0
        and missing_ids == 0 and unexpected_ids == 0
        and valid_occurrence == {"1": 1200, "2": 120}
    )
    return {
        "unique_opaque_ids": len(parsed),
        "duplicate_ids": duplicate_ids,
        "duplicate_valid_ids": duplicate_valid_ids,
        "missing_ids": missing_ids,
        "unexpected_ids": unexpected_ids,
        "valid_primary": valid_occurrence["1"],
        "valid_repeats": valid_occurrence["2"],
        "expected_primary": 1200,
        "expected_repeats": 120,
        "complete_expected_1320": is_complete,
    }
