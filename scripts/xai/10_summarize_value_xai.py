#!/usr/bin/env python
"""
RF-04B-VALUE: Summarise TreeSHAP outputs for both VALUE models.

Produces under data/processed/modeling/xai/outputs/value/:
  target_distribution.csv
  tidy_predictor_summary.csv
  tidy_group_summary.csv
  cdf_nocdf_comparison.csv
  cdf_nocdf_group_detail.csv
  seasonal_djf_group_<exp>.csv / seasonal_jja_group_<exp>.csv
  seasonal_djf_predictor_<exp>.csv / seasonal_jja_predictor_<exp>.csv
  seasonal_target_<exp>.csv
  spatial_fold_group_<exp>.csv
  spatial_stability_<exp>.csv
  sign_split_summary.csv
  dependence_features.json

2020 SEALED.
"""
import json
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from scipy.stats import spearmanr

IN_DIR          = Path("data/processed/modeling/xai/outputs/value")
EXPS            = ["da_cdf", "da_nocdf"]
TARGET          = "value_ae"
SPATIAL_ID_COLS = ["gleam_y_index", "gleam_x_index"]


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
    out   = pd.DataFrame(rows)
    total = out["group_abs_importance"].sum()
    out["normalized_group_importance"] = out["group_abs_importance"] / (total if total > 0 else 1)
    return out.sort_values("group_abs_importance", ascending=False).reset_index(drop=True)


def rho(a, b):
    r, _ = spearmanr(a, b)
    return float(r)


def overlap(s1, s2, n):
    return len(set(s1.head(n)["feature"]) & set(s2.head(n)["feature"]))


def target_stats(vals, label, season=None):
    row = {
        "experiment":    label,
        "n":             int(len(vals)),
        "mean":          float(np.mean(vals)),
        "median":        float(np.median(vals)),
        "std":           float(np.std(vals)),
        "p05":           float(np.percentile(vals, 5)),
        "p25":           float(np.percentile(vals, 25)),
        "p75":           float(np.percentile(vals, 75)),
        "p95":           float(np.percentile(vals, 95)),
        "frac_positive": float(np.mean(vals > 0)),
        "frac_negative": float(np.mean(vals < 0)),
        "frac_zero":     float(np.mean(vals == 0)),
    }
    if season:
        row["season"] = season
    return row


def main():
    print("Summarising VALUE XAI...", flush=True)
    fg      = load_fg()
    groups  = list(fg.keys())
    summaries   = {}
    group_summs = {}
    all_features = None

    # ── 1. Per-model summaries + SHAP-vs-perm ─────────────────────────────────
    for exp in EXPS:
        tag  = f"{exp}_{TARGET}"
        df   = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)
        if all_features is None:
            all_features = set(features)
        else:
            assert set(features) == all_features, f"Feature set mismatch for {tag}!"

        summ  = get_summaries(df, features)
        g_sum = get_group_imp(summ, fg, features)

        feat_to_group = {f: g for g, fs in fg.items() for f in fs}
        summ["feature_group"] = summ["feature"].map(feat_to_group).fillna("unmapped")
        assert (summ["feature_group"] == "unmapped").sum() == 0, f"Unmapped features in {tag}"
        summ["experiment"]  = exp
        g_sum["experiment"] = exp
        summaries[exp]   = summ
        group_summs[exp] = g_sum

        # SHAP vs permutation
        with open(IN_DIR / f"permutation_{tag}.json") as f:
            perm = json.load(f)
        perm_df = (
            pd.DataFrame({"feature": perm["features"], "perm_imp": perm["importances_mean"]})
              .sort_values("perm_imp", ascending=False).reset_index(drop=True)
        )
        perm_df["perm_rank"] = perm_df.index + 1
        mm  = pd.merge(
            summ[["feature", "rank_mean_abs_shap"]],
            perm_df[["feature", "perm_rank"]], on="feature"
        )
        r_perm  = rho(mm["rank_mean_abs_shap"], mm["perm_rank"])
        t5_perm = overlap(summ, perm_df.rename(columns={"perm_rank": "rank_mean_abs_shap"}), 5)
        t10_perm = overlap(summ, perm_df.rename(columns={"perm_rank": "rank_mean_abs_shap"}), 10)
        print(
            f"  [{exp}] SHAP vs Perm: ρ={r_perm:.3f}  top5={t5_perm}/5  top10={t10_perm}/10",
            flush=True,
        )

    # ── 2. Target distribution (2019 global) ──────────────────────────────────
    dist_rows = []
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        dist_rows.append(target_stats(df["target"].values, exp))
    pd.DataFrame(dist_rows).to_csv(IN_DIR / "target_distribution.csv", index=False)
    for r in dist_rows:
        print(
            f"  [{r['experiment']}] value_ae: n={r['n']}  mean={r['mean']:.4f}  "
            f"med={r['median']:.4f}  std={r['std']:.4f}  "
            f"p05={r['p05']:.4f}  p95={r['p95']:.4f}  "
            f"frac>0={r['frac_positive']:.3f}  frac<0={r['frac_negative']:.3f}",
            flush=True,
        )

    # ── 3. Save tidy tables ────────────────────────────────────────────────────
    pd.concat(summaries.values()).to_csv(IN_DIR / "tidy_predictor_summary.csv", index=False)
    pd.concat(group_summs.values()).to_csv(IN_DIR / "tidy_group_summary.csv", index=False)
    print("  Saved tidy summaries", flush=True)

    # ── 4. CDF vs NoCDF comparison ────────────────────────────────────────────
    cdf_s   = summaries["da_cdf"]
    nocdf_s = summaries["da_nocdf"]
    mm = pd.merge(
        cdf_s[["feature","rank_mean_abs_shap"]],
        nocdf_s[["feature","rank_mean_abs_shap"]],
        on="feature", suffixes=("_cdf","_nocdf"),
    )
    r_pred = rho(mm["rank_mean_abs_shap_cdf"], mm["rank_mean_abs_shap_nocdf"])
    t5   = overlap(cdf_s, nocdf_s, 5)
    t10  = overlap(cdf_s, nocdf_s, 10)
    cdf_g   = group_summs["da_cdf"].set_index("group")["normalized_group_importance"]
    nocdf_g = group_summs["da_nocdf"].set_index("group")["normalized_group_importance"]
    g_c  = [float(cdf_g.get(g, 0)) for g in groups]
    g_n  = [float(nocdf_g.get(g, 0)) for g in groups]
    r_grp = rho(g_c, g_n)
    print(
        f"  CDF vs NoCDF: pred ρ={r_pred:.3f}  top5={t5}/5  top10={t10}/10  group ρ={r_grp:.3f}",
        flush=True,
    )
    pd.DataFrame([{
        "predictor_rho": r_pred, "top5_overlap": t5,
        "top10_overlap": t10,   "group_rho": r_grp,
    }]).to_csv(IN_DIR / "cdf_nocdf_comparison.csv", index=False)

    detail_rows = []
    for g in groups:
        c = float(cdf_g.get(g, 0)); n = float(nocdf_g.get(g, 0))
        detail_rows.append({"group": g, "cdf": c, "nocdf": n, "cdf_minus_nocdf": c - n})
    pd.DataFrame(detail_rows).to_csv(IN_DIR / "cdf_nocdf_group_detail.csv", index=False)

    # ── 5. Seasonal analysis ───────────────────────────────────────────────────
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)
        seasonal_tgt = []
        for season, months in [("djf", [12,1,2]), ("jja", [6,7,8])]:
            sub  = df[df["month"].isin(months)]
            summ = get_summaries(sub, features)
            g    = get_group_imp(summ, fg, features)
            g.to_csv(IN_DIR / f"seasonal_{season}_group_{exp}.csv", index=False)
            summ.to_csv(IN_DIR / f"seasonal_{season}_predictor_{exp}.csv", index=False)
            seasonal_tgt.append(target_stats(sub["target"].values, exp, season=season))
        pd.DataFrame(seasonal_tgt).to_csv(IN_DIR / f"seasonal_target_{exp}.csv", index=False)
    print("  Saved seasonal analyses", flush=True)

    # ── 6. Spatial-fold stability ──────────────────────────────────────────────
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
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
        fg_df.to_csv(IN_DIR / f"spatial_fold_group_{exp}.csv", index=False)
        stab = (fg_df.groupby("group")["normalized_group_importance"]
                    .agg(["mean","std","min","max"]).reset_index())
        stab.to_csv(IN_DIR / f"spatial_stability_{exp}.csv", index=False)
    print("  Saved spatial-fold analyses", flush=True)

    # ── 7. Sign-based descriptive split (same SHAP cohort, descriptive only) ──
    sign_rows = []
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = get_features(df)
        for sign_label, mask in [
            ("positive_value_ae", df["target"] > 0),
            ("negative_value_ae", df["target"] < 0),
        ]:
            sub  = df[mask]
            if len(sub) < 10:
                continue
            summ = get_summaries(sub, features)
            g    = get_group_imp(summ, fg, features)
            for _, row in g.iterrows():
                sign_rows.append({
                    "experiment":                    exp,
                    "sign_split":                    sign_label,
                    "n_rows":                        int(mask.sum()),
                    "group":                         row["group"],
                    "normalized_group_importance":   row["normalized_group_importance"],
                })
    pd.DataFrame(sign_rows).to_csv(IN_DIR / "sign_split_summary.csv", index=False)
    print("  Saved sign-based descriptive summaries", flush=True)

    # ── 8. Frozen top-4 dependence predictor selection ────────────────────────
    cdf_s   = summaries["da_cdf"][["feature","mean_abs_shap"]]
    nocdf_s = summaries["da_nocdf"][["feature","mean_abs_shap"]]
    mm = pd.merge(cdf_s, nocdf_s, on="feature", suffixes=("_cdf","_nocdf"))
    mm["global_imp"] = (mm["mean_abs_shap_cdf"] + mm["mean_abs_shap_nocdf"]) / 2
    mm = mm.sort_values(["global_imp","feature"], ascending=[False,True]).reset_index(drop=True)
    top4 = mm.head(4)["feature"].tolist()
    print(f"\n  Frozen top-4 dependence predictors: {top4}", flush=True)
    with open(IN_DIR / "dependence_features.json", "w") as f:
        json.dump({
            "selection_rule": (
                "top-4 by mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF) on identical support, "
                "ties by feature name ascending"
            ),
            "top_4_dependence_features": top4,
        }, f, indent=2)

    print("\nVALUE summarisation complete.", flush=True)


if __name__ == "__main__":
    main()
