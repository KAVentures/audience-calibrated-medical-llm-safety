# Model Generation Run Report

## Status

- Completed analytic responses: 1200 / 1200

- Unique response IDs: 1200

- Generation date range UTC: 2026-07-08 22:31:55.070430+00:00 to 2026-07-14 18:30:54.934071+00:00

- Generation date range Europe/Stockholm: 2026-07-09 00:31:55.070430+02:00 to 2026-07-14 20:30:54.934071+02:00

- Prompt hashes present for every row: True

- System prompt hashes present for every row: True


## Exact Model IDs and Parameters

### claude_4_8_opus

- Provider: anthropic

- Exact provider model ID: `claude-opus-4-8`

- Responses: 300

- First response UTC: 2026-07-09 01:46:17.104680+00:00

- Last response UTC: 2026-07-14 17:56:34.320787+00:00

- First response Europe/Stockholm: 2026-07-09 03:46:17.104680+02:00

- Last response Europe/Stockholm: 2026-07-14 19:56:34.320787+02:00

- Temperature requested: 0

- Temperature parameter sent: `omitted_unsupported_or_deprecated`

- Reasoning effort requested: `high_where_available`

- Reasoning effort parameter sent: `omitted_or_provider_default`

- Max output tokens: 1200

- Input tokens recorded: 88537

- Output tokens recorded: 291644

- Reasoning tokens recorded: 0


### gemini_3_5_flash

- Provider: google

- Exact provider model ID: `gemini-3.5-flash`

- Responses: 300

- First response UTC: 2026-07-09 01:15:24.673390+00:00

- Last response UTC: 2026-07-14 18:30:25.410851+00:00

- First response Europe/Stockholm: 2026-07-09 03:15:24.673390+02:00

- Last response Europe/Stockholm: 2026-07-14 20:30:25.410851+02:00

- Temperature requested: 0

- Temperature parameter sent: `0`

- Reasoning effort requested: `high_where_available`

- Reasoning effort parameter sent: `omitted_or_provider_default`

- Max output tokens: 8192

- Input tokens recorded: 56196

- Output tokens recorded: 235816

- Reasoning tokens recorded: 310780


### gpt_5_5

- Provider: openai

- Exact provider model ID: `gpt-5.5`

- Responses: 300

- First response UTC: 2026-07-08 23:17:35.257365+00:00

- Last response UTC: 2026-07-14 18:30:54.934071+00:00

- First response Europe/Stockholm: 2026-07-09 01:17:35.257365+02:00

- Last response Europe/Stockholm: 2026-07-14 20:30:54.934071+02:00

- Temperature requested: 0

- Temperature parameter sent: `omitted_unsupported_or_deprecated`

- Reasoning effort requested: `high_where_available`

- Reasoning effort parameter sent: `high`

- Max output tokens: 1200

- Input tokens recorded: 64759

- Output tokens recorded: 385986

- Reasoning tokens recorded: 153794


### grok_4_3

- Provider: xai

- Exact provider model ID: `grok-4.3`

- Responses: 300

- First response UTC: 2026-07-08 22:31:55.070430+00:00

- Last response UTC: 2026-07-09 03:22:14.917929+00:00

- First response Europe/Stockholm: 2026-07-09 00:31:55.070430+02:00

- Last response Europe/Stockholm: 2026-07-09 05:22:14.917929+02:00

- Temperature requested: 0

- Temperature parameter sent: `0`

- Reasoning effort requested: `high_where_available`

- Reasoning effort parameter sent: `omitted_or_provider_default`

- Max output tokens: 1200

- Input tokens recorded: 109358

- Output tokens recorded: 95303

- Reasoning tokens recorded: 0


## Retry Notes

Smoke-test outputs are preserved under `responses/smoke_tests/` and are excluded from the analytic response CSV.

Transient main-run failures are preserved in `responses/generation_errors.jsonl`; all missing analytic cells were retried until 1,200 unique responses were present.

GPT-5.5 and Claude Opus 4.8 rejected explicit temperature parameters, so temperature was requested as 0 in the protocol but omitted in the actual API calls and logged as omitted unsupported/deprecated.

OpenAI GPT-5.5 received `reasoning: {effort: high}`. The other providers did not receive a provider-specific reasoning-effort parameter in this runner and are logged as omitted or provider default.
