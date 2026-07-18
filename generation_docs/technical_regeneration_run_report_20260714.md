# Technical Regeneration Run Report

## Outcome

- Original responses retained unchanged: 754
- Technically regenerated responses: 446
- Final analytic responses: 1,200 unique model-prompt cells
- Final coverage: 300 responses per model and 400 responses per prompt version
- Validation: passed
- Empty answers: 0
- Serialized API objects substituted for answers: 0
- Regenerated responses with incomplete provider status: 0

## Exact Run Times

The technical regeneration ran on 2026-07-14.

- UTC: 2026-07-14 17:48:06 to 2026-07-14 18:30:54
- Europe/Stockholm: 2026-07-14 19:48:06 to 2026-07-14 20:30:54 CEST

## Model-Specific Regeneration

### GPT-5.5

- Requested model ID: `gpt-5.5`
- Returned model ID: `gpt-5.5-2026-04-23`
- Regenerated responses: 148
- Reasoning parameter: `reasoning.effort=high`
- Temperature: omitted because unsupported/rejected
- Output allowance: 8,192 tokens for 146 responses; 16,384 tokens for two technical retries
- Provider completion status: `completed` for all 148 accepted responses

### Gemini 3.5 Flash

- Requested and returned model ID: `gemini-3.5-flash`
- Regenerated responses: 271
- Reasoning parameter: omitted/provider default to match the original within-model run settings
- Temperature: 0
- Output allowance: 8,192 tokens for 268 responses; 16,384 tokens for three timeout retries
- Provider finish reason: `STOP` for all 271 accepted responses

### Claude Opus 4.8

- Requested and returned model ID: `claude-opus-4-8`
- Regenerated responses: 27
- Reasoning parameter: omitted/provider default to match the original within-model run settings
- Temperature: omitted because unsupported/deprecated
- Output allowance: 8,192 tokens
- Provider stop reason: `end_turn` for all 27 accepted responses

### Grok 4.3

- Regenerated responses: 0
- All 300 original responses were retained because none met the frozen technical-regeneration criteria.

## Data Lineage

Every regenerated row records `technical_regeneration=true`, its regeneration reason, original timestamp, original response SHA-256, original output-token count, new timestamp, returned model ID, finish reason, and new response SHA-256. Raw provider responses are retained for all 446 regenerated rows. The 754 retained rows preserve their original response text, timestamps, and hashes.

## Physician Packets

Two blinded reviewer packets contain 720 responses each: 600 primary assignments and 120 reliability-overlap assignments. The packets overlap on 240 responses and together cover all 1,200 responses. Model identity and assignment status are absent from reviewer-facing files. Internal blinding and assignment keys must not be shared with reviewers.
