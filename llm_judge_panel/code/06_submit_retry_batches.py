#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from common import MODEL_CONFIG, PANEL_ROOT, STATE_DIR, load_keys, post_json, sha256_file, utc_now, write_json


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", required=True, choices=["gemini_3_5_flash", "claude_4_8_opus"])
    args = parser.parse_args()
    if os.getenv("API_CALLS_APPROVED") != "YES" or os.getenv("COST_ACKNOWLEDGED") != "YES":
        raise SystemExit("Live calls blocked")
    cfg = MODEL_CONFIG[args.only]
    key = load_keys()[cfg["key_name"]]
    path = PANEL_ROOT / "batch_inputs" / "technical_retries" / f"{args.only}_retry.jsonl"
    requests = read_jsonl(path)
    state_path = STATE_DIR / f"{args.only}_retry.json"
    if state_path.exists() and json.loads(state_path.read_text()).get("batch_id"):
        print("Existing retry batch state found; not resubmitting")
        return
    if args.only == "gemini_3_5_flash":
        created = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model_id']}:batchGenerateContent?key={key}", {},
            {"batch": {
                "display_name": "audience-medical-safety-gemini-technical-retry-20260718",
                "input_config": {"requests": {"requests": [
                    {"request": item["request"], "metadata": {"key": item["key"]}} for item in requests
                ]}},
            }}, timeout=300,
        )
        batch_id = created["name"]
    else:
        created = post_json(
            "https://api.anthropic.com/v1/messages/batches",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {"requests": requests}, timeout=300,
        )
        batch_id = created["id"]
    state = {
        "judge_key": args.only, "provider": cfg["provider"], "model_id_requested": cfg["model_id"],
        "batch_id": batch_id, "submitted_at_utc": utc_now(), "request_count": len(requests),
        "input_sha256": sha256_file(path), "batch": created,
    }
    write_json(state_path, state)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
