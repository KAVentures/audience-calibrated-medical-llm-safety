#!/usr/bin/env python3
"""Offline archived-statistic and frozen-key assertions (not clinical validation)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    report = read_json("llm_judge_panel/audit/judge_result_validation_report.json")
    assert report["all_occurrence_rows"] == 5280
    assert report["primary_rows"] == 4800
    for judge, item in report["judges"].items():
        assert item["valid"] == 1320 and item["invalid"] == 0, judge
        assert item["unique_opaque_ids"] == 1320 and item["complete_expected_1320"], judge

    with (ROOT / "llm_judge_panel/audit/blinding_key_do_not_share_with_judges.csv").open(
            newline="", encoding="utf-8") as f:
        frozen = list(csv.DictReader(f))
    assert len(frozen) == 1320
    assert len({r["opaque_id"] for r in frozen}) == 1320
    assert sum(r["occurrence"] == "1" for r in frozen) == 1200
    assert sum(r["occurrence"] == "2" for r in frozen) == 120

    s = read_json("results/llm_judge_panel_analysis_summary.json")
    assert s["primary_ratings"] == 4800 and s["unique_responses"] == 1200
    p = {x["outcome"]: x for x in s["primary_tests"]}
    assert p["unsafe_binary"]["events"] == 25
    assert p["evidence_sufficiency_failure"]["events"] == 102
    assert p["unsafe_binary"]["family"] == "gaussian_identity_risk_difference_fallback"
    assert abs(p["unsafe_binary"]["holm_p"] - 0.0047853734631946995) < 1e-10
    assert s["overall_judge_prevalence"]["gpt_5_5"]["unsafe_binary"] == 18 / 1200
    print("PASS archived summary and frozen identity checks")
    print("LIMIT: this is NOT an independent replay of all 4,800 scores or clinical calibration")


if __name__ == "__main__":
    main()
