#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from common import (
    AUDIT_DIR,
    INPUT_DIR,
    MODEL_CONFIG,
    STATE_DIR,
    get_json,
    load_keys,
    multipart_upload,
    post_json,
    sha256_file,
    utc_now,
    write_json,
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def probe_model(cfg: dict, key: str) -> dict:
    provider = cfg["provider"]
    model_id = cfg["model_id"]
    if provider == "openai":
        data = get_json(f"https://api.openai.com/v1/models/{model_id}", {"Authorization": f"Bearer {key}"})
    elif provider == "anthropic":
        data = get_json(
            f"https://api.anthropic.com/v1/models/{model_id}",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
        )
    elif provider == "google":
        data = get_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}?key={key}", {})
    elif provider == "xai":
        data = get_json(f"https://api.x.ai/v1/models/{model_id}", {"Authorization": f"Bearer {key}"})
    else:
        raise ValueError(provider)
    return {
        "requested_model_id": model_id,
        "returned_model_id": data.get("id") or data.get("name") or data.get("model") or "",
        "display_name": data.get("displayName") or data.get("display_name") or "",
        "raw_probe": data,
    }


def submit_openai(path, cfg, key):
    headers = {"Authorization": f"Bearer {key}"}
    uploaded = multipart_upload("https://api.openai.com/v1/files", headers, path, {"purpose": "batch"})
    batch = post_json(
        "https://api.openai.com/v1/batches",
        headers,
        {
            "input_file_id": uploaded["id"],
            "endpoint": "/v1/responses",
            "completion_window": "24h",
            "metadata": {"study": "audience_calibrated_medical_safety", "role": "llm_judge"},
        },
    )
    return {"input_file": uploaded, "batch": batch, "batch_id": batch["id"]}


def submit_anthropic(path, cfg, key):
    requests = read_jsonl(path)
    batch = post_json(
        "https://api.anthropic.com/v1/messages/batches",
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
        {"requests": requests},
        timeout=300,
    )
    return {"batch": batch, "batch_id": batch["id"]}


def submit_google(path, cfg, key):
    requests = read_jsonl(path)
    batch = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model_id']}:batchGenerateContent?key={key}",
        {},
        {
            "batch": {
                "display_name": "audience-medical-safety-llm-judge-gemini-20260718",
                "input_config": {"requests": {"requests": [
                    {"request": item["request"], "metadata": {"key": item["key"]}}
                    for item in requests
                ]}},
            }
        },
        timeout=300,
    )
    return {"batch": batch, "batch_id": batch["name"]}


def submit_xai(path, cfg, key):
    headers = {"Authorization": f"Bearer {key}"}
    uploaded = multipart_upload("https://api.x.ai/v1/files", headers, path)
    file_id = uploaded.get("id") or uploaded.get("file_id")
    if not file_id:
        raise RuntimeError(f"xAI upload did not return a file ID: {uploaded}")
    batch = post_json(
        "https://api.x.ai/v1/batches",
        headers,
        {"name": "audience-medical-safety-llm-judge-grok-20260718", "input_file_id": file_id},
    )
    batch_id = batch.get("batch_id") or batch.get("id")
    if not batch_id:
        raise RuntimeError(f"xAI batch creation did not return a batch ID: {batch}")
    return {"input_file": uploaded, "batch": batch, "batch_id": batch_id}


SUBMITTERS = {
    "openai": submit_openai,
    "anthropic": submit_anthropic,
    "google": submit_google,
    "xai": submit_xai,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(MODEL_CONFIG), action="append")
    args = parser.parse_args()
    if os.getenv("API_CALLS_APPROVED") != "YES" or os.getenv("COST_ACKNOWLEDGED") != "YES":
        raise SystemExit("Live calls blocked: set API_CALLS_APPROVED=YES and COST_ACKNOWLEDGED=YES")

    preflight = json.loads((AUDIT_DIR / "preflight_report.json").read_text(encoding="utf-8"))
    if not all(preflight["checks"].values()):
        raise SystemExit("Preflight checks are not all true")
    keys = load_keys()
    selected = args.only or list(MODEL_CONFIG)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    for judge_key in selected:
        cfg = MODEL_CONFIG[judge_key]
        state_path = STATE_DIR / f"{judge_key}.json"
        if state_path.exists() and json.loads(state_path.read_text()).get("batch_id"):
            print(f"{judge_key}: existing submission state found; not resubmitting")
            continue
        key = keys.get(cfg["key_name"], "")
        if not key:
            raise SystemExit(f"Missing {cfg['key_name']}")
        path = INPUT_DIR / f"{judge_key}.jsonl"
        expected_hash = preflight["inputs"][judge_key]["sha256"]
        if sha256_file(path) != expected_hash:
            raise SystemExit(f"Input hash changed for {judge_key}")

        print(f"{judge_key}: probing exact model ID {cfg['model_id']}")
        probe = probe_model(cfg, key)
        print(f"{judge_key}: submitting {preflight['requests_per_judge']} requests")
        try:
            submission = SUBMITTERS[cfg["provider"]](path, cfg, key)
        except Exception as exc:
            write_json(state_path, {
                "judge_key": judge_key,
                "provider": cfg["provider"],
                "model_id_requested": cfg["model_id"],
                "attempted_at_utc": utc_now(),
                "input_sha256": expected_hash,
                "probe": probe,
                "submission_error": str(exc),
            })
            raise
        state = {
            "judge_key": judge_key,
            "provider": cfg["provider"],
            "model_id_requested": cfg["model_id"],
            "reasoning_effort_requested": cfg["reasoning"],
            "temperature_requested": 0,
            "max_output_tokens": 4096,
            "batch_discount_documented": cfg["batch_discount"],
            "submitted_at_utc": utc_now(),
            "input_sha256": expected_hash,
            "request_count": preflight["requests_per_judge"],
            "probe": probe,
            **submission,
        }
        write_json(state_path, state)
        print(f"{judge_key}: submitted batch {state['batch_id']}")


if __name__ == "__main__":
    main()
