import pandas as pd
import numpy as np
import os
import json
import yaml
from pathlib import Path

def load_feature_groups():
    with open("configs/xai/feature_groups.yaml", "r") as f:
        groups = yaml.safe_load(f)
    feat_to_group = {}
    for g, feats in groups.items():
        for feat in feats:
            feat_to_group[feat] = g
    return feat_to_group

def get_group_importances(shap_df, feat_to_group):
    # Calculate mean absolute SHAP for each feature
    # shap_df columns: feature names containing SHAP values
    mean_abs_shap = shap_df.abs().mean()
    
    # Group and sum
    group_imp = {}
    for feat, imp in mean_abs_shap.items():
        g = feat_to_group.get(feat, "other")
        group_imp[g] = group_imp.get(g, 0) + imp
        
    # Normalize
    total_imp = sum(group_imp.values())
    if total_imp == 0:
        return {g: 0.0 for g in group_imp}
    
    return {g: v / total_imp for g, v in group_imp.items()}

def classify_dependence(x, y):
    # Heuristics for classifying the relationship
    # x: predictor, y: SHAP values
    if len(x) == 0:
        return "weak", "No data"
        
    x_std = x.std()
    y_std = y.std()
    
    if y_std < 1e-4:
        return "approximately flat", "very small SHAP amplitude"
        
    from scipy.stats import spearmanr
    rho, pval = spearmanr(x, y)
    
    if abs(rho) > 0.6:
        direction = "positive" if rho > 0 else "negative"
        return "clearly informative monotonic", f"strong {direction} correlation (rho={rho:.2f})"
    elif abs(rho) > 0.3:
        return "informative nonlinear", f"moderate correlation (rho={rho:.2f}) with dispersion"
    else:
        # Check if it has non-linear variance
        if y_std > 0.01:
            return "heterogeneous / no simple global relationship", f"strong dispersion at similar predictor values, low rho ({rho:.2f})"
        else:
            return "weak", f"low amplitude and correlation (rho={rho:.2f})"

def main():
    feat_to_group = load_feature_groups()
    
    # ---------------------------------------------------------
    # A. Target Distributions
    # ---------------------------------------------------------
    td_path = "reports/modeling/final_2020/target_distributions/target_distributions_2020.csv"
    td_out_path = "reports/modeling/final_2020/target_distributions/final_target_distributions_2020.csv"
    
    df_td = pd.read_csv(td_path)
    # Rename columns
    df_td = df_td.rename(columns={
        "fraction_lt_0": "fraction_negative",
        "fraction_eq_0": "fraction_zero",
        "fraction_gt_0": "fraction_positive"
    })
    # For SOURCE, set fractions to NA
    mask_source = df_td["block"] == "SOURCE"
    df_td.loc[mask_source, ["fraction_negative", "fraction_zero", "fraction_positive"]] = np.nan
    df_td.to_csv(td_out_path, index=False)
    
    # ---------------------------------------------------------
    # Process SHAP cohorts for B, C, D
    # ---------------------------------------------------------
    shap_dir = Path("data/processed/modeling/xai/final_2020/shap")
    
    seasonal_rows = []
    spatial_rows = []
    dep_rows = []
    
    # Frozen dependence lists
    dep_targets = {
        "SOURCE": ["ssm_lag1", "precip_lag1", "rzsm_lag1", "land_cover_fraction_16"],
        "TRANSFER_delta_rzsm": ["rzsm_opl_lag1", "ssm_opl_lag1", "baseflow_opl_lag1"],
        "TRANSFER_delta_et": ["et_opl_lag1", "ssm_opl_lag1", "source_signed_increment_pre7d_sum"],
        "TRANSFER_delta_surface_runoff": ["precip_t", "land_cover_fraction_16", "soil_texture_fraction_6"],
        "TRANSFER_delta_baseflow": ["baseflow_opl_lag1", "land_cover_fraction_16", "rzsm_opl_lag1"],
        "VALUE": ["ssm_opl_lag1", "et_opl_lag1", "tair_t", "land_cover_fraction_16"]
    }
    
    # Collect all cohort JSONs
    cohort_dir = Path("data/processed/modeling/xai/final_2020/cohorts")
    
    models = [
        ("SOURCE", "da_cdf", "daily_absolute_increment", "matched_support"),
        ("SOURCE", "da_nocdf", "daily_absolute_increment", "matched_support"),
        ("TRANSFER", "da_cdf", "delta_rzsm", "native_support"),
        ("TRANSFER", "da_cdf", "delta_et", "native_support"),
        ("TRANSFER", "da_cdf", "delta_surface_runoff", "native_support"),
        ("TRANSFER", "da_cdf", "delta_baseflow", "native_support"),
        ("TRANSFER", "da_nocdf", "delta_rzsm", "native_support"),
        ("TRANSFER", "da_nocdf", "delta_et", "native_support"),
        ("TRANSFER", "da_nocdf", "delta_surface_runoff", "native_support"),
        ("TRANSFER", "da_nocdf", "delta_baseflow", "native_support"),
        ("VALUE", "da_cdf", "value_ae", "native_support"),
        ("VALUE", "da_nocdf", "value_ae", "native_support")
    ]
    
    for block, exp, target, support in models:
        key = f"{block}_{exp}_{target}_{support}"
        shap_file = shap_dir / f"shap_{key}_cohort.parquet"
        
        if not shap_file.exists():
            print(f"Missing SHAP file: {shap_file}")
            continue
            
        shap_df_full = pd.read_parquet(shap_file)
        
        # Extract shap columns
        shap_cols = [c for c in shap_df_full.columns if c.startswith("shap__")]
        shap_df = shap_df_full[shap_cols].rename(columns=lambda x: x.replace("shap__", ""))
        
        df_subset = shap_df_full

                
        # B. SEASONAL
        # DJF = 12, 1, 2. JJA = 6, 7, 8
        if "month" in df_subset.columns:
            mask_djf = df_subset["month"].isin([12, 1, 2])
            mask_jja = df_subset["month"].isin([6, 7, 8])
            
            djf_shap = shap_df[mask_djf.values]
            jja_shap = shap_df[mask_jja.values]
            
            djf_imp = get_group_importances(djf_shap, feat_to_group)
            jja_imp = get_group_importances(jja_shap, feat_to_group)
            
            all_groups = set(djf_imp.keys()).union(set(jja_imp.keys()))
            for g in all_groups:
                djf_val = djf_imp.get(g, 0.0)
                jja_val = jja_imp.get(g, 0.0)
                seasonal_rows.append({
                    "model_key": key,
                    "block": block,
                    "experiment": exp,
                    "target": target,
                    "group": g,
                    "DJF_normalized_importance": djf_val,
                    "JJA_normalized_importance": jja_val,
                    "DJF_minus_JJA": djf_val - jja_val
                })
                
        # C. SPATIAL
        if "spatial_fold" in df_subset.columns:
            folds = sorted(df_subset["spatial_fold"].unique())
            group_fold_imps = {g: [] for g in set(feat_to_group.values())}
            
            for fold in folds:
                mask_fold = df_subset["spatial_fold"] == fold
                fold_shap = shap_df[mask_fold.values]
                fold_imp = get_group_importances(fold_shap, feat_to_group)
                for g in group_fold_imps.keys():
                    group_fold_imps[g].append(fold_imp.get(g, 0.0))
                    
            for g, imps in group_fold_imps.items():
                if len(imps) > 0:
                    spatial_rows.append({
                        "model_key": key,
                        "block": block,
                        "experiment": exp,
                        "target": target,
                        "group": g,
                        "mean": np.mean(imps),
                        "std": np.std(imps),
                        "min": np.min(imps),
                        "max": np.max(imps)
                    })
                    
        # D. DEPENDENCE
        if block == "SOURCE":
            dep_list = dep_targets["SOURCE"]
        elif block == "TRANSFER":
            dep_list = dep_targets[f"TRANSFER_{target}"]
        elif block == "VALUE":
            dep_list = dep_targets["VALUE"]
            
        for feat in dep_list:
            if f"value__{feat}" in df_subset.columns and feat in shap_df.columns:
                x = df_subset[f"value__{feat}"].values
                y = shap_df[feat].values
                cls, note = classify_dependence(x, y)
                dep_rows.append({
                    "model_key": key,
                    "block": block,
                    "experiment": exp,
                    "target": target,
                    "predictor": feat,
                    "classification": cls,
                    "evidence_note": note
                })
                
    # Save summaries
    df_seasonal = pd.DataFrame(seasonal_rows)
    df_seasonal.to_csv("data/processed/modeling/xai/final_2020/summaries/seasonal_group_summary_2020.csv", index=False)
    
    df_spatial = pd.DataFrame(spatial_rows)
    df_spatial.to_csv("data/processed/modeling/xai/final_2020/summaries/spatial_group_stability_2020.csv", index=False)
    
    df_dep = pd.DataFrame(dep_rows)
    df_dep.to_csv("data/processed/modeling/xai/final_2020/summaries/dependence_summary_2020.csv", index=False)
    
if __name__ == "__main__":
    main()
