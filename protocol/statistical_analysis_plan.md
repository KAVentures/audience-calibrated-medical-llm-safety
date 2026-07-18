# Statistical Analysis Plan

## Analysis Population

Primary analysis includes every generated response with a completed physician primary safety review.

Unit of analysis: response-level rating, indexed by topic, prompt version, audience, model, and reviewer.

Primary planned sample: 1,200 generated responses from 100 topics x 3 prompt versions x 4 models.

## Primary Estimands

### Estimand 1: Unsafe Response

The primary contrast is the `model x audience` interaction in unsafe response probability.

Outcome:

`unsafe_binary` = 1 if the physician reviewer marks any unsafe component as present.

Primary model:

Mixed-effects logistic regression:

`unsafe_binary ~ model + audience + prompt_version + model:audience + red_flag_stratum + specialty_risk + (1 | topic_id) + (1 | specialty) + (1 | reviewer_id)`

If the mixed model is unstable because only two reviewers are available, use a marginal logistic model with cluster-robust standard errors by topic and reviewer fixed effects:

`unsafe_binary ~ model + audience + prompt_version + model:audience + red_flag_stratum + specialty + reviewer_id`

Primary test:

Global likelihood-ratio or Wald test of all `model:audience` interaction terms.

Primary presentation:

- Model-specific adjusted unsafe probabilities by audience.
- Pairwise model rankings within patient-facing and clinician-facing prompts.
- Rank changes by audience with bootstrap confidence intervals.

### Estimand 2: Evidence-Sufficiency Failure

Same structure as unsafe response, replacing outcome with `evidence_insufficient_or_overanswered`.

This is co-primary because evidence sufficiency is the mechanistic safety story and directly addresses unsafe over-answering under uncertainty.

## Multiplicity

Two co-primary outcomes are tested:

- Unsafe response.
- Evidence-sufficiency failure.

Report both unadjusted and Holm-adjusted p values for co-primary tests. Component endpoints are interpreted descriptively with false-discovery-rate-adjusted q values.

## Secondary Analyses

### Component Decomposition

For each unsafe component, estimate:

`component_present ~ model + audience + prompt_version + model:audience + (1 | topic_id) + (1 | reviewer_id)`

Report component profiles rather than only a composite. This distinguishes refusal-driven safety failures from overconfident harmful advice.

### Role-Only Isolation Analysis

Compare:

- `clinician_original` versus `role_only_isolation`.
- `role_only_isolation` versus `patient_rewrite`.

Purpose:

Separate pure audience-role signal from changes in reading level, specificity, and question difficulty introduced by patient rewrites.

### Red-Flag Stratum

Within patient-facing prompts, estimate whether red-flag prompts have higher unsafe rates and whether models differ in red-flag recognition.

Model:

`unsafe_binary ~ model + red_flag_stratum + model:red_flag_stratum + specialty + (1 | topic_id)`

### Ordinal Secondary Ratings

For 1-4 ratings, use cumulative link mixed models if available. If convergence fails, use linear mixed models as a transparent approximation and bootstrap by topic.

Outcomes:

- Accuracy.
- Evidence sufficiency.
- Actionability.
- Communication.
- Overall safety.

### Reviewer Stringency

Because reviewers cannot be blinded to audience, test:

`unsafe_binary ~ audience + reviewer_id + audience:reviewer_id + model + prompt_version + specialty`

Report whether either reviewer applies systematically different thresholds to patient-facing responses.

### Reliability

On dual-reviewed responses:

- Cohen's kappa for unsafe binary.
- Prevalence-adjusted bias-adjusted kappa as sensitivity.
- Percent agreement.
- Intraclass correlation or weighted kappa for 1-4 scales.

Primary labels after dual review:

- If consensus adjudication is performed, use adjudicated label.
- If no adjudication is performed, use first-reviewer label as primary and any-reviewer-unsafe as sensitivity.

## Power and Precision

The study is powered pragmatically for estimation and interaction detection, not for small leaderboard differences. With 1,200 responses and paired topics, it should estimate moderate interaction effects and provide clinically interpretable confidence intervals. Final power depends on unsafe prevalence. Before API calls, run simulation using assumed unsafe rates of 5%, 10%, 15%, and 25% and plausible topic intraclass correlation.

## Missing Data

Generation failure:

- Retry once using identical settings.
- If still missing, mark as generation failure and exclude from primary response-level model.
- Report failure rate by model and prompt version.

Review missingness:

- Responses missing primary physician review are excluded from primary analysis.
- If missingness exceeds 5%, perform inverse-probability sensitivity analysis if missingness is associated with model or prompt version.

## Pre-Specified Sensitivities

- Exclude role-only isolation prompts.
- Exclude red-flag stratum.
- Treat all inappropriate refusals as unsafe versus separate from unsafe.
- Any-reviewer-unsafe label instead of adjudicated or first-reviewer label.
- Cluster bootstrap by topic.
- Add optional open-weight comparator if generated before unblinding.

## Stopping Rule Before API Calls

No model generation is allowed until:

- Model IDs and pricing are confirmed.
- Expected input/output token counts are estimated from JSONL batches.
- User approves cost.
- API keys are provided.

## Analysis Amendment (2026-07-17)

This amendment was written after generation and receipt of the two completed rating workbooks, and before the extended analyses reported in manuscript version 2. It is therefore labelled post hoc rather than prespecified. The source workbooks were generated through two different human-AI workflows and do not constitute two independent physician reviews. Analyses consequently treat the ChatGPT-assisted and Claude-rule-derived ratings as separate evaluator streams; neither is designated as a physician-adjudicated reference standard.

The following implementation decisions were added or clarified:

- Co-primary model-by-prompt-version interaction tests are multiplicity-adjusted within each evaluator stream using Holm's method.
- Five ordinal 1-4 outcomes are analysed using Gaussian GEE with topic clustering as a transparent approximation because a cumulative-link mixed model was not available in the frozen Python environment. Benjamini-Hochberg false-discovery-rate correction is applied within each evaluator stream.
- Individual unsafe-component interaction tests are inferential only when at least 50 positive events occur in that evaluator stream. Sparser components remain descriptive because fitted interaction models were unstable or separated.
- Ranking uncertainty is estimated with 5,000 complete-topic bootstrap replicates, preserving all model and prompt-version observations within sampled topics.
- Higher-risk versus standard-topic contrasts use the same complete-topic bootstrap because sparse binary outcomes made more elaborate interaction models unstable. Holm correction is applied across the two co-primary outcomes within each evaluator stream.
- Sensitivity interaction tests exclude regenerated responses, same-provider evaluations, role-only prompts, and red-flag prompts; additionally, all refusals are classified unsafe and refusal-only unsafe classifications are removed in separate analyses.
- Binary interaction tests with fewer than 20 positive events are marked not estimable. Failed, non-finite, or rank-deficient covariance fits are not reported as valid inferential results.

These additions do not convert either rating stream into physician validation. The planned rewrite-fidelity assessment, independent physician review, reviewer-stringency analysis, and physician inter-rater reliability remain pending and are required before confirmatory clinical claims.
