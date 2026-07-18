# Supplementary appendix

## S1. Reproducibility statement

The replication package freezes all 300 prompts, 1,200 final responses, generation provenance, model-visible judge inputs, the exact judge prompt and schema, provider outputs, 5,280 validated panel ratings, three legacy evaluator workbooks, scoring-engine code, randomization and duplicate keys, analysis code, tables, figures, and document source. API credentials are excluded. No live API call is needed to reproduce the reported analysis.

Analysis freeze: July 18, 2026.  
Bootstrap seed: 20260718.  
Bootstrap replicates: 5,000 complete-topic resamples.  
Primary rating table SHA-256: `9864e3e2862e5c87a4e5aa6aa4cf221e44b9c64a7a90309d63b5b06bda30aea5`.  
All-occurrence table SHA-256: `2e91add7b4b7c479af9cd7575cb62380c87ea8f82bb3a452d7912c867853e7ce`.

## S2. Exact study questions

The source population was the 620-query `questions` split of `jjfenglab/Real-POCQi`. One hundred seed-fixed topics were used. Each contributed:

1. `clinician_original`: the original clinician-facing question.
2. `role_only_isolation`: a patient/caregiver role declaration with the underlying clinical question retained.
3. `patient_rewrite`: a patient-readable rewrite preserving the clinical issue and requesting discussion points and warning signs where appropriate.

The authoritative exact questions are in `data/source/prompt_families.csv`; the full model-visible generator prompts and system prompts are in `data/source/model_responses.csv` and `prompts/`. The rewrite rules are in `protocol/rewrite_protocol.md`. These row-level files, rather than prose examples, permit exact repetition.

## S3. Generator execution

Generation occurred July 8-14, 2026 UTC. Temperature 0 was sent where accepted. Explicit high reasoning was sent to GPT-5.5; the original runner recorded provider defaults for the other generators.

| Generator | Requested ID | Responses | UTC window | Temperature sent | Reasoning sent | Technical regenerations |
|---|---|---:|---|---|---|---:|
| Grok | `grok-4.3` | 300 | Jul 8 22:31-Jul 9 03:22 | 0 | Provider default | 0 |
| GPT | `gpt-5.5` | 300 | Jul 8 23:17-Jul 14 18:30 | Omitted | High for repaired calls | 148 |
| Gemini | `gemini-3.5-flash` | 300 | Jul 9 01:15-Jul 14 18:30 | 0 | Provider default | 271 |
| Claude | `claude-opus-4-8` | 300 | Jul 9 01:46-Jul 14 17:56 | Omitted | Provider default | 27 |

An audit found 446 outputs truncated mid-sentence. Only those IDs were regenerated with stored prompts. The final table retains original and replacement hashes, dates, and technical-regeneration status. Because regeneration was strongly model-dependent, an original-only analysis would be a selected subset and is not used as a confirmatory population.

## S4. Judge-panel protocol

The protocol was frozen July 18, 2026 before submission. Every response was judged by four fixed models. A balanced sample of 120 responses, ten from every generator-by-prompt cell, was duplicated for each judge under a new opaque ID. Duplicate selection and request order used Python Mersenne Twister seed 20260718.

Judges saw only:

`MEDICAL QUESTION`  
`[exact prompt text]`  
`CANDIDATE RESPONSE`  
`[exact final answer]`

They did not receive generator identity, provider, topic, specialty, prompt-version label, response ID, other answers, or duplicate status. The exact system prompt is `llm_judge_panel/instrument/judge_system_prompt.txt`; its SHA-256 is `06b1e8dd0c4e18ea8b45357e9c9b8d7fca24dc73d817e9e0b0542ad53d65f51a`. The exact schema is `judge_schema.json`; its SHA-256 is `72a25fe2fa8631b0624c6cec275e04c80f13cb2f62cb890bf8bd021aeea33c59`.

## S5. Judge API settings and exact IDs

All primary judge calls ran July 18, 2026 UTC. No tools, search, retrieval, or cross-response context were enabled.

| Judge | Requested ID | Returned ID/version | Reasoning | Temperature | Primary maximum |
|---|---|---|---|---|---:|
| Grok | `grok-4.3` | `grok-4.3` | High model configuration | 0 | 4,096 |
| GPT | `gpt-5.5` | `gpt-5.5-2026-04-23` | `reasoning.effort=high` | Omitted as incompatible | 4,096 |
| Gemini | `gemini-3.5-flash` | `gemini-3.5-flash`; probe `3.5-flash-05-2026` | Thinking HIGH | 0 | 4,096 |
| Claude | `claude-opus-4-8` | `claude-opus-4-8` | Adaptive thinking; effort high | Omitted as unsupported | 4,096 |

Primary batch IDs were `batch_aa55b63a-7262-46eb-8fd4-6a64e3d2d909`, `batch_6a5b480f1bb88190a90d3d0e99b616c9`, `batches/2jdrdukxs31hpuxlvarccv01gtmo2nkqd3tq`, and `msgbatch_013eBFuf7oEQHYU6XMrAr8zh`. The complete retry history, excluded invalid-schema Gemini batches, token counts, timestamps, and cost records are in `llm_judge_panel/audit/final_execution_report_20260718.md`.

## S6. Technical judge completion

Provider-success status was never treated as analytic success without local validation. Every output was parsed and checked for exact fields, types, ranges, and `unsafe_binary == (harm_severity >= 2)`.

- Grok: 1,320 valid primary batch outputs.
- GPT: 1,307 batch outputs retained; 13 missing and six structurally incomplete outputs completed synchronously.
- Gemini: 1,305 valid primary outputs, six valid technical batch retries, and nine synchronous completions.
- Claude: 1,314 valid primary outputs, six account-credit retries, and one synchronous completion replacing a truncated refusal.

Format-repair calls were triggered without reference to the clinical label. They retained the same clinical rubric and visible question/response, added only concise output-field requirements, and increased the technical output allowance. All fallback IDs are listed in machine-readable audit manifests.

## S7. Rating instrument

Harm severity was 0-3. Severity 2 indicated plausible moderate harm, meaningful delay, dangerous reassurance, or materially wrong management; severity 3 indicated plausible severe harm, dangerous treatment, or urgent-care failure. Unsafe was true exactly for severity 2-3.

Evidence-sufficiency failure was separate and captured conclusions or management beyond the supplied evidence, or failure to identify information essential for safe interpretation. Ten component flags distinguished factual error, missed red flag, false reassurance, unsafe self-management, overconfident diagnosis or treatment, unsupported recommendation, hallucinated source or guideline, inappropriate refusal, omitted critical clinician caveat, and audience miscalibration. Accuracy, evidence sufficiency, actionability, communication, overall safety, and confidence were rated 1-4.

## S8. Statistical analysis details

Panel rates average the four judges equally. Complete-topic bootstrap samples preserve all 48 primary ratings nested within each topic. The planned model was:

`outcome ~ generator*prompt + judge*prompt + generator*judge`

with binomial family, logit link, exchangeable working correlation within topic, and robust sandwich covariance. The global generator-by-prompt test was co-primary. A saturated `generator*prompt*judge` model tested evaluator heterogeneity. Holm correction covered unsafe and evidence-sufficiency outcomes.

Structural zero cells produced non-finite logistic covariance for both outcomes. Logistic interaction tests are therefore not reported as estimable. A post hoc Gaussian identity-link GEE with the same fixed effects estimates interactions on the absolute-risk scale. Effective degrees of freedom are the numerical covariance rank. These fallback p values are exploratory.

Secondary outputs include judge-specific rates and ranks, leave-one-judge-out ranks, panel prompt contrasts, vote-count summaries, component profiles, same-provider paired differences, pairwise exact agreement, Cohen kappa, Gwet AC1, and within-judge blinded-repeat agreement. Majority and unanimity are explicitly labelled aggregation summaries rather than ground truth.

An influence analysis repeated the same Gaussian identity-link generator-by-prompt test after excluding each judge in turn. This retained the full-panel risk-difference scale and topic-clustered robust covariance. We report raw p values, Holm adjustment across unsafe and evidence-sufficiency outcomes within each omitted-judge analysis, and Holm adjustment across all eight leave-one-judge-out tests. This sensitivity analysis was added after concern about concentration of unsafe events in GPT-5.5 ratings and is explicitly exploratory.

## S9. Main numerical results

| Outcome | Positive ratings / 4,800 | Overall panel rate | Generator-by-prompt test | Holm p |
|---|---:|---:|---|---:|
| Unsafe | 25 | 0.52% | chi-square 14.41; effective 3 df | 0.0048 |
| Evidence insufficiency | 102 | 2.13% | chi-square 6.26; 6 df | 0.39 |

Unsafe response-level vote distribution included 1,180 responses with no positive vote, 16 with one vote, three with two votes, one with three votes, and none with four votes. Pairwise unsafe kappa was 0.00-0.28; evidence-sufficiency kappa was 0.30-0.71. Unsafe blinded-repeat exact agreement was 98.3-100%; evidence-sufficiency repeat agreement was 97.5-100%.

GPT-5.5 contributed 18/25 unsafe ratings. The unsafe interaction was not detected after GPT-5.5 was omitted (7 events; chi-square 6.01; effective 3 df; raw p=0.111; within-omission Holm p=0.223; eight-test Holm p=0.556). It remained detected after omission of Grok, Gemini, or Claude (raw p range 0.0024-0.0038; within-omission Holm p range 0.0048-0.0077). The full table is `results/llm_judge_panel_tables/table_leave_one_judge_interaction_tests.csv`.

All exact cell rates and confidence intervals are in `results/llm_judge_panel_tables/table_panel_standardized_rates.csv`; prompt contrasts are in `table_panel_prompt_contrasts.csv`; judge-specific rates and ranks, agreement, repeatability, vote summaries, component counts, self-provider comparisons, and leave-one-out results are in the same directory.

## S10. Secondary evaluator-method comparison

Before the four-judge panel was run, the author supplied three completed workbooks over the same 1,200 blinded responses. One used a holistic GPT-5.6 process reportedly calibrated from ten physician-scored examples. The ten examples were not marked, and the exact extrapolation prompt and complete model-execution logs were not retained. It is therefore a physician-calibrated AI-assisted evaluator stream, not a physician reference standard.

The other two workbooks were labelled as Claude and GPT applications of the same risk-averse scoring logic. The supplied Python engine used regular expressions for warning signs, clinician caveats, uncertainty, dose directives, reassurance, refusals, named sources with specific figures, and selected patient-facing terminology. Its documentation explicitly stated that it could not verify clinical truth. Field-level audit found exact agreement on all 15 scored fields and all 1,200 rationales for all 1,200 responses. The two workbooks are therefore counted once as one deterministic evaluator specification.

| Evaluator specification | Unsafe | Evidence insufficiency | Unsafe generator-by-prompt interaction |
|---|---:|---:|---:|
| GPT-5.6 holistic | 7/1,200 (0.58%) | 21/1,200 (1.75%) | p=0.94 |
| Deterministic scoring engine | 256/1,200 (21.33%) | 57/1,200 (4.75%) | Holm p=0.000006 |
| Four-judge panel, per rating | 25/4,800 (0.52%) | 102/4,800 (2.13%) | post hoc identity-link Holm p=0.0048 |

The holistic and engine streams used topic-clustered logistic models, whereas the panel value is from a post hoc identity-link fallback after logistic separation; p values are not directly exchangeable. The purpose of the comparison is to show dependence on evaluator implementation, not to select the evaluator closest to truth. Exact rates, pairwise agreement, discordance, interaction results, and duplicate-field checks are in `results/evaluator_method_tables/`. The raw workbooks and their SHA-256 hashes are retained.

## S11. Clinical implications of the deterministic engine

The engine is suitable for reproducible high-sensitivity text screening but not stand-alone clinical judgment. Its unsafe composite is triggered by the union of lexical features. Consequently, it can penalize a specialist answer for omitting generic safety-netting, treat absence of a clinician disclaimer as a critical caveat failure, or mark a named guideline with a specific figure as potentially hallucinated without checking whether the claim is true. Conversely, safety phrases can satisfy a rule even when substantive medical advice is incorrect. Engine-positive results should therefore be described as rule triggers and adjudicated clinically before use as harm labels.

## S12. Minimum physician validation extension

A clinically interpretable extension should use two independent physicians rating the same stratified subset. It should include every response with any panel unsafe vote, all split or majority cases, a stratified sample of holistic-engine discordances spanning engine trigger mechanisms, a balanced sample across the 12 generator-by-prompt cells, and enough all-negative responses to estimate false-negative risk. Ratings should be independent before adjudication, with severity 2-3 disagreements explicitly resolved. The LLM panel and evaluator specifications can then be evaluated against, rather than substituted for, that reference.

## S13. Submission checks

- Retain the written self-assessment documenting why ethical review was not required under the Swedish Ethical Review Act (2003:460).
- Confirm the author's full affiliation address and credentials.
- Verify provider and dataset terms before public redistribution.
- Archive a public version without API keys, local blinding keys if inappropriate, or provider credentials.
- Label every safety rate as evaluator-assigned unless physician adjudication is added.
