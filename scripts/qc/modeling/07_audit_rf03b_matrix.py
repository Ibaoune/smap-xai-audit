#!/usr/bin/env python
import json
import pandas as pd
from pathlib import Path
import argparse
import glob

def audit_rf03b(workspace_root="."):
    base = Path(workspace_root) / "reports" / "modeling" / "models" / "random_forest"
    out_dir = base / "rf03b"
    out_dir.mkdir(exist_ok=True)

    # Expected primary matrix:
    # SOURCE: CDF native, NoCDF native, CDF matched, NoCDF matched
    # VALUE: CDF native, NoCDF native
    # TRANSFER: CDF native x 4, NoCDF native x 4
    # Total = 4 + 2 + 8 = 14

    all_runs = []

    # Find all fold_3 models that are part of rf03b (using support_mode format)
    # The run names ended with `_{candidate}_fold_3_{support_mode}`
    # Example: SOURCE_da_cdf_daily_absolute_increment_context_only_feature_set_RF_A_fold_3_native_support
    pattern = str(base / "*_fold_3_*_support" / "metadata.json")
    meta_files = glob.glob(pattern)

    for mf in meta_files:
        with open(mf, "r") as f:
            meta = json.load(f)

        assert meta["model_family"] == "random_forest"
        assert meta["CONDA_DEFAULT_ENV"] == "smap-xai-audit"
        assert meta["fold"] == "fold_3"
        assert meta["model_file_size"] > 0, f"Model file must be saved for {mf}"

        # Isolation check
        assert meta["validation_end"].startswith("2019"), f"Val end must be 2019, got {meta['validation_end']}"
        assert meta["train_start"] == "2016-01-08"
        assert meta["train_end"] == "2018-12-31"
        assert meta["validation_start"] == "2019-01-01"
        assert meta["validation_end"] == "2019-12-31"

        target = meta["target"]
        assert target not in meta["fitted_features"], f"Leakage: target in features!"

        row = {
            "model_family": meta["model_family"],
            "block": meta["block"],
            "experiment": meta["experiment"],
            "target": meta["target"],
            "feature_set": meta["feature_set"],
            "support_mode": meta["support_mode"],
            "config": meta["candidate"],
            "N_train": meta["N_train"],
            "N_validation": meta["N_validation"],
            "N_features": meta["N_features"],
            "MAE": meta["MAE"],
            "RMSE": meta["RMSE"],
            "bias": meta["bias"],
            "R2": meta["R2"],
            "Pearson": meta["Pearson"],
            "baseline_reference": meta["baseline_reference"],
            "baseline_MAE": meta["baseline_MAE"],
            "baseline_RMSE": meta["baseline_RMSE"],
            "MAE_skill": meta["MAE_skill"],
            "RMSE_skill": meta["RMSE_skill"],
            "elapsed": meta.get("fit_walltime", 0),
            "model_size_mb": meta["model_file_size"] / (1024 * 1024)
        }
        all_runs.append(row)

    df = pd.DataFrame(all_runs)

    if len(df) == 0:
        print("No RF-03B models found yet.")
        return

    print(f"Audited {len(df)} RF-03B models so far.")

    # Separate matched vs primary
    df_primary = df[df["support_mode"] == "native_support"].copy()
    df_matched = df[df["support_mode"] == "matched_support"].copy()

    if len(df_primary) > 0:
        df_primary.to_csv(out_dir / "rf03b_primary_metrics.csv", index=False)

    if len(df_matched) > 0:
        df_matched.to_csv(out_dir / "rf03b_source_matched_metrics.csv", index=False)

        # Check if matched keys are equal
        if len(df_matched) == 2:
            n_tr_cdf = df_matched[df_matched["experiment"] == "da_cdf"]["N_train"].iloc[0]
            n_tr_noc = df_matched[df_matched["experiment"] == "da_nocdf"]["N_train"].iloc[0]
            n_val_cdf = df_matched[df_matched["experiment"] == "da_cdf"]["N_validation"].iloc[0]
            n_val_noc = df_matched[df_matched["experiment"] == "da_nocdf"]["N_validation"].iloc[0]

            assert n_tr_cdf == n_tr_noc, f"Matched train count mismatch: {n_tr_cdf} vs {n_tr_noc}"
            assert n_val_cdf == n_val_noc, f"Matched val count mismatch: {n_val_cdf} vs {n_val_noc}"
            print(f"Matched support passed! N_train={n_tr_cdf}, N_val={n_val_cdf}")

    # Paper-ready table
    paper_cols = ["block", "experiment", "target", "MAE", "RMSE", "R2", "Pearson", "MAE_skill", "RMSE_skill"]
    paper_df = df_primary[paper_cols].copy() if len(df_primary) > 0 else pd.DataFrame(columns=paper_cols)
    paper_df.to_csv(out_dir / "rf03b_paper_ready_table.csv", index=False)

    # Resource summary
    res_cols = ["block", "experiment", "target", "support_mode", "elapsed", "model_size_mb"]
    res_df = df[res_cols].copy()
    res_df.to_csv(out_dir / "rf03b_resource_summary.csv", index=False)

    print("\n--- Paper Ready Preview ---")
    print(paper_df.to_string(index=False))

    print(f"\nTotal Artifact Size: {df['model_size_mb'].sum():.2f} MB")

if __name__ == "__main__":
    audit_rf03b()
