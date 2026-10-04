#!/usr/bin/env python
import argparse
import yaml
import json
import os
import sys
import psutil
import sklearn
import joblib
import pandas as pd
import hashlib
from pathlib import Path

from smap_xai.modeling.training import get_model, audit_leakage, load_data, train_model

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
        features = cfg[feature_set_name]
    elif 'feature_sets' in cfg and feature_set_name in cfg['feature_sets']:
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

def get_fingerprint(df, coord_cols):
    keys = df[["date"] + coord_cols].copy()
    keys["date"] = keys["date"].astype(str)
    keys = keys.sort_values(by=["date"] + coord_cols)
    key_str = keys.to_csv(index=False).encode('utf-8')
    return hashlib.md5(key_str).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--block", type=str, required=True, choices=["SOURCE", "TRANSFER", "VALUE"])
    parser.add_argument("--experiment", type=str, required=True, choices=["da_cdf", "da_nocdf"])
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--support-mode", type=str, default="native_support", choices=["native_support", "matched_support"])
    parser.add_argument("--workspace-root", type=str, default=".")
    args = parser.parse_args()

    # Freeze constraints
    freeze_commit = "bb777c91889d76ecab02067520c9a9f948f3563e"
    
    if args.block == "SOURCE":
        candidate = "RF_A"
        feature_set = "context_only_feature_set"
    elif args.block == "TRANSFER":
        candidate = "RF_A"
        feature_set = "source_context_feature_set"
    elif args.block == "VALUE":
        candidate = "RF_B"
        feature_set = "value_context_feature_set"
    
    # 1. Resolve features
    config_path = f"{args.workspace_root}/configs/datasets/{args.block.lower()}.yaml"
    requested_features = parse_features(config_path, feature_set)
    zero_variance_features = parse_zero_variance(config_path, args.block)
    fitted_features = sorted([f for f in requested_features if f not in zero_variance_features])

    # Enforce predictor counts
    if args.block == "SOURCE": assert len(fitted_features) == 35
    elif args.block == "TRANSFER": assert len(fitted_features) == 52
    elif args.block == "VALUE": assert len(fitted_features) == 52

    # 2. Audit leakage
    audit_leakage(fitted_features, args.target, args.block)

    # 3. Load model config
    with open(f"{args.workspace_root}/configs/modeling/models.yaml", 'r') as f:
        model_cfg = yaml.safe_load(f)
    model_params = model_cfg['models']["random_forest"][candidate]
    model_params['n_jobs'] = int(os.environ.get("SLURM_CPUS_PER_TASK", 1))
    
    if "save_model" in model_params:
        del model_params["save_model"]

    # 4. Load Training Data (2016-2019 ONLY)
    train_start, train_end = "2016-01-08", "2019-12-31"
    
    coord_cols = ["y_index", "x_index"] if args.block in ["SOURCE", "TRANSFER"] else ["gleam_y_index", "gleam_x_index"]
    print("Loading train data...")
    df_train = load_data(args.block, args.experiment, args.target, fitted_features, train_start, train_end, meta_cols=["date"] + coord_cols)
    
    # STRICT 2020 SEAL
    assert df_train["date"].max() <= pd.to_datetime("2019-12-31"), "2020 data leaked into training!"
    assert len(df_train[df_train["date"].dt.year == 2020]) == 0, "2020 row found!"

    # Matched support logic
    if args.support_mode == "matched_support":
        print("Applying matched support keys...")
        matched_df = pd.read_parquet(f"{args.workspace_root}/data/processed/modeling/splits/source_matched_support.parquet")
        # Ensure matched support doesn't extend beyond 2019
        matched_df["date"] = pd.to_datetime(matched_df["date"])
        matched_df = matched_df[matched_df["date"] <= pd.to_datetime("2019-12-31")]
        df_train = pd.merge(df_train, matched_df, on=["date", "y_index", "x_index"], how="inner")

    fingerprint = get_fingerprint(df_train, coord_cols)
    print(f"Training Support Fingerprint: {fingerprint}")

    X_train = df_train[fitted_features]
    y_train = df_train[args.target]

    # 5. Train
    print(f"Training {candidate} model for {args.block} / {args.experiment} / {args.target}...")
    model = get_model("random_forest", model_params)
    train_meta = train_model(model, X_train, y_train)

    # 6. Save model and metadata
    metadata = {
        "stage": "RF-05",
        "status": "FINAL_REFIT_PRE_2020",
        "freeze_commit": freeze_commit,
        "diagnostic_block": args.block,
        "experiment": args.experiment,
        "target": args.target,
        "support_mode": args.support_mode,
        "feature_set": feature_set,
        "rf_configuration": candidate,
        "training_start": train_start,
        "training_end": df_train["date"].dt.strftime("%Y-%m-%d").max(),
        "n_training_rows": len(X_train),
        "n_training_dates": df_train["date"].nunique(),
        "n_training_pixels": df_train.drop_duplicates(subset=coord_cols).shape[0],
        "n_features": len(fitted_features),
        "fitted_features": fitted_features,
        "random_state": model_params.get("random_state", 42),
        "model_parameters": model_params,
        "training_support_fingerprint": fingerprint,
        
        # System metadata
        "sys_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "sklearn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "git_SHA": get_git_revision_short_hash()
    }
    
    out_dir = Path(f"{args.workspace_root}/reports/modeling/models/final_refit_2016_2019/{args.block.lower()}/{args.experiment}/{args.target}/{args.support_mode}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = out_dir / "model.joblib"
    joblib.dump(model, model_path)
    
    meta_path = out_dir / "metadata.json"
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Saved final refit to {out_dir}")

if __name__ == "__main__":
    main()
