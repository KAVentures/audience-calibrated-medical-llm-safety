# Data Dictionary

## `data/processed/topic_sample.csv`

- `topic_id`: study-specific topic identifier.
- `question_id`: Real-POCQi source question identifier.
- `question_text`: original clinician-facing question.
- `specialty`: Real-POCQi specialty.
- `eligible_patient_rewrite`: automated screen for whether a patient rewrite appears plausible.
- `specialty_risk`: `higher_risk` for specialties with high acute-care or harm potential, otherwise `standard`.
- `decision_type`: coarse prompt type: diagnosis, management, medication/treatment, test interpretation, evidence, or general information.
- `selection_seed`: reproducibility seed.
- `rewrite_status`: whether prompt family requires fidelity check.

## `data/processed/prompt_families.csv`

- `prompt_id`: unique prompt identifier.
- `prompt_version`: `clinician_original`, `patient_rewrite`, or `role_only_isolation`.
- `audience`: intended user category.
- `prompt_text`: prompt sent to the model.
- `red_flag_stratum`: whether the item includes obvious red-flag or high-acuity features.
- `rewrite_fidelity_status`: source original or requires human fidelity check.
- `rewrite_notes`: notes for prompt curation.

## Expected `responses/model_responses.csv`

Required columns after live generation:

- `response_id`
- `request_id`
- `model_key`
- `topic_id`
- `prompt_id`
- `prompt_version`
- `audience`
- `specialty`
- `prompt_text`
- `response_text`
- `created_at`
- `provider_response_id`
- `input_tokens`
- `output_tokens`
- `reasoning_tokens`
- `generation_status`
- `error_message`

## Expected `reviews/physician_reviews.csv`

Required columns:

- `review_id`
- `response_id`
- `reviewer_id`
- `unsafe_binary`
- `evidence_insufficient_or_overanswered`
- Unsafe component columns from `instruments/reviewer_form_template.csv`
- `accuracy_1_4`
- `evidence_sufficiency_1_4`
- `actionability_1_4`
- `communication_1_4`
- `overall_safety_1_4`
- `free_text_rationale`

