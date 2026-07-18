# Evaluator-method analysis addendum

Date frozen: 2026-07-18, after receipt of the rescored workbook and after completion of the four-judge panel.

## Status

This is an explicitly post hoc secondary methodological analysis. It does not alter the panel's co-primary outcomes or create a clinical reference standard.

## Objective

Assess whether the prevalence and generator-by-prompt conclusions are stable across evaluator specifications applied to the same 1,200 responses.

## Evaluator specifications

1. Four blinded LLM judges using one frozen structured rubric, analysed individually and as an equally weighted panel.
2. A physician-calibrated holistic GPT-5.6 evaluator stream supplied by the author.
3. A deterministic risk-averse text-feature scoring engine.

The Claude-labelled and GPT-labelled engine workbooks will first be compared on every scored field and rationale. If identical, they will be counted once and interpreted as duplicate execution of one evaluator specification, not independent judges.

## Outcomes

Nominally matched unsafe and evidence-sufficiency binary labels are compared as evaluator outputs. No method is assumed to measure clinical truth. Component and ordinal outcomes are used to describe mechanism, not to construct a pooled composite.

## Analyses

- Positive counts, rates, and 95% complete-topic bootstrap confidence intervals for each complete evaluator stream.
- Pairwise exact agreement, Cohen kappa, and Gwet AC1.
- Paired discordance between holistic GPT and deterministic engine labels.
- Generator-by-prompt interaction results reported under each method's implemented model, with estimating-family differences made explicit.
- Exact field-level audit of the two scoring-engine-labelled workbooks.

Bootstrap seed: 20260718. Bootstrap replicates: 5,000.

## Interpretation constraints

- Do not pool evaluator streams.
- Do not count duplicate engine workbooks as separate votes.
- Do not describe AI-assisted or rule-engine outputs as physician review.
- Do not infer sensitivity, specificity, or clinical prevalence without independent physician adjudication.
