#!/usr/bin/env python3
from __future__ import annotations

import json

from common import AUDIT_DIR, INPUT_DIR, PANEL_ROOT, RAW_DIR, sha256_file, utc_now, write_json


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    retry_dir = PANEL_ROOT / "batch_inputs" / "technical_retries"
    retry_dir.mkdir(parents=True, exist_ok=True)
    report = {"prepared_at_utc": utc_now(), "retries": {}}

    gemini_results = json.loads((RAW_DIR / "gemini_3_5_flash_results.json").read_text(encoding="utf-8"))
    bad_ids = []
    reasons = {}
    for item in gemini_results["response"]["inlinedResponses"]["inlinedResponses"]:
        opaque_id = item["metadata"]["key"]
        try:
            candidate = item["response"]["candidates"][0]
            text = candidate["content"]["parts"][0]["text"]
            json.loads(text)
        except Exception:
            bad_ids.append(opaque_id)
            reasons[opaque_id] = (item.get("response", {}).get("candidates") or [{}])[0].get("finishReason", "missing")
    source = {item["key"]: item for item in read_jsonl(INPUT_DIR / "gemini_3_5_flash.jsonl")}
    gemini_path = retry_dir / "gemini_3_5_flash_retry.jsonl"
    with gemini_path.open("w", encoding="utf-8") as handle:
        for opaque_id in sorted(bad_ids):
            item = source[opaque_id]
            item["request"]["generation_config"]["max_output_tokens"] = 8192
            handle.write(json.dumps(item, separators=(",", ":")) + "\n")
    report["retries"]["gemini_3_5_flash"] = {
        "count": len(bad_ids), "opaque_ids": sorted(bad_ids), "original_finish_reasons": reasons,
        "only_change": "max_output_tokens 4096 to 8192", "path": str(gemini_path.relative_to(PANEL_ROOT)),
        "sha256": sha256_file(gemini_path),
    }

    claude_results = read_jsonl(RAW_DIR / "claude_4_8_opus_results.jsonl")
    claude_bad = sorted(item["custom_id"] for item in claude_results if item["result"]["type"] != "succeeded")
    source = {item["custom_id"]: item for item in read_jsonl(INPUT_DIR / "claude_4_8_opus.jsonl")}
    claude_path = retry_dir / "claude_4_8_opus_retry.jsonl"
    with claude_path.open("w", encoding="utf-8") as handle:
        for opaque_id in claude_bad:
            handle.write(json.dumps(source[opaque_id], separators=(",", ":")) + "\n")
    report["retries"]["claude_4_8_opus"] = {
        "count": len(claude_bad), "opaque_ids": claude_bad,
        "only_change": "none; identical retry after provider billing rejection",
        "path": str(claude_path.relative_to(PANEL_ROOT)), "sha256": sha256_file(claude_path),
    }
    write_json(AUDIT_DIR / "technical_retry_manifest.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
