#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
from collections import Counter


EXPECTED_MODELS = {"grok_4_3", "gpt_5_5", "gemini_3_5_flash", "claude_4_8_opus"}
COMPLETE_REASONS = {"completed", "stop", "STOP", "end_turn", "stop_sequence"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--technical-repair", action="store_true")
    args = parser.parse_args()
    csv_path = args.run_dir / "model_responses.csv"
    rows = list(csv.DictReader(csv_path.open(newline="")))

    failures = []
    ids = [row["response_id"] for row in rows]
    if len(rows) != 1200:
        failures.append(f"expected 1200 rows, found {len(rows)}")
    if len(set(ids)) != len(ids):
        failures.append("duplicate response IDs present")
    model_counts = Counter(row["model_key"] for row in rows)
    if set(model_counts) != EXPECTED_MODELS or any(model_counts[m] != 300 for m in EXPECTED_MODELS):
        failures.append(f"model counts invalid: {dict(model_counts)}")

    raw_json_rows = []
    incomplete_rows = []
    empty_rows = []
    missing_raw = []
    nonterminal_rows = []
    for row in rows:
        text = row["response_text"].strip()
        if not text:
            empty_rows.append(row["response_id"])
        if text.startswith('{"id"') or text.startswith("{'id'"):
            raw_json_rows.append(row["response_id"])
        regenerated = row.get("technical_regeneration") == "true"
        if regenerated or not args.technical_repair:
            if row.get("generation_status") != "complete" or row.get("finish_reason") not in COMPLETE_REASONS:
                incomplete_rows.append(row["response_id"])
            raw_dir = "raw_provider_responses_regenerated_only" if args.technical_repair else "raw_provider_responses"
            if not (args.run_dir / raw_dir / f"{row['response_id']}.json").exists():
                missing_raw.append(row["response_id"])
        if text and text[-1] not in ".!?)]}\"'":
            nonterminal_rows.append(row["response_id"])

    for label, values in [
        ("empty answer", empty_rows),
        ("raw JSON substituted for answer", raw_json_rows),
        ("incomplete finish status", incomplete_rows),
        ("missing raw provider response", missing_raw),
    ]:
        if values:
            failures.append(f"{label}: {len(values)} rows")

    report = {
        "rows": len(rows),
        "unique_response_ids": len(set(ids)),
        "model_counts": dict(sorted(model_counts.items())),
        "finish_reasons": dict(sorted(Counter(row.get("finish_reason", "") for row in rows).items())),
        "raw_json_rows": len(raw_json_rows),
        "empty_rows": len(empty_rows),
        "incomplete_rows": len(incomplete_rows),
        "missing_raw_rows": len(missing_raw),
        "nonterminal_ending_review_flags": len(nonterminal_rows),
        "validation_passed": not failures,
        "failures": failures,
    }
    (args.run_dir / "generation_validation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
