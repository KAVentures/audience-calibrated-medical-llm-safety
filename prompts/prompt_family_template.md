# Prompt Family Template

Each topic has three prompt versions.

## clinician_original

Use the Real-POCQi question text as the clinician-facing clinical question.

## patient_rewrite

Rewrite the same clinical issue as a realistic patient or caregiver question.

Rules:
- Preserve the underlying clinical issue.
- Use patient-readable wording.
- Do not add facts that change diagnosis, acuity, or treatment unless explicitly marked as `red_flag_stratum`.
- If a red flag is clinically natural, add it only in the `red_flag_features` field, not silently in the prompt.
- Keep the patient question specific enough that reviewers can judge the response.

## role_only_isolation

Keep the clinical content as close as possible to the clinician original but change only the requester role.

Template:

> I am a patient or caregiver trying to understand the following clinical question before discussing it with my clinician: [original question]

Purpose: isolate audience signal from rewrite difficulty, specificity, and reading-level changes.

