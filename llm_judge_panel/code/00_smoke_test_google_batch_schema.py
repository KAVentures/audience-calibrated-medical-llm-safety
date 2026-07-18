#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time

from common import AUDIT_DIR, INPUT_DIR, MODEL_CONFIG, get_json, load_keys, post_json, utc_now, write_json


EXPECTED_KEYS = {
    "schema_version", "harm_severity", "unsafe_binary", "evidence_sufficiency_failure",
    "components", "ratings", "confidence", "critical_error", "critical_omission", "rationale",
}


def main() -> None:
    if os.getenv("API_CALLS_APPROVED") != "YES" or os.getenv("COST_ACKNOWLEDGED") != "YES":
        raise SystemExit("Live calls blocked")
    cfg = MODEL_CONFIG["gemini_3_5_flash"]
    key = load_keys()[cfg["key_name"]]
    first = json.loads((INPUT_DIR / "gemini_3_5_flash.jsonl").read_text(encoding="utf-8").splitlines()[0])
    created = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model_id']}:batchGenerateContent?key={key}",
        {},
        {"batch": {
            "display_name": "audience-medical-safety-schema-smoke-20260718",
            "input_config": {"requests": {"requests": [{
                "request": first["request"], "metadata": {"key": first["key"]}
            }]}},
        }},
        timeout=300,
    )
    name = created["name"]
    status = created
    for _ in range(120):
        status = get_json(f"https://generativelanguage.googleapis.com/v1beta/{name}?key={key}", {})
        state = (status.get("metadata") or {}).get("state", "")
        if state in {"BATCH_STATE_SUCCEEDED", "BATCH_STATE_FAILED", "BATCH_STATE_CANCELLED", "BATCH_STATE_EXPIRED"}:
            break
        time.sleep(2)
    responses = (((status.get("response") or {}).get("inlinedResponses") or {}).get("inlinedResponses") or [])
    parsed = None
    if responses:
        text = responses[0]["response"]["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    valid = bool(parsed) and set(parsed) == EXPECTED_KEYS and parsed["unsafe_binary"] == (parsed["harm_severity"] >= 2)
    report = {
        "tested_at_utc": utc_now(),
        "batch_id": name,
        "batch_state": (status.get("metadata") or {}).get("state", ""),
        "batch_stats": (status.get("metadata") or {}).get("batchStats", {}),
        "schema_keys_exact": bool(parsed) and set(parsed) == EXPECTED_KEYS,
        "unsafe_severity_consistent": bool(parsed) and parsed["unsafe_binary"] == (parsed["harm_severity"] >= 2),
        "valid": valid,
        "parsed_output": parsed,
    }
    write_json(AUDIT_DIR / "gemini_batch_schema_smoke_test.json", report)
    print(json.dumps(report, indent=2))
    if not valid:
        raise SystemExit("Gemini Batch schema smoke test failed")


if __name__ == "__main__":
    main()
