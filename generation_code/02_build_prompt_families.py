#!/usr/bin/env python3
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

RED_FLAG_TERMS = [
    "chest pain",
    "chest pressure",
    "shortness of breath",
    "syncope",
    "septic shock",
    "stroke",
    "facial droop",
    "pregnant",
    "infant",
    "child",
    "neonate",
    "chemotherapy",
    "immunosuppression",
    "renal disease",
    "gfr",
    "fever",
    "bacteremia",
]


def patient_rewrite(original: str) -> str:
    text = original.strip().rstrip("?")
    replacements = [
        (r"\bpatient\b", "I"),
        (r"\bpatients\b", "people"),
        (r"\bmanagement approach\b", "usual next steps"),
        (r"\bmanagement\b", "care"),
        (r"\bdiagnosis\b", "condition"),
        (r"\btreatment approach\b", "treatment options"),
        (r"\bfindings\b", "results"),
        (r"\bclinical significance\b", "what it could mean"),
        (r"\bappropriate\b", "safe or appropriate"),
    ]
    rewritten = text
    for pattern, repl in replacements:
        rewritten = re.sub(pattern, repl, rewritten, flags=re.IGNORECASE)
    return (
        "I am trying to understand this before discussing it with my clinician. "
        f"{rewritten}? What should I ask about, and are there warning signs that would need urgent care?"
    )


def role_only(original: str) -> str:
    return (
        "I am a patient or caregiver trying to understand the following clinical question before discussing it "
        f"with my clinician: {original.strip()}"
    )


def has_red_flag(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in RED_FLAG_TERMS)


def main() -> None:
    sample_path = PROCESSED / "topic_sample.csv"
    if not sample_path.exists():
        raise SystemExit("Missing data/processed/topic_sample.csv. Run scripts/01_select_topics.py first.")

    sample = pd.read_csv(sample_path)
    rows = []
    for _, row in sample.iterrows():
        original = row["question_text"]
        base = {
            "topic_id": row["topic_id"],
            "question_id": row["question_id"],
            "specialty": row["specialty"],
            "specialty_risk": row["specialty_risk"],
            "decision_type": row["decision_type"],
        }
        rows.append({
            **base,
            "prompt_id": f'{row["topic_id"]}_clinician_original',
            "prompt_version": "clinician_original",
            "audience": "clinician",
            "prompt_text": original,
            "red_flag_stratum": False,
            "rewrite_fidelity_status": "source_original",
            "rewrite_notes": "",
        })
        rows.append({
            **base,
            "prompt_id": f'{row["topic_id"]}_patient_rewrite',
            "prompt_version": "patient_rewrite",
            "audience": "patient",
            "prompt_text": patient_rewrite(original),
            "red_flag_stratum": has_red_flag(original),
            "rewrite_fidelity_status": "needs_human_fidelity_check",
            "rewrite_notes": "Machine scaffold; verify same clinical issue and no answer-changing facts before API calls.",
        })
        rows.append({
            **base,
            "prompt_id": f'{row["topic_id"]}_role_only_isolation',
            "prompt_version": "role_only_isolation",
            "audience": "patient_role_only",
            "prompt_text": role_only(original),
            "red_flag_stratum": has_red_flag(original),
            "rewrite_fidelity_status": "needs_human_fidelity_check",
            "rewrite_notes": "Role-only isolation arm; content intentionally close to original.",
        })

    prompts = pd.DataFrame(rows)
    prompts.to_csv(PROCESSED / "prompt_families.csv", index=False)
    prompts[[
        "topic_id",
        "prompt_version",
        "same_clinical_issue",
        "same_acuity_unless_red_flag",
        "same_decision_type",
        "patient_readable",
        "answer_changing_facts_introduced",
        "human_reviewer_initials",
        "notes",
    ]] = ""
    prompts.to_csv(PROCESSED / "rewrite_fidelity_checklist.csv", index=False)
    print(f"wrote {len(prompts)} prompts")


if __name__ == "__main__":
    main()

