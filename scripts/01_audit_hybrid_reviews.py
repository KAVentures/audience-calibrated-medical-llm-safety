#!/usr/bin/env python3
from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "data" / "processed" / "workbook_extraction"
OUT = ROOT / "data" / "processed"
KEY = ROOT / "data" / "source" / "blinding_key_do_not_share_with_reviewers.csv"
RESPONSES = ROOT / "data" / "source" / "model_responses.csv"

BINARY = [
    "unsafe_binary", "evidence_insufficient_or_overanswered", "missed_red_flag",
    "false_reassurance", "unsafe_self_management",
    "overconfident_diagnosis_or_treatment", "unsupported_recommendation",
    "hallucinated_source_or_guideline", "inappropriate_refusal",
    "critical_clinician_caveat_omitted",
]
ORDINAL = [
    "accuracy_1_4", "evidence_sufficiency_1_4", "actionability_1_4",
    "communication_1_4", "overall_safety_1_4",
]


def load_extraction(label: str) -> tuple[pd.DataFrame, list[list]]:
    payload = json.loads((EXTRACT / f"{label}.json").read_text())
    values = payload["Review packet"]["values"]
    frame = pd.DataFrame(values[1:], columns=values[0])
    instructions = payload["Instructions"]["values"]
    return frame, instructions


def cohen_kappa(a: np.ndarray, b: np.ndarray, labels: list[int]) -> float:
    matrix = np.zeros((len(labels), len(labels)), dtype=float)
    index = {value: i for i, value in enumerate(labels)}
    for left, right in zip(a, b):
        matrix[index[int(left)], index[int(right)]] += 1
    n = matrix.sum()
    observed = np.trace(matrix) / n
    expected = (matrix.sum(axis=1) * matrix.sum(axis=0)).sum() / (n * n)
    return float((observed - expected) / (1 - expected)) if expected < 1 else np.nan


def weighted_kappa(a: np.ndarray, b: np.ndarray, labels: list[int]) -> float:
    q = len(labels)
    matrix = np.zeros((q, q), dtype=float)
    index = {value: i for i, value in enumerate(labels)}
    for left, right in zip(a, b):
        matrix[index[int(left)], index[int(right)]] += 1
    n = matrix.sum()
    expected = np.outer(matrix.sum(axis=1), matrix.sum(axis=0)) / n
    weights = np.fromfunction(lambda i, j: ((i - j) / (q - 1)) ** 2, (q, q))
    observed_disagreement = (weights * matrix).sum() / n
    expected_disagreement = (weights * expected).sum() / n
    return float(1 - observed_disagreement / expected_disagreement) if expected_disagreement else np.nan


def gwet_ac1_binary(a: np.ndarray, b: np.ndarray) -> float:
    observed = float(np.mean(a == b))
    prevalence = float((a.sum() + b.sum()) / (2 * len(a)))
    chance = 2 * prevalence * (1 - prevalence)
    return (observed - chance) / (1 - chance) if chance < 1 else np.nan


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chat, chat_instructions = load_extraction("chatgpt_human")
    claude, claude_instructions = load_extraction("claude_human")
    rescored, rescored_instructions = load_extraction("chatgpt_rescored_engine")
    key = pd.read_csv(KEY, dtype=str)
    responses = pd.read_csv(RESPONSES, dtype=str)

    streams = [
        (chat, "chatgpt_holistic"),
        (claude, "deterministic_engine_claude_label"),
        (rescored, "deterministic_engine_gpt_label"),
    ]
    for frame, label in streams:
        frame["review_source"] = label
        for col in BINARY + ORDINAL:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame["blinded_response_id"] = frame["blinded_response_id"].astype(str)

    id_checks = {
        "chat_rows": len(chat),
        "claude_rows": len(claude),
        "chat_unique_ids": chat["blinded_response_id"].nunique(),
        "claude_unique_ids": claude["blinded_response_id"].nunique(),
        "rescored_rows": len(rescored),
        "rescored_unique_ids": rescored["blinded_response_id"].nunique(),
        "same_id_set": set(chat["blinded_response_id"]) == set(claude["blinded_response_id"]),
        "same_id_order": chat["blinded_response_id"].tolist() == claude["blinded_response_id"].tolist(),
        "all_three_same_id_set": (
            set(chat["blinded_response_id"])
            == set(claude["blinded_response_id"])
            == set(rescored["blinded_response_id"])
        ),
    }
    domain_checks = {}
    for frame, label in streams:
        domain_checks[label] = {
            "reviewer_ids": sorted(frame["reviewer_id"].dropna().astype(str).unique().tolist()),
            "missing_binary": int(frame[BINARY].isna().sum().sum()),
            "missing_ordinal": int(frame[ORDINAL].isna().sum().sum()),
            "invalid_binary": int((~frame[BINARY].isin([0, 1])).sum().sum()),
            "invalid_ordinal": int((~frame[ORDINAL].isin([1, 2, 3, 4])).sum().sum()),
            "empty_rationales": int(frame["free_text_rationale"].fillna("").str.strip().eq("").sum()),
            "automated_rationale_mentions": int(frame["free_text_rationale"].fillna("").str.contains("automated|heuristic|algorithm", case=False, regex=True).sum()),
            "human_or_calibration_mentions": int(frame["free_text_rationale"].fillna("").str.contains("human|manual|calibrat", case=False, regex=True).sum()),
        }

    instruction_text = {
        "chatgpt_hybrid": "\n".join(str(cell) for row in chat_instructions for cell in row if cell not in (None, "")),
        "claude_hybrid": "\n".join(str(cell) for row in claude_instructions for cell in row if cell not in (None, "")),
        "chatgpt_rescored_engine": "\n".join(str(cell) for row in rescored_instructions for cell in row if cell not in (None, "")),
    }

    suffix = key.merge(
        responses[[
            "response_id", "provider_model_id", "topic_id", "prompt_id",
            "prompt_version", "audience", "specialty", "technical_regeneration",
        ]],
        on=["response_id", "prompt_id"],
        how="left",
        validate="one_to_one",
    )
    chat = chat.merge(suffix, on=["blinded_response_id", "topic_id", "prompt_version", "audience", "specialty"], how="left", validate="one_to_one")
    claude = claude.merge(suffix, on=["blinded_response_id", "topic_id", "prompt_version", "audience", "specialty"], how="left", validate="one_to_one")
    rescored = rescored.merge(suffix, on=["blinded_response_id", "topic_id", "prompt_version", "audience", "specialty"], how="left", validate="one_to_one")
    if chat["model_key"].isna().any() or claude["model_key"].isna().any() or rescored["model_key"].isna().any():
        raise SystemExit("Blinding-key merge failed for one or more review rows")

    chat.to_csv(OUT / "chatgpt_hybrid_ratings.csv", index=False)
    claude.to_csv(OUT / "claude_hybrid_ratings.csv", index=False)
    rescored.to_csv(OUT / "chatgpt_rescored_engine_ratings.csv", index=False)

    engine_comparison = claude[["blinded_response_id", *BINARY, *ORDINAL, "free_text_rationale"]].merge(
        rescored[["blinded_response_id", *BINARY, *ORDINAL, "free_text_rationale"]],
        on="blinded_response_id",
        suffixes=("_claude_label", "_gpt_label"),
        validate="one_to_one",
    )
    engine_rows = []
    for col in [*BINARY, *ORDINAL, "free_text_rationale"]:
        left = engine_comparison[f"{col}_claude_label"].fillna("").astype(str)
        right = engine_comparison[f"{col}_gpt_label"].fillna("").astype(str)
        engine_rows.append({
            "field": col,
            "n": len(engine_comparison),
            "exact_matches": int(left.eq(right).sum()),
            "exact_agreement": float(left.eq(right).mean()),
        })
    engine_agreement = pd.DataFrame(engine_rows)
    engine_agreement.to_csv(OUT / "deterministic_engine_duplicate_agreement.csv", index=False)

    paired = chat[["blinded_response_id", *BINARY, *ORDINAL]].merge(
        claude[["blinded_response_id", *BINARY, *ORDINAL]],
        on="blinded_response_id",
        suffixes=("_chatgpt", "_claude"),
        validate="one_to_one",
    )
    agreement = []
    for col in BINARY:
        a = paired[f"{col}_chatgpt"].to_numpy(dtype=int)
        b = paired[f"{col}_claude"].to_numpy(dtype=int)
        agreement.append({
            "outcome": col, "scale": "binary", "n": len(a),
            "raw_agreement": float(np.mean(a == b)),
            "cohen_kappa": cohen_kappa(a, b, [0, 1]),
            "gwet_ac1": gwet_ac1_binary(a, b),
            "weighted_kappa": np.nan,
            "chatgpt_mean": float(a.mean()), "claude_mean": float(b.mean()),
        })
    for col in ORDINAL:
        a = paired[f"{col}_chatgpt"].to_numpy(dtype=int)
        b = paired[f"{col}_claude"].to_numpy(dtype=int)
        agreement.append({
            "outcome": col, "scale": "ordinal", "n": len(a),
            "raw_agreement": float(np.mean(a == b)),
            "cohen_kappa": cohen_kappa(a, b, [1, 2, 3, 4]),
            "gwet_ac1": np.nan,
            "weighted_kappa": weighted_kappa(a, b, [1, 2, 3, 4]),
            "chatgpt_mean": float(a.mean()), "claude_mean": float(b.mean()),
        })
    agreement_df = pd.DataFrame(agreement)
    agreement_df.to_csv(OUT / "hybrid_rater_agreement.csv", index=False)

    paired_full = chat.merge(
        claude[["blinded_response_id", *BINARY, *ORDINAL, "free_text_rationale"]],
        on="blinded_response_id",
        suffixes=("_chatgpt", "_claude"),
        validate="one_to_one",
    )
    paired_full.to_csv(OUT / "paired_hybrid_ratings_with_metadata.csv", index=False)

    fingerprints = {
        "chatgpt_workbook_sha256": hashlib.sha256((ROOT / "data/raw_review_workbooks/physician_review_packet_chatgpt + human.xlsx").read_bytes()).hexdigest(),
        "claude_workbook_sha256": hashlib.sha256((ROOT / "data/raw_review_workbooks/physician_review_packet_claude + human.xlsx").read_bytes()).hexdigest(),
        "chatgpt_rescored_engine_workbook_sha256": hashlib.sha256((ROOT / "data/raw_review_workbooks/physician_review_packet_chatgpt + human_rescored.xlsx").read_bytes()).hexdigest(),
    }
    report = {
        "id_checks": id_checks,
        "domain_checks": domain_checks,
        "instruction_text": instruction_text,
        "fingerprints": fingerprints,
        "human_calibration_rows_identifiable": False,
        "human_calibration_row_reason": "No row-level field identifies the 10 physician-calibrated examples in either workbook.",
        "engine_duplicate_check": {
            "all_15_score_fields_exact_for_all_1200_rows": bool(
                engine_agreement[engine_agreement.field.isin(BINARY + ORDINAL)].exact_matches.eq(len(engine_comparison)).all()
            ),
            "all_rationales_exact_for_all_1200_rows": bool(
                engine_agreement.loc[engine_agreement.field.eq("free_text_rationale"), "exact_matches"].eq(len(engine_comparison)).all()
            ),
            "interpretation": "The two labelled workbooks are treated as duplicate implementations of one deterministic scoring specification, not independent judges.",
        },
    }
    (OUT / "hybrid_review_audit.json").write_text(json.dumps(report, indent=2) + "\n")

    lines = ["# Hybrid Review Audit", "", f"- Rows per workbook: {len(chat)}", f"- Same 1,200 blinded response IDs: {id_checks['same_id_set']}", ""]
    for label, values in domain_checks.items():
        lines.extend([
            f"## {label}", "",
            f"- Reviewer IDs: {values['reviewer_ids']}",
            f"- Missing binary ratings: {values['missing_binary']}",
            f"- Missing ordinal ratings: {values['missing_ordinal']}",
            f"- Invalid binary ratings: {values['invalid_binary']}",
            f"- Invalid ordinal ratings: {values['invalid_ordinal']}",
            f"- Rationales mentioning automated/heuristic/algorithm: {values['automated_rationale_mentions']}", "",
        ])
    lines.extend([
        "## Calibration Traceability", "",
        "The 10 physician-calibrated rows are not identified at row level in either workbook. Human-subset validation cannot be computed from the supplied files.", "",
        "## Interpretation", "",
        "The three workbooks provide two analytically distinct evaluator methods over the same 1,200 responses: one holistic GPT stream and one deterministic engine represented twice. They do not constitute independent physician reviews.", "",
        "## Duplicate scoring-engine implementation", "",
        "The GPT-labelled rescored workbook and Claude-labelled scoring-engine workbook match on all 15 score fields and every rationale for all 1,200 responses. They are one evaluator specification for inference and are not counted as two independent votes.", "",
    ])
    (OUT / "hybrid_review_audit.md").write_text("\n".join(lines))
    print(json.dumps(report, indent=2))
    print(agreement_df.to_string(index=False))


if __name__ == "__main__":
    main()
