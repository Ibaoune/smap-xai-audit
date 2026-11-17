#!/usr/bin/env python3
"""
build_rf_eval_metrics.py
========================
Extracts and standardizes regression metrics for Random Forest evaluation:
1. 2019 Temporal Validation (Train: 2016-2018, Valid: 2019)
2. Five-fold Spatial-Block Cross-Validation (2016-2019 spatial blocks)
3. Independent 2020 Holdout (Train: 2016-2019, Test: 2020)
4. Supplementary 2020 Metrics Table (Table S2)

Provenance:
- 2019 Validation: reports/modeling/models/random_forest/rf03b/
  * rf03b_source_matched_metrics.csv
  * rf03b_primary_metrics.csv
- Spatial CV: reports/modeling/models/random_forest/rf03_spatial/
  * rf03_spatial_source_fold_metrics.csv
  * rf03_spatial_transfer_fold_metrics.csv
  * rf03_spatial_value_fold_metrics.csv
- 2020 Holdout: reports/modeling/final_2020/final_metrics_2020.csv

All metrics use standard regression formulas (R², Pearson r, MAE, RMSE, Bias).
Direct CDF-NoCDF comparison on SOURCE uses matched-support models.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Canonical target ordering and naming
TARGET_ORDER = ["SOURCE", "RZSM", "ET", "Surface runoff", "Baseflow", "VALUE"]

EXP_MAP = {
    "da_cdf": "CDF",
    "da_nocdf": "NoCDF",
    "CDF": "CDF",
    "NoCDF": "NoCDF"
}

RAW_TARGET_MAP = {
    "daily_absolute_increment": "SOURCE",
    "delta_rzsm": "RZSM",
    "delta_et": "ET",
    "delta_surface_runoff": "Surface runoff",
    "delta_baseflow": "Baseflow",
    "value_ae": "VALUE"
}

def resolve_paths(repo_root=None):
    if repo_root is None:
        # Determine from current script location or cwd
        current = Path.cwd()
        if (current / "reports" / "modeling").exists():
            repo_root = current
        else:
            repo_root = Path(__file__).resolve().parents[5]
    out_dir = repo_root / "figures" / "manuscript" / "rf" / "rf_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    return repo_root, out_dir

def build_2019_temporal_validation(repo_root, out_dir):
    src_matched_p = repo_root / "reports" / "modeling" / "models" / "random_forest" / "rf03b" / "rf03b_source_matched_metrics.csv"
    primary_p = repo_root / "reports" / "modeling" / "models" / "random_forest" / "rf03b" / "rf03b_primary_metrics.csv"

    if not src_matched_p.exists() or not primary_p.exists():
        raise FileNotFoundError("Missing RF03B metrics files in reports/modeling/models/random_forest/rf03b/")

    df_src = pd.read_csv(src_matched_p)
    df_prim = pd.read_csv(primary_p)

    # Exclude native support for SOURCE to guarantee matched-sample comparison
    df_prim_filtered = df_prim[df_prim["block"] != "SOURCE"].copy()

    df_all = pd.concat([df_src, df_prim_filtered], ignore_index=True)

    rows = []
    for _, r in df_all.iterrows():
        tgt = RAW_TARGET_MAP.get(r["target"], r["target"])
        exp = EXP_MAP.get(r["experiment"], r["experiment"])
        rows.append({
            "target": tgt,
            "experiment": exp,
            "n": int(r["N_validation"]),
            "mae": float(r["MAE"]),
            "rmse": float(r["RMSE"]),
            "bias": float(r["bias"]),
            "r2": float(r["R2"]),
            "pearson_r": float(r["Pearson"])
        })

    df_2019 = pd.DataFrame(rows)

    # Ensure canonical sort order
    df_2019["sort_key"] = df_2019["target"].map(lambda x: TARGET_ORDER.index(x) if x in TARGET_ORDER else 99)
    df_2019 = df_2019.sort_values(by=["sort_key", "experiment"]).drop(columns=["sort_key"]).reset_index(drop=True)

    out_csv = out_dir / "Figure4_2019_temporal_validation_metrics.csv"
    df_2019.to_csv(out_csv, index=False)
    print(f"[✓] Saved 2019 temporal validation metrics to {out_csv} ({len(df_2019)} records)")
    return df_2019

def build_spatial_block_cv(repo_root, out_dir):
    spatial_dir = repo_root / "reports" / "modeling" / "models" / "random_forest" / "rf03_spatial"
    files = {
        "SOURCE": spatial_dir / "rf03_spatial_source_fold_metrics.csv",
        "RZSM": spatial_dir / "rf03_spatial_transfer_fold_metrics.csv",
        "VALUE": spatial_dir / "rf03_spatial_value_fold_metrics.csv"
    }

    fold_rows = []
    for tgt_name, fpath in files.items():
        if not fpath.exists():
            raise FileNotFoundError(f"Missing spatial CV file: {fpath}")
        df_fold = pd.read_csv(fpath)
        for _, r in df_fold.iterrows():
            exp = EXP_MAP.get(r["experiment"], r["experiment"])
            fold_rows.append({
                "target": tgt_name,
                "experiment": exp,
                "fold": str(r["fold"]),
                "n_train": int(r["N_train"]),
                "n_valid": int(r["N_validation"]),
                "mae": float(r["MAE"]),
                "rmse": float(r["RMSE"]),
                "bias": float(r["bias"]),
                "r2": float(r["R2"]),
                "pearson_r": float(r["Pearson"])
            })

    df_folds = pd.DataFrame(fold_rows)
    df_folds["sort_key"] = df_folds["target"].map(lambda x: TARGET_ORDER.index(x) if x in TARGET_ORDER else 99)
    df_folds = df_folds.sort_values(by=["sort_key", "experiment", "fold"]).drop(columns=["sort_key"]).reset_index(drop=True)

    out_folds_csv = out_dir / "Figure4_spatial_block_cv_metrics.csv"
    df_folds.to_csv(out_folds_csv, index=False)
    print(f"[✓] Saved spatial block fold metrics to {out_folds_csv} ({len(df_folds)} records)")

    # Compute summary across 5 folds
    summary_rows = []
    for (tgt, exp), grp in df_folds.groupby(["target", "experiment"]):
        summary_rows.append({
            "target": tgt,
            "experiment": exp,
            "mean_r2": float(grp["r2"].mean()),
            "sd_r2": float(grp["r2"].std(ddof=1)),
            "mean_r": float(grp["pearson_r"].mean()),
            "sd_r": float(grp["pearson_r"].std(ddof=1)),
            "mean_mae": float(grp["mae"].mean()),
            "sd_mae": float(grp["mae"].std(ddof=1)),
            "mean_rmse": float(grp["rmse"].mean()),
            "sd_rmse": float(grp["rmse"].std(ddof=1))
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary["sort_key"] = df_summary["target"].map(lambda x: TARGET_ORDER.index(x) if x in TARGET_ORDER else 99)
    df_summary = df_summary.sort_values(by=["sort_key", "experiment"]).drop(columns=["sort_key"]).reset_index(drop=True)

    out_summary_csv = out_dir / "Figure4_spatial_block_cv_summary.csv"
    df_summary.to_csv(out_summary_csv, index=False)
    print(f"[✓] Saved spatial block summary to {out_summary_csv} ({len(df_summary)} records)")
    return df_folds, df_summary

def build_2020_holdout(repo_root, out_dir):
    final_p = repo_root / "reports" / "modeling" / "final_2020" / "final_metrics_2020.csv"
    if not final_p.exists():
        raise FileNotFoundError(f"Missing final 2020 metrics file: {final_p}")

    df_raw = pd.read_csv(final_p)

    # Exclude native support for SOURCE to keep strictly matched SOURCE models
    df_filtered = df_raw[~((df_raw["block"] == "SOURCE") & (df_raw["support"] == "native_support"))].copy()

    rows = []
    for _, r in df_filtered.iterrows():
        tgt = RAW_TARGET_MAP.get(r["target"], r["target"])
        exp = EXP_MAP.get(r["experiment"], r["experiment"])
        rows.append({
            "target": tgt,
            "experiment": exp,
            "n": int(r["N"]),
            "mae": float(r["MAE"]),
            "rmse": float(r["RMSE"]),
            "bias": float(r["bias"]),
            "r2": float(r["R2"]),
            "pearson_r": float(r["pearson_r"])
        })

    df_2020 = pd.DataFrame(rows)
    df_2020["sort_key"] = df_2020["target"].map(lambda x: TARGET_ORDER.index(x) if x in TARGET_ORDER else 99)
    df_2020 = df_2020.sort_values(by=["sort_key", "experiment"]).drop(columns=["sort_key"]).reset_index(drop=True)

    out_2020_csv = out_dir / "Figure4_2020_holdout_metrics.csv"
    df_2020.to_csv(out_2020_csv, index=False)
    print(f"[✓] Saved 2020 holdout metrics to {out_2020_csv} ({len(df_2020)} records)")

    # Build Supplementary Table S2
    table_s2 = df_2020.rename(columns={
        "target": "Target",
        "experiment": "Experiment",
        "n": "N",
        "mae": "MAE",
        "rmse": "RMSE",
        "bias": "Bias",
        "r2": "R²",
        "pearson_r": "Pearson r"
    })
    table_s2_csv = out_dir / "TableS2_RF_2020_metrics.csv"
    table_s2.to_csv(table_s2_csv, index=False)
    print(f"[✓] Saved Table S2 (RF 2020 metrics) to {table_s2_csv} ({len(table_s2)} records)")

    return df_2020, table_s2

def run_qc_checks(df_2019, df_folds, df_summary, df_2020):
    print("\n--- Running Automated QC Checks ---")
    # Check 1: 12 combinations in 2019 and 2020
    assert len(df_2019) == 12, f"Expected 12 records in 2019, got {len(df_2019)}"
    assert len(df_2020) == 12, f"Expected 12 records in 2020, got {len(df_2020)}"

    # Check 2: Matched SOURCE sample counts
    src_2019 = df_2019[df_2019["target"] == "SOURCE"]
    assert src_2019["n"].nunique() == 1, "SOURCE 2019 matched counts do not match!"
    src_2020 = df_2020[df_2020["target"] == "SOURCE"]
    assert src_2020["n"].nunique() == 1, "SOURCE 2020 matched counts do not match!"
    print(f"[QC PASS] Matched SOURCE N counts verified: 2019 N={src_2019['n'].iloc[0]}, 2020 N={src_2020['n'].iloc[0]}")

    # Check 3: Finite values
    for name, df in [("2019", df_2019), ("2020", df_2020), ("Folds", df_folds), ("Summary", df_summary)]:
        assert not df.isna().any().any(), f"NaN values detected in {name} dataset!"
        assert not np.isinf(df.select_dtypes(include=np.number)).any().any(), f"Inf values detected in {name} dataset!"
    print("[QC PASS] Zero NaN/Inf values confirmed across all tables.")

    # Check 4: Positive / Realistic metric ranges
    assert (df_2019["r2"] >= -1.0).all() and (df_2019["r2"] <= 1.0).all(), "R² outside valid range in 2019"
    assert (df_2020["r2"] >= -1.0).all() and (df_2020["r2"] <= 1.0).all(), "R² outside valid range in 2020"
    assert (df_2019["pearson_r"] >= -1.0).all() and (df_2019["pearson_r"] <= 1.0).all(), "Pearson r outside [-1, 1] in 2019"
    assert (df_2020["pearson_r"] >= -1.0).all() and (df_2020["pearson_r"] <= 1.0).all(), "Pearson r outside [-1, 1] in 2020"
    print("[QC PASS] Metric ranges validated within valid mathematical bounds.")

    print("All QC checks passed successfully!\n")

def main():
    repo_root, out_dir = resolve_paths()
    print(f"Building RF evaluation metrics in: {out_dir}")
    df_2019 = build_2019_temporal_validation(repo_root, out_dir)
    df_folds, df_summary = build_spatial_block_cv(repo_root, out_dir)
    df_2020, table_s2 = build_2020_holdout(repo_root, out_dir)
    run_qc_checks(df_2019, df_folds, df_summary, df_2020)

if __name__ == "__main__":
    main()
