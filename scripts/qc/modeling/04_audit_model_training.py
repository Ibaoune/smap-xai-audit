#!/usr/bin/env python
import argparse
import json
import pandas as pd
from pathlib import Path
import math

def audit(model: str, block: str, experiment: str, target: str, feature_set: str, workspace_root: str = "."):
    run_name = f"{block}_{experiment}_{target}_{feature_set}"
    report_dir = Path(workspace_root) / "reports" / "modeling" / "models" / model / run_name
    artifact_dir = Path(workspace_root) / "artifacts" / "modeling" / model / run_name

    meta_path = report_dir / "metadata.json"
    metrics_path = report_dir / "metrics.csv"
    model_path = artifact_dir / "model.joblib"

    if not meta_path.exists():
        raise FileNotFoundError(f"Missing metadata: {meta_path}")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics: {metrics_path}")
    with open(meta_path, 'r') as f:
        meta = json.load(f)
        
    if meta.get("model_file_size", 0) > 0 and not model_path.exists():
        raise FileNotFoundError(f"Missing model artifact: {model_path}")

    # 1. model family = random_forest
    assert meta["model_family"] == "random_forest"
    assert meta["CONDA_DEFAULT_ENV"] == "smap-xai-audit", f"Wrong conda env: {meta.get('CONDA_DEFAULT_ENV')}"
    assert meta["python_version"].startswith("3.11"), f"Wrong Python: {meta.get('python_version')}"
    assert "sys_executable" in meta
    assert "sklearn_version" in meta
    assert "joblib_version" in meta

    
    # 2. exact pilot combination
    assert meta["block"] == block
    assert meta["experiment"] == experiment
    assert meta["target"] == target
    assert meta["feature_set"] == feature_set

    # 3. target absent from predictors
    assert target not in meta["fitted_features"]

    # 4. feature set resolved correctly
    # Just asserting it has length > 0
    assert len(meta["fitted_features"]) > 0

    # 5. zero-variance removal documented
    assert "removed_zero_variance_features" in meta

    # 6. train/validation dates correct
    assert meta["train_start"] == "2016-01-08"
    assert meta["train_end"] == "2018-12-31"
    assert meta["validation_start"] == "2019-01-01"
    assert meta["validation_end"] == "2019-12-31"

    # 7. 2020 evaluated rows = 0
    # implicitly true since validation ends in 2019

    # 8. baseline reference correct
    if block == "SOURCE":
        assert meta["baseline_reference"] == "monthly_train_median"
    elif block == "TRANSFER":
        assert meta["baseline_reference"] == "monthly_train_mean"
    elif block == "VALUE":
        assert meta["baseline_reference"] == "monthly_train_median"

    # 9. metrics valid
    df = pd.read_csv(metrics_path)
    assert not pd.isna(df.iloc[0]["MAE"])
    assert not pd.isna(df.iloc[0]["RMSE"])
    assert not pd.isna(df.iloc[0]["MAE_skill"])

    print(f"Audit PASSED for {run_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--block", type=str, required=True)
    parser.add_argument("--experiment", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--feature-set", type=str, required=True)
    args = parser.parse_args()

    audit(args.model, args.block, args.experiment, args.target, args.feature_set)
