#!/usr/bin/env python3
from pathlib import Path
import hashlib

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESPONSES = ROOT / "data" / "source" / "model_responses.csv"
OUT = ROOT / "review_materials"
OUT.mkdir(parents=True, exist_ok=True)


def blind_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def main() -> None:
    if not RESPONSES.exists():
        raise SystemExit(
            "Missing data/source/model_responses.csv. Restore the frozen response file before exporting review packets."
        )
    df = pd.read_csv(RESPONSES)
    required = {
        "response_id",
        "topic_id",
        "prompt_id",
        "prompt_version",
        "audience",
        "specialty",
        "prompt_text",
        "model_key",
        "response_text",
    }
    missing = required.difference(df.columns)
    if missing:
        raise SystemExit(f"Missing required response columns: {sorted(missing)}")

    df = df.copy()
    df["blinded_response_id"] = df["response_id"].map(blind_id)
    df["review_order"] = range(1, len(df) + 1)
    df = df.sample(frac=1, random_state=20260708).reset_index(drop=True)

    review_cols = [
        "review_order",
        "blinded_response_id",
        "topic_id",
        "prompt_version",
        "audience",
        "specialty",
        "prompt_text",
        "response_text",
    ]
    packet = df[review_cols]
    packet.to_csv(OUT / "physician_review_packet_all.csv", index=False)

    # Balanced primary assignment within each model-by-prompt-version stratum.
    assignments = []
    for _, group in df.groupby(["model_key", "prompt_version"], sort=True):
        group = group.sample(frac=1, random_state=20260714).reset_index(drop=True)
        midpoint = len(group) // 2
        group.loc[: midpoint - 1, "primary_reviewer"] = "PHYSICIAN_A"
        group.loc[midpoint:, "primary_reviewer"] = "PHYSICIAN_B"
        assignments.append(group)
    assigned = pd.concat(assignments, ignore_index=True)
    overlap_parts = []
    for _, group in assigned.groupby(["model_key", "prompt_version", "primary_reviewer"], sort=True):
        overlap_parts.append(group.sample(n=len(group) // 5, random_state=20260714))
    overlap = pd.concat(overlap_parts, ignore_index=True)
    overlap_ids = set(overlap["response_id"])
    assigned["reliability_overlap"] = assigned["response_id"].isin(overlap_ids)

    for reviewer, other in [("PHYSICIAN_A", "PHYSICIAN_B"), ("PHYSICIAN_B", "PHYSICIAN_A")]:
        reviewer_rows = assigned[
            (assigned["primary_reviewer"] == reviewer)
            | ((assigned["primary_reviewer"] == other) & assigned["reliability_overlap"])
        ].sample(frac=1, random_state=20260714).reset_index(drop=True)
        reviewer_rows["review_order"] = range(1, len(reviewer_rows) + 1)
        reviewer_rows[review_cols].to_csv(
            OUT / f"{reviewer.lower()}_review_packet.csv", index=False
        )

    assignment_key = assigned[[
        "blinded_response_id", "response_id", "model_key", "prompt_id",
        "primary_reviewer", "reliability_overlap",
    ]]
    assignment_key.to_csv(OUT / "reviewer_assignment_key_do_not_share.csv", index=False)

    key = df[["blinded_response_id", "response_id", "model_key", "prompt_id"]]
    key.to_csv(OUT / "blinding_key_do_not_share_with_reviewers.csv", index=False)
    print(f"wrote {len(packet)} master rows and two 720-row reviewer packets")


if __name__ == "__main__":
    main()
