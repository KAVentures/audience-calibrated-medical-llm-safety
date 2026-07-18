#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request

from common import MODEL_CONFIG, RAW_DIR, STATE_DIR, get_json, load_keys, utc_now, write_json


def download_bytes(url: str, headers: dict[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def poll_openai(state, key):
    headers = {"Authorization": f"Bearer {key}"}
    status = get_json(f"https://api.openai.com/v1/batches/{state['batch_id']}", headers)
    complete = status.get("status") == "completed"
    if complete and status.get("output_file_id"):
        data = download_bytes(f"https://api.openai.com/v1/files/{status['output_file_id']}/content", headers)
        (RAW_DIR / "gpt_5_5_results.jsonl").write_bytes(data)
    if status.get("error_file_id"):
        data = download_bytes(f"https://api.openai.com/v1/files/{status['error_file_id']}/content", headers)
        (RAW_DIR / "gpt_5_5_errors.jsonl").write_bytes(data)
    return status, complete


def poll_anthropic(state, key):
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    status = get_json(f"https://api.anthropic.com/v1/messages/batches/{state['batch_id']}", headers)
    complete = status.get("processing_status") == "ended"
    if complete:
        data = download_bytes(f"https://api.anthropic.com/v1/messages/batches/{state['batch_id']}/results", headers)
        (RAW_DIR / "claude_4_8_opus_results.jsonl").write_bytes(data)
    return status, complete


def poll_google(state, key):
    status = get_json(f"https://generativelanguage.googleapis.com/v1beta/{state['batch_id']}?key={key}", {})
    job_state = status.get("state") or (status.get("metadata") or {}).get("state")
    complete = job_state in {
        "JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED",
        "BATCH_STATE_SUCCEEDED", "BATCH_STATE_FAILED", "BATCH_STATE_CANCELLED", "BATCH_STATE_EXPIRED",
    }
    if complete:
        write_json(RAW_DIR / "gemini_3_5_flash_results.json", status)
    return status, complete


def poll_xai(state, key):
    headers = {"Authorization": f"Bearer {key}"}
    status = get_json(f"https://api.x.ai/v1/batches/{state['batch_id']}", headers)
    batch_state = status.get("state") or {}
    pending = batch_state.get("num_pending")
    complete = pending == 0 and (batch_state.get("num_requests") or 0) > 0
    if complete:
        all_results = []
        pagination_token = ""
        while True:
            url = f"https://api.x.ai/v1/batches/{state['batch_id']}/results?limit=1000"
            if pagination_token:
                url += "&pagination_token=" + urllib.parse.quote(pagination_token, safe="")
            page = get_json(url, headers)
            all_results.extend(page.get("results", []))
            pagination_token = page.get("next_page_token") or page.get("pagination_token") or ""
            if not pagination_token:
                break
        write_json(RAW_DIR / "grok_4_3_results.json", {"results": all_results, "count": len(all_results)})
    return status, complete


POLLERS = {"openai": poll_openai, "anthropic": poll_anthropic, "google": poll_google, "xai": poll_xai}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(MODEL_CONFIG), action="append")
    args = parser.parse_args()
    keys = load_keys()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    selected = args.only or list(MODEL_CONFIG)
    summary = {}
    for judge_key in selected:
        state_path = STATE_DIR / f"{judge_key}.json"
        if not state_path.exists():
            summary[judge_key] = {"status": "not_submitted"}
            continue
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if not state.get("batch_id"):
            summary[judge_key] = {"status": "submission_failed", "error": state.get("submission_error")}
            continue
        cfg = MODEL_CONFIG[judge_key]
        status, complete = POLLERS[cfg["provider"]](state, keys[cfg["key_name"]])
        write_json(RAW_DIR / f"{judge_key}_status.json", status)
        summary[judge_key] = {"batch_id": state["batch_id"], "complete": complete, "status": status}
        print(f"{judge_key}: {'complete' if complete else 'in progress'}")
    write_json(RAW_DIR / "panel_poll_summary.json", {"polled_at_utc": utc_now(), "judges": summary})


if __name__ == "__main__":
    main()
