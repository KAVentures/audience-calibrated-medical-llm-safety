#!/usr/bin/env python3
"""Analysis of the frozen four-LLM medical-safety judge panel."""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import chi2


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "llm_judge_panel"
DATA = PANEL / "data" / "processed"
TABLES = ROOT / "results" / "llm_judge_panel_tables"
FIGURES = ROOT / "results" / "llm_judge_panel_figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

SEED = 20260718
N_BOOT = 5000
MODELS = ["grok_4_3", "gpt_5_5", "gemini_3_5_flash", "claude_4_8_opus"]
JUDGES = MODELS.copy()
PROMPTS = ["clinician_original", "role_only_isolation", "patient_rewrite"]
OUTCOMES = ["unsafe_binary", "evidence_sufficiency_failure"]
COMPONENTS = [
    "factual_error", "missed_red_flag", "false_reassurance", "unsafe_self_management",
    "overconfident_diagnosis_or_treatment", "unsupported_recommendation",
    "hallucinated_source_or_guideline", "inappropriate_refusal",
    "critical_clinician_caveat_omitted", "audience_miscalibration",
]
LABELS = {
    "grok_4_3": "Grok 4.3", "gpt_5_5": "GPT-5.5",
    "gemini_3_5_flash": "Gemini 3.5 Flash", "claude_4_8_opus": "Claude Opus 4.8",
    "clinician_original": "Clinician original", "role_only_isolation": "Patient role-only",
    "patient_rewrite": "Patient rewrite",
}
COLORS = {"grok_4_3": "#176B87", "gpt_5_5": "#2A9D8F", "gemini_3_5_flash": "#D89B2B", "claude_4_8_opus": "#7A5195"}


def holm(values):
    values = np.asarray(values, float)
    order = np.argsort(values)
    out = np.empty(len(values))
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (len(values) - rank) * values[idx])
        out[idx] = min(1.0, running)
    return out


def bh(values):
    values = np.asarray(values, float)
    order = np.argsort(values)[::-1]
    out = np.empty(len(values))
    running = 1.0
    for reverse_rank, idx in enumerate(order):
        rank = len(values) - reverse_rank
        running = min(running, values[idx] * len(values) / rank)
        out[idx] = min(1.0, running)
    return out


def wald_terms(fit, marker):
    names = list(fit.params.index)
    idx = [i for i, name in enumerate(names) if marker(name)]
    r = np.zeros((len(idx), len(names)))
    for row, col in enumerate(idx):
        r[row, col] = 1
    contrast = r @ fit.params.to_numpy()
    cov = r @ fit.cov_params().to_numpy() @ r.T
    rank = int(np.linalg.matrix_rank(cov))
    stat = float(contrast.T @ np.linalg.pinv(cov) @ contrast)
    return stat, rank, float(chi2.sf(stat, rank))


def fit_primary(frame, outcome):
    work = frame.copy()
    judge_order = [judge for judge in JUDGES if judge in set(work["judge_key"])]
    for col, order in [("model_key", MODELS), ("prompt_version", PROMPTS), ("judge_key", judge_order)]:
        work[col] = pd.Categorical(work[col], order)
    formula = (
        f"{outcome} ~ C(model_key)*C(prompt_version) + "
        "C(judge_key)*C(prompt_version) + C(model_key)*C(judge_key)"
    )
    family_name = "binomial_logit"
    fallback_reason = ""
    try:
        fit = smf.gee(formula, groups="topic_id", data=work, family=sm.families.Binomial(),
                       cov_struct=sm.cov_struct.Exchangeable()).fit(maxiter=200)
        if not np.all(np.isfinite(fit.params)) or not np.all(np.isfinite(fit.cov_params())):
            raise ValueError("non-finite logistic coefficients or covariance from separation")
        interaction = wald_terms(fit, lambda n: "C(model_key)" in n and "C(prompt_version)" in n and n.count(":") == 1)
    except Exception as exc:
        family_name = "gaussian_identity_risk_difference_fallback"
        fallback_reason = str(exc)
        fit = smf.gee(formula, groups="topic_id", data=work, family=sm.families.Gaussian(),
                       cov_struct=sm.cov_struct.Exchangeable()).fit(maxiter=200)
        interaction = wald_terms(fit, lambda n: "C(model_key)" in n and "C(prompt_version)" in n and n.count(":") == 1)
    saturated = smf.gee(
        f"{outcome} ~ C(model_key)*C(prompt_version)*C(judge_key)", groups="topic_id", data=work,
        family=sm.families.Gaussian() if "fallback" in family_name else sm.families.Binomial(),
        cov_struct=sm.cov_struct.Exchangeable(),
    ).fit(maxiter=200)
    if not np.all(np.isfinite(saturated.cov_params())):
        saturated = smf.gee(
            f"{outcome} ~ C(model_key)*C(prompt_version)*C(judge_key)", groups="topic_id", data=work,
            family=sm.families.Gaussian(), cov_struct=sm.cov_struct.Exchangeable(),
        ).fit(maxiter=200)
        family_name += "; three_way_gaussian_fallback"
    heterogeneity = wald_terms(saturated, lambda n: n.count(":") == 2)
    return {
        "outcome": outcome, "n_ratings": int(fit.nobs), "events": int(work[outcome].sum()),
        "panel_model_prompt_chi2": interaction[0], "panel_model_prompt_df": interaction[1],
        "panel_model_prompt_p": interaction[2], "three_way_chi2": heterogeneity[0],
        "three_way_df": heterogeneity[1], "three_way_p": heterogeneity[2],
        "formula": formula, "family": family_name, "fallback_reason": fallback_reason,
        "correlation": "exchangeable within topic; robust sandwich covariance",
    }


def boot_cell_rates(frame, outcome):
    cells = pd.MultiIndex.from_product([MODELS, PROMPTS, JUDGES], names=["model_key", "prompt_version", "judge_key"])
    topics = sorted(frame.topic_id.unique())
    matrix = frame.groupby(["topic_id", "model_key", "prompt_version", "judge_key"])[outcome].mean().unstack([1, 2, 3]).reindex(index=topics, columns=cells).to_numpy()
    panel = matrix.reshape(len(topics), len(MODELS), len(PROMPTS), len(JUDGES)).mean(axis=3)
    rng = np.random.default_rng(SEED + OUTCOMES.index(outcome))
    sampled = rng.integers(0, len(topics), size=(N_BOOT, len(topics)))
    boots = panel[sampled].mean(axis=1)
    point = panel.mean(axis=0)
    rows = []
    for mi, model in enumerate(MODELS):
        for pi, prompt in enumerate(PROMPTS):
            subset = frame[(frame.model_key == model) & (frame.prompt_version == prompt)]
            rows.append({
                "outcome": outcome, "model_key": model, "prompt_version": prompt,
                "responses": int(subset.response_id.nunique()), "judge_ratings": len(subset),
                "events": int(subset[outcome].sum()), "rate": float(point[mi, pi]),
                "ci_low": float(np.quantile(boots[:, mi, pi], .025)),
                "ci_high": float(np.quantile(boots[:, mi, pi], .975)),
            })
    return pd.DataFrame(rows), boots


def judge_rates(frame):
    return (frame.groupby(["judge_key", "model_key", "prompt_version"])[OUTCOMES]
            .agg(["sum", "count", "mean"]).reset_index())


def kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    po = np.mean(a == b)
    pa, pb = np.mean(a), np.mean(b)
    pe = pa * pb + (1 - pa) * (1 - pb)
    kap = (po - pe) / (1 - pe) if pe < 1 else np.nan
    pbar = (pa + pb) / 2
    pe_ac1 = 2 * pbar * (1 - pbar)
    ac1 = (po - pe_ac1) / (1 - pe_ac1) if pe_ac1 < 1 else np.nan
    return po, kap, ac1


def between_judge_agreement(frame):
    rows = []
    for outcome in OUTCOMES:
        wide = frame.pivot(index="response_id", columns="judge_key", values=outcome)
        for a, b in combinations(JUDGES, 2):
            po, kap, ac1 = kappa(wide[a], wide[b])
            rows.append({"outcome": outcome, "judge_a": a, "judge_b": b, "n": len(wide),
                         "exact_agreement": po, "cohen_kappa": kap, "gwet_ac1": ac1,
                         "prevalence_a": wide[a].mean(), "prevalence_b": wide[b].mean()})
    return pd.DataFrame(rows)


def duplicate_repeatability(all_rows):
    rows = []
    for outcome in OUTCOMES + ["harm_severity", "rating_overall_safety"]:
        wide = all_rows.pivot_table(index=["judge_key", "response_id"], columns="occurrence", values=outcome, aggfunc="first").dropna()
        for judge in JUDGES:
            pair = wide.loc[judge]
            if outcome in OUTCOMES:
                po, kap, ac1 = kappa(pair["1"], pair["2"])
                rows.append({"judge_key": judge, "outcome": outcome, "n": len(pair), "exact_agreement": po,
                             "cohen_kappa": kap, "gwet_ac1": ac1, "mean_absolute_difference": np.nan})
            else:
                rows.append({"judge_key": judge, "outcome": outcome, "n": len(pair),
                             "exact_agreement": np.mean(pair["1"] == pair["2"]), "cohen_kappa": np.nan,
                             "gwet_ac1": np.nan, "mean_absolute_difference": np.mean(np.abs(pair["1"] - pair["2"]))})
    return pd.DataFrame(rows)


def consensus_summary(frame):
    rows = []
    for outcome in OUTCOMES:
        base = frame.groupby(["response_id", "model_key", "prompt_version", "topic_id"])[outcome].sum().reset_index(name="positive_judges")
        for keys, part in base.groupby(["model_key", "prompt_version"]):
            rows.append({"outcome": outcome, "model_key": keys[0], "prompt_version": keys[1], "n": len(part),
                         "majority_3_or_4": int((part.positive_judges >= 3).sum()),
                         "unanimous_4": int((part.positive_judges == 4).sum()),
                         "split_2_2": int((part.positive_judges == 2).sum()),
                         "any_1_or_more": int((part.positive_judges >= 1).sum())})
    return pd.DataFrame(rows)


def leave_one_out(frame):
    rows = []
    for outcome in OUTCOMES:
        for omitted in JUDGES:
            part = frame[frame.judge_key != omitted]
            rates = part.groupby(["model_key", "prompt_version"])[outcome].mean().reset_index()
            rates["rank_lowest_rate"] = rates.groupby("prompt_version")[outcome].rank(method="min").astype(int)
            rates.insert(0, "outcome", outcome); rates.insert(1, "omitted_judge", omitted)
            rows.append(rates)
    return pd.concat(rows, ignore_index=True)


def leave_one_judge_interaction(frame):
    rows = []
    for omitted in JUDGES:
        part = frame[frame.judge_key != omitted].copy()
        judge_order = [judge for judge in JUDGES if judge != omitted]
        for col, order in [("model_key", MODELS), ("prompt_version", PROMPTS), ("judge_key", judge_order)]:
            part[col] = pd.Categorical(part[col], order)
        for outcome in OUTCOMES:
            formula = (
                f"{outcome} ~ C(model_key)*C(prompt_version) + "
                "C(judge_key)*C(prompt_version) + C(model_key)*C(judge_key)"
            )
            fit = smf.gee(
                formula, groups="topic_id", data=part, family=sm.families.Gaussian(),
                cov_struct=sm.cov_struct.Exchangeable(),
            ).fit(maxiter=200)
            interaction = wald_terms(
                fit,
                lambda name: "C(model_key)" in name and "C(prompt_version)" in name and name.count(":") == 1,
            )
            rows.append({
                "outcome": outcome,
                "omitted_judge": omitted,
                "remaining_judges": ";".join(judge for judge in JUDGES if judge != omitted),
                "n_ratings": int(fit.nobs),
                "events": int(part[outcome].sum()),
                "model_prompt_chi2": interaction[0],
                "effective_df": interaction[1],
                "raw_p": interaction[2],
                "family": "gaussian_identity_risk_difference_sensitivity",
                "rationale": "Same risk-scale estimating family as the reported full-panel fallback",
            })
    result = pd.DataFrame(rows)
    result["holm_p_within_omission"] = (
        result.groupby("omitted_judge", group_keys=False)["raw_p"].transform(lambda values: holm(values.to_numpy()))
    )
    result["holm_p_all_8_sensitivity_tests"] = holm(result.raw_p)
    return result


def same_provider(frame):
    rows = []
    rng = np.random.default_rng(SEED + 31)
    for outcome in OUTCOMES:
        for model in MODELS:
            part = frame[frame.model_key == model]
            same = part[part.judge_key == model].set_index("response_id")[outcome]
            other = part[part.judge_key != model].groupby("response_id")[outcome].mean()
            topic = part.drop_duplicates("response_id").set_index("response_id")["topic_id"]
            values = pd.DataFrame({"same": same, "other": other, "topic_id": topic}).groupby("topic_id")[["same", "other"]].mean()
            diff = values["same"] - values["other"]
            boots = np.array([diff.iloc[rng.integers(0, len(diff), len(diff))].mean() for _ in range(N_BOOT)])
            rows.append({"outcome": outcome, "generator_model": model, "same_provider_rate": same.mean(),
                         "other_judges_rate": other.mean(), "paired_difference": diff.mean(),
                         "ci_low": np.quantile(boots, .025), "ci_high": np.quantile(boots, .975)})
    return pd.DataFrame(rows)


def panel_contrasts_and_ranks(rates, boot_arrays):
    contrasts, ranks = [], []
    for outcome in OUTCOMES:
        subset = rates[rates.outcome == outcome].set_index(["model_key", "prompt_version"])
        boots = boot_arrays[outcome]
        point = boots.mean(axis=0)
        for mi, model in enumerate(MODELS):
            for pi, prompt in enumerate(PROMPTS[1:], start=1):
                diff = boots[:, mi, pi] - boots[:, mi, 0]
                contrasts.append({"outcome": outcome, "model_key": model, "contrast": f"{prompt}_minus_clinician",
                                  "risk_difference": subset.loc[(model, prompt), "rate"] - subset.loc[(model, PROMPTS[0]), "rate"],
                                  "ci_low": np.quantile(diff, .025), "ci_high": np.quantile(diff, .975)})
        for pi, prompt in enumerate(PROMPTS):
            cell = subset.xs(prompt, level="prompt_version")["rate"].reindex(MODELS)
            for model in MODELS:
                ranks.append({"outcome": outcome, "prompt_version": prompt, "model_key": model,
                              "rate": cell[model], "rank_lowest_rate": int(cell.rank(method="min")[model])})
    return pd.DataFrame(contrasts), pd.DataFrame(ranks)


def judge_rankings(frame):
    rows = []
    for outcome in OUTCOMES:
        rates = frame.groupby(["judge_key", "prompt_version", "model_key"])[outcome].mean()
        for (judge, prompt), cell in rates.groupby(level=[0, 1]):
            cell = cell.droplevel([0, 1]).reindex(MODELS)
            rank = cell.rank(method="min")
            for model in MODELS:
                rows.append({"outcome": outcome, "judge_key": judge, "prompt_version": prompt,
                             "model_key": model, "rate": cell[model], "rank_lowest_rate": int(rank[model])})
    return pd.DataFrame(rows)


def component_table(frame):
    grouped = frame.groupby(["judge_key", "model_key", "prompt_version"])[COMPONENTS].agg(["sum", "mean"])
    return grouped.stack(level=0, future_stack=True).reset_index().rename(columns={"level_3": "component"})


def plot_rates(rates, outcome, filename):
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    x = np.arange(len(PROMPTS)); offsets = np.linspace(-.27, .27, 4)
    for offset, model in zip(offsets, MODELS):
        cell = rates[(rates.outcome == outcome) & (rates.model_key == model)].set_index("prompt_version").reindex(PROMPTS)
        y, lo, hi = [100 * cell[c].to_numpy() for c in ["rate", "ci_low", "ci_high"]]
        ax.errorbar(x + offset, y, yerr=[y-lo, hi-y], fmt="o", ms=7, capsize=3, lw=1.5,
                    color=COLORS[model], label=LABELS[model])
    ax.set_xticks(x, [LABELS[p] for p in PROMPTS]); ax.set_ylabel("Evaluator-assigned responses, %")
    ax.grid(axis="y", color="#dddddd", lw=.7); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    ax.set_title("Unsafe response" if outcome == "unsafe_binary" else "Evidence-sufficiency failure", fontweight="bold")
    fig.tight_layout(rect=[0, .08, 1, 1])
    for ext in ["png", "pdf", "svg"]: fig.savefig(FIGURES / f"{filename}.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_agreement(agreement):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8))
    for panel_index, (ax, outcome) in enumerate(zip(axes, OUTCOMES)):
        matrix = np.full((4, 4), np.nan)
        for _, row in agreement[agreement.outcome == outcome].iterrows():
            i, j = JUDGES.index(row.judge_a), JUDGES.index(row.judge_b)
            matrix[i, j] = matrix[j, i] = row.cohen_kappa
        cmap = plt.get_cmap("RdYlGn").copy()
        cmap.set_bad("#E5E7EB")
        im = ax.imshow(matrix, vmin=-.1, vmax=.75, cmap=cmap)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, "" if i == j else f"{matrix[i,j]:.2f}", ha="center", va="center", fontsize=9)
        ax.set_xticks(range(4), [LABELS[j].replace(" ", "\n", 1) for j in JUDGES], fontsize=8)
        ax.set_yticks(range(4), [LABELS[j] for j in JUDGES] if panel_index == 0 else ["", "", "", ""], fontsize=8)
        ax.set_title("Unsafe" if outcome == "unsafe_binary" else "Evidence sufficiency", fontweight="bold")
    fig.colorbar(im, ax=axes, label="Cohen's kappa", fraction=.035, pad=.04)
    fig.suptitle("Between-judge agreement", fontweight="bold")
    fig.savefig(FIGURES / "figure_4_between_judge_agreement.png", dpi=320, bbox_inches="tight")
    fig.savefig(FIGURES / "figure_4_between_judge_agreement.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "figure_4_between_judge_agreement.svg", bbox_inches="tight")
    plt.close(fig)


def plot_judge_prevalence(frame):
    rates = frame.groupby("judge_key")[OUTCOMES].mean() * 100
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    x = np.arange(4); width = .34
    ax.bar(x-width/2, rates.unsafe_binary, width, label="Unsafe", color="#C64B55")
    ax.bar(x+width/2, rates.evidence_sufficiency_failure, width, label="Evidence insufficiency", color="#176B87")
    ax.set_xticks(x, [LABELS[j] for j in JUDGES]); ax.set_ylabel("All ratings positive, %")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#dddddd", lw=.7); ax.legend(frameon=False)
    ax.set_title("Evaluator thresholds differ across the fixed judge panel", fontweight="bold")
    fig.tight_layout()
    for ext in ["png", "pdf", "svg"]: fig.savefig(FIGURES / f"figure_3_judge_prevalence.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main():
    for ext in ("png", "pdf", "svg"):
        (FIGURES / f"figure_3_judge_prevalence.{ext}").unlink(missing_ok=True)
    primary = pd.read_csv(DATA / "llm_judge_ratings_primary.csv", dtype={"occurrence": str})
    all_rows = pd.read_csv(DATA / "llm_judge_ratings_all_occurrences.csv", dtype={"occurrence": str})
    for frame in [primary, all_rows]:
        for col in OUTCOMES + COMPONENTS: frame[col] = frame[col].astype(int)

    tests = pd.DataFrame([fit_primary(primary, outcome) for outcome in OUTCOMES])
    tests["holm_p"] = holm(tests.panel_model_prompt_p)
    tests["three_way_holm_p"] = holm(tests.three_way_p)
    tests.to_csv(TABLES / "table_primary_interaction_tests.csv", index=False)

    rate_frames = []; boot_arrays = {}
    for outcome in OUTCOMES:
        rates, boots = boot_cell_rates(primary, outcome); rate_frames.append(rates); boot_arrays[outcome] = boots
    rates = pd.concat(rate_frames, ignore_index=True)
    rates.to_csv(TABLES / "table_panel_standardized_rates.csv", index=False)
    judge_rates(primary).to_csv(TABLES / "table_judge_specific_rates.csv", index=False)
    agreement = between_judge_agreement(primary); agreement.to_csv(TABLES / "table_between_judge_agreement.csv", index=False)
    duplicate_repeatability(all_rows).to_csv(TABLES / "table_within_judge_repeatability.csv", index=False)
    consensus_summary(primary).to_csv(TABLES / "table_vote_summaries_not_ground_truth.csv", index=False)
    leave_one_out(primary).to_csv(TABLES / "table_leave_one_judge_out.csv", index=False)
    leave_one_judge_interaction(primary).to_csv(TABLES / "table_leave_one_judge_interaction_tests.csv", index=False)
    same_provider(primary).to_csv(TABLES / "table_same_provider_descriptive.csv", index=False)
    component_table(primary).to_csv(TABLES / "table_component_profiles.csv", index=False)
    contrasts, panel_ranks = panel_contrasts_and_ranks(rates, boot_arrays)
    contrasts.to_csv(TABLES / "table_panel_prompt_contrasts.csv", index=False)
    panel_ranks.to_csv(TABLES / "table_panel_model_ranks.csv", index=False)
    judge_rankings(primary).to_csv(TABLES / "table_judge_specific_model_ranks.csv", index=False)

    plot_rates(rates, "unsafe_binary", "figure_2_panel_unsafe_rates")
    plot_rates(rates, "evidence_sufficiency_failure", "figure_3_panel_evidence_rates")
    plot_agreement(agreement)

    summary = {
        "analysis_at_utc": pd.Timestamp.now(tz="UTC").isoformat(), "seed": SEED, "bootstrap_replicates": N_BOOT,
        "primary_ratings": len(primary), "unique_responses": int(primary.response_id.nunique()),
        "judges": JUDGES, "models": MODELS, "prompt_versions": PROMPTS,
        "primary_tests": tests.to_dict(orient="records"),
        "overall_judge_prevalence": primary.groupby("judge_key")[OUTCOMES].mean().to_dict(orient="index"),
        "overall_panel_prevalence": {o: float(primary[o].mean()) for o in OUTCOMES},
    }
    (ROOT / "results" / "llm_judge_panel_analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
