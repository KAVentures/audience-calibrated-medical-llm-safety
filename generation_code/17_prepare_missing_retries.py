#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
from collections import Counter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_csv", type=Path)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    with args.manifest_csv.open(newline="") as f:
        manifest = list(csv.DictReader(f))
    completed = []
    for path in args.runs_dir.glob("*/model_responses.jsonl"):
        completed.extend(json.loads(line)["request_id"] for line in path.read_text().splitlines() if line.strip())
    completed_set = set(completed)
    missing = [row for row in manifest if row["request_id"] not in completed_set]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for model_key in sorted({row["model_key"] for row in missing}):
        values = [row["request_id"] for row in missing if row["model_key"] == model_key]
        (args.output_dir / f"{model_key}_missing_request_ids.txt").write_text("\n".join(values) + "\n")
    print(f"completed_unique={len(completed_set)} duplicates={len(completed)-len(completed_set)} missing={len(missing)}")
    print(dict(sorted(Counter(row["model_key"] for row in missing).items())))


if __name__ == "__main__":
    main()
