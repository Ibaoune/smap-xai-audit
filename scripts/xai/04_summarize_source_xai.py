#!/usr/bin/env python
"""
RF-04B-SOURCE: Summarise TreeSHAP outputs for all four SOURCE models.

Produces:
  - tidy_predictor_summary.csv  : per-predictor global statistics per model
  - tidy_group_summary.csv      : per-group global importance per model
  - matched_group_comparison.csv: CDF vs NoCDF on matched support
  - dependence_features.json    : top-4 predictors by frozen selection rule
  - seasonal_djf/jja_*.csv      : DJF / JJA breakdowns (matched support)
  - spatial_fold_group_*.csv    : per-spatial-fold breakdowns (matched)
  - spatial_stability.csv       : stability statistics across folds

All statistics are on the 10,000-row balanced compute cohort.
2020 is SEALED.
"""
import json
import sys
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr


IN_DIR = Path("data/processed/modeling/xai/outputs/source")
MODELS = [
    ("da_cdf",   "native"),
    ("da_nocdf", "native"),
    ("da_cdf",   "matched"),
    ("da_nocdf", "matched"),
]


def get_summaries(df, features):
    rows = []
    for f in features:
        vals = df[f"shap__{f}"].values
        rows.append({
            "feature":                f,
            "mean_abs_shap":          float(np.mean(np.abs(vals))),
            "mean_signed_shap":       float(np.mean(vals)),
            "median_shap":            float(np.median(vals)),
            "positive_shap_fraction": float(np.mean(vals > 0)),
            "negative_shap_fraction": float(np.mean(vals < 0)),
        })
    out = pd.DataFrame(rows).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    out["rank_mean_abs_shap"] = out.index + 1
    return out


def get_group_importance(summary_df, feature_groups):
    rows = []
    for g, feats in feature_groups.items():
        g_df = summary_df[summary_df["feature"].isin(feats)]
        g_abs = float(g_df["mean_abs_shap"].sum())
        rows.append({"group": g, "group_abs_importance": g_abs})
    out = pd.DataFrame(rows)
    total = out["group_abs_importance"].sum()
    out["normalized_group_importance"] = out["group_abs_importance"] / total
    out["normalized_group_importance_pct"] = out["normalized_group_importance"] * 100
    out = out.sort_values("group_abs_importance", ascending=False).reset_index(drop=True)
    return out


def overlap(a, b):
    return len(set(a) & set(b))


def print_table(title, df, cols):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(df[cols].to_string(index=False))


def main():
    print("Summarising SOURCE XAI...", flush=True)

    with open("configs/xai/feature_groups.yaml") as f:
        feature_groups = yaml.safe_load(f)

    summaries     = {}
    group_summs   = {}
    all_features  = None

    # ── 1. Per-model global summaries ─────────────────────────────────────────
    for exp, sup in MODELS:
        df = pd.read_parquet(IN_DIR / f"shap_{exp}_{sup}.parquet")
        features = [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]
        if all_features is None:
            all_features = set(features)
        else:
            assert set(features) == all_features, "Feature set differs across models!"

        summ  = get_summaries(df, features)
        g_sum = get_group_importance(summ, feature_groups)

        summ["experiment"]  = exp
        summ["support_mode"] = sup
        g_sum["experiment"] = exp
        g_sum["support_mode"] = sup

        # Map feature_group into predictor summary
        feat_to_group = {f: g for g, fs in feature_groups.items() for f in fs}
        summ["feature_group"] = summ["feature"].map(feat_to_group).fillna("unmapped")
        assert (summ["feature_group"] == "unmapped").sum() == 0, "Unmapped features found!"

        summaries[f"{exp}_{sup}"]   = summ
        group_summs[f"{exp}_{sup}"] = g_sum

        # SHAP vs Permutation agreement
        with open(IN_DIR / f"permutation_{exp}_{sup}.json") as f_perm:
            perm = json.load(f_perm)
        perm_df = pd.DataFrame({
            "feature": perm["features"],
            "perm_imp": perm["importances_mean"],
        }).sort_values("perm_imp", ascending=False).reset_index(drop=True)
        perm_df["perm_rank"] = perm_df.index + 1

        mm = pd.merge(summ[["feature", "rank_mean_abs_shap"]], perm_df[["feature", "perm_rank"]], on="feature")
        rho, _ = spearmanr(mm["rank_mean_abs_shap"], mm["perm_rank"])
        t5  = overlap(summ.head(5)["feature"], perm_df.head(5)["feature"])
        t10 = overlap(summ.head(10)["feature"], perm_df.head(10)["feature"])
        print(f"  [{exp} {sup}] SHAP vs Permutation: ρ={rho:.3f}  top5={t5}/5  top10={t10}/10", flush=True)

    # ── 2. Save tidy tables ────────────────────────────────────────────────────
    pd.concat(summaries.values()).to_csv(IN_DIR / "tidy_predictor_summary.csv", index=False)
    pd.concat(group_summs.values()).to_csv(IN_DIR / "tidy_group_summary.csv", index=False)
    print("\n  Saved tidy_predictor_summary.csv and tidy_group_summary.csv", flush=True)

    # ── 3. Matched CDF vs NoCDF comparisons ───────────────────────────────────
    cdf_s   = summaries["da_cdf_matched"]
    nocdf_s = summaries["da_nocdf_matched"]
    m_pred  = pd.merge(cdf_s, nocdf_s, on="feature", suffixes=("_cdf", "_nocdf"))
    rho_matched, _ = spearmanr(m_pred["rank_mean_abs_shap_cdf"], m_pred["rank_mean_abs_shap_nocdf"])
    t5_m  = overlap(cdf_s.head(5)["feature"], nocdf_s.head(5)["feature"])
    t10_m = overlap(cdf_s.head(10)["feature"], nocdf_s.head(10)["feature"])
    print(f"\n  Matched CDF vs NoCDF predictor: ρ={rho_matched:.3f}  top5={t5_m}/5  top10={t10_m}/10")

    cdf_g   = group_summs["da_cdf_matched"]
    nocdf_g = group_summs["da_nocdf_matched"]
    m_grp   = pd.merge(cdf_g, nocdf_g, on="group", suffixes=("_cdf", "_nocdf"))
    rho_g, _ = spearmanr(m_grp["normalized_group_importance_cdf"],
                         m_grp["normalized_group_importance_nocdf"])
    m_grp["difference_cdf_minus_nocdf"] = (
        m_grp["normalized_group_importance_cdf"] - m_grp["normalized_group_importance_nocdf"]
    )
    m_grp.to_csv(IN_DIR / "matched_group_comparison.csv", index=False)
    print(f"  Matched CDF vs NoCDF group: ρ={rho_g:.3f}", flush=True)

    print_table(
        "Matched CDF group importance (%)",
        cdf_g, ["group", "normalized_group_importance_pct"],
    )
    print_table(
        "Matched NoCDF group importance (%)",
        nocdf_g, ["group", "normalized_group_importance_pct"],
    )
    print_table(
        "Top-10 matched CDF predictors",
        cdf_s.head(10), ["rank_mean_abs_shap", "feature", "feature_group", "mean_abs_shap", "mean_signed_shap"],
    )
    print_table(
        "Top-10 matched NoCDF predictors",
        nocdf_s.head(10), ["rank_mean_abs_shap", "feature", "feature_group", "mean_abs_shap", "mean_signed_shap"],
    )

    # ── 4. Native vs Matched sensitivity ──────────────────────────────────────
    print("\n  Native vs Matched sensitivity:", flush=True)
    for exp in ["da_cdf", "da_nocdf"]:
        nat = summaries[f"{exp}_native"]
        mat = summaries[f"{exp}_matched"]
        mm  = pd.merge(nat, mat, on="feature", suffixes=("_nat", "_mat"))
        rho_s, _ = spearmanr(mm["rank_mean_abs_shap_nat"], mm["rank_mean_abs_shap_mat"])
        t10_s  = overlap(nat.head(10)["feature"], mat.head(10)["feature"])
        nat_g  = group_summs[f"{exp}_native"]
        mat_g  = group_summs[f"{exp}_matched"]
        mm_g   = pd.merge(nat_g, mat_g, on="group", suffixes=("_nat", "_mat"))
        rho_g2, _ = spearmanr(mm_g["normalized_group_importance_nat"],
                              mm_g["normalized_group_importance_mat"])
        print(f"    {exp}: predictor ρ={rho_s:.3f}  top10={t10_s}/10  group ρ={rho_g2:.3f}")

    # ── 5. Frozen dependence-predictor selection rule ─────────────────────────
    # "mean of mean_abs_shap across matched CDF and NoCDF, then sort descending,
    #  ties broken by feature name ascending"
    dep_df = pd.merge(
        cdf_s[["feature", "mean_abs_shap"]],
        nocdf_s[["feature", "mean_abs_shap"]],
        on="feature", suffixes=("_cdf", "_nocdf"),
    )
    dep_df["global_importance"] = (dep_df["mean_abs_shap_cdf"] + dep_df["mean_abs_shap_nocdf"]) / 2.0
    dep_df = dep_df.sort_values(["global_importance", "feature"], ascending=[False, True]).reset_index(drop=True)
    top_4 = dep_df.head(4)["feature"].tolist()
    with open(IN_DIR / "dependence_features.json", "w") as f:
        json.dump({"top_4_dependence_features": top_4,
                   "selection_rule": "mean(mean_abs_shap_cdf, mean_abs_shap_nocdf) on matched support, ties by name"},
                  f, indent=2)
    print(f"\n  Dependence-plot top-4 (frozen): {top_4}", flush=True)

    # ── 6. DJF / JJA seasonal analysis (matched support) ─────────────────────
    for exp in ["da_cdf", "da_nocdf"]:
        df = pd.read_parquet(IN_DIR / f"shap_{exp}_matched.parquet")
        for season, months in [("djf", [12, 1, 2]), ("jja", [6, 7, 8])]:
            sub = df[df["month"].isin(months)]
            s   = get_summaries(sub, all_features)
            g   = get_group_importance(s, feature_groups)
            s.to_csv(IN_DIR / f"seasonal_{season}_predictor_{exp}.csv", index=False)
            g.to_csv(IN_DIR / f"seasonal_{season}_group_{exp}.csv",     index=False)
        print(f"  Seasonal analysis saved for {exp}", flush=True)

    # ── 7. Spatial-fold stability (matched support) ────────────────────────────
    spatial_stability = []
    for exp in ["da_cdf", "da_nocdf"]:
        df = pd.read_parquet(IN_DIR / f"shap_{exp}_matched.parquet")
        fold_rows = []
        for fold in range(5):
            sub   = df[df["spatial_fold"] == fold]
            s     = get_summaries(sub, all_features)
            g     = get_group_importance(s, feature_groups)
            g["spatial_fold"] = fold
            fold_rows.append(g)
        fg = pd.concat(fold_rows)
        fg.to_csv(IN_DIR / f"spatial_fold_group_{exp}.csv", index=False)
        stab = (fg.groupby("group")["normalized_group_importance"]
                  .agg(["mean", "std", "min", "max"])
                  .reset_index())
        stab["experiment"] = exp
        spatial_stability.append(stab)
        print(f"  Spatial-fold analysis saved for {exp}", flush=True)
    pd.concat(spatial_stability).to_csv(IN_DIR / "spatial_stability.csv", index=False)

    print("\nSummarisation complete.", flush=True)


if __name__ == "__main__":
    main()
