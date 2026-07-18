# LLM Judge Batch Execution Status

Status captured: 2026-07-18 12:08 CEST / 2026-07-18 10:08 UTC

## Frozen Settings

- Corpus: 1,200 responses plus 120 blinded duplicates per judge.
- Requests: 1,320 per judge; 5,280 planned panel judgments.
- Model-visible input: medical question plus candidate response only.
- Generator identity and study metadata: withheld using opaque IDs.
- Reasoning: high or closest provider-supported equivalent.
- Temperature: 0 where accepted.
- Tools/search/retrieval: disabled.
- Primary maximum output: 4,096 tokens.
- Structured output: frozen JSON schema SHA-256 `72a25fe2fa8631b0624c6cec275e04c80f13cb2f62cb890bf8bd021aeea33c59`.
- System prompt SHA-256: `06b1e8dd0c4e18ea8b45357e9c9b8d7fca24dc73d817e9e0b0542ad53d65f51a`.

## Provider Jobs

### xAI

- Exact requested and returned model: `grok-4.3`.
- Batch ID: `batch_aa55b63a-7262-46eb-8fd4-6a64e3d2d909`.
- Result: 1,320/1,320 succeeded.
- Provider-reported cost: USD 4.39082276.
- Tokens: 2,277,171 prompt; 335,435 visible completion; 1,306,676 reasoning.
- Documented batch discount: 20%.

### OpenAI

- Exact requested model: `gpt-5.5`.
- Batch ID: `batch_6a5b480f1bb88190a90d3d0e99b616c9`.
- Current status: in progress, 1,291/1,320 completed and 0 failed at the latest poll.
- Reasoning effort: high.
- Documented batch discount: 50%.

### Google

- Exact requested and returned model: `gemini-3.5-flash`.
- Valid full-batch ID: `batches/2jdrdukxs31hpuxlvarccv01gtmo2nkqd3tq`.
- Result: 1,305 schema-valid responses; 14 `MAX_TOKENS` and one `RECITATION` technical failure.
- Technical retry batch: `batches/kedtzdm0b2krfmy4kt01c89ceopyml8m42m0`, 15 requests, in progress.
- Retry changed only maximum output from 4,096 to 8,192 tokens.
- Documented batch discount: 50%.

Two earlier Google batches completed but ignored the requested schema because of Batch API field-name handling. Both are archived and excluded from every analysis:

- `batches/daisyb2gmww1v4g2x4i9idjvw2k7jtdknale`
- `batches/379ga4qdiua8tyrg3njimrkrpfoty4m8q9by`

The exact snake-case Batch API request was validated with a one-item batch before the valid full-batch submission. The two excluded full batches cost an estimated USD 12.34 in total based on returned token usage and published batch prices. They are retained solely for execution and cost audit.

### Anthropic

- Exact requested and returned model: `claude-opus-4-8`.
- Batch ID: `msgbatch_013eBFuf7oEQHYU6XMrAr8zh`.
- Result: 1,314/1,320 succeeded with schema-valid structured output.
- Six requests were rejected only because the account credit balance was exhausted; all six belong to primary rather than duplicate occurrences.
- Estimated completed-batch cost from returned usage: USD 21.82.
- Estimated additional cost for six identical retries: approximately USD 0.10.
- Retry input is frozen but has not been submitted because the provider reported insufficient credit.
- Documented batch discount: 50%.

## Interpretation

No API consensus or majority label will be described as clinical ground truth. These jobs support evaluator-assigned safety analyses, judge heterogeneity, audience calibration, ranking stability, self-provider effects, and within-judge repeatability.
