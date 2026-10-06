#!/usr/bin/env python
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

IN_DIR = Path("data/processed/modeling/xai/final_2020")

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
    out["normalized_group_importance"] = out["group_abs_importance"] / total if total > 0 else 0
    out["normalized_group_importance_pct"] = out["normalized_group_importance"] * 100
    out = out.sort_values("group_abs_importance", ascending=False).reset_index(drop=True)
    return out

def overlap(a, b):
    return len(set(a) & set(b))

def main():
    print("Summarising Final 2020 XAI...")

    with open("configs/xai/feature_groups.yaml") as f:
        feature_groups = yaml.safe_load(f)

    summaries = []
    group_summs = []
    
    out_dir = IN_DIR / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    (IN_DIR / "seasonal").mkdir(exist_ok=True)
    (IN_DIR / "spatial").mkdir(exist_ok=True)

    shap_files = list((IN_DIR / "shap").rglob("shap_*.parquet"))
    
    for shap_file in shap_files:
        df = pd.read_parquet(shap_file)
        # Parse name: shap_{block}_{experiment}_{target}_{support}_cohort.parquet
        name_parts = shap_file.stem.replace("shap_", "").replace("_cohort", "").split("_", 3)
        block = name_parts[0]
        exp_part1 = name_parts[1]
        exp_part2 = name_parts[2]
        # It's tricky to parse since experiment has _ (e.g., da_cdf), target has _, and support has _.
        # It's easier to just match from the filename components.
        base_name = shap_file.stem.replace("shap_", "")
        
        # We can extract from metadata or simply use the base name as model key.
        model_key = base_name.replace("_cohort", "")
        
        features = [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]
        
        summ = get_summaries(df, features)
        g_sum = get_group_importance(summ, feature_groups)
        
        summ["model_key"] = model_key
        g_sum["model_key"] = model_key
        
        feat_to_group = {f: g for g, fs in feature_groups.items() for f in fs}
        summ["feature_group"] = summ["feature"].map(feat_to_group).fillna("unmapped")
        
        summaries.append(summ)
        group_summs.append(g_sum)
        
        # SHAP vs Permutation
        perm_file = IN_DIR / "permutation" / f"permutation_{base_name}.json"
        with open(perm_file) as f_perm:
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
        
        with open(out_dir / f"robustness_{model_key}.json", "w") as f:
            json.dump({
                "spearman_rho": float(rho),
                "top5_overlap": t5,
                "top10_overlap": t10
            }, f, indent=2)
            
        # Seasonal DJF/JJA
        for season, months in [("djf", [12, 1, 2]), ("jja", [6, 7, 8])]:
            sub = df[df["month"].isin(months)]
            if len(sub) > 0:
                s = get_summaries(sub, features)
                g = get_group_importance(s, feature_groups)
                s.to_csv(IN_DIR / "seasonal" / f"seasonal_{season}_predictor_{model_key}.csv", index=False)
                g.to_csv(IN_DIR / "seasonal" / f"seasonal_{season}_group_{model_key}.csv", index=False)
                
        # Spatial-fold stability
        fold_rows = []
        for fold in df["spatial_fold"].dropna().unique():
            sub = df[df["spatial_fold"] == fold]
            if len(sub) > 0:
                s = get_summaries(sub, features)
                g = get_group_importance(s, feature_groups)
                g["spatial_fold"] = fold
                fold_rows.append(g)
        if fold_rows:
            fg = pd.concat(fold_rows)
            stab = (fg.groupby("group")["normalized_group_importance"]
                      .agg(["mean", "std", "min", "max"])
                      .reset_index())
            stab.to_csv(IN_DIR / "spatial" / f"spatial_stability_{model_key}.csv", index=False)
            
    pd.concat(summaries).to_csv(out_dir / "tidy_predictor_summary.csv", index=False)
    pd.concat(group_summs).to_csv(out_dir / "tidy_group_summary.csv", index=False)
    
    # Matched SOURCE comparison
    df_summ = pd.concat(summaries)
    df_grp = pd.concat(group_summs)
    
    cdf_key = "SOURCE_da_cdf_daily_absolute_increment_matched_support"
    nocdf_key = "SOURCE_da_nocdf_daily_absolute_increment_matched_support"
    
    if cdf_key in df_summ["model_key"].values and nocdf_key in df_summ["model_key"].values:
        cdf_s = df_summ[df_summ["model_key"] == cdf_key]
        nocdf_s = df_summ[df_summ["model_key"] == nocdf_key]
        
        m_pred = pd.merge(cdf_s, nocdf_s, on="feature", suffixes=("_cdf", "_nocdf"))
        rho_matched, _ = spearmanr(m_pred["rank_mean_abs_shap_cdf"], m_pred["rank_mean_abs_shap_nocdf"])
        t5_m = overlap(cdf_s.head(5)["feature"], nocdf_s.head(5)["feature"])
        t10_m = overlap(cdf_s.head(10)["feature"], nocdf_s.head(10)["feature"])
        
        cdf_g = df_grp[df_grp["model_key"] == cdf_key]
        nocdf_g = df_grp[df_grp["model_key"] == nocdf_key]
        m_grp = pd.merge(cdf_g, nocdf_g, on="group", suffixes=("_cdf", "_nocdf"))
        rho_g, _ = spearmanr(m_grp["normalized_group_importance_cdf"], m_grp["normalized_group_importance_nocdf"])
        
        m_grp["difference_cdf_minus_nocdf"] = (
            m_grp["normalized_group_importance_cdf"] - m_grp["normalized_group_importance_nocdf"]
        )
        m_grp.to_csv(out_dir / "source_matched_group_comparison.csv", index=False)
        
        with open(out_dir / "source_matched_comparison_stats.json", "w") as f:
            json.dump({
                "predictor_rho": float(rho_matched),
                "top5_overlap": t5_m,
                "top10_overlap": t10_m,
                "group_rho": float(rho_g)
            }, f, indent=2)
            
    print("Summarisation complete.")

if __name__ == "__main__":
    main()
