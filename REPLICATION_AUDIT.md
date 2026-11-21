# Research integrity and replication audit

## Main contribution and claim boundary

The paired 100-topic, 1,200-response design crosses four generator models,
three prompt formulations and four blinded AI judges. The experimental result
is **measurement sensitivity**: fixed responses received substantially
different automated harm labels depending on the scoring procedure. This is
clinically relevant evidence that safety rankings can be evaluator-sensitive;
it is **not** an independently physician-calibrated measure of actual harm.

## Quantified robustness limits

- The panel assigned 25/4,800 primary ratings unsafe (0.52%).
  GPT-5.5 supplied 18/25 (72%) of the positive ratings.
- The prespecified logistic interaction analysis was not estimable because of
  structural zeros. The identity-link interaction analysis was post hoc.
- The unsafe generator-by-prompt interaction was no longer detected after
  removing GPT-5.5 from the judge panel (7 positive events; P=0.111 raw).
  The interaction is therefore **judge-dependent**, not a stable clinical
  audience effect established across judges.
- The independent physician reference standard is absent. Ten examples
  discussed by the author and an AI assistant for an exploratory scoring
  stream do not establish physician-only rating provenance and cannot
  establish clinical sensitivity, specificity or model ranking.
- 446/1,200 final responses were regenerated under frozen technical criteria
  following truncation; the regeneration was highly uneven (GPT 148,
  Gemini 271, Claude 27, Grok 0). The original/ replacement lineage is
  documented in `generation_docs/technical_regeneration_run_report_20260714.md`.
  Differential truncation and re-generation remain possible model-comparison
  confounders and should not be concealed or interpreted as clinical findings.
- Three legacy secondary workbooks had incomplete inference provenance;
  two rule-engine workbooks were byte-for-byte equivalent in scored values
  and rationales and are correctly counted as **one** deterministic evaluator.
- Clinician-original and patient-rewrite prompts differ in both audience and
  language. The controlled role-only condition isolates a narrower audience
  cue, not a fully ecological patient consultation.

## Reproducibility engineering

The merged panel must include exactly the 1,320 frozen opaque IDs for each
judge: 1,200 primary and 120 blinded repeat occurrences. The fixed validator
rejects duplicate, missing, unexpected, invalid, and wrong-occurrence records
before writing analysis-ready files. Negative regression tests reproduce
the ID-swap and duplicate failure modes. The previously archived audit
records 1,320 distinct valid IDs per judge, so the defect was a defensive
validation gap, not evidence the released analysis was contaminated.

Run `python -m unittest discover -s tests -v` and
`python scripts/check_research_integrity.py` for offline structural and
archived-summary consistency checks. These are **not** substitutes for
independently reproducing every published statistic from the raw responses
or acquiring independent physician reference data.

## Artifacts and independent review

The manuscript source is `manuscript/manuscript.md` and is mirrored in
`PAPER.md`. Word and PDF derivatives must be regenerated after source edits
and visually inspected to ensure they contain the same wording.
Neither the presence of a checked-in PDF nor passing static tests is proof
of scientific correctness.

Related clinical LLM benchmarking studies may use public Real-POCQi topics
or model families overlapping this work. Shared source topics do not
constitute independent replication. Any actual overlap of evaluated outputs
or judge evaluations should be checked before claiming independent evidence.
