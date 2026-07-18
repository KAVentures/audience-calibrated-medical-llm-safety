# Evaluator-dependent conclusions in audience-calibrated medical LLM safety assessment: a paired multi-model benchmark study

Koyar Afrasyab, MD^1^

^1^ Kinvectum AB, Sweden

Correspondence: Koyar Afrasyab, Kinvectum AB; koyar@kinvectum.com  
ORCID: 0009-0009-3530-4606

## Abstract

### Background

Large language models (LLMs) increasingly evaluate other LLMs, but medical-safety conclusions may depend on the evaluator and scoring specification. We examined this dependence while varying intended audience within paired clinical topics.

### Objective

To test whether evaluator-assigned safety and evidence-sufficiency outcomes varied by audience and generator, and whether conclusions were stable across evaluators.

### Methods

We sampled 100 Real-POCQi topics and created clinician-original, patient role-only, and patient-rewritten prompts. Grok 4.3, GPT-5.5, Gemini 3.5 Flash, and Claude Opus 4.8 each answered all 300 prompts (1,200 responses). Responses received four blinded ratings under a frozen rubric (4,800 total); 480 ratings were repeated. Co-primary outcomes were evaluator-assigned unsafe response and evidence-sufficiency failure. Topic-clustered models and 5,000 complete-topic bootstrap resamples assessed generator-by-prompt interactions. Secondary analysis compared the panel with physician-calibrated holistic GPT-5.6 scoring and a deterministic risk-averse text-feature engine.

### Results

The panel assigned 25/4,800 ratings unsafe (0.52%) and 102/4,800 evidence-insufficient (2.13%). Judge-specific unsafe prevalence ranged from 0% to 1.50%; one response reached a three-of-four unsafe majority and none reached unanimity. Unsafe rates decreased from clinician prompts to patient rewrites for Grok-generated responses (2.00% to 0.25%) but increased for Gemini-generated responses (0.25% to 2.50%). The planned logistic model was not estimable because of structural zeros; a post hoc identity-link model detected an unsafe generator-by-prompt interaction (Holm p=0.0048), but not an evidence-sufficiency interaction (p=0.39). After GPT-5.5 was excluded, seven unsafe events remained and the interaction was not detected (risk-scale p=0.11). Pairwise unsafe kappa was 0.00-0.28 despite 98.5-99.8% exact agreement; repeat agreement was 98.3-100%. Holistic GPT-5.6 classified 7/1,200 responses unsafe (0.58%), versus 256/1,200 (21.33%) for the engine, a 36.6-fold difference. The holistic interaction was absent (p=0.94), whereas the engine interaction was present (Holm p=0.000006). GPT-labelled and Claude-labelled engine workbooks matched on every score and rationale, showing duplicate rule execution rather than independent corroboration.

### Conclusions

Evaluator specification should be treated as part of the intervention in medical LLM safety assessment because it changed apparent prevalence and audience dependence. A multi-LLM panel exposed but did not resolve this instability. Comparative safety claims require evaluator-specific reporting and independent physician validation.

## Introduction

Large language models encode substantial clinical knowledge and are increasingly used for professional decision support and public health questions.[1,2] Their evaluation has expanded from examinations to consumer advice, real clinical queries, and simulated care interactions.[3-7] These settings impose different safety requirements. Clinicians may need differential diagnosis, treatment detail, and explicit assumptions; patients may need plain language, uncertainty calibration, warning signs, and protection against unsupported self-management. Safety is therefore relational: it depends on the answer, the evidence supplied, the intended user, and the actions that reasonable reliance could produce.

Most medical LLM benchmarks fix one audience. Real-POCQi and related real-query studies improve ecological validity by using questions submitted by clinicians,[4,5] whereas patient-facing red-teaming evaluates advice-seeking risk.[6] Comparing results across these datasets cannot isolate audience because the clinical topics, wording, models, and graders also differ. Rewriting a clinician question for a patient is realistic but changes reading level, specificity, and sometimes the practical question. A role-only formulation that retains the clinical wording offers a more controlled, although less natural, audience contrast.

Evaluator choice creates a second and potentially larger source of variation. LLM judges permit complete, rapid scoring but are susceptible to threshold, verbosity, self-preference, and other biases.[8-10] Medical safety also presents a prevalence problem: high exact agreement can coexist with poor chance-corrected agreement when positive events are rare. Moreover, a composite can give the same headline label to opposite mechanisms, such as inappropriate refusal and overconfident management. A deterministic rule engine may be reproducible yet clinically invalid if it treats lexical signals as equivalent to correct reasoning.

We therefore used audience calibration as a controlled test case for evaluator sensitivity. The primary analysis asked whether unsafe and evidence-sufficiency ratings varied across generator models and prompt formulations in a fully crossed four-LLM judge panel. The secondary methodological analysis asked whether the prevalence and interaction conclusion persisted under two previously supplied evaluator specifications: holistic GPT scoring calibrated on physician examples and a risk-averse deterministic scoring engine. We did not treat any LLM, rule set, or vote threshold as clinical ground truth.

## Methods

### Study design and data source

This was an offline, fully crossed, paired benchmark using the public `questions` split of Real-POCQi, a dataset of real questions submitted by physicians across specialties.[4] One hundred of 620 topics were selected with a fixed seed. Every topic was crossed with three prompt formulations, four response-generating models, and four primary LLM judges. The response corpus therefore contained 1,200 answers and the primary judge panel contained 4,800 ratings.

### Prompt construction

Each topic contributed a clinician-original, patient role-only, and patient-rewrite prompt. The patient role-only prompt declared that the asker was a patient or caregiver while retaining the underlying clinician question as far as possible. The patient rewrite followed a fixed protocol to replace professional shorthand, preserve the clinical issue, and request questions for the treating clinician and warning signs when appropriate. Thus, the role-only contrast was intended to isolate an audience cue, whereas the patient rewrite represented the ecologically realistic estimand of the same clinical issue expressed as a different question. Exact prompts, machine-readable prompt identifiers, and the rewrite protocol are provided in the replication package.

### Response generation

The 300 prompts were submitted to `grok-4.3`, `gpt-5.5`, `gemini-3.5-flash`, and `claude-opus-4-8`. Generation occurred July 8-14, 2026 UTC. Temperature 0 was sent where accepted; explicit high reasoning was sent to GPT-5.5. The original runner recorded provider defaults for reasoning settings not explicitly exposed or sent for the other generators. A technical audit identified 446 outputs truncated mid-sentence. Only those response identifiers were regenerated with their stored prompts. The final corpus retained original and replacement hashes, timestamps, returned model identifiers, and technical-regeneration status.

### Evaluation procedures

#### Four-LLM judge panel

The panel protocol was frozen on July 18, 2026 before judge submission. The judges were `grok-4.3`, `gpt-5.5`, `gemini-3.5-flash`, and `claude-opus-4-8`. Each evaluated all 1,200 responses. A balanced sample of 120 responses, ten from every generator-by-prompt cell, was repeated for each judge under a different opaque identifier, producing 5,280 planned judgments.

Judges saw only `MEDICAL QUESTION` and `CANDIDATE RESPONSE`. Generator identity, provider, topic, specialty, prompt label, response identifier, and repeat status were withheld. Order was randomized with seed 20260718. Style could still reveal model family, so blinding reduced but could not eliminate identity inference. All judges used the same system prompt and JSON schema, internal knowledge only, no tools or retrieval, and high reasoning effort or the closest provider-supported equivalent. Temperature 0 was used where accepted and omitted where incompatible with reasoning. Every output underwent exact-key, type, range, and severity-to-binary consistency validation. Technical retries were limited to missing or structurally invalid outputs.

#### Secondary evaluator-method comparison

Before the four-judge panel was assembled, the author supplied three completed workbooks covering the same 1,200 blinded responses. In the first, the author reports manually scoring ten randomly selected examples and using GPT-5.6 with high reasoning to extrapolate the physician's holistic scoring style to the remaining responses. The ten calibration rows were not identified, and complete model-execution logs and the exact extrapolation prompt were not retained. This stream was therefore analysed as a physician-calibrated, AI-assisted holistic evaluator, not as independent physician review.

The second workbook contained outputs from a disclosed risk-averse deterministic Python scoring engine. The engine used regular expressions to detect lexical signals for warning signs, clinician caveats, uncertainty, dose directives, reassurance, refusals, named sources with specific figures, and selected audience-inappropriate terminology. Its own documentation stated that it could not verify clinical truth and required physician adjudication. The third, GPT-labelled rescored workbook was reported to apply the same scoring logic. Audit showed that the second and third workbooks matched on all 15 score fields and every free-text rationale for all 1,200 responses. In the absence of separate execution logs and because the rationales were deterministic engine strings, we treated them as duplicate implementations of one rule-based evaluator, not as two independent model judges.

These evaluator-method comparisons were secondary and exploratory. They were not pooled with the four-judge panel and were not used to create a reference label.

### Outcomes

The first co-primary outcome was evaluator-assigned unsafe response. In the four-judge panel, judges assigned harm severity from 0 to 3; severity 2 or 3, indicating plausible moderate or severe harm, dangerous reassurance, delayed care, or materially wrong management, defined `unsafe_binary`. The second co-primary outcome was evidence-sufficiency failure: a diagnosis, recommendation, reassurance, or treatment pathway beyond the information supplied, or failure to identify information essential for safe interpretation.

Component flags captured factual error, missed red flag, false reassurance, unsafe self-management, overconfident diagnosis or treatment, unsupported recommendation, hallucinated or unverifiable source, inappropriate refusal, omitted critical clinician caveat, and, in the panel, audience miscalibration. Because implementation differed across evaluator specifications, nominally matched binary outcomes were compared as measurement outputs, not assumed to be exchangeable clinical endpoints.

### Statistical analysis

The primary unit was one panel-judge rating of one response. Panel cell rates weighted the four fixed judges equally. Confidence intervals resampled all observations from 100 complete topics 5,000 times with seed 20260718, preserving the 4-generator by 3-prompt by 4-judge structure.

For each co-primary outcome, the planned marginal logistic model included generator, prompt version, judge, generator-by-prompt, judge-by-prompt, and generator-by-judge interactions, with exchangeable topic clustering and robust covariance.[13] The global generator-by-prompt interaction was the primary test. A saturated generator-by-prompt-by-judge model assessed evaluator heterogeneity. Holm correction covered the two co-primary tests.

Both logistic panel fits had non-finite covariance because of structural zero cells. We report them as not estimable and use a post hoc Gaussian identity-link generalized estimating equation with the same design matrix to test interactions on the absolute-risk scale. Effective Wald degrees of freedom reflect covariance rank. These p values are exploratory.

Secondary panel analyses reported judge-specific rates and ranks, three-of-four majority, unanimity, two-two split, any-positive votes, leave-one-judge-out ranks, component profiles, and same-provider differences. To assess influence on the headline interaction, we repeated the identity-link generator-by-prompt test after excluding each judge in turn, retaining the same topic clustering and reporting raw p values, Holm adjustment across the two outcomes within each omission, and Holm adjustment across all eight leave-one-judge-out tests. Between-judge binary agreement used exact agreement, Cohen's kappa, and Gwet's AC1.[14,15] Within-judge repeatability compared each primary rating with its blinded duplicate.

For the evaluator-method analysis, each evaluator contributed one classification per response. We reported complete-topic bootstrap intervals, pairwise exact agreement, kappa, AC1, and paired discordance. The holistic and deterministic streams used their previously implemented topic-clustered logistic interaction models; their p values were not treated as directly commensurable with the post hoc panel identity-link test. The duplicate engine workbooks were compared field by field and counted once.

Analyses used Python, pandas, NumPy, SciPy, statsmodels, and matplotlib. Exact versions, code, seeds, source tables, and output hashes are supplied.

### Ethics and reporting

This study used publicly released, deidentified benchmark questions and machine-generated text outputs, with no human participants, patient contact, intervention, or processing of personal data. Under the Swedish Ethical Review Act (2003:460), such research does not require ethical review, and no application to the Swedish Ethical Review Authority was made. A written self-assessment documenting this determination is retained in the replication package. Reporting was informed by DECIDE-AI, CONSORT-AI, and FUTURE-AI principles, although this was neither a clinical trial nor an in-care evaluation.

### Role of the funding source

Kinvectum AB funded the study. The funder had no personnel or governance role separate from the author's roles. The corresponding author had full access to all data and final responsibility for submission.

## Results

### Study corpus and technical completion

All 1,200 planned responses, 4,800 primary panel ratings, and 480 blinded repeat ratings were complete. Returned judge identifiers were `grok-4.3`, `gpt-5.5-2026-04-23`, `gemini-3.5-flash` (probe version `3.5-flash-05-2026`), and `claude-opus-4-8`. Final panel validation occurred July 18, 2026 at 11:33 UTC. Exact batch identifiers, timestamps, tokens, prompts, schema hashes, retries, and fallback manifests are retained.

Across the six evaluator specifications applied to the same 1,200 responses, unsafe prevalence ranged from 0% to 21.33% and evidence-sufficiency failure from 1.08% to 4.75% (Figure 1). This evaluator-method contrast frames the detailed panel results below.

<!-- FIGURE_1 -->

### Primary panel outcomes

The panel assigned 25/4,800 ratings unsafe (0.52%) and 102/4,800 evidence-insufficient (2.13%). Unsafe prevalence was 0/1,200 for Grok as judge, 18/1,200 (1.50%) for GPT-5.5, 4/1,200 (0.33%) for Gemini, and 3/1,200 (0.25%) for Claude. Evidence-sufficiency failure was 18/1,200 (1.50%), 51/1,200 (4.25%), 13/1,200 (1.08%), and 20/1,200 (1.67%), respectively.

At response level, 1,180/1,200 answers received no unsafe vote, 16 received one vote, three received two votes, and one received three votes. No response was unanimously unsafe. Evidence-sufficiency failure was more concordant: 59 responses received at least one positive vote, 14 reached a three-of-four majority, and seven were unanimous.

### Audience effects and model rankings

For Grok-generated responses, panel-average unsafe rates were 2.00% (95% topic-bootstrap CI 0.50-4.25) for clinician originals, 0.25% (0-0.75) for role-only prompts, and 0.25% (0-0.75) for patient rewrites. The patient-rewrite minus clinician risk difference was -1.75 percentage points (-3.50 to -0.50).

Gemini-generated responses showed the opposite pattern: 0.25% (0-0.75) for clinician originals, 1.00% (0.25-2.00) for role-only prompts, and 2.50% (1.00-4.50) for patient rewrites. The corresponding risk difference was 2.25 points (0.50-4.25). GPT-5.5- and Claude-generated responses had no unsafe ratings in any prompt cell. The post hoc identity-link generator-by-prompt test yielded chi-square 14.41 with effective 3 df (Holm-adjusted p=0.0048). Judge-by-generator-by-prompt heterogeneity was not significant after adjustment (adjusted p=0.17), although sparse events limited power and covariance rank.

Figure 2 shows panel-average evaluator-assigned unsafe rates across the three prompt formulations.

<!-- FIGURE_2 -->

GPT-5.5 contributed 18/25 unsafe ratings. After its exclusion, seven events remained and the risk-scale interaction was not detected (chi-square 6.01, effective 3 df; raw p=0.111; Holm p within omission=0.223; Holm p across all eight sensitivity tests=0.556). In contrast, the unsafe interaction remained detected when Grok, Gemini, or Claude was omitted (raw p range 0.0024-0.0038; within-omission Holm p range 0.0048-0.0077). Thus, the full-panel interaction was not robust to exclusion of the judge with the highest positive prevalence.

Panel evidence-sufficiency rates were highest for Gemini-generated responses: 4.75% for clinician originals, 7.50% for role-only prompts, and 8.25% for patient rewrites. Corresponding rates were 1.75%, 1.75%, and 0.75% for Grok; 0%, 0.25%, and 0% for GPT-5.5; and 0%, 0.25%, and 0.25% for Claude. The generator-by-prompt interaction was not detected (Holm-adjusted p=0.39).

Figure 3 shows the corresponding evidence-sufficiency failure rates.

<!-- FIGURE_3 -->

The panel therefore placed Grok highest on unsafe rate for clinician prompts and Gemini highest for both patient formulations, whereas GPT-5.5 and Claude tied at zero in every prompt cell. These ranks describe the fixed evaluator panel and should not be interpreted as superiority or equivalence.

### Evaluator-method comparison

The holistic GPT-5.6 stream classified 7/1,200 responses unsafe (0.58%, 95% topic-bootstrap CI 0.25-1.00) and 21/1,200 as evidence-insufficient (1.75%, 1.00-2.67). The deterministic scoring engine classified 256/1,200 unsafe (21.33%, 17.67-25.08) and 57/1,200 as evidence-insufficient (4.75%, 2.75-6.92). Unsafe prevalence was therefore 36.6 times higher under the engine than under holistic GPT scoring. All seven holistic unsafe classifications were also engine-positive; an additional 249 responses were engine-positive. For evidence sufficiency, 19 responses were positive only under holistic scoring and 55 only under the engine.

The nominal audience conclusion also changed by evaluator specification. The holistic GPT stream did not detect a generator-by-prompt interaction for unsafe classification (Wald chi-square 1.82, 6 df; p=0.94). The deterministic engine did (chi-square 35.66, 6 df; Holm-adjusted p=0.000006), driven largely by its rule that high-acuity answers without explicit safety-netting or clinician caveats were unsafe. The four-judge panel also detected an unsafe interaction, but only in the post hoc identity-link model after logistic separation. No evaluator specification detected a corrected evidence-sufficiency interaction.

The Claude-labelled and GPT-labelled scoring-engine workbooks matched exactly on every binary outcome, every ordinal score, and every rationale for all 1,200 responses. This perfect reproducibility reflects application of the same deterministic rules. It does not show that two independent models reached the same clinical judgment.

### Agreement and repeatability

Within the four-judge panel, pairwise exact agreement for unsafe classification ranged from 98.5% to 99.8%, but kappa ranged from 0.00 to 0.28; Gwet's AC1 ranged from 0.985 to 0.998. Evidence-sufficiency exact agreement ranged from 96.3% to 99.3%, with kappa 0.30-0.71. High raw agreement therefore primarily reflected the rarity of positive classifications.

Figure 4 contrasts between-judge kappa for the two co-primary outcomes, with uninformative diagonal cells suppressed.

<!-- FIGURE_4 -->

On 120 blinded repeats per judge, unsafe exact agreement was 100% for Grok and Gemini, 99.2% for GPT-5.5, and 98.3% for Claude. Evidence-sufficiency repeat agreement was 97.5-100%. High within-evaluator repeatability coexisted with material between-evaluator threshold differences.

### Failure mechanisms and same-provider evaluation

Across 4,800 panel ratings, the most frequent component flags were factual error (100), omitted critical clinician caveat (92), missed red flag (65), overconfident diagnosis or treatment (32), unsupported recommendation (31), and audience miscalibration (29). GPT-5.5 as judge assigned 67 factual-error, 75 omitted-caveat, and 40 missed-red-flag flags, more than the other panel members. Unsafe self-management was never flagged.

Same-provider comparisons were descriptive because judge and generator identities were structurally coupled. Grok judging Grok-generated responses assigned 1.11 percentage points fewer unsafe labels than the mean of the other judges (95% topic-bootstrap CI -2.56 to -0.11); the corresponding Gemini difference was -1.22 points (-2.22 to -0.33). These findings are compatible with self-preference but cannot distinguish provider affinity from judge-specific calibration.

## Discussion

### Principal findings

This study's most robust finding is not an audience-specific model ranking. It is that the measurement system materially changed the answer. The same 1,200 responses produced unsafe prevalence estimates from 0% to 1.50% across individual LLM judges, 0.58% under holistic GPT scoring, and 21.33% under a deterministic rule engine. The engine and holistic evaluator also disagreed on whether a generator-by-prompt interaction existed. The four-judge panel exposed threshold variation and audience-associated rank reversals, but only one response reached a majority-unsafe classification, the planned logistic model was separated, and the risk-scale interaction disappeared when GPT-5.5 was excluded.

The audience result remains informative as a stress test. Grok-generated responses received fewer unsafe ratings after a patient cue, while Gemini-generated responses received more. The role-only arm suggests that intended-user framing can matter even without a complete rewrite. However, the realistic patient rewrite also changed specificity, context, and requested content. The estimand is therefore the same clinical issue presented in a different audience-specific question, not a pure causal effect of speaker identity.

### Interpretation of evaluator dependence

The perfect agreement between the GPT-labelled and Claude-labelled engine workbooks is reproducibility, not validity. A deterministic implementation should produce identical outputs when given identical text and rules. Model labels add no independent information when all fields and rationales are copied from the same feature engine. Counting those workbooks as two judges would create pseudoreplication and artificially increase confidence.

The engine's clinical limitations explain its high positive rate. It inferred safety from the presence or absence of lexical features rather than evaluating whether the medical content was correct in context. It could classify a clinically adequate specialist answer as unsafe because it omitted generic warning signs, penalize a clinician-facing response for lacking a referral disclaimer, or label a named guideline with a number as hallucinated merely because no verification caveat appeared. Conversely, the presence of safety language could satisfy a rule despite incorrect medical advice. These design choices are useful for high-sensitivity screening but do not operationalize material patient harm.

Holistic LLM review has the opposite vulnerability: it can integrate context but apply an opaque and potentially lenient threshold. The GPT-5.6 holistic stream was calibrated from ten physician examples, but those rows were not marked and the extrapolation prompt and execution logs were not retained. Its low event rate cannot be interpreted as clinical specificity. The four-judge panel improves transparency by crossing evaluators, freezing the rubric, blinding identifiers, and measuring repeats, but shared training data and correlated model behaviour mean that voting still does not create an independent reference standard. Here, GPT-5.5 supplied 72% of unsafe events; removing it abolished the interaction despite retention of the directional Grok-versus-Gemini pattern. Panel averaging therefore converted one judge's lower threshold into apparent inferential stability.

### Relation to previous work

Real-POCQi and other clinician-query studies demonstrate the value of ecologically grounded questions and physician evaluation.[4,5] Patient-facing studies show that clinically knowledgeable models can still provide unsafe advice when the user context changes.[6,7] Our findings connect these literatures by showing that audience and evaluator must be considered jointly. They also extend general LLM-as-judge evidence: self-preference and evaluator bias are not merely ranking nuisances in medicine, because they can determine which responses cross a harm threshold.[8-10]

The contrast between high repeatability and low validity is particularly important. Repeat testing showed that each judge was stable, yet judges differed substantially in positive prevalence and component use. Reliability is necessary for measurement but cannot establish that the measured construct corresponds to clinically meaningful harm. DECIDE-AI and FUTURE-AI similarly emphasise context, human factors, and evidence appropriate to the intended deployment setting.[11,16]

### Implications

Medical LLM evaluations should treat the evaluator specification as part of the intervention being studied. At minimum, reports should publish the exact rubric and prompt, retain component-level outcomes, disclose model and reasoning settings, show judge-specific prevalence, include blinded repeats, and avoid presenting majority vote as truth. Deterministic rules can be valuable for reproducible screening and case enrichment, but positives should be described as rule triggers. LLM panels can identify disagreement and prioritize review; comparative clinical-safety claims require independent physician adjudication.

A feasible validation extension need not ask physicians to rereview all 1,200 responses. Two independent physicians should assess the same stratified subset containing every response with any panel unsafe vote, all panel split or majority cases, all holistic or engine discordances sampled across mechanism classes, a balanced sample from the 12 generator-by-prompt cells, and enough all-negative responses to assess false-negative risk. Independent ratings should precede adjudication. This would permit estimation of evaluator sensitivity, specificity, and calibration against a clinical reference while concentrating scarce physician time.

### Strengths and limitations

Strengths include complete crossing of 100 topics with three prompt formulations, four generators, and four judges; a role-only arm addressing the rewrite confound; blinded randomized judge inputs; a frozen structured rubric; local validation of every output; blinded repeats; exact dates, model identifiers, hashes, and technical-repair records; and an explicit comparison of holistic, panel, and deterministic evaluation.

The principal limitation is the absence of an independent physician-adjudicated reference set. Outcomes are evaluator-assigned and cannot estimate true clinical error prevalence, sensitivity, or specificity. Second, unsafe events were sparse, the planned logistic panel analysis was not estimable, and the identity-link fallback was post hoc. Eighteen of 25 events came from GPT-5.5, and the interaction was not detected after that judge was excluded; the full-panel p value should therefore be interpreted as judge-sensitive rather than confirmatory evidence of an audience effect. Third, the legacy holistic calibration examples were unmarked and its exact prompt and execution metadata were incomplete; those results are exploratory. Fourth, the deterministic engine measures text features and cannot verify clinical truth. Fifth, 446 generated responses required technical regeneration after truncation, disproportionately across generators. Sixth, all generators and panel judges were proprietary frontier models; open-weight deployment was not represented. Seventh, the English-language single-turn benchmark did not measure user comprehension, behaviour, patient outcomes, longitudinal context, or tool-enabled performance. Finally, rewrite fidelity was protocol-driven but not independently rated by humans.

### Conclusions

In this paired medical LLM benchmark, evaluator specification changed unsafe prevalence by more than an order of magnitude and altered the apparent audience-by-model conclusion. The panel interaction was not robust to excluding its most positive judge. The four-judge design made this instability visible but did not resolve it. Until calibrated against independent clinicians, LLM judges and deterministic engines should be used for scalable screening, disagreement discovery, and uncertainty mapping, not as stand-alone evidence that one model is clinically safer than another.

## Declarations

### Author contributions

Koyar Afrasyab conceived the study, specified the clinical question and design, provided clinical oversight, interpreted the findings, and is accountable for the work. AI systems assisted with prompt construction, code, API execution, structured evaluation, analysis implementation, figure production, and manuscript drafting. The author reviewed the study package and retains responsibility for accuracy and submission.

### Funding

Kinvectum AB funded the study.

### Competing interests

Koyar Afrasyab is the founder and sole shareholder of Kinvectum AB, a healthcare consultancy and technology company. No model provider funded the work. API services were purchased as study materials.

### Data availability

The replication package contains all 300 prompts, 1,200 final responses, generation provenance, exact panel judge inputs, judge prompt and schema, 5,280 validated panel ratings, the three legacy evaluator workbooks, scoring-engine duplicate audit, analysis code, tables, figures, and technical execution reports. API keys are excluded. Public redistribution should be checked against source-dataset and provider terms.

## References

1. Singhal K, Azizi S, Tu T, et al. Large language models encode clinical knowledge. *Nature*. 2023;620:172-180. doi:10.1038/s41586-023-06291-2.
2. Thirunavukarasu AJ, Ting DSJ, Elangovan K, et al. Large language models in medicine. *Nat Med*. 2023;29:1930-1940. doi:10.1038/s41591-023-02448-8.
3. OpenAI. HealthBench: evaluating large language models towards improved human health. Technical report. 2025. https://cdn.openai.com/pdf/bd7a39d5-9e9f-47b3-903c-8b847ca650c7/healthbench_paper.pdf.
4. Feng J, Patel V, Heagerty P, et al. Expert evaluation of clinical AI tools on real point-of-care clinical queries. arXiv:2606.28960. 2026. doi:10.48550/arXiv.2606.28960.
5. Vishwanath K, Alyakin A, Ghosh M, et al. General-purpose large language models outperform specialized clinical AI tools on medical benchmarks. *Nat Med*. 2026. doi:10.1038/s41591-026-04431-5.
6. Draelos RL, Afreen S, Blasko B, et al. Large language models provide unsafe answers to patient-posed medical questions. arXiv:2507.18905. 2025. doi:10.48550/arXiv.2507.18905.
7. Corbeil JP, Kim M, Griot M, et al. MedRiskEval: medical risk evaluation benchmark of language models, on the importance of user perspectives in healthcare settings. arXiv:2507.07248v4. 2026. doi:10.48550/arXiv.2507.07248.
8. Zheng L, Chiang WL, Sheng Y, et al. Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. arXiv:2306.05685. 2023. doi:10.48550/arXiv.2306.05685.
9. Panickssery A, Bowman SR, Feng S. LLM evaluators recognize and favor their own generations. arXiv:2404.13076. 2024. doi:10.48550/arXiv.2404.13076.
10. Wataoka K, Takahashi T, Ri R. Self-preference bias in LLM-as-a-judge. arXiv:2410.21819. 2024. doi:10.48550/arXiv.2410.21819.
11. Vasey B, Nagendran M, Campbell B, et al. Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. *Nat Med*. 2022;28:924-933. doi:10.1038/s41591-022-01772-9.
12. Liu X, Cruz Rivera S, Moher D, et al. Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. *Nat Med*. 2020;26:1364-1374. doi:10.1038/s41591-020-1034-x.
13. Liang KY, Zeger SL. Longitudinal data analysis using generalized linear models. *Biometrika*. 1986;73:13-22. doi:10.1093/biomet/73.1.13.
14. Cohen J. A coefficient of agreement for nominal scales. *Educ Psychol Meas*. 1960;20:37-46. doi:10.1177/001316446002000104.
15. Gwet KL. Computing inter-rater reliability and its variance in the presence of high agreement. *Br J Math Stat Psychol*. 2008;61:29-48. doi:10.1348/000711006X126600.
16. Lekadir K, Frangi AF, Porras AR, et al. FUTURE-AI: international consensus guideline for trustworthy and deployable artificial intelligence in healthcare. *BMJ*. 2025;388:e081554. doi:10.1136/bmj-2024-081554.
