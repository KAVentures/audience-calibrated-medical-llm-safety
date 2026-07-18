#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 20260708
N_TOPICS = 100

HIGH_RISK_SPECIALTIES = {
    "Cardiology",
    "Critical Care",
    "Emergency Medicine",
    "Infectious Disease",
    "Neurology",
    "OB / GYN",
    "Oncology / Hematology",
    "Pediatrics",
    "Pulmonology",
}

EXCLUDE_PATTERNS = [
    "what percentage",
    "trial",
    "recent study",
    "research suggesting",
    "financial penalties",
]


def classify_decision_type(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["dose", "dosage", "prescribe", "drug", "antibiotic", "steroid", "methimazole"]):
        return "medication_or_treatment"
    if any(x in t for x in ["diagnosis", "differential", "most likely", "causes"]):
        return "diagnosis_or_differential"
    if any(x in t for x in ["ct", "mri", "echo", "ecg", "lab", "test", "findings", "panel"]):
        return "test_interpretation"
    if any(x in t for x in ["management", "approach", "next step", "evaluation"]):
        return "management"
    if any(x in t for x in ["evidence", "compare", "benefits", "role"]):
        return "evidence_question"
    return "general_clinical_information"


def plausible_patient_rewrite(text: str) -> bool:
    t = text.lower()
    return not any(p in t for p in EXCLUDE_PATTERNS)


def main() -> None:
    questions_path = RAW / "questions.parquet"
    if not questions_path.exists():
        raise SystemExit("Missing data/raw/questions.parquet. Run scripts/00_fetch_real_pocqi.py first.")

    df = pd.read_parquet(questions_path)
    df = df.rename(columns={c: c.strip() for c in df.columns})
    required = {"question_id", "question_text", "specialty"}
    missing = required.difference(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    df["eligible_patient_rewrite"] = df["question_text"].map(plausible_patient_rewrite)
    eligible = df[df["eligible_patient_rewrite"]].copy()
    eligible["specialty_risk"] = eligible["specialty"].apply(lambda x: "higher_risk" if x in HIGH_RISK_SPECIALTIES else "standard")
    eligible["decision_type"] = eligible["question_text"].map(classify_decision_type)

    per_specialty = max(1, N_TOPICS // max(1, eligible["specialty"].nunique()))
    sample_parts = []
    for _, group in eligible.groupby("specialty", sort=True):
        take = min(per_specialty, len(group))
        sample_parts.append(group.sample(n=take, random_state=SEED))
    sample = pd.concat(sample_parts).drop_duplicates("question_id")

    if len(sample) < N_TOPICS:
        remaining = eligible[~eligible["question_id"].isin(sample["question_id"])]
        need = N_TOPICS - len(sample)
        risk_remaining = remaining.sort_values("specialty_risk", ascending=True)
        sample = pd.concat([sample, risk_remaining.sample(n=need, random_state=SEED)])
    elif len(sample) > N_TOPICS:
        sample = sample.sample(n=N_TOPICS, random_state=SEED)

    sample = sample.sort_values(["specialty", "question_id"]).reset_index(drop=True)
    sample.insert(0, "topic_id", [f"T{i:03d}" for i in range(1, len(sample) + 1)])
    sample["selection_seed"] = SEED
    sample["rewrite_status"] = "needs_human_fidelity_check"
    sample.to_csv(OUT / "topic_sample.csv", index=False)

    summary = sample.groupby(["specialty", "specialty_risk"]).size().reset_index(name="n")
    summary.to_csv(OUT / "topic_sample_specialty_summary.csv", index=False)
    print(f"wrote {len(sample)} topics")


if __name__ == "__main__":
    main()

