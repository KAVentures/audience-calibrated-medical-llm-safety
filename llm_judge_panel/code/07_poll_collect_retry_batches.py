#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request

from common import MODEL_CONFIG, RAW_DIR, STATE_DIR, get_json, load_keys, write_json


def download(url, headers):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=300) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", required=True, choices=["gemini_3_5_flash", "claude_4_8_opus"])
    args = parser.parse_args()
    cfg = MODEL_CONFIG[args.only]
    key = load_keys()[cfg["key_name"]]
    state = json.loads((STATE_DIR / f"{args.only}_retry.json").read_text())
    if args.only == "gemini_3_5_flash":
        status = get_json(f"https://generativelanguage.googleapis.com/v1beta/{state['batch_id']}?key={key}", {})
        batch_state = (status.get("metadata") or {}).get("state", "")
        complete = batch_state in {"BATCH_STATE_SUCCEEDED", "BATCH_STATE_FAILED", "BATCH_STATE_CANCELLED", "BATCH_STATE_EXPIRED"}
        if complete: write_json(RAW_DIR / "gemini_3_5_flash_retry_results.json", status)
    else:
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        status = get_json(f"https://api.anthropic.com/v1/messages/batches/{state['batch_id']}", headers)
        complete = status.get("processing_status") == "ended"
        if complete:
            (RAW_DIR / "claude_4_8_opus_retry_results.jsonl").write_bytes(
                download(f"https://api.anthropic.com/v1/messages/batches/{state['batch_id']}/results", headers)
            )
    write_json(RAW_DIR / f"{args.only}_retry_status.json", status)
    print(f"{args.only}: {'complete' if complete else 'in progress'}")


if __name__ == "__main__":
    main()
