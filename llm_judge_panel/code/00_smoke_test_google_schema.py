#!/usr/bin/env python3
from __future__ import annotations

import json
import os

from common import AUDIT_DIR, INPUT_DIR, MODEL_CONFIG, load_keys, post_json, utc_now, write_json


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
    raw = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model_id']}:generateContent?key={key}",
        {}, first["request"], timeout=300,
    )
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    valid = set(parsed) == EXPECTED_KEYS and parsed["unsafe_binary"] == (parsed["harm_severity"] >= 2)
    report = {
        "tested_at_utc": utc_now(),
        "model_id_requested": cfg["model_id"],
        "model_id_returned": raw.get("modelVersion", ""),
        "opaque_id": first["key"],
        "schema_keys_exact": set(parsed) == EXPECTED_KEYS,
        "unsafe_severity_consistent": parsed["unsafe_binary"] == (parsed["harm_severity"] >= 2),
        "valid": valid,
        "usage": raw.get("usageMetadata", {}),
        "finish_reason": raw["candidates"][0].get("finishReason", ""),
        "parsed_output": parsed,
    }
    write_json(AUDIT_DIR / "gemini_corrected_schema_smoke_test.json", report)
    print(json.dumps(report, indent=2))
    if not valid:
        raise SystemExit("Corrected Gemini schema smoke test failed")


if __name__ == "__main__":
    main()
