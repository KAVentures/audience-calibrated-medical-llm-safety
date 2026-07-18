#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
BATCHES = ROOT / "api_batches"
CONFIG = ROOT / "config" / "models.yaml"
SYSTEM_PROMPT = (ROOT / "prompts" / "system_prompt.txt").read_text()
BATCHES.mkdir(exist_ok=True)

MODEL_KEYS = [
    "grok_4_3",
    "gpt_5_5",
    "gemini_3_5_flash",
    "claude_4_8_opus",
]


def rough_tokens(text: str) -> int:
    return max(1, int(len(re.findall(r"\S+", text)) / 0.75))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    prompts_path = PROCESSED / "prompt_families.csv"
    if not prompts_path.exists():
        raise SystemExit("Missing data/processed/prompt_families.csv. Run scripts/02_build_prompt_families.py first.")

    prompts = pd.read_csv(prompts_path)
    system_prompt_sha256 = sha256_text(SYSTEM_PROMPT)
    rows = []
    for model_key in MODEL_KEYS:
        out_path = BATCHES / f"{model_key}_requests.jsonl"
        with out_path.open("w") as f:
            for _, row in prompts.iterrows():
                request_id = f'{row["prompt_id"]}_{model_key}'
                prompt_sha256 = sha256_text(row["prompt_text"])
                body = {
                    "request_id": request_id,
                    "model_key": model_key,
                    "topic_id": row["topic_id"],
                    "prompt_id": row["prompt_id"],
                    "prompt_version": row["prompt_version"],
                    "audience": row["audience"],
                    "specialty": row["specialty"],
                    "prompt_sha256": prompt_sha256,
                    "system_prompt_sha256": system_prompt_sha256,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": row["prompt_text"]},
                    ],
                    "generation": {
                        "temperature": 0,
                        "reasoning_effort": "high_where_available",
                        "max_output_tokens": 1200,
                    },
                    "live_call_allowed": False,
                }
                f.write(json.dumps(body, ensure_ascii=False) + "\n")
                rows.append({
                    "request_id": request_id,
                    "model_key": model_key,
                    "prompt_id": row["prompt_id"],
                    "prompt_version": row["prompt_version"],
                    "audience": row["audience"],
                    "prompt_sha256": prompt_sha256,
                    "system_prompt_sha256": system_prompt_sha256,
                    "input_tokens_estimate": rough_tokens(SYSTEM_PROMPT + "\n" + row["prompt_text"]),
                    "max_output_tokens": 1200,
                })
        print(f"wrote {out_path}")

    estimates = pd.DataFrame(rows)
    estimates.to_csv(BATCHES / "cost_estimation_inputs.csv", index=False)
    summary = estimates.groupby("model_key").agg(
        requests=("request_id", "count"),
        input_tokens_estimate=("input_tokens_estimate", "sum"),
        max_output_tokens=("max_output_tokens", "sum"),
    ).reset_index()
    summary["note"] = "Use vendor prices to calculate cost before live calls."
    summary.to_csv(BATCHES / "cost_estimation_summary.csv", index=False)
    print("wrote cost estimation tables")


if __name__ == "__main__":
    main()
