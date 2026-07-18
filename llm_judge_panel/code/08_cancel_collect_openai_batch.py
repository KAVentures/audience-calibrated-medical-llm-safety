#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.request

from common import RAW_DIR, STATE_DIR, get_json, load_keys, post_json, utc_now, write_json


def download(url, headers):
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def main() -> None:
    state = json.loads((STATE_DIR / "gpt_5_5.json").read_text())
    key = load_keys()["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {key}"}
    status = get_json(f"https://api.openai.com/v1/batches/{state['batch_id']}", headers)
    if status.get("status") not in {"completed", "cancelled", "expired", "failed"}:
        status = post_json(f"https://api.openai.com/v1/batches/{state['batch_id']}/cancel", headers, {})
    terminal = {"completed", "cancelled", "expired", "failed"}
    for _ in range(240):
        if status.get("status") in terminal:
            break
        time.sleep(5)
        status = get_json(f"https://api.openai.com/v1/batches/{state['batch_id']}", headers)
    write_json(RAW_DIR / "gpt_5_5_status.json", status)
    if status.get("output_file_id"):
        (RAW_DIR / "gpt_5_5_results.jsonl").write_bytes(
            download(f"https://api.openai.com/v1/files/{status['output_file_id']}/content", headers)
        )
    if status.get("error_file_id"):
        (RAW_DIR / "gpt_5_5_errors.jsonl").write_bytes(
            download(f"https://api.openai.com/v1/files/{status['error_file_id']}/content", headers)
        )
    report = {
        "cancel_collect_finished_at_utc": utc_now(),
        "batch_id": state["batch_id"],
        "status": status.get("status"),
        "request_counts": status.get("request_counts"),
        "output_file_id": status.get("output_file_id"),
        "error_file_id": status.get("error_file_id"),
    }
    write_json(RAW_DIR / "gpt_5_5_cancel_collect_report.json", report)
    print(json.dumps(report, indent=2))
    if status.get("status") not in terminal:
        raise SystemExit("OpenAI cancellation did not reach a terminal state within 20 minutes")
    if not status.get("output_file_id"):
        raise SystemExit("OpenAI did not expose an output file after terminal batch state")


if __name__ == "__main__":
    main()
