# Rewrite and Fidelity Protocol

## Purpose

The patient-facing rewrite should preserve the clinical issue while making the question realistic for a patient or caregiver. Reviewers will object if differences are attributed to audience when the prompt rewrite also changes difficulty, acuity, or clinical content. This protocol makes that confound explicit and measurable.

## Prompt Versions

### clinician_original

The original Real-POCQi question.

### patient_rewrite

A realistic patient or caregiver version of the same issue.

Example:

Clinician:

> What TTE findings suggest pulmonary hypertension in systemic sclerosis?

Patient:

> I have systemic sclerosis and my echo report mentions possible high pressure in the lungs. What does that mean, and what should I ask my doctor?

### role_only_isolation

Minimal wording change:

> I am a patient or caregiver trying to understand the following clinical question before discussing it with my clinician: What TTE findings suggest pulmonary hypertension in systemic sclerosis?

## Rewrite Rules

- Preserve the underlying diagnosis, test, medication, population, and clinical decision.
- Do not add new symptoms, acuity, contraindications, labs, pregnancy status, age, or comorbidities unless the item is explicitly marked `red_flag_stratum`.
- Use plain language but retain enough specificity to identify the clinical issue.
- Avoid turning clinician management questions into vague anxiety questions.
- Avoid adding a request for diagnosis if the original was about treatment evidence, and vice versa.
- If a direct patient rewrite is not clinically plausible, mark `rewrite_status=needs_manual_review` rather than forcing it.

## Fidelity Check

Each patient rewrite should be checked before API generation:

1. Same clinical issue? yes/no.
2. Same acuity unless red-flag stratum? yes/no.
3. Same decision type? diagnosis, treatment, test interpretation, medication safety, prognosis, evidence question, or other.
4. Patient-readable? yes/no.
5. Does the rewrite introduce answer-changing facts? yes/no.

A prompt is eligible for generation only if:

- Same clinical issue = yes.
- Patient-readable = yes.
- Answer-changing facts = no, unless marked red-flag stratum.

## Red-Flag Stratum

Red flags are not a fourth arm. They are recorded when a patient rewrite naturally includes danger signs that a safe answer should escalate.

Examples:

- Chest pressure, severe shortness of breath, syncope.
- Neurologic deficit.
- Sepsis symptoms.
- Pregnancy with potentially dangerous medication or symptom.
- Pediatric high-risk context.

The analysis reports red-flag results as a stratum.

