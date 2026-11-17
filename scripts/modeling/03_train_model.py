#!/usr/bin/env python
import argparse
import yaml
import json
import os
import time
import sys
import psutil
import sklearn
import joblib
import pandas as pd
from pathlib import Path

from smap_xai.modeling.training import get_model, audit_leakage, load_data, train_model
from smap_xai.modeling.evaluation import load_baseline_metrics, evaluate_model
from smap_xai.modeling.splits import get_temporal_fold_bounds

def get_git_revision_short_hash() -> str:
    import subprocess
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def parse_features(config_path, feature_set_name):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)

    if feature_set_name in cfg:
        # source.yaml style
        features = cfg[feature_set_name]
    elif 'feature_sets' in cfg and feature_set_name in cfg['feature_sets']:
        # transfer.yaml / value.yaml style
        includes = cfg['feature_sets'][feature_set_name]['includes']
        features = []
        for inc in includes:
            features.extend(cfg[inc])
    else:
        raise ValueError(f"Feature set {feature_set_name} not found in {config_path}")
    return list(set(features))

def parse_zero_variance(config_path, block):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    key = f"zero_variance_on_{block.lower()}_support"
    if key in cfg and cfg[key].get('exclude_from_model_by_default', False):
        return cfg[key].get('features', [])
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--block", type=str, required=True, choices=["SOURCE", "TRANSFER", "VALUE"])
    parser.add_argument("--experiment", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--feature-set", type=str, required=True)
    parser.add_argument("--candidate", type=str, default="pilot", help="Model candidate config name")
    parser.add_argument("--fold", type=str, default="fold_3", help="Temporal fold name")
    parser.add_argument("--spatial-fold", type=str, default=None, help="Spatial fold name (e.g., spatial_0)")
    parser.add_argument("--support-mode", type=str, default="native_support", choices=["native_support", "matched_support"])
    parser.add_argument("--workspace-root", type=str, default=".")
    args = parser.parse_args()

    # Determine baseline
    if args.block == "SOURCE":
        baseline_ref = "monthly_train_median"
    elif args.block == "TRANSFER":
        baseline_ref = "monthly_train_mean"
    elif args.block == "VALUE":
        baseline_ref = "monthly_train_median"
    else:
        raise ValueError("Unknown block")

    # Load baseline
    if args.spatial_fold:
        baseline_type = "spatial"
        baseline_fold = args.spatial_fold
        args.fold = args.spatial_fold  # For naming output dirs
    else:
        baseline_type = "temporal"
        baseline_fold = args.fold

    print("Loading baseline metrics...")
    baseline_metrics = load_baseline_metrics(
        args.block, args.experiment, args.target, baseline_ref,
        fold=baseline_fold, workspace_root=args.workspace_root, baseline_type=baseline_type,
        support_mode=args.support_mode
    )
    print(f"Baseline loaded: {baseline_metrics}")

    # Resolve features
    config_path = f"{args.workspace_root}/configs/datasets/{args.block.lower()}.yaml"
    requested_features = parse_features(config_path, args.feature_set)
    zero_variance_features = parse_zero_variance(config_path, args.block)

    fitted_features = [f for f in requested_features if f not in zero_variance_features]

    # Audit leakage
    audit_leakage(fitted_features, args.target, args.block)

    # Load model config
    with open(f"{args.workspace_root}/configs/modeling/models.yaml", 'r') as f:
        model_cfg = yaml.safe_load(f)
    model_params = model_cfg['models'][args.model][args.candidate]

    if args.model == "random_forest":
        # Get n_jobs from SLURM if available
        cpus = int(os.environ.get("SLURM_CPUS_PER_TASK", 1))
        model_params['n_jobs'] = cpus

    save_model = model_params.pop("save_model", True)

    # Train and Val dates
    if args.spatial_fold:
        train_start, train_end, val_start, val_end = "2016-01-08", "2019-12-31", "2016-01-08", "2019-12-31"
        print("Loading data for spatial CV...")
        coord_cols = ["y_index", "x_index"] if args.block in ["SOURCE", "TRANSFER"] else ["gleam_y_index", "gleam_x_index"]
        mapping_file = "noahmp_spatial_blocks.parquet" if args.block in ["SOURCE", "TRANSFER"] else "gleam_spatial_blocks.parquet"

        df_all = load_data(args.block, args.experiment, args.target, fitted_features, train_start, train_end, meta_cols=["date"] + coord_cols)
        mapping_df = pd.read_parquet(f"{args.workspace_root}/data/processed/modeling/splits/{mapping_file}")

        df_all = pd.merge(df_all, mapping_df[coord_cols + ["spatial_fold"]], on=coord_cols, how="inner")

        target_fold_int = int(args.spatial_fold.split("_")[-1])
        df_train = df_all[df_all["spatial_fold"] != target_fold_int]
        df_val = df_all[df_all["spatial_fold"] == target_fold_int]

    else:
        train_start, train_end, val_start, val_end = get_temporal_fold_bounds(args.fold)
        print("Loading train data...")
        coord_cols = ["y_index", "x_index"] if args.block in ["SOURCE", "TRANSFER"] else ["gleam_y_index", "gleam_x_index"]
        df_train = load_data(args.block, args.experiment, args.target, fitted_features, train_start, train_end, meta_cols=["date"] + coord_cols)
        print("Loading validation data...")
        df_val = load_data(args.block, args.experiment, args.target, fitted_features, val_start, val_end, meta_cols=["date"] + coord_cols)

        if args.support_mode == "matched_support":
            print("Applying matched support keys...")
            matched_df = pd.read_parquet(f"{args.workspace_root}/data/processed/modeling/splits/source_matched_support.parquet")
            matched_df["date"] = pd.to_datetime(matched_df["date"])
            df_train = pd.merge(df_train, matched_df, on=["date", "y_index", "x_index"], how="inner")
            df_val = pd.merge(df_val, matched_df, on=["date", "y_index", "x_index"], how="inner")

    if args.block == "TRANSFER":
        # Resource estimation
        n_rows, n_cols = df_train.shape
        ram_bytes = df_train.memory_usage(deep=True).sum()
        avail_ram = psutil.virtual_memory().available
        print(f"TRANSFER resource estimate:")
        print(f"  N_train: {n_rows}")
        print(f"  N_features: {len(fitted_features)}")
        print(f"  DataFrame RAM: {ram_bytes / 1024**3:.2f} GB")
        print(f"  Available RAM: {avail_ram / 1024**3:.2f} GB")

    X_train = df_train[fitted_features]
    y_train = df_train[args.target]

    # Train
    print("Training model...")
    model = get_model(args.model, model_params)
    train_meta = train_model(model, X_train, y_train)

    X_val = df_val[fitted_features]
    y_val = df_val[args.target]

    print("Predicting and evaluating...")
    y_pred = model.predict(X_val)

    metrics = evaluate_model(y_val, y_pred, baseline_metrics)

    # Prepare metadata
    metadata = {
        "model_family": args.model,
        "sys_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "CONDA_DEFAULT_ENV": os.environ.get("CONDA_DEFAULT_ENV", "unknown"),
        "sklearn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "git_SHA": get_git_revision_short_hash(),
        "SLURM_JOB_ID": os.environ.get("SLURM_JOB_ID", "local"),
        "hostname": os.uname().nodename,
        "block": args.block,
        "experiment": args.experiment,
        "target": args.target,
        "feature_set": args.feature_set,
        "candidate": args.candidate,
        "fold": args.fold,
        "support_mode": args.support_mode,
        "train_start": train_start,
        "train_end": train_end,
        "validation_start": val_start,
        "validation_end": val_end,
        "N_train": len(X_train),
        "N_validation": len(X_val),
        "N_features": len(fitted_features),
        "requested_features": requested_features,
        "removed_zero_variance_features": zero_variance_features,
        "fitted_features": fitted_features,
        "hyperparameters": model_params,
        "baseline_reference": baseline_ref,
        "baseline_MAE": baseline_metrics["baseline_MAE"],
        "baseline_RMSE": baseline_metrics["baseline_RMSE"],
        "MAE": metrics["MAE"],
        "RMSE": metrics["RMSE"],
        "bias": metrics["bias"],
        "R2": metrics["R2"],
        "Pearson": metrics["Pearson"],
        "MAE_skill": metrics["MAE_skill"],
        "RMSE_skill": metrics["RMSE_skill"],
        "fit_walltime": train_meta.get("fit_walltime_seconds", 0)
    }

    # Save artifacts
    if args.candidate == "pilot":
        run_name = f"{args.block}_{args.experiment}_{args.target}_{args.feature_set}"
    else:
        run_name = f"{args.block}_{args.experiment}_{args.target}_{args.feature_set}_{args.candidate}_{args.fold}_{args.support_mode}"

    artifact_dir = Path(args.workspace_root) / "artifacts" / "modeling" / args.model / run_name
    report_dir = Path(args.workspace_root) / "reports" / "modeling" / "models" / args.model / run_name

    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    if save_model:
        model_path = artifact_dir / "model.joblib"
        model.save(str(model_path))
        metadata["model_file_size"] = os.path.getsize(model_path)
    else:
        metadata["model_file_size"] = 0

    with open(report_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    metrics_df = pd.DataFrame([metadata])
    # subset columns
    cols = ["model_family", "block", "experiment", "target", "feature_set", "candidate", "fold", "support_mode",
            "train_start", "train_end", "validation_start", "validation_end",
            "N_train", "N_validation", "N_features", "MAE", "RMSE", "bias", "R2", "Pearson",
            "baseline_reference", "baseline_MAE", "baseline_RMSE", "MAE_skill", "RMSE_skill",
            "fit_walltime", "model_file_size"]
    # only include existing columns to avoid errors if some are missing
    cols = [c for c in cols if c in metrics_df.columns]
    metrics_df = metrics_df[cols]
    metrics_df.to_csv(report_dir / "metrics.csv", index=False)

    if save_model:
        print(f"Model saved to {model_path}")
    print(f"Metadata saved to {report_dir / 'metadata.json'}")
    print(f"Metrics saved to {report_dir / 'metrics.csv'}")

if __name__ == "__main__":
    main()
