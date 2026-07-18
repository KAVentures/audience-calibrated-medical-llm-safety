#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
import shutil


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("input_dirs", nargs="+", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_out = args.output_dir / "raw_provider_responses"
    raw_out.mkdir(exist_ok=True)

    rows = []
    errors = []
    for input_dir in args.input_dirs:
        with (input_dir / "model_responses.csv").open(newline="") as f:
            rows.extend(csv.DictReader(f))
        error_path = input_dir / "generation_errors.jsonl"
        if error_path.exists():
            errors.extend(line for line in error_path.read_text().splitlines() if line.strip())
        for raw_path in (input_dir / "raw_provider_responses").glob("*.json"):
            target = raw_out / raw_path.name
            if target.exists():
                raise SystemExit(f"Duplicate raw response: {raw_path.name}")
            shutil.copy2(raw_path, target)

    response_ids = [row["response_id"] for row in rows]
    if len(response_ids) != len(set(response_ids)):
        raise SystemExit("Duplicate response IDs across input runs")
    rows.sort(key=lambda row: (row["model_key"], row["request_id"]))
    fieldnames = list(rows[0])
    with (args.output_dir / "model_responses.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with (args.output_dir / "model_responses.jsonl").open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if errors:
        (args.output_dir / "generation_errors.jsonl").write_text("\n".join(errors) + "\n")
    print(f"merged {len(rows)} unique responses")


if __name__ == "__main__":
    main()
