#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
import shutil


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_run_rows(run_dir: Path) -> list[dict]:
    csv_path = run_dir / "model_responses.csv"
    if csv_path.exists():
        return read_csv(csv_path)
    jsonl_path = run_dir / "model_responses.jsonl"
    return [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original_csv", type=Path)
    parser.add_argument("manifest_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("replacement_dirs", nargs="+", type=Path)
    args = parser.parse_args()

    original_rows = read_csv(args.original_csv)
    manifest = {row["response_id"]: row for row in read_csv(args.manifest_csv)}
    replacements = {}
    for run_dir in args.replacement_dirs:
        for row in read_run_rows(run_dir):
            if row["response_id"] in replacements:
                continue
            replacements[row["response_id"]] = row
    if set(replacements) != set(manifest):
        missing = sorted(set(manifest) - set(replacements))
        extra = sorted(set(replacements) - set(manifest))
        raise SystemExit(f"Replacement/manifest mismatch: missing={len(missing)} extra={len(extra)}")

    final_rows = []
    for original in original_rows:
        response_id = original["response_id"]
        if response_id in replacements:
            row = replacements[response_id].copy()
            audit = manifest[response_id]
            row["technical_regeneration"] = "true"
            row["technical_regeneration_reason"] = audit["technical_regeneration_reason"]
            row["original_created_at_utc"] = audit["original_created_at_utc"]
            row["original_response_sha256"] = audit["original_response_sha256"]
            row["original_output_tokens"] = audit["original_output_tokens"]
        else:
            row = original.copy()
            row["technical_regeneration"] = "false"
            row["technical_regeneration_reason"] = ""
            row["original_created_at_utc"] = ""
            row["original_response_sha256"] = ""
            row["original_output_tokens"] = ""
            row.setdefault("provider_model_id_returned", "not_recorded_original_run")
            row.setdefault("provider_status", "not_recorded_original_run")
            row.setdefault("finish_reason", "not_recorded_original_run")
        final_rows.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_out = args.output_dir / "raw_provider_responses_regenerated_only"
    raw_out.mkdir(exist_ok=True)
    for run_dir in args.replacement_dirs:
        for raw_path in (run_dir / "raw_provider_responses").glob("*.json"):
            shutil.copy2(raw_path, raw_out / raw_path.name)

    fieldnames = []
    for row in final_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with (args.output_dir / "model_responses.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(final_rows)
    with (args.output_dir / "model_responses.jsonl").open("w") as f:
        for row in final_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    shutil.copy2(args.manifest_csv, args.output_dir / "technical_regeneration_manifest.csv")
    print(f"finalized {len(final_rows)} rows with {len(replacements)} technical replacements")


if __name__ == "__main__":
    main()
