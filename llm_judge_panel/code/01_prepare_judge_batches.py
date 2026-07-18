#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict

from common import (
    AUDIT_DIR,
    INPUT_DIR,
    INSTRUMENT_DIR,
    MODEL_CONFIG,
    PANEL_ROOT,
    SOURCE_CSV,
    model_visible_user_text,
    provider_schema,
    sha256_file,
    utc_now,
    write_json,
)


SEED = 20260718
MAX_OUTPUT_TOKENS = 4096
DUPLICATES_PER_CELL = 10


def request_body(provider: str, model_id: str, system: str, user: str, schema: dict) -> dict:
    if provider == "openai":
        return {
            "model": model_id,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "reasoning": {"effort": "high"},
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "medical_safety_judgment",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
    if provider == "xai":
        return {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "reasoning_effort": "high",
            "max_tokens": MAX_OUTPUT_TOKENS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "medical_safety_judgment",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
    if provider == "anthropic":
        return {
            "model": model_id,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "thinking": {"type": "adaptive", "display": "omitted"},
            "output_config": {
                "effort": "high",
                "format": {"type": "json_schema", "schema": schema},
            },
        }
    if provider == "google":
        return {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generation_config": {
                "temperature": 0,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "thinking_config": {"thinking_level": "HIGH", "include_thoughts": False},
                "response_mime_type": "application/json",
                "response_json_schema": schema,
            },
        }
    raise ValueError(provider)


def main() -> None:
    for path in [INPUT_DIR, AUDIT_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    system = (INSTRUMENT_DIR / "judge_system_prompt.txt").read_text(encoding="utf-8").strip()
    schema = provider_schema()
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1200, f"Expected 1200 rows, found {len(rows)}"
    assert len({row["response_id"] for row in rows}) == 1200
    assert all(row["prompt_text"].strip() and row["response_text"].strip() for row in rows)
    coverage = Counter((r["model_key"], r["prompt_version"]) for r in rows)
    assert set(coverage.values()) == {100}, coverage

    rng = random.Random(SEED)
    primary = rows[:]
    rng.shuffle(primary)
    by_cell = defaultdict(list)
    for row in rows:
        by_cell[(row["model_key"], row["prompt_version"])].append(row)
    duplicates = []
    for cell in sorted(by_cell):
        candidates = sorted(by_cell[cell], key=lambda r: r["response_id"])
        duplicates.extend(rng.sample(candidates, DUPLICATES_PER_CELL))
    assert len(duplicates) == 120

    occurrences = [(row, 1) for row in primary] + [(row, 2) for row in duplicates]
    rng.shuffle(occurrences)
    blind_rows = []
    for index, (row, occurrence) in enumerate(occurrences, start=1):
        opaque_id = f"J{index:06d}"
        blind_rows.append({
            "opaque_id": opaque_id,
            "response_id": row["response_id"],
            "occurrence": occurrence,
            "model_key": row["model_key"],
            "provider": row["provider"],
            "topic_id": row["topic_id"],
            "prompt_id": row["prompt_id"],
            "prompt_version": row["prompt_version"],
            "audience": row["audience"],
            "specialty": row["specialty"],
            "prompt_sha256": row["prompt_sha256"],
            "response_sha256": row["response_sha256"],
        })

    key_path = AUDIT_DIR / "blinding_key_do_not_share_with_judges.csv"
    with key_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(blind_rows[0]))
        writer.writeheader()
        writer.writerows(blind_rows)

    row_lookup = {row["response_id"]: row for row in rows}
    input_summaries = {}
    for judge_key, cfg in MODEL_CONFIG.items():
        path = INPUT_DIR / f"{judge_key}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for blind in blind_rows:
                row = row_lookup[blind["response_id"]]
                body = request_body(
                    cfg["provider"],
                    cfg["model_id"],
                    system,
                    model_visible_user_text(row["prompt_text"], row["response_text"]),
                    schema,
                )
                if cfg["provider"] == "openai":
                    request = {"custom_id": blind["opaque_id"], "method": "POST", "url": "/v1/responses", "body": body}
                elif cfg["provider"] == "xai":
                    request = {"custom_id": blind["opaque_id"], "method": "POST", "url": "/v1/chat/completions", "body": body}
                elif cfg["provider"] == "anthropic":
                    request = {"custom_id": blind["opaque_id"], "params": body}
                else:
                    request = {"key": blind["opaque_id"], "request": body}
                handle.write(json.dumps(request, separators=(",", ":"), ensure_ascii=True) + "\n")
        input_summaries[judge_key] = {
            **cfg,
            "path": str(path.relative_to(PANEL_ROOT)),
            "requests": len(occurrences),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    report = {
        "prepared_at_utc": utc_now(),
        "protocol_version": "1.0",
        "random_seed": SEED,
        "source_csv": str(SOURCE_CSV),
        "source_csv_sha256": sha256_file(SOURCE_CSV),
        "source_responses": len(rows),
        "duplicate_responses": len(duplicates),
        "requests_per_judge": len(occurrences),
        "total_requests": len(occurrences) * len(MODEL_CONFIG),
        "coverage": {f"{a}|{b}": count for (a, b), count in sorted(coverage.items())},
        "duplicate_coverage": dict(Counter(f"{r['model_key']}|{r['prompt_version']}" for r in duplicates)),
        "system_prompt_sha256": sha256_file(INSTRUMENT_DIR / "judge_system_prompt.txt"),
        "schema_sha256": sha256_file(INSTRUMENT_DIR / "judge_schema.json"),
        "blinding_key_sha256": sha256_file(key_path),
        "inputs": input_summaries,
        "checks": {
            "source_count_1200": True,
            "unique_response_ids": True,
            "complete_factorial_coverage": True,
            "nonempty_prompts_and_responses": True,
            "balanced_duplicate_sample": True,
            "opaque_model_visible_identifiers": True,
        },
    }
    write_json(AUDIT_DIR / "preflight_report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
