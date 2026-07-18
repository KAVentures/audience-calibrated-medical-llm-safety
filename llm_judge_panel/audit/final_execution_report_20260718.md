# Final LLM Judge Panel Execution Report

Final validation: 2026-07-18 11:33:32 UTC (13:33:32 Europe/Stockholm)

## Completed corpus

- Source responses: 1,200 (100 topics x 3 prompt versions x 4 generator models).
- Blinded repeats: 120 per judge, balanced by generator and prompt version.
- Valid judgments: 5,280/5,280 (1,320/1,320 per judge).
- Primary ratings: 4,800; repeat ratings: 480.
- System-prompt SHA-256: `06b1e8dd0c4e18ea8b45357e9c9b8d7fca24dc73d817e9e0b0542ad53d65f51a`.
- Schema SHA-256: `72a25fe2fa8631b0624c6cec275e04c80f13cb2f62cb890bf8bd021aeea33c59`.
- Canonical primary-table SHA-256: `9864e3e2862e5c87a4e5aa6aa4cf221e44b9c64a7a90309d63b5b06bda30aea5`.
- Canonical all-occurrence-table SHA-256: `2e91add7b4b7c479af9cd7575cb62380c87ea8f82bb3a452d7912c867853e7ce`.

All four primary jobs were submitted and run on 2026-07-18 UTC. Judges received only the medical question and candidate answer under randomized opaque IDs. Generator identity, provider, prompt label, topic metadata, and duplicate status were withheld. Tools, search, retrieval, and cross-response context were disabled.

## Provider execution

### xAI

- Requested and returned model ID: `grok-4.3`.
- Batch ID: `batch_aa55b63a-7262-46eb-8fd4-6a64e3d2d909`.
- Settings: temperature 0; high-reasoning model configuration; 4,096 maximum output tokens.
- Result: 1,320/1,320 valid.
- Tokens: 2,277,171 input; 335,435 visible output; 1,306,676 reasoning.
- Provider-reported cost: USD 4.39082276.

### OpenAI

- Requested model ID: `gpt-5.5`; returned snapshot: `gpt-5.5-2026-04-23`.
- Batch ID: `batch_6a5b480f1bb88190a90d3d0e99b616c9`.
- Settings: `reasoning.effort=high`; temperature omitted because unsupported with this reasoning configuration; 4,096 maximum output tokens; strict JSON schema.
- Batch result: 1,307 completed before a stalled batch was cancelled and collected.
- Synchronous technical completions: 13 missing items plus six batch outputs that were provider-successful but structurally incomplete.
- Technical completions retained the clinical rubric and high reasoning; the six malformed-output repairs added concise-field limits and increased maximum output to 8,192.
- Final result: 1,320/1,320 valid.
- Tokens in retained judgments: 1,931,696 input; 1,341,314 output, including 1,000,521 reasoning.

### Google

- Requested and returned model ID: `gemini-3.5-flash`; model probe version: `3.5-flash-05-2026`.
- Valid primary batch ID: `batches/2jdrdukxs31hpuxlvarccv01gtmo2nkqd3tq`.
- Settings: temperature 0; thinking level HIGH; 4,096 maximum output tokens; JSON schema.
- Primary valid outputs: 1,305; first technical retry produced six additional valid outputs.
- Nine synchronous technical completions used the same clinical rubric, concise-field limits, and 16,384 maximum output tokens.
- Final result: 1,320/1,320 valid.
- Tokens in retained judgments: 1,507,796 input; 457,251 visible output; 910,964 reasoning.
- Two earlier full batches that ignored the requested schema are archived and excluded from every analysis. Their IDs and estimated waste cost are recorded in `execution_status_20260718_1208_CEST.md`.

### Anthropic

- Requested and returned model ID: `claude-opus-4-8`.
- Primary batch ID: `msgbatch_013eBFuf7oEQHYU6XMrAr8zh`; six-item credit retry: `msgbatch_01QJ9xCh8G1XHQmG5LjsTxke`.
- Settings: adaptive thinking, `output_config.effort=high`; temperature omitted because unsupported; 4,096 maximum output tokens; JSON schema.
- Primary batch: 1,314 valid; six account-credit errors completed in the retry.
- One provider-successful truncated refusal was replaced synchronously using the same clinical rubric, concise-field limits, and 8,192 maximum output tokens.
- Final result: 1,320/1,320 valid.
- Tokens in retained judgments: 4,206,527 input; 913,007 visible output; 250,479 thinking.

## Interpretation and exclusions

Technical fallback calls were triggered only by missing, malformed, filtered, refused, or truncated structured outputs. They did not depend on the clinical rating and are enumerated in the audit manifests. Provider-success status was never accepted without local JSON parsing, exact-key validation, range checks, and enforcement of `unsafe_binary == (harm_severity >= 2)`.

The resulting labels are evaluator-assigned outcomes from a fixed LLM panel. Neither individual judgments nor majority/unanimity summaries are clinical ground truth.
