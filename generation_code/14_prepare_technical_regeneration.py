#!/usr/bin/env python3
from pathlib import Path
import csv
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "responses" / "model_responses.csv"
OUT = ROOT / "responses" / "technical_regeneration_20260714"


def is_raw_api_json(text: str) -> bool:
    value = text.lstrip()
    return value.startswith('{"id"') or value.startswith("{'id'")


def likely_mid_sentence(text: str) -> bool:
    value = text.rstrip()
    return bool(value) and value[-1] not in ".!?)]}\"'"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(SOURCE.open(newline="")))
    selected = []
    for row in rows:
        reasons = []
        output_tokens = int(row.get("output_tokens") or 0)
        if is_raw_api_json(row["response_text"]):
            reasons.append("raw_api_object_substituted_for_answer")
        if row["model_key"] in {"gpt_5_5", "claude_4_8_opus"} and output_tokens >= 1200:
            reasons.append("original_output_token_limit_reached")
        if row["model_key"] == "gemini_3_5_flash" and likely_mid_sentence(row["response_text"]):
            reasons.append("likely_mid_sentence_original_finish_metadata_unavailable")
        if reasons:
            selected.append({
                "request_id": row["request_id"],
                "response_id": row["response_id"],
                "model_key": row["model_key"],
                "prompt_id": row["prompt_id"],
                "original_created_at_utc": row["created_at_utc"],
                "original_output_tokens": row["output_tokens"],
                "original_response_sha256": row["response_sha256"],
                "technical_regeneration_reason": ";".join(reasons),
            })

    fieldnames = list(selected[0])
    with (OUT / "technical_regeneration_manifest.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)
    for model_key in sorted({row["model_key"] for row in selected}):
        values = [row["request_id"] for row in selected if row["model_key"] == model_key]
        (OUT / f"{model_key}_request_ids.txt").write_text("\n".join(values) + "\n")
    print(f"selected {len(selected)} responses: {dict(sorted(Counter(row['model_key'] for row in selected).items()))}")


if __name__ == "__main__":
    main()
