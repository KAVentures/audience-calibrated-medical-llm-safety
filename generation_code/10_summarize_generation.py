#!/usr/bin/env python3
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESPONSES = ROOT / "responses" / "model_responses.csv"
ERRORS = ROOT / "responses" / "generation_errors.jsonl"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
RESULTS.mkdir(exist_ok=True)


def main() -> None:
    df = pd.read_csv(RESPONSES)
    df["created_at_utc"] = pd.to_datetime(df["created_at_utc"], utc=True)
    df["created_at_stockholm"] = df["created_at_utc"].dt.tz_convert("Europe/Stockholm")

    summary = df.groupby(["model_key", "provider", "provider_model_id"]).agg(
        responses=("response_id", "count"),
        first_response_utc=("created_at_utc", "min"),
        last_response_utc=("created_at_utc", "max"),
        first_response_stockholm=("created_at_stockholm", "min"),
        last_response_stockholm=("created_at_stockholm", "max"),
        input_tokens=("input_tokens", "sum"),
        output_tokens=("output_tokens", "sum"),
        reasoning_tokens=("reasoning_tokens", "sum"),
        max_output_tokens=("max_output_tokens", "first"),
        temperature_requested=("temperature_requested", "first"),
        temperature_parameter_sent=("temperature_parameter_sent", "first"),
        reasoning_effort_requested=("reasoning_effort_requested", "first"),
        reasoning_effort_parameter_sent=("reasoning_effort_parameter_sent", "first"),
    ).reset_index()
    summary.to_csv(RESULTS / "generation_run_summary_by_model.csv", index=False)

    prompt_counts = df.groupby(["model_key", "prompt_version"]).size().reset_index(name="n")
    prompt_counts.to_csv(RESULTS / "generation_prompt_coverage.csv", index=False)

    errors = []
    if ERRORS.exists():
        for line in ERRORS.read_text().splitlines():
            if line.strip():
                errors.append(json.loads(line))
    error_summary = pd.DataFrame(errors)
    if len(error_summary):
        error_summary.to_csv(RESULTS / "generation_error_log.csv", index=False)

    report = []
    report.append("# Model Generation Run Report\n")
    report.append("## Status\n")
    report.append(f"- Completed analytic responses: {len(df)} / 1200\n")
    report.append(f"- Unique response IDs: {df['response_id'].nunique()}\n")
    report.append(f"- Generation date range UTC: {df['created_at_utc'].min()} to {df['created_at_utc'].max()}\n")
    report.append(f"- Generation date range Europe/Stockholm: {df['created_at_stockholm'].min()} to {df['created_at_stockholm'].max()}\n")
    report.append(f"- Prompt hashes present for every row: {df['prompt_sha256'].notna().all()}\n")
    report.append(f"- System prompt hashes present for every row: {df['system_prompt_sha256'].notna().all()}\n")
    report.append("\n## Exact Model IDs and Parameters\n")
    for _, row in summary.iterrows():
        report.append(f"### {row['model_key']}\n")
        report.append(f"- Provider: {row['provider']}\n")
        report.append(f"- Exact provider model ID: `{row['provider_model_id']}`\n")
        report.append(f"- Responses: {row['responses']}\n")
        report.append(f"- First response UTC: {row['first_response_utc']}\n")
        report.append(f"- Last response UTC: {row['last_response_utc']}\n")
        report.append(f"- First response Europe/Stockholm: {row['first_response_stockholm']}\n")
        report.append(f"- Last response Europe/Stockholm: {row['last_response_stockholm']}\n")
        report.append(f"- Temperature requested: {row['temperature_requested']}\n")
        report.append(f"- Temperature parameter sent: `{row['temperature_parameter_sent']}`\n")
        report.append(f"- Reasoning effort requested: `{row['reasoning_effort_requested']}`\n")
        report.append(f"- Reasoning effort parameter sent: `{row['reasoning_effort_parameter_sent']}`\n")
        report.append(f"- Max output tokens: {row['max_output_tokens']}\n")
        report.append(f"- Input tokens recorded: {row['input_tokens']}\n")
        report.append(f"- Output tokens recorded: {row['output_tokens']}\n")
        report.append(f"- Reasoning tokens recorded: {row['reasoning_tokens']}\n")
        report.append("")
    report.append("## Retry Notes\n")
    report.append("Smoke-test outputs are preserved under `responses/smoke_tests/` and are excluded from the analytic response CSV.\n")
    report.append("Transient main-run failures are preserved in `responses/generation_errors.jsonl`; all missing analytic cells were retried until 1,200 unique responses were present.\n")
    report.append("GPT-5.5 and Claude Opus 4.8 rejected explicit temperature parameters, so temperature was requested as 0 in the protocol but omitted in the actual API calls and logged as omitted unsupported/deprecated.\n")
    report.append("OpenAI GPT-5.5 received `reasoning: {effort: high}`. The other providers did not receive a provider-specific reasoning-effort parameter in this runner and are logged as omitted or provider default.\n")
    (DOCS / "model_generation_run_report.md").write_text("\n".join(report))

    print(f"responses: {len(df)}")
    print(f"unique responses: {df['response_id'].nunique()}")
    print(f"wrote {RESULTS / 'generation_run_summary_by_model.csv'}")
    print(f"wrote {DOCS / 'model_generation_run_report.md'}")


if __name__ == "__main__":
    main()

