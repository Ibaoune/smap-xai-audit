#!/usr/bin/env python
import json
import pandas as pd
from pathlib import Path
import argparse

def audit_and_aggregate_spatial(block, experiment, target, feature_set, config, workspace_root="."):
    base = Path(workspace_root) / "reports" / "modeling" / "models" / "random_forest"
    folds = ["spatial_0", "spatial_1", "spatial_2", "spatial_3", "spatial_4"]

    rows = []

    for f in folds:
        run_name = f"{block}_{experiment}_{target}_{feature_set}_{config}_{f}"
        meta_path = base / run_name / "metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Missing metadata for {run_name}")

        with open(meta_path, "r") as f_meta:
            meta = json.load(f_meta)

        # Audit checks
        assert meta["model_family"] == "random_forest"
        assert meta["CONDA_DEFAULT_ENV"] == "smap-xai-audit"
        assert meta["block"] == block
        assert meta["candidate"] == config
        assert meta["fold"] == f
        assert meta["model_file_size"] == 0, f"Model file should not be saved for {run_name}"
        assert target not in meta["fitted_features"], f"Leakage: target {target} in features!"
        # 2020 isolation check implicitly passed if validation_end doesn't exceed 2019
        assert meta["validation_end"].startswith("2016") or meta["validation_end"].startswith("2017") or meta["validation_end"].startswith("2018") or meta["validation_end"].startswith("2019")
        # Ensure training period matches 2016 to 2019
        assert meta["train_start"] == "2016-01-08"
        assert meta["train_end"] == "2019-12-31"
        assert meta["validation_start"] == "2016-01-08"
        assert meta["validation_end"] == "2019-12-31"

        row = {
            "model_family": meta["model_family"],
            "block": meta["block"],
            "experiment": meta["experiment"],
            "target": meta["target"],
            "feature_set": meta["feature_set"],
            "config": meta["candidate"],
            "fold": meta["fold"],
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
            "walltime": meta.get("fit_walltime", 0)
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Check feature count consistency
    assert df["N_features"].nunique() == 1, "Feature count varies across folds!"

    # Save fold metrics
    out_dir = base / "rf03_spatial"
    out_dir.mkdir(exist_ok=True)

    fold_csv = out_dir / f"rf03_spatial_{block.lower()}_fold_metrics.csv"
    df.to_csv(fold_csv, index=False)

    # Compute summary across 5 folds (unweighted)
    summary_df = pd.DataFrame([{
        "block": block,
        "config": config,
        "mean_MAE_skill": df["MAE_skill"].mean(),
        "std_MAE_skill": df["MAE_skill"].std(),
        "min_MAE_skill": df["MAE_skill"].min(),
        "max_MAE_skill": df["MAE_skill"].max(),
        "mean_RMSE_skill": df["RMSE_skill"].mean(),
        "std_RMSE_skill": df["RMSE_skill"].std(),
        "min_RMSE_skill": df["RMSE_skill"].min(),
        "max_RMSE_skill": df["RMSE_skill"].max(),
        "total_walltime": df["walltime"].sum()
    }])

    summary_csv = out_dir / f"rf03_spatial_{block.lower()}_summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    print(f"Audit PASSED for {block} RF-03A (Spatial)")
    print(f"Summary saved to {summary_csv}")
    print(summary_df[["config", "mean_MAE_skill", "std_MAE_skill", "min_MAE_skill", "max_MAE_skill"]])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--block", type=str, required=True)
    parser.add_argument("--experiment", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--feature-set", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()

    audit_and_aggregate_spatial(args.block, args.experiment, args.target, args.feature_set, args.config)
