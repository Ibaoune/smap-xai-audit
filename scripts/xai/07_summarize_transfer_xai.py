#!/usr/bin/env python
"""
RF-04B-TRANSFER: Summarise TreeSHAP outputs for all 8 TRANSFER models.

Produces (in data/processed/modeling/xai/outputs/transfer/):
  tidy_predictor_summary.csv   — per-predictor, per-model statistics
  tidy_group_summary.csv       — per-group, per-model importance
  group_matrix_cdf.csv         — targets × groups, CDF
  group_matrix_nocdf.csv       — targets × groups, NoCDF
  group_matrix_diff.csv        — CDF minus NoCDF per group × target
  cross_target_pred_corr_cdf.csv   — 4×4 predictor-rank correlation matrix, CDF
  cross_target_pred_corr_nocdf.csv — 4×4 predictor-rank correlation matrix, NoCDF
  cross_target_group_corr_cdf.csv  — 4×4 group-importance correlation matrix, CDF
  cross_target_group_corr_nocdf.csv
  cdf_nocdf_comparison.csv     — per-target CDF vs NoCDF metrics
  seasonal_djf_group_<exp>_<tgt>.csv
  seasonal_jja_group_<exp>_<tgt>.csv
  spatial_fold_group_<exp>_<tgt>.csv
  spatial_stability_<exp>_<tgt>.csv
  dependence_features.json     — frozen top-3 per target

2020 is SEALED.
"""
import json
import numpy as np
import pandas as pd
import yaml
from itertools import combinations
from pathlib import Path
from scipy.stats import spearmanr

IN_DIR  = Path("data/processed/modeling/xai/outputs/transfer")
TARGETS = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
EXPS    = ["da_cdf", "da_nocdf"]
MODELS  = [(e, t) for e in EXPS for t in TARGETS]


def load_fg():
    with open("configs/xai/feature_groups.yaml") as f:
        return yaml.safe_load(f)


def get_features(df):
    return [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]


def get_summaries(df, features):
    rows = []
    for feat in features:
        v = df[f"shap__{feat}"].values
        rows.append({
            "feature":                feat,
            "mean_abs_shap":          float(np.mean(np.abs(v))),
            "mean_signed_shap":       float(np.mean(v)),
            "median_shap":            float(np.median(v)),
            "positive_shap_fraction": float(np.mean(v > 0)),
            "negative_shap_fraction": float(np.mean(v < 0)),
        })
    out = (pd.DataFrame(rows)
             .sort_values("mean_abs_shap", ascending=False)
             .reset_index(drop=True))
    out["rank_mean_abs_shap"] = out.index + 1
    return out


def get_group_imp(summ, fg, features):
    rows = []
    for g, fs in fg.items():
        active = [f for f in fs if f in features]
        g_abs  = float(summ[summ["feature"].isin(active)]["mean_abs_shap"].sum())
        rows.append({"group": g, "group_abs_importance": g_abs})
    out = pd.DataFrame(rows)
    total = out["group_abs_importance"].sum()
    out["normalized_group_importance"] = out["group_abs_importance"] / (total if total > 0 else 1)
    return out.sort_values("group_abs_importance", ascending=False).reset_index(drop=True)


def rho(a, b):
    r, _ = spearmanr(a, b)
    return float(r)


def overlap(s1, s2, n):
    return len(set(s1.head(n)["feature"]) & set(s2.head(n)["feature"]))


def main():
    print("Summarising TRANSFER XAI...", flush=True)
    fg = load_fg()

    summaries   = {}   # (exp, tgt) -> predictor df
    group_summs = {}   # (exp, tgt) -> group df
    all_features = None

    # ── 1. Per-model predictor and group summaries ────────────────────────────
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)

        if all_features is None:
            all_features = set(features)
        else:
            assert set(features) == all_features, f"Feature set differs for {tag}!"

        summ  = get_summaries(df, features)
        g_sum = get_group_imp(summ, fg, features)

        feat_to_group = {f: g for g, fs in fg.items() for f in fs}
        summ["feature_group"] = summ["feature"].map(feat_to_group).fillna("unmapped")
        assert (summ["feature_group"] == "unmapped").sum() == 0, f"Unmapped features in {tag}"

        summ["experiment"]  = exp
        summ["target"]      = tgt
        g_sum["experiment"] = exp
        g_sum["target"]     = tgt

        summaries[(exp, tgt)]   = summ
        group_summs[(exp, tgt)] = g_sum

        # SHAP vs Permutation
        with open(IN_DIR / f"permutation_{tag}.json") as f:
            perm = json.load(f)
        perm_df = (pd.DataFrame({"feature": perm["features"], "perm_imp": perm["importances_mean"]})
                     .sort_values("perm_imp", ascending=False).reset_index(drop=True))
        perm_df["perm_rank"] = perm_df.index + 1
        mm = pd.merge(summ[["feature", "rank_mean_abs_shap"]], perm_df[["feature", "perm_rank"]], on="feature")
        r  = rho(mm["rank_mean_abs_shap"], mm["perm_rank"])
        t5  = overlap(summ, perm_df.rename(columns={"perm_rank": "rank_mean_abs_shap"}), 5)
        t10 = overlap(summ, perm_df.rename(columns={"perm_rank": "rank_mean_abs_shap"}), 10)
        print(f"  [{exp} {tgt}] SHAP vs Perm: ρ={r:.3f}  top5={t5}/5  top10={t10}/10", flush=True)

    # ── 2. Save tidy tables ────────────────────────────────────────────────────
    pd.concat(summaries.values()).to_csv(IN_DIR / "tidy_predictor_summary.csv", index=False)
    pd.concat(group_summs.values()).to_csv(IN_DIR / "tidy_group_summary.csv", index=False)
    print("\n  Saved tidy summaries", flush=True)

    # ── 3. Group importance matrices (targets × groups) ───────────────────────
    groups = list(fg.keys())
    for exp in EXPS:
        rows = []
        for tgt in TARGETS:
            g_df = group_summs[(exp, tgt)].set_index("group")["normalized_group_importance"]
            row  = {"target": tgt}
            for g in groups:
                row[g] = float(g_df.get(g, 0.0))
            rows.append(row)
        pd.DataFrame(rows).to_csv(IN_DIR / f"group_matrix_{exp.split('_')[1]}.csv", index=False)

    # CDF minus NoCDF difference matrix
    diff_rows = []
    for tgt in TARGETS:
        cdf_g   = group_summs[("da_cdf",   tgt)].set_index("group")["normalized_group_importance"]
        nocdf_g = group_summs[("da_nocdf", tgt)].set_index("group")["normalized_group_importance"]
        row = {"target": tgt}
        for g in groups:
            row[g] = float(cdf_g.get(g, 0.0) - nocdf_g.get(g, 0.0))
        diff_rows.append(row)
    pd.DataFrame(diff_rows).to_csv(IN_DIR / "group_matrix_diff.csv", index=False)
    print("  Saved group importance matrices", flush=True)

    # ── 4. Cross-target predictor-rank and group correlation matrices ─────────
    for exp in EXPS:
        label = exp.split("_")[1]
        # Predictor-rank 4×4
        pred_mat = pd.DataFrame(index=TARGETS, columns=TARGETS, dtype=float)
        for t1, t2 in [(t1, t2) for t1 in TARGETS for t2 in TARGETS]:
            s1 = summaries[(exp, t1)]
            s2 = summaries[(exp, t2)]
            mm = pd.merge(s1[["feature","rank_mean_abs_shap"]], s2[["feature","rank_mean_abs_shap"]], on="feature")
            pred_mat.loc[t1, t2] = rho(mm["rank_mean_abs_shap_x"], mm["rank_mean_abs_shap_y"])
        pred_mat.to_csv(IN_DIR / f"cross_target_pred_corr_{label}.csv")

        # Group importance 4×4
        grp_mat = pd.DataFrame(index=TARGETS, columns=TARGETS, dtype=float)
        for t1, t2 in [(t1, t2) for t1 in TARGETS for t2 in TARGETS]:
            g1 = group_summs[(exp, t1)].set_index("group")["normalized_group_importance"]
            g2 = group_summs[(exp, t2)].set_index("group")["normalized_group_importance"]
            vals1 = [float(g1.get(g, 0)) for g in groups]
            vals2 = [float(g2.get(g, 0)) for g in groups]
            grp_mat.loc[t1, t2] = rho(vals1, vals2)
        grp_mat.to_csv(IN_DIR / f"cross_target_group_corr_{label}.csv")
    print("  Saved cross-target correlation matrices", flush=True)

    # Print summaries
    for exp in EXPS:
        label = exp.split("_")[1].upper()
        print(f"\n  Cross-target predictor rank ρ ({label}):")
        print(pd.read_csv(IN_DIR / f"cross_target_pred_corr_{label.lower()}.csv", index_col=0).to_string())

    # ── 5. CDF-vs-NoCDF comparison by target ──────────────────────────────────
    cdf_nocdf_rows = []
    for tgt in TARGETS:
        cdf_s   = summaries[("da_cdf",   tgt)]
        nocdf_s = summaries[("da_nocdf", tgt)]
        mm = pd.merge(cdf_s[["feature","rank_mean_abs_shap"]], nocdf_s[["feature","rank_mean_abs_shap"]], on="feature")
        r_pred = rho(mm["rank_mean_abs_shap_x"], mm["rank_mean_abs_shap_y"])
        t5  = overlap(cdf_s, nocdf_s, 5)
        t10 = overlap(cdf_s, nocdf_s, 10)
        cdf_g   = group_summs[("da_cdf",   tgt)].set_index("group")["normalized_group_importance"]
        nocdf_g = group_summs[("da_nocdf", tgt)].set_index("group")["normalized_group_importance"]
        g_vals_cdf   = [float(cdf_g.get(g,   0)) for g in groups]
        g_vals_nocdf = [float(nocdf_g.get(g,  0)) for g in groups]
        r_grp = rho(g_vals_cdf, g_vals_nocdf)
        cdf_nocdf_rows.append({
            "target": tgt, "predictor_rho": r_pred,
            "top5_overlap": t5, "top10_overlap": t10, "group_rho": r_grp,
        })
        print(f"  CDF vs NoCDF [{tgt}]: pred ρ={r_pred:.3f}  top5={t5}/5  top10={t10}/10  group ρ={r_grp:.3f}")

    cdf_nocdf_df = pd.DataFrame(cdf_nocdf_rows)
    cdf_nocdf_df.to_csv(IN_DIR / "cdf_nocdf_comparison.csv", index=False)

    # Per-group CDF/NoCDF/diff table
    diff_detail_rows = []
    for tgt in TARGETS:
        cdf_g   = group_summs[("da_cdf",   tgt)].set_index("group")["normalized_group_importance"]
        nocdf_g = group_summs[("da_nocdf", tgt)].set_index("group")["normalized_group_importance"]
        for g in groups:
            c = float(cdf_g.get(g, 0)); n = float(nocdf_g.get(g, 0))
            diff_detail_rows.append({"target": tgt, "group": g, "cdf": c, "nocdf": n, "cdf_minus_nocdf": c - n})
    pd.DataFrame(diff_detail_rows).to_csv(IN_DIR / "cdf_nocdf_group_detail.csv", index=False)
    print("  Saved CDF/NoCDF comparison", flush=True)

    # ── 6. DJF / JJA seasonal analysis ────────────────────────────────────────
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)
        for season, months in [("djf", [12, 1, 2]), ("jja", [6, 7, 8])]:
            sub  = df[df["month"].isin(months)]
            summ = get_summaries(sub, features)
            g    = get_group_imp(summ, fg, features)
            g.to_csv(IN_DIR / f"seasonal_{season}_group_{tag}.csv", index=False)
            summ.to_csv(IN_DIR / f"seasonal_{season}_predictor_{tag}.csv", index=False)
    print("  Saved seasonal analyses", flush=True)

    # ── 7. Spatial-fold stability ──────────────────────────────────────────────
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)
        fold_rows = []
        for fold in range(5):
            sub  = df[df["spatial_fold"] == fold]
            summ = get_summaries(sub, features)
            g    = get_group_imp(summ, fg, features)
            g["spatial_fold"] = fold
            fold_rows.append(g)
        fg_df = pd.concat(fold_rows)
        fg_df.to_csv(IN_DIR / f"spatial_fold_group_{tag}.csv", index=False)
        stab = (fg_df.groupby("group")["normalized_group_importance"]
                     .agg(["mean", "std", "min", "max"])
                     .reset_index())
        stab.to_csv(IN_DIR / f"spatial_stability_{tag}.csv", index=False)
    print("  Saved spatial-fold analyses", flush=True)

    # ── 8. Frozen dependence-predictor selection (top-3 per target) ───────────
    dep_dict = {}
    print("\n  Frozen dependence predictors:", flush=True)
    for tgt in TARGETS:
        cdf_s   = summaries[("da_cdf",   tgt)][["feature", "mean_abs_shap"]]
        nocdf_s = summaries[("da_nocdf", tgt)][["feature", "mean_abs_shap"]]
        mm = pd.merge(cdf_s, nocdf_s, on="feature", suffixes=("_cdf", "_nocdf"))
        mm["global_imp"] = (mm["mean_abs_shap_cdf"] + mm["mean_abs_shap_nocdf"]) / 2
        mm = mm.sort_values(["global_imp", "feature"], ascending=[False, True]).reset_index(drop=True)
        top3 = mm.head(3)["feature"].tolist()
        dep_dict[tgt] = top3
        print(f"    {tgt}: {top3}")

    with open(IN_DIR / "dependence_features.json", "w") as f:
        json.dump({
            "selection_rule": "top-3 by mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF) on identical support, ties by name ascending",
            "targets": dep_dict,
        }, f, indent=2)

    print("\nSummarisation complete.", flush=True)


if __name__ == "__main__":
    main()
