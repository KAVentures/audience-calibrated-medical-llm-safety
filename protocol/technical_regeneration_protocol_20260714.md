# Technical Regeneration Protocol

## Purpose

This protocol repairs responses that were technically incomplete in the original generation run without regenerating valid responses. The repair is not a second sampling pass and is not based on response quality, correctness, safety, or model identity as perceived from the answer text.

## Original Run Defect

The original generation runner imposed a maximum of 1,200 output tokens. Provider finish metadata and raw provider responses were not retained. Some models used part of this allowance for hidden reasoning, and the runner treated any HTTP-successful response as complete. This caused mid-sentence truncation and, in 38 GPT-5.5 cases, substitution of a serialized raw API response when no visible answer text was returned.

## Objective Selection Rules

A response was selected for technical regeneration if one or more of the following rules applied:

1. GPT-5.5 or Claude Opus 4.8 reported at least 1,200 output tokens, indicating that the original output ceiling was reached.
2. The response text began with a serialized provider response object rather than a medical answer.
3. A Gemini 3.5 Flash response ended without terminal punctuation or a closing delimiter, indicating likely mid-sentence termination. This text-based rule was necessary because the original Gemini finish reason was not retained.

The resulting frozen regeneration set contains 446 responses: 148 GPT-5.5, 271 Gemini 3.5 Flash, and 27 Claude Opus 4.8 responses. No Grok 4.3 response met a regeneration criterion.

## Regeneration Settings

- The original prompt text, system prompt, prompt hashes, requested model ID, and API endpoint are unchanged.
- The maximum output allowance is increased from 1,200 to 8,192 tokens.
- A response rejected for timeout or for exhausting 8,192 tokens is retried once at 16,384 tokens. This escalation applied to three Gemini and two GPT responses.
- Within each model, the reasoning and temperature parameters match the original run. GPT-5.5 receives high reasoning effort. Grok, Gemini, and Claude retain the original omitted/provider-default reasoning settings. Temperature remains 0 for Grok and Gemini and omitted for GPT and Claude because those APIs rejected or disallowed explicit temperature control.
- Every regenerated response must contain non-empty answer text and a provider completion reason. Incomplete responses are rejected rather than exported.
- Raw provider responses are retained for regenerated rows.

## Data Lineage

Valid original responses retain their original response text, timestamp, and SHA-256 hash. Regenerated rows retain the same study response ID and request ID but receive a new timestamp and response hash. The final dataset includes the original timestamp, original response hash, original output-token count, and technical regeneration reason for every replaced row.

## Analysis Handling

Technical regeneration status is metadata, not an outcome. The primary analysis includes the final complete response for each of the 1,200 prespecified model-prompt cells. A sensitivity analysis should compare primary results with and without technically regenerated rows to assess whether the repair materially affects conclusions.
