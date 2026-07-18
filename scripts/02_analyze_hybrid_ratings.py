#!/usr/bin/env python3
"""Reproducible analysis of the two supplied hybrid rating streams.

The streams are analyzed separately because neither is an independent physician
review and their thresholds differ materially. Confidence intervals resample
whole topics, preserving the paired 3-prompt x 4-model structure.
"""
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import chi2


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
RNG_SEED = 20260717
N_BOOT = 5000

MODELS = ["grok_4_3", "gpt_5_5", "gemini_3_5_flash", "claude_4_8_opus"]
MODEL_LABELS = {
    "grok_4_3": "Grok 4.3",
    "gpt_5_5": "GPT-5.5",
    "gemini_3_5_flash": "Gemini 3.5 Flash",
    "claude_4_8_opus": "Claude Opus 4.8",
}
PROMPTS = ["clinician_original", "role_only_isolation", "patient_rewrite"]
PROMPT_LABELS = {
    "clinician_original": "Clinician original",
    "role_only_isolation": "Patient role only",
    "patient_rewrite": "Patient rewrite",
}
RATERS = ["chatgpt", "claude"]
RATER_LABELS = {
    "chatgpt": "ChatGPT-assisted extrapolation",
    "claude": "Claude rule-based scoring",
}
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
COLORS = {
    "grok_4_3": "#16697A",
    "gpt_5_5": "#2A9D8F",
    "gemini_3_5_flash": "#E9C46A",
    "claude_4_8_opus": "#D1495B",
}


def long_data() -> pd.DataFrame:
    wide = pd.read_csv(DATA / "paired_hybrid_ratings_with_metadata.csv")
    prompt_metadata = pd.read_csv(ROOT / "data" / "source" / "prompt_families.csv")[
        ["prompt_id", "specialty_risk", "red_flag_stratum"]
    ].drop_duplicates("prompt_id")
    frames = []
    base = [
        "blinded_response_id", "response_id", "topic_id", "prompt_id", "prompt_version",
        "audience", "specialty", "model_key", "provider_model_id",
        "technical_regeneration",
    ]
    for rater in RATERS:
        rename = {f"{col}_{rater}": col for col in BINARY + ORDINAL}
        cols = base + list(rename)
        part = wide[cols].rename(columns=rename).copy()
        part["rater_stream"] = rater
        part["same_provider_evaluation"] = (
            ((rater == "chatgpt") & part["model_key"].eq("gpt_5_5"))
            | ((rater == "claude") & part["model_key"].eq("claude_4_8_opus"))
        )
        frames.append(part.merge(prompt_metadata, on="prompt_id", how="left", validate="many_to_one"))
    return pd.concat(frames, ignore_index=True)


def holm_adjust(p_values: pd.Series) -> pd.Series:
    values = p_values.to_numpy(dtype=float)
    adjusted = np.full(len(values), np.nan)
    valid = np.flatnonzero(np.isfinite(values))
    if not len(valid):
        return pd.Series(adjusted, index=p_values.index)
    order = valid[np.argsort(values[valid])]
    running = 0.0
    m = len(order)
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * values[idx])
        adjusted[idx] = min(1.0, running)
    return pd.Series(adjusted, index=p_values.index)


def bh_adjust(p_values: pd.Series) -> pd.Series:
    values = p_values.to_numpy(dtype=float)
    adjusted = np.full(len(values), np.nan)
    valid = np.flatnonzero(np.isfinite(values))
    if not len(valid):
        return pd.Series(adjusted, index=p_values.index)
    order = valid[np.argsort(values[valid])[::-1]]
    running = 1.0
    m = len(order)
    for reverse_rank, idx in enumerate(order):
        rank = m - reverse_rank
        running = min(running, values[idx] * m / rank)
        adjusted[idx] = min(1.0, running)
    return pd.Series(adjusted, index=p_values.index)


def cluster_boot_rates(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    topics = np.array(sorted(frame["topic_id"].unique()))
    cells = pd.MultiIndex.from_product([MODELS, PROMPTS], names=["model_key", "prompt_version"])
    grouped = frame.groupby(["topic_id", "model_key", "prompt_version"])[outcome].mean().unstack([1, 2])
    grouped = grouped.reindex(index=topics, columns=cells)
    point = grouped.mean(axis=0)
    rng = np.random.default_rng(RNG_SEED)
    boots = np.empty((N_BOOT, len(cells)))
    values = grouped.to_numpy()
    for i in range(N_BOOT):
        idx = rng.integers(0, len(topics), len(topics))
        boots[i] = np.nanmean(values[idx], axis=0)
    rows = []
    for j, (model, prompt) in enumerate(cells):
        rows.append({
            "model_key": model,
            "prompt_version": prompt,
            "n": int(frame[(frame.model_key == model) & (frame.prompt_version == prompt)][outcome].notna().sum()),
            "events": int(frame[(frame.model_key == model) & (frame.prompt_version == prompt)][outcome].sum()),
            "rate": float(point.iloc[j]),
            "ci_low": float(np.quantile(boots[:, j], 0.025)),
            "ci_high": float(np.quantile(boots[:, j], 0.975)),
        })
    return pd.DataFrame(rows)


def cluster_boot_contrasts(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    topics = np.array(sorted(frame["topic_id"].unique()))
    cells = pd.MultiIndex.from_product([MODELS, PROMPTS], names=["model_key", "prompt_version"])
    values = frame.groupby(["topic_id", "model_key", "prompt_version"])[outcome].mean().unstack([1, 2]).reindex(index=topics, columns=cells).to_numpy()
    rng = np.random.default_rng(RNG_SEED + 1)
    rows = []
    for model_idx, model in enumerate(MODELS):
        clinician = model_idx * len(PROMPTS)
        for prompt_idx, prompt in enumerate(PROMPTS[1:], start=1):
            target = clinician + prompt_idx
            point = float(np.nanmean(values[:, target] - values[:, clinician]))
            boot = np.empty(N_BOOT)
            for i in range(N_BOOT):
                idx = rng.integers(0, len(topics), len(topics))
                boot[i] = np.nanmean(values[idx, target] - values[idx, clinician])
            p = float(2 * min(np.mean(boot <= 0), np.mean(boot >= 0)))
            rows.append({
                "model_key": model, "contrast": f"{prompt}_minus_clinician",
                "risk_difference": point,
                "ci_low": float(np.quantile(boot, 0.025)),
                "ci_high": float(np.quantile(boot, 0.975)),
                "bootstrap_p": min(1.0, p),
            })
    return pd.DataFrame(rows)


def robust_wald(fit, indices: list[int]) -> tuple[float, int, float]:
    restriction = np.zeros((len(indices), len(fit.params)))
    for row, col in enumerate(indices):
        restriction[row, col] = 1
    contrast = restriction @ fit.params.to_numpy()
    covariance = restriction @ fit.cov_params().to_numpy() @ restriction.T
    rank = int(np.linalg.matrix_rank(covariance))
    if rank < 1:
        raise ValueError("Constraint covariance has rank zero")
    statistic = float(contrast.T @ np.linalg.pinv(covariance) @ contrast)
    if not np.isfinite(statistic) or statistic < -1e-8:
        raise ValueError("Wald statistic is non-finite or negative")
    statistic = max(0.0, statistic)
    return statistic, rank, float(chi2.sf(statistic, rank))


def gee_interaction(frame: pd.DataFrame, outcome: str, family="binomial", minimum_events=0) -> dict:
    work = frame.copy()
    present_models = [value for value in MODELS if value in set(work["model_key"])]
    present_prompts = [value for value in PROMPTS if value in set(work["prompt_version"])]
    work["model_key"] = pd.Categorical(work["model_key"], present_models)
    work["prompt_version"] = pd.Categorical(work["prompt_version"], present_prompts)
    formula = f"{outcome} ~ C(model_key) * C(prompt_version)"
    event_count = int(work[outcome].sum()) if family == "binomial" else np.nan
    if family == "binomial" and event_count < minimum_events:
        return {
            "converged": False, "n": int(work[outcome].notna().sum()),
            "events": event_count,
            "error": f"Fewer than {minimum_events} events; inferential test not estimated",
            "formula": formula,
        }
    if work[outcome].nunique(dropna=True) < 2 and family == "binomial":
        return {
            "converged": False, "n": int(work[outcome].notna().sum()),
            "error": "Outcome has no variation", "formula": formula,
        }
    try:
        gee_family = sm.families.Binomial() if family == "binomial" else sm.families.Gaussian()
        fit = smf.gee(
            formula, groups="topic_id", data=work,
            family=gee_family, cov_struct=sm.cov_struct.Exchangeable(),
        ).fit()
        names = list(fit.params.index)
        idx = [i for i, name in enumerate(names) if ":" in name]
        statistic, rank, p_value = robust_wald(fit, idx)
        return {
            "converged": True, "n": int(fit.nobs), "events": event_count,
            "wald_chi2": statistic, "df": rank, "p_value": p_value,
            "formula": formula, "family": family,
            "covariance": "exchangeable; topic-clustered robust SE",
        }
    except Exception as exc:
        return {"converged": False, "error": str(exc), "formula": formula}


def ordinal_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(RNG_SEED + 2)
    for outcome in ORDINAL:
        for model in MODELS:
            for prompt in PROMPTS:
                cell = frame[(frame.model_key == model) & (frame.prompt_version == prompt)]
                topic_values = cell.groupby("topic_id")[outcome].mean().to_numpy()
                boots = np.array([
                    rng.choice(topic_values, size=len(topic_values), replace=True).mean()
                    for _ in range(N_BOOT)
                ])
                rows.append({
                    "outcome": outcome, "model_key": model, "prompt_version": prompt,
                    "n": len(cell), "mean": float(topic_values.mean()),
                    "sd": float(cell[outcome].std(ddof=1)),
                    "ci_low": float(np.quantile(boots, 0.025)),
                    "ci_high": float(np.quantile(boots, 0.975)),
                })
    return pd.DataFrame(rows)


def component_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in BINARY[2:]:
        grouped = frame.groupby(["model_key", "prompt_version"])[outcome].agg(["sum", "count", "mean"]).reset_index()
        grouped.insert(0, "component", outcome)
        rows.append(grouped.rename(columns={"sum": "events", "count": "n", "mean": "rate"}))
    return pd.concat(rows, ignore_index=True)


def rank_table(rates: pd.DataFrame) -> pd.DataFrame:
    out = rates.copy()
    out["rank_lowest_rate"] = out.groupby("prompt_version")["rate"].rank(method="min", ascending=True).astype(int)
    return out.sort_values(["prompt_version", "rank_lowest_rate", "model_key"])


def bootstrap_rank_uncertainty(frame: pd.DataFrame, outcome: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    topics = np.array(sorted(frame["topic_id"].unique()))
    cells = pd.MultiIndex.from_product([PROMPTS, MODELS], names=["prompt_version", "model_key"])
    grouped = frame.groupby(["topic_id", "prompt_version", "model_key"])[outcome].mean().unstack([1, 2])
    values = grouped.reindex(index=topics, columns=cells).to_numpy().reshape(len(topics), len(PROMPTS), len(MODELS))
    point_rates = np.nanmean(values, axis=0)
    point_ranks = 1 + (point_rates[:, :, None] > point_rates[:, None, :]).sum(axis=2)
    rng = np.random.default_rng(RNG_SEED + 3)
    boot_ranks = np.empty((N_BOOT, len(PROMPTS), len(MODELS)))
    for i in range(N_BOOT):
        sampled = values[rng.integers(0, len(topics), len(topics))]
        rates = np.nanmean(sampled, axis=0)
        boot_ranks[i] = 1 + (rates[:, :, None] > rates[:, None, :]).sum(axis=2)

    uncertainty = []
    for prompt_idx, prompt in enumerate(PROMPTS):
        for model_idx, model in enumerate(MODELS):
            ranks = boot_ranks[:, prompt_idx, model_idx]
            uncertainty.append({
                "model_key": model, "prompt_version": prompt,
                "point_rate": float(point_rates[prompt_idx, model_idx]),
                "point_rank_lowest_rate": int(point_ranks[prompt_idx, model_idx]),
                "mean_bootstrap_rank": float(ranks.mean()),
                "rank_ci_low": float(np.quantile(ranks, 0.025)),
                "rank_ci_high": float(np.quantile(ranks, 0.975)),
                "probability_tied_for_lowest_rate": float(np.mean(ranks == 1)),
            })

    changes = []
    for model_idx, model in enumerate(MODELS):
        change = boot_ranks[:, 2, model_idx] - boot_ranks[:, 0, model_idx]
        changes.append({
            "model_key": model,
            "point_rank_change_patient_minus_clinician": int(point_ranks[2, model_idx] - point_ranks[0, model_idx]),
            "mean_bootstrap_rank_change": float(change.mean()),
            "rank_change_ci_low": float(np.quantile(change, 0.025)),
            "rank_change_ci_high": float(np.quantile(change, 0.975)),
            "probability_rank_improves": float(np.mean(change < 0)),
            "probability_rank_worsens": float(np.mean(change > 0)),
        })
    return pd.DataFrame(uncertainty), pd.DataFrame(changes)


def bootstrap_specialty_risk(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(RNG_SEED + 4)
    for model in ["all_models", *MODELS]:
        subset = frame if model == "all_models" else frame[frame.model_key == model]
        topic_values = subset.groupby(["topic_id", "specialty_risk"])[outcome].mean().reset_index()
        standard = topic_values[topic_values.specialty_risk == "standard"][outcome].to_numpy()
        higher = topic_values[topic_values.specialty_risk == "higher_risk"][outcome].to_numpy()
        point = float(higher.mean() - standard.mean())
        boot = np.empty(N_BOOT)
        for i in range(N_BOOT):
            boot[i] = (
                rng.choice(higher, len(higher), replace=True).mean()
                - rng.choice(standard, len(standard), replace=True).mean()
            )
        p_value = min(1.0, float(2 * min(np.mean(boot <= 0), np.mean(boot >= 0))))
        rows.append({
            "model_key": model, "standard_topics": len(standard),
            "higher_risk_topics": len(higher),
            "risk_difference_higher_minus_standard": point,
            "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)),
            "bootstrap_p": p_value,
        })
    return pd.DataFrame(rows)


def plot_rates(all_rates: pd.DataFrame, outcome: str, filename: str, title: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.3), sharey=True)
    x = np.arange(len(PROMPTS))
    offsets = np.linspace(-0.27, 0.27, len(MODELS))
    for ax, rater in zip(axes, RATERS):
        subset = all_rates[(all_rates.rater_stream == rater) & (all_rates.outcome == outcome)]
        for offset, model in zip(offsets, MODELS):
            cell = subset[subset.model_key == model].set_index("prompt_version").reindex(PROMPTS)
            y = 100 * cell["rate"].to_numpy()
            lo = 100 * cell["ci_low"].to_numpy()
            hi = 100 * cell["ci_high"].to_numpy()
            ax.errorbar(x + offset, y, yerr=[y - lo, hi - y], fmt="o", ms=6,
                        capsize=3, lw=1.5, color=COLORS[model], label=MODEL_LABELS[model])
        ax.set_title(RATER_LABELS[rater], fontsize=11, fontweight="bold")
        ax.set_xticks(x, [PROMPT_LABELS[p] for p in PROMPTS], rotation=18, ha="right")
        ymax = 100 * subset["ci_high"].max()
        ax.set_ylim(-1.5, max(8, ymax * 1.16))
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Rated responses, % (95% topic-bootstrap CI)")
    axes[1].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)
    fig.text(0.01, -0.01, "Each cell contains 100 responses. CIs resample the 100 clinical topics; streams are not independent physician reviewers.", fontsize=8.5)
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"{filename}.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_flow() -> None:
    fig, ax = plt.subplots(figsize=(12.2, 6.4))
    ax.set_xlim(0, 12.2)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    boxes = [
        (0.4, 4.8, 2.4, 1.0, "Real-POCQi backbone\n620 public clinician queries"),
        (3.35, 4.8, 2.4, 1.0, "Seed-fixed sample\n100 clinical topics"),
        (6.3, 4.8, 2.4, 1.0, "Paired prompt family\n3 versions per topic"),
        (9.25, 4.8, 2.4, 1.0, "Four API models\n1,200 responses"),
        (1.3, 2.65, 3.1, 1.05, "Generation provenance\n754 retained original outputs\n446 technical regenerations"),
        (4.75, 2.65, 3.1, 1.05, "ChatGPT-assisted stream\n10 unmarked physician examples\n1,200 extrapolated ratings"),
        (8.2, 2.65, 3.1, 1.05, "Claude deterministic stream\nRule-based text-feature engine\n1,200 ratings"),
        (3.2, 0.65, 5.8, 1.05, "Rater-specific analysis\nTopic-clustered GEE + 5,000 topic bootstraps\nNo pooled physician endpoint or adjudicated ground truth"),
    ]
    for i, (x, y, w, h, label) in enumerate(boxes):
        color = "#E8F1F2" if i < 4 else ("#F7F3E8" if i < 7 else "#E9ECEF")
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#37474F", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9.5)
    arrows = [
        ((2.8, 5.3), (3.35, 5.3)), ((5.75, 5.3), (6.3, 5.3)), ((8.7, 5.3), (9.25, 5.3)),
        ((10.45, 4.8), (2.85, 3.7)), ((10.45, 4.8), (6.3, 3.7)), ((10.45, 4.8), (9.75, 3.7)),
        ((2.85, 2.65), (5.25, 1.7)), ((6.3, 2.65), (6.1, 1.7)), ((9.75, 2.65), (6.95, 1.7)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", color="#59666C", lw=1.2))
    ax.text(0.4, 6.15, "Figure 1. Study design and analytic flow", fontsize=15, fontweight="bold", ha="left")
    ax.text(0.4, 0.18, "The supplied files do not identify the 10 physician-scored calibration rows and do not constitute two independent physician reviews.", fontsize=8.8)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"figure_1_study_flow.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_agreement() -> None:
    agree = pd.read_csv(DATA / "hybrid_rater_agreement.csv")
    primary = agree[agree.outcome.isin(["unsafe_binary", "evidence_insufficient_or_overanswered", *ORDINAL])].copy()
    primary["label"] = primary.outcome.str.replace("_1_4", "", regex=False).str.replace("_", " ").str.title()
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0))
    binary = primary[primary.scale == "binary"].iloc[::-1]
    axes[0].barh(binary.label, binary.raw_agreement * 100, color="#5B8E7D")
    for y, (_, row) in enumerate(binary.iterrows()):
        axes[0].text(row.raw_agreement * 100 + 1, y, f"k={row.cohen_kappa:.02f}", va="center", fontsize=9)
    axes[0].set_xlim(0, 105)
    axes[0].set_xlabel("Exact agreement, %")
    axes[0].set_title("Binary outcomes", fontweight="bold")
    ordinal = primary[primary.scale == "ordinal"].iloc[::-1]
    axes[1].barh(ordinal.label, ordinal.weighted_kappa, color="#C76D5E")
    axes[1].axvline(0, color="#333333", lw=0.8)
    axes[1].set_xlim(-0.05, 0.25)
    axes[1].set_xlabel("Quadratic weighted kappa")
    axes[1].set_title("Ordinal outcomes", fontweight="bold")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#E3E3E3", lw=0.7)
    fig.suptitle("Agreement between supplied hybrid rating streams", fontsize=14, fontweight="bold")
    fig.text(0.01, -0.015, "High raw agreement for rare binary flags coexists with near-zero kappa; prevalence differs sharply between streams.", fontsize=8.5)
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"figure_4_hybrid_rater_agreement.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = long_data()
    data["red_flag_stratum"] = data["red_flag_stratum"].fillna(False).astype(bool)
    data.to_csv(DATA / "analysis_long.csv", index=False)

    all_rates = []
    all_contrasts = []
    all_ordinals = []
    all_components = []
    interactions = []
    sensitivities = []
    component_tests = []
    ordinal_tests = []
    rank_uncertainty = []
    rank_changes = []
    specialty_rates = []
    specialty_tests = []
    sensitivity_tests = []
    red_flag_descriptive = []
    for rater in RATERS:
        frame = data[data.rater_stream == rater].copy()
        for outcome in BINARY[:2]:
            rates = cluster_boot_rates(frame, outcome)
            rates.insert(0, "outcome", outcome)
            rates.insert(0, "rater_stream", rater)
            all_rates.append(rates)
            contrasts = cluster_boot_contrasts(frame, outcome)
            contrasts.insert(0, "outcome", outcome)
            contrasts.insert(0, "rater_stream", rater)
            all_contrasts.append(contrasts)
            result = gee_interaction(frame, outcome)
            result.update({"rater_stream": rater, "outcome": outcome})
            interactions.append(result)
        ordinals = ordinal_summary(frame)
        ordinals.insert(0, "rater_stream", rater)
        all_ordinals.append(ordinals)
        components = component_summary(frame)
        components.insert(0, "rater_stream", rater)
        all_components.append(components)

        for outcome in BINARY[2:]:
            result = gee_interaction(frame, outcome, minimum_events=50)
            result.update({"rater_stream": rater, "component": outcome})
            component_tests.append(result)
        for outcome in ORDINAL:
            result = gee_interaction(frame, outcome, family="gaussian")
            result.update({"rater_stream": rater, "outcome": outcome})
            ordinal_tests.append(result)
        for outcome in BINARY[:2]:
            uncertainty, changes = bootstrap_rank_uncertainty(frame, outcome)
            uncertainty.insert(0, "outcome", outcome)
            uncertainty.insert(0, "rater_stream", rater)
            changes.insert(0, "outcome", outcome)
            changes.insert(0, "rater_stream", rater)
            rank_uncertainty.append(uncertainty)
            rank_changes.append(changes)

            grouped_risk = frame.groupby(["specialty_risk", "model_key"])[outcome].agg(
                events="sum", n="count", rate="mean"
            ).reset_index()
            grouped_risk.insert(0, "outcome", outcome)
            grouped_risk.insert(0, "rater_stream", rater)
            specialty_rates.append(grouped_risk)
            risk_test = bootstrap_specialty_risk(frame, outcome)
            risk_test.insert(0, "outcome", outcome)
            risk_test.insert(0, "rater_stream", rater)
            specialty_tests.append(risk_test)

            grouped_red_flag = frame.groupby(["red_flag_stratum", "model_key"])[outcome].agg(
                events="sum", n="count", rate="mean"
            ).reset_index()
            grouped_red_flag.insert(0, "outcome", outcome)
            grouped_red_flag.insert(0, "rater_stream", rater)
            red_flag_descriptive.append(grouped_red_flag)

        subsets = {
            "all": frame,
            "original_complete_only": frame[~frame.technical_regeneration.astype(bool)],
            "exclude_same_provider": frame[~frame.same_provider_evaluation],
            "exclude_role_only": frame[frame.prompt_version != "role_only_isolation"],
            "exclude_red_flag_prompts": frame[~frame.red_flag_stratum],
        }
        for subset_name, subset in subsets.items():
            for outcome in BINARY[:2]:
                grouped = subset.groupby(["model_key", "prompt_version"])[outcome].agg(["sum", "count", "mean"]).reset_index()
                grouped.insert(0, "outcome", outcome)
                grouped.insert(0, "subset", subset_name)
                grouped.insert(0, "rater_stream", rater)
                sensitivities.append(grouped.rename(columns={"sum": "events", "count": "n", "mean": "rate"}))
                result = gee_interaction(subset, outcome, minimum_events=20)
                result.update({"rater_stream": rater, "subset": subset_name, "outcome": outcome})
                sensitivity_tests.append(result)

        refusal_sensitivities = frame.copy()
        refusal_sensitivities["unsafe_any_refusal"] = refusal_sensitivities[
            ["unsafe_binary", "inappropriate_refusal"]
        ].max(axis=1)
        refusal_sensitivities["unsafe_without_refusal"] = (
            refusal_sensitivities["unsafe_binary"].astype(bool)
            & ~refusal_sensitivities["inappropriate_refusal"].astype(bool)
        ).astype(int)
        for outcome in ["unsafe_any_refusal", "unsafe_without_refusal"]:
            result = gee_interaction(refusal_sensitivities, outcome, minimum_events=20)
            result.update({"rater_stream": rater, "subset": outcome, "outcome": "unsafe_binary"})
            sensitivity_tests.append(result)

    rates = pd.concat(all_rates, ignore_index=True)
    contrasts = pd.concat(all_contrasts, ignore_index=True)
    ordinals = pd.concat(all_ordinals, ignore_index=True)
    components = pd.concat(all_components, ignore_index=True)
    interaction_df = pd.DataFrame(interactions)
    interaction_df["p_value_holm"] = interaction_df.groupby("rater_stream", group_keys=False)["p_value"].apply(holm_adjust)
    sensitivity_df = pd.concat(sensitivities, ignore_index=True)
    component_test_df = pd.DataFrame(component_tests)
    component_test_df["q_value_bh"] = component_test_df.groupby("rater_stream", group_keys=False)["p_value"].apply(bh_adjust)
    ordinal_test_df = pd.DataFrame(ordinal_tests)
    ordinal_test_df["q_value_bh"] = ordinal_test_df.groupby("rater_stream", group_keys=False)["p_value"].apply(bh_adjust)
    rank_uncertainty_df = pd.concat(rank_uncertainty, ignore_index=True)
    rank_changes_df = pd.concat(rank_changes, ignore_index=True)
    specialty_rates_df = pd.concat(specialty_rates, ignore_index=True)
    specialty_tests_df = pd.concat(specialty_tests, ignore_index=True)
    overall_risk = specialty_tests_df.model_key.eq("all_models")
    specialty_tests_df["p_value_holm"] = np.nan
    specialty_tests_df.loc[overall_risk, "p_value_holm"] = (
        specialty_tests_df[overall_risk]
        .groupby("rater_stream", group_keys=False)["bootstrap_p"]
        .apply(holm_adjust)
    )
    sensitivity_tests_df = pd.DataFrame(sensitivity_tests)
    red_flag_df = pd.concat(red_flag_descriptive, ignore_index=True)
    rates.to_csv(TABLES / "table_2_primary_rates.csv", index=False)
    contrasts.to_csv(TABLES / "table_3_prompt_contrasts.csv", index=False)
    interaction_df.to_csv(TABLES / "table_4_global_interaction_tests.csv", index=False)
    components.to_csv(TABLES / "table_5_failure_components.csv", index=False)
    ordinals.to_csv(TABLES / "table_6_ordinal_scores.csv", index=False)
    sensitivity_df.to_csv(TABLES / "table_7_sensitivity_analyses.csv", index=False)
    component_test_df.to_csv(TABLES / "table_9_component_interaction_tests.csv", index=False)
    ordinal_test_df.to_csv(TABLES / "table_10_ordinal_interaction_tests.csv", index=False)
    rank_uncertainty_df.to_csv(TABLES / "table_11_rank_uncertainty.csv", index=False)
    rank_changes_df.to_csv(TABLES / "table_12_rank_changes.csv", index=False)
    specialty_rates_df.to_csv(TABLES / "table_13_specialty_risk_rates.csv", index=False)
    specialty_tests_df.to_csv(TABLES / "table_14_specialty_risk_tests.csv", index=False)
    sensitivity_tests_df.to_csv(TABLES / "table_15_sensitivity_interaction_tests.csv", index=False)
    red_flag_df.to_csv(TABLES / "table_16_red_flag_descriptive.csv", index=False)

    rank_frames = []
    for (rater, outcome), group in rates.groupby(["rater_stream", "outcome"]):
        ranked = rank_table(group)
        rank_frames.append(ranked)
    pd.concat(rank_frames).to_csv(TABLES / "table_8_model_ranks_by_prompt.csv", index=False)

    generation = pd.read_csv(ROOT / "data" / "source" / "model_responses.csv")
    generation_summary = generation.groupby("model_key", as_index=False).agg(
        n=("response_id", "size"),
        first_created_utc=("created_at_utc", "min"),
        last_created_utc=("created_at_utc", "max"),
        requested_model_id=("provider_model_id", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        returned_model_id=("provider_model_id_returned", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        requested_reasoning=("reasoning_effort_requested", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        sent_reasoning=("reasoning_effort_parameter_sent", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        requested_temperature=("temperature_requested", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        sent_temperature=("temperature_parameter_sent", lambda x: "; ".join(sorted(x.dropna().astype(str).unique()))),
        regenerated=("technical_regeneration", "sum"),
    )
    generation_summary.to_csv(TABLES / "table_1_generation_provenance.csv", index=False)

    plot_flow()
    plot_rates(rates, "unsafe_binary", "figure_2_unsafe_rates", "Unsafe classifications vary by prompt and evaluator")
    plot_rates(rates, "evidence_insufficient_or_overanswered", "figure_3_evidence_failure_rates", "Evidence-sufficiency failure by prompt and evaluator")
    plot_agreement()

    summary = {
        "analysis_date": "2026-07-17",
        "bootstrap_seed": RNG_SEED,
        "bootstrap_replicates": N_BOOT,
        "n_responses": int(data.blinded_response_id.nunique()),
        "n_rating_records": len(data),
        "n_topics": int(data.topic_id.nunique()),
        "primary_rates": rates.to_dict("records"),
        "global_interactions": interaction_df.to_dict("records"),
        "component_interactions": component_test_df.to_dict("records"),
        "ordinal_interactions": ordinal_test_df.to_dict("records"),
        "specialty_risk_tests": specialty_tests_df.to_dict("records"),
        "sensitivity_interactions": sensitivity_tests_df.to_dict("records"),
    }
    (ROOT / "results" / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(rates.to_string(index=False))
    print("\nGlobal interaction tests\n", interaction_df.to_string(index=False))


if __name__ == "__main__":
    main()
