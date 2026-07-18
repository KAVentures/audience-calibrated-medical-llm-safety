## Abstract

### Objective

To determine whether medical large language model (LLM) safety conclusions vary by audience, response generator, and evaluator specification.

### Materials and Methods

We sampled 100 Real-POCQi topics and created clinician-original, patient role-only, and patient-rewritten prompts. Four LLMs answered all 300 prompts (1,200 responses). Four blinded LLM judges applied a frozen rubric, producing 4,800 primary ratings and 480 repeated ratings. Co-primary outcomes were evaluator-assigned unsafe response and evidence-sufficiency failure. Topic-clustered models and complete-topic bootstrap resampling assessed generator-by-prompt interactions. Secondary analyses compared the panel with physician-calibrated holistic GPT-5.6 scoring and a deterministic risk-averse text-feature engine.

### Results

The panel assigned 25/4,800 ratings unsafe (0.52%) and 102/4,800 evidence-insufficient (2.13%). Judge-specific unsafe prevalence ranged from 0% to 1.50%. A post hoc identity-link model detected an unsafe generator-by-prompt interaction after the planned logistic model was non-estimable (Holm-adjusted P=.0048); after excluding GPT-5.5, seven events remained and the interaction was not detected (P=.11). Pairwise unsafe kappa was 0.00-0.28 despite 98.5%-99.8% exact agreement. Holistic GPT-5.6 classified 7/1,200 responses unsafe (0.58%), compared with 256/1,200 (21.33%) for the deterministic engine; their interaction conclusions also differed.

### Discussion

Evaluator specification changed estimated prevalence and the apparent audience interaction. Sparse events and concentration within one judge limited the stability of the headline interaction.

### Conclusion

Evaluator specification should be treated as part of the intervention in medical LLM safety studies. Comparative claims require evaluator-specific reporting and independent physician validation.
