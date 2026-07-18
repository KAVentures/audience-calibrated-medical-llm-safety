# Reproducibility and Audit Plan

This study must be reproducible from the public dataset, scripts, prompts, API request files, generated responses, and physician ratings.

## What Is Frozen Before API Calls

- Real-POCQi source files in `data/raw/`.
- Topic sample in `data/processed/topic_sample.csv`.
- Full prompt list in `data/processed/prompt_families.csv`.
- Frozen prompt manifest in `docs/frozen_prompt_manifest.csv`.
- System prompt in `prompts/system_prompt.txt`.
- Request batches in `api_batches/*_requests.jsonl`.
- Cost-estimation table in `api_batches/cost_estimation_summary.csv`.
- Study manifest in `docs/study_reproducibility_manifest.json`.

## What Must Be Logged During API Calls

For each response:

- `response_id`
- `request_id`
- `model_key`
- Exact provider model ID.
- Provider response ID, if returned.
- Timestamp in UTC.
- Prompt ID and SHA-256 hash.
- System prompt SHA-256 hash.
- Temperature.
- Reasoning-effort parameter, if supported.
- Max output tokens.
- Input token count.
- Output token count.
- Reasoning token count, if returned.
- Raw response text.
- Any provider warning, refusal metadata, safety block, or retry event.

## Public Reproducibility Package

A public package should include:

- All non-secret scripts.
- All prompt text.
- All response text.
- All deidentified physician ratings.
- Blinding key after review completion.
- Analysis outputs and manuscript tables.
- Exact provider model IDs and generation dates.

Do not include API keys, private billing records, or reviewer identities.

## Review Blinding

Reviewers receive `data/review_packets/physician_review_packet_all.csv`, which hides model identity. The unblinded model mapping is stored separately as `data/review_packets/blinding_key_do_not_share_with_reviewers.csv`.

## Repeatability Boundary

Exact output reproduction is not guaranteed across future provider model updates, even with identical prompts and parameters. The manuscript must therefore report model IDs and generation dates, and the archived response text is the analytic dataset.

