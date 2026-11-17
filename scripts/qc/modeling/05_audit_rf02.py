#!/usr/bin/env python
import json
import pandas as pd
from pathlib import Path
import argparse

def audit_and_aggregate(block, experiment, target, feature_set, workspace_root="."):
    base = Path(workspace_root) / "reports" / "modeling" / "models" / "random_forest"
    candidates = ["RF_A", "RF_B", "RF_C", "RF_D"]
    folds = ["fold_1", "fold_2", "fold_3"]

    rows = []

    for cand in candidates:
        for f in folds:
            run_name = f"{block}_{experiment}_{target}_{feature_set}_{cand}_{f}"
            meta_path = base / run_name / "metadata.json"
            if not meta_path.exists():
                raise FileNotFoundError(f"Missing metadata for {run_name}")

            with open(meta_path, "r") as f_meta:
                meta = json.load(f_meta)

            # Audit checks
            assert meta["model_family"] == "random_forest"
            assert meta["CONDA_DEFAULT_ENV"] == "smap-xai-audit"
            assert meta["block"] == block
            assert meta["candidate"] == cand
            assert meta["fold"] == f
            assert meta["model_file_size"] == 0, f"Model file should not be saved for {run_name}"
            assert target not in meta["fitted_features"], f"Leakage: target {target} in features!"
            # 2020 isolation check implicitly passed if validation_end doesn't exceed 2019
            assert meta["validation_end"].startswith("2017") or meta["validation_end"].startswith("2018") or meta["validation_end"].startswith("2019")

            row = {
                "model_family": meta["model_family"],
                "block": meta["block"],
                "experiment": meta["experiment"],
                "target": meta["target"],
                "feature_set": meta["feature_set"],
                "candidate": meta["candidate"],
                "fold": meta["fold"],
                "train_start": meta["train_start"],
                "train_end": meta["train_end"],
                "validation_year": meta["validation_end"][:4],
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
                "relative_MAE": meta["MAE"] / meta["baseline_MAE"],
                "relative_RMSE": meta["RMSE"] / meta["baseline_RMSE"],
                "fold_relative_error": 0.5 * ((meta["MAE"] / meta["baseline_MAE"]) + (meta["RMSE"] / meta["baseline_RMSE"])),
                "walltime": meta.get("fit_walltime", 0),
                "MaxRSS": 0  # To be extracted from slurm separately if needed, leave 0 for now
            }
            rows.append(row)

    df = pd.DataFrame(rows)

    # Check feature count consistency
    assert df["N_features"].nunique() == 1, "Feature count varies across candidates/folds!"

    # Save fold metrics
    out_dir = base / "rf02"
    out_dir.mkdir(exist_ok=True)

    fold_csv = out_dir / f"rf02_{block.lower()}_fold_metrics.csv"
    df.to_csv(fold_csv, index=False)

    # Compute summary
    summary_rows = []
    for cand in candidates:
        cand_df = df[df["candidate"] == cand]
        if len(cand_df) != 3:
            raise ValueError(f"Missing folds for {cand}")

        summary_rows.append({
            "block": block,
            "candidate": cand,
            "CV_relative_error": cand_df["fold_relative_error"].mean(),
            "fold_relative_error_std": cand_df["fold_relative_error"].std(),
            "mean_MAE_skill": cand_df["MAE_skill"].mean(),
            "mean_RMSE_skill": cand_df["RMSE_skill"].mean(),
            "min_MAE_skill": cand_df["MAE_skill"].min(),
            "min_RMSE_skill": cand_df["RMSE_skill"].min(),
            "total_walltime": cand_df["walltime"].sum(),
            "peak_MaxRSS": cand_df["MaxRSS"].max()
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_csv = out_dir / f"rf02_{block.lower()}_candidate_summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    # Selection rule
    best_cand = summary_df.loc[summary_df["CV_relative_error"].idxmin()]
    # complexity logic logic goes here, manually inspect for now or code a tie-break:
    # "If two configurations have essentially equivalent CV performance (diff <= 0.01),
    # prefer: lower max_depth, larger min_samples_leaf, smaller model complexity"

    print(f"Audit PASSED for {block} RF-02")
    print(f"Summary saved to {summary_csv}")
    print(summary_df[["candidate", "CV_relative_error", "fold_relative_error_std", "min_MAE_skill"]])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--block", type=str, required=True)
    parser.add_argument("--experiment", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--feature-set", type=str, required=True)
    args = parser.parse_args()

    audit_and_aggregate(args.block, args.experiment, args.target, args.feature_set)
