#!/usr/bin/env python3
"""Compare evaluator specifications without treating any as clinical truth.

The analysis keeps one observation per response for each individual evaluator.
The two supplied scoring-engine workbooks are audited as duplicate
implementations of one deterministic rule set and are never counted twice.
"""
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
PANEL = ROOT / "llm_judge_panel" / "data" / "processed" / "llm_judge_ratings_primary.csv"
TABLES = ROOT / "results" / "evaluator_method_tables"
FIGURES = ROOT / "results" / "evaluator_method_figures"
SEED = 20260718
N_BOOT = 5000

OUTCOMES = {
    "unsafe_binary": "Unsafe",
    "evidence_failure": "Evidence-sufficiency failure",
}
METHOD_LABELS = {
    "judge_grok_4_3": "Grok 4.3 judge",
    "judge_gpt_5_5": "GPT-5.5 judge",
    "judge_gemini_3_5_flash": "Gemini 3.5 Flash judge",
    "judge_claude_4_8_opus": "Claude Opus 4.8 judge",
    "gpt_5_6_holistic": "GPT-5.6 holistic",
    "deterministic_engine": "Deterministic scoring engine",
}
METHOD_ORDER = list(METHOD_LABELS)
COLORS = ["#227C9D", "#4C78A8", "#59A14F", "#B07AA1", "#F28E2B", "#5B6670"]


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    observed = float(np.mean(a == b))
    pa = float(a.mean())
    pb = float(b.mean())
    expected = pa * pb + (1 - pa) * (1 - pb)
    return (observed - expected) / (1 - expected) if expected < 1 else np.nan


def gwet_ac1(a: np.ndarray, b: np.ndarray) -> float:
    observed = float(np.mean(a == b))
    prevalence = float((a.sum() + b.sum()) / (2 * len(a)))
    chance = 2 * prevalence * (1 - prevalence)
    return (observed - chance) / (1 - chance) if chance < 1 else np.nan


def topic_bootstrap(frame: pd.DataFrame, outcome: str) -> tuple[float, float, float]:
    grouped = frame.groupby("topic_id", sort=True)[outcome].mean().to_numpy(dtype=float)
    rng = np.random.default_rng(SEED)
    sampled = rng.integers(0, len(grouped), size=(N_BOOT, len(grouped)))
    boots = grouped[sampled].mean(axis=1)
    return float(grouped.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def load_methods() -> pd.DataFrame:
    panel = pd.read_csv(PANEL)
    panel = panel.rename(columns={"evidence_sufficiency_failure": "evidence_failure"})
    panel["method"] = "judge_" + panel["judge_key"].astype(str)
    panel = panel[["method", "response_id", "topic_id", "model_key", "prompt_version", *OUTCOMES]]

    holistic = pd.read_csv(PROCESSED / "chatgpt_hybrid_ratings.csv").rename(
        columns={"evidence_insufficient_or_overanswered": "evidence_failure"}
    )
    holistic["method"] = "gpt_5_6_holistic"

    engine = pd.read_csv(PROCESSED / "claude_hybrid_ratings.csv").rename(
        columns={"evidence_insufficient_or_overanswered": "evidence_failure"}
    )
    engine["method"] = "deterministic_engine"

    cols = ["method", "response_id", "topic_id", "model_key", "prompt_version", *OUTCOMES]
    combined = pd.concat([panel, holistic[cols], engine[cols]], ignore_index=True)
    combined["method"] = pd.Categorical(combined["method"], METHOD_ORDER, ordered=True)
    return combined.sort_values(["method", "response_id"]).reset_index(drop=True)


def overall_summary(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method in METHOD_ORDER:
        part = data[data.method == method]
        for outcome, label in OUTCOMES.items():
            rate, low, high = topic_bootstrap(part, outcome)
            rows.append({
                "method": method,
                "method_label": METHOD_LABELS[method],
                "outcome": outcome,
                "outcome_label": label,
                "n": int(len(part)),
                "events": int(part[outcome].sum()),
                "rate": rate,
                "ci_low": low,
                "ci_high": high,
            })
    return pd.DataFrame(rows)


def cell_summary(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby(["method", "model_key", "prompt_version"], observed=True)
        .agg(
            n=("response_id", "size"),
            unsafe_events=("unsafe_binary", "sum"),
            unsafe_rate=("unsafe_binary", "mean"),
            evidence_events=("evidence_failure", "sum"),
            evidence_rate=("evidence_failure", "mean"),
        )
        .reset_index()
        .assign(method_label=lambda x: x.method.astype(str).map(METHOD_LABELS))
    )


def pairwise_agreement(data: pd.DataFrame) -> pd.DataFrame:
    wide = data.pivot(index="response_id", columns="method", values=list(OUTCOMES))
    rows = []
    for i, left in enumerate(METHOD_ORDER):
        for right in METHOD_ORDER[i + 1:]:
            for outcome, label in OUTCOMES.items():
                pair = wide[outcome][[left, right]].dropna().astype(int)
                a = pair[left].to_numpy()
                b = pair[right].to_numpy()
                rows.append({
                    "outcome": outcome,
                    "outcome_label": label,
                    "method_a": left,
                    "method_a_label": METHOD_LABELS[left],
                    "method_b": right,
                    "method_b_label": METHOD_LABELS[right],
                    "n": len(pair),
                    "a_positive": int(a.sum()),
                    "b_positive": int(b.sum()),
                    "exact_agreement": float(np.mean(a == b)),
                    "cohen_kappa": kappa(a, b),
                    "gwet_ac1": gwet_ac1(a, b),
                })
    return pd.DataFrame(rows)


def paired_method_contrast(data: pd.DataFrame) -> pd.DataFrame:
    wide = data.pivot(index="response_id", columns="method", values=list(OUTCOMES))
    rows = []
    for outcome, label in OUTCOMES.items():
        pair = wide[outcome][["gpt_5_6_holistic", "deterministic_engine"]].dropna().astype(int)
        a = pair["gpt_5_6_holistic"]
        b = pair["deterministic_engine"]
        a_only = int(((a == 1) & (b == 0)).sum())
        b_only = int(((a == 0) & (b == 1)).sum())
        discordant = a_only + b_only
        p_value = float(binomtest(min(a_only, b_only), discordant, 0.5).pvalue) if discordant else 1.0
        rows.append({
            "outcome": outcome,
            "outcome_label": label,
            "n": len(pair),
            "holistic_events": int(a.sum()),
            "engine_events": int(b.sum()),
            "engine_to_holistic_rate_ratio": float(b.mean() / a.mean()) if a.mean() else np.inf,
            "holistic_only_positive": a_only,
            "engine_only_positive": b_only,
            "paired_exact_p": p_value,
            "interpretation": "Paired method contrast; neither evaluator is a reference standard.",
        })
    return pd.DataFrame(rows)


def interaction_summary() -> pd.DataFrame:
    legacy = pd.read_csv(ROOT / "results" / "tables" / "table_4_global_interaction_tests.csv")
    panel = pd.read_csv(ROOT / "results" / "llm_judge_panel_tables" / "table_primary_interaction_tests.csv")
    rows = []
    for _, row in legacy.iterrows():
        method = "gpt_5_6_holistic" if row.rater_stream == "chatgpt" else "deterministic_engine"
        outcome = "evidence_failure" if row.outcome == "evidence_insufficient_or_overanswered" else row.outcome
        rows.append({
            "method": method,
            "method_label": METHOD_LABELS[method],
            "outcome": outcome,
            "events": int(row.events),
            "estimating_model": "Logistic GEE",
            "wald_chi2": row.wald_chi2,
            "effective_df": int(row.df),
            "raw_p": row.p_value,
            "holm_p": row.p_value_holm,
            "status": "Previously implemented stream-specific analysis; secondary here",
        })
    for _, row in panel.iterrows():
        outcome = "evidence_failure" if row.outcome == "evidence_sufficiency_failure" else row.outcome
        rows.append({
            "method": "four_judge_panel",
            "method_label": "Four-judge panel",
            "outcome": outcome,
            "events": int(row.events),
            "estimating_model": str(row.family),
            "wald_chi2": row.panel_model_prompt_chi2,
            "effective_df": int(row.panel_model_prompt_df),
            "raw_p": row.panel_model_prompt_p,
            "holm_p": row.holm_p,
            "status": "Post hoc identity-link fallback after logistic separation",
        })
    return pd.DataFrame(rows)


def duplicate_audit() -> pd.DataFrame:
    audit = pd.read_csv(PROCESSED / "deterministic_engine_duplicate_agreement.csv")
    audit["comparison"] = "Claude-labelled engine workbook vs GPT-labelled rescored workbook"
    audit["inference_role"] = "Reproducibility check only; not independent votes"
    return audit[["comparison", "field", "n", "exact_matches", "exact_agreement", "inference_role"]]


def plot_method_prevalence(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.8))
    for ax, (outcome, label) in zip(axes, OUTCOMES.items()):
        part = summary[summary.outcome == outcome].set_index("method").loc[METHOD_ORDER].reset_index()
        y = np.arange(len(part))
        rates = 100 * part.rate.to_numpy()
        low = 100 * part.ci_low.to_numpy()
        high = 100 * part.ci_high.to_numpy()
        ax.errorbar(rates, y, xerr=[rates - low, high - rates], fmt="none", ecolor="#4B5563", capsize=3, lw=1.2)
        ax.scatter(rates, y, c=COLORS, s=58, zorder=3)
        ax.set_yticks(y, part.method_label)
        ax.invert_yaxis()
        ax.set_xlabel("Positive classifications, % (95% topic-bootstrap CI)")
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.grid(axis="x", color="#E5E7EB", lw=0.8)
        ax.spines[["top", "right", "left"]].set_visible(False)
        if outcome == "unsafe_binary":
            ax.set_xscale("symlog", linthresh=0.1, linscale=1.0, base=10)
            ax.set_xticks([0, 0.1, 0.5, 1, 5, 25], ["0", "0.1", "0.5", "1", "5", "25"])
            ax.set_xlim(left=0, right=30)
            ax.set_xlabel("Positive classifications, % (symlog scale; linear below 0.1%)")
        else:
            ax.set_xlim(left=0, right=max(max(high) * 1.08, 1.0))
    fig.suptitle("Nominally matched safety outcomes vary with evaluator specification", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"figure_1_evaluator_method_prevalence.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        (FIGURES / f"figure_5_evaluator_method_prevalence.{ext}").unlink(missing_ok=True)
    data = load_methods()
    summary = overall_summary(data)
    cells = cell_summary(data)
    agreement = pairwise_agreement(data)
    contrast = paired_method_contrast(data)
    interactions = interaction_summary()
    duplicates = duplicate_audit()

    data.to_csv(PROCESSED / "evaluator_method_long.csv", index=False)
    summary.to_csv(TABLES / "table_evaluator_method_overall_rates.csv", index=False)
    cells.to_csv(TABLES / "table_evaluator_method_cell_rates.csv", index=False)
    agreement.to_csv(TABLES / "table_evaluator_pairwise_agreement.csv", index=False)
    contrast.to_csv(TABLES / "table_holistic_vs_engine_paired_contrast.csv", index=False)
    interactions.to_csv(TABLES / "table_evaluator_method_interaction_tests.csv", index=False)
    duplicates.to_csv(TABLES / "table_scoring_engine_duplicate_audit.csv", index=False)
    plot_method_prevalence(summary)

    payload = {
        "analysis_date": "2026-07-18",
        "bootstrap_seed": SEED,
        "bootstrap_replicates": N_BOOT,
        "primary_inference_source": "four_judge_panel",
        "legacy_streams_role": "secondary evaluator-method comparison",
        "deterministic_engine_counted_once": True,
        "overall_rates": summary.to_dict("records"),
        "paired_holistic_engine_contrast": contrast.to_dict("records"),
        "engine_duplicate_audit": duplicates.to_dict("records"),
    }
    (ROOT / "results" / "evaluator_method_analysis_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(summary.to_string(index=False))
    print("\nHolistic versus deterministic engine\n", contrast.to_string(index=False))


if __name__ == "__main__":
    main()
