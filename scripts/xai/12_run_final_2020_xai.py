#!/usr/bin/env python
import argparse
import json
import sys
import joblib
import numpy as np
import pandas as pd
import shap
import yaml
import hashlib
from pathlib import Path
from sklearn.inspection import permutation_importance
from joblib import Parallel, delayed

from smap_xai.modeling.training import load_data

SHAP_COMPUTE_SIZE = 10_000
PERM_SIZE = 5_000
SEED = 42

def balanced_subsample(df, size, key_cols, seed):
    if len(df) <= size:
        return df.sort_values(key_cols).reset_index(drop=True)
    cells = df.groupby(["month", "spatial_fold"])
    n_cells = df[["month", "spatial_fold"]].drop_duplicates().shape[0]
    per_cell = size // n_cells
    remainder = size % n_cells

    rng = np.random.default_rng(seed)
    parts = []
    for i, (_, g) in enumerate(cells):
        n = per_cell + (1 if i < remainder else 0)
        n = min(n, len(g))
        parts.append(g.sample(n=n, random_state=seed))

    result = pd.concat(parts).sort_values(key_cols).reset_index(drop=True)
    return result

def _evaluate_shap_chunk(model_obj, chunk_df, chunk_idx, total_chunks):
    explainer = shap.TreeExplainer(
        model_obj,
        feature_perturbation="tree_path_dependent",
        model_output="raw",
    )
    vals = explainer.shap_values(chunk_df)
    print(f"  [TreeSHAP Chunk {chunk_idx + 1}/{total_chunks}] Finished {len(chunk_df)} samples", flush=True)
    return vals

def run_shap(model, X, fitted_features, n_jobs=1):
    explainer0 = shap.TreeExplainer(
        model.model,
        feature_perturbation="tree_path_dependent",
        model_output="raw",
    )
    expected_value = explainer0.expected_value
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = float(np.squeeze(expected_value))
    predictions = model.predict(X)

    if n_jobs <= 1 or len(X) <= 1:
        print(f"Running TreeSHAP sequentially on {len(X)} samples...", flush=True)
        shap_values = explainer0.shap_values(X)
        return shap_values, expected_value, predictions

    actual_jobs = min(n_jobs, len(X))
    chunks = np.array_split(X, actual_jobs)
    print(f"Running TreeSHAP in parallel across {actual_jobs} chunks ({len(X)} samples total)...", flush=True)
    chunk_results = Parallel(n_jobs=actual_jobs)(
        delayed(_evaluate_shap_chunk)(model.model, chunk, idx, actual_jobs)
        for idx, chunk in enumerate(chunks)
    )
    shap_values = np.vstack(chunk_results)
    print(f"TreeSHAP completed: aggregated {shap_values.shape[0]} samples.", flush=True)
    return shap_values, expected_value, predictions

def get_fingerprint(df, coord_cols):
    keys = df[["date"] + coord_cols].copy()
    keys["date"] = keys["date"].astype(str)
    keys = keys.sort_values(by=["date"] + coord_cols)
    key_str = keys.to_csv(index=False).encode('utf-8')
    return hashlib.md5(key_str).hexdigest()

def matches_model_key(target_key: str, block: str, experiment: str, target: str, support: str) -> bool:
    if not target_key:
        return True
    tk = target_key.lower().replace("-", "_").replace("_cohort", "").strip()
    full_key = f"{block}_{experiment}_{target}_{support}".lower()
    path_key = f"{block.lower()}/{experiment}/{target}/{support}"
    if tk in (full_key, path_key, path_key.replace("/", "_")):
        return True
    tokens = [t for t in tk.replace("/", "_").split("_") if t]
    return all(t in full_key.split("_") for t in tokens)

def main():
    parser = argparse.ArgumentParser(description="Run 2020 XAI (SHAP & Permutation)")
    parser.add_argument("--model-key", type=str, default=None, help="Specific model key to process (e.g. source_da_cdf_native)")
    parser.add_argument("--shap-n-jobs", type=int, default=1, help="Number of parallel workers for chunked TreeSHAP")
    parser.add_argument("--workspace-root", type=str, default=".")
    args = parser.parse_args()

    workspace = args.workspace_root
    out_dir = Path(workspace) / "data" / "processed" / "modeling" / "xai" / "final_2020"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    (out_dir / "cohorts").mkdir(exist_ok=True)
    (out_dir / "shap").mkdir(exist_ok=True)
    (out_dir / "permutation").mkdir(exist_ok=True)
    
    matched_keys_df = pd.read_parquet(f"{workspace}/data/processed/modeling/splits/source_matched_support_2020.parquet")
    spatial_map = pd.read_parquet(f"{workspace}/data/processed/modeling/splits/noahmp_spatial_blocks.parquet")
    gleam_spatial_map = pd.read_parquet(f"{workspace}/data/processed/modeling/splits/gleam_spatial_blocks.parquet")

    models_dir = Path(workspace) / "reports" / "modeling" / "models" / "final_refit_2016_2019"
    meta_files = list(models_dir.rglob("metadata.json"))

    for meta_path in meta_files:
        with open(meta_path) as f:
            meta = json.load(f)
            
        block = meta["diagnostic_block"]
        experiment = meta["experiment"]
        target = meta["target"]
        support = meta["support_mode"]
        features = meta["fitted_features"]
        
        if args.model_key and not matches_model_key(args.model_key, block, experiment, target, support):
            continue
            
        print(f"XAI for 2020: {block} / {experiment} / {target} / {support} ...")
        
        # Load Model
        model = joblib.load(meta_path.parent / "model.joblib")
        
        # Load 2020 Data
        coord_cols = ["y_index", "x_index"] if block in ["SOURCE", "TRANSFER"] else ["gleam_y_index", "gleam_x_index"]
        df = load_data(block, experiment, target, features, "2020-01-01", "2020-12-31", meta_cols=["date"] + coord_cols, allow_2020=True)
        
        if support == "matched_support":
            df = pd.merge(df, matched_keys_df, on=["date", "y_index", "x_index"], how="inner")
            
        df["month"] = pd.to_datetime(df["date"]).dt.month
        
        if block in ["SOURCE", "TRANSFER"]:
            df = pd.merge(df, spatial_map[["y_index", "x_index", "spatial_fold"]], on=["y_index", "x_index"], how="left")
        else:
            df = pd.merge(df, gleam_spatial_map[["gleam_y_index", "gleam_x_index", "spatial_fold"]], on=["gleam_y_index", "gleam_x_index"], how="left")
            
        df = df.dropna(subset=["spatial_fold"])
            
        cohort_name = f"{block}_{experiment}_{target}_{support}_cohort"
        perm_file = out_dir / "permutation" / f"permutation_{cohort_name}.json"
        if perm_file.exists():
            print(f"Skipping {cohort_name}, already exists.", flush=True)
            continue
        
        # 1. Representative Cohort (50k)
        cohort = balanced_subsample(df, 50000, ["date"] + coord_cols, SEED)
        
        # Save cohort
        cohort_fingerprint = get_fingerprint(cohort, coord_cols)
        cohort.to_parquet(out_dir / "cohorts" / f"{cohort_name}.parquet", index=False)
        
        # 2. TreeSHAP Subset (10k)
        compute_keys = balanced_subsample(cohort, SHAP_COMPUTE_SIZE, ["date"] + coord_cols, SEED)
        shap_fingerprint = get_fingerprint(compute_keys, coord_cols)
        
        X = compute_keys[features]
        y = compute_keys[target]
        
        shap_vals, expected_value, predictions = run_shap(model, X, features, n_jobs=args.shap_n_jobs)
        
        # Save SHAP
        out_df = compute_keys[["date", "month", "spatial_fold"] + coord_cols].copy()
        out_df["target"] = y.values
        out_df["prediction"] = predictions
        out_df["expected_value"] = expected_value
        for i, feat in enumerate(features):
            out_df[f"shap__{feat}"] = shap_vals[:, i]
            out_df[f"value__{feat}"] = X[feat].values
            
        out_df.to_parquet(out_dir / "shap" / f"shap_{cohort_name}.parquet", index=False)
        
        # 3. Permutation Subset (5k nested)
        X_perm = X.head(PERM_SIZE)
        y_perm = y.head(PERM_SIZE)
        
        perm_res = permutation_importance(
            model.model, X_perm, y_perm,
            scoring="neg_mean_absolute_error",
            n_repeats=5,
            random_state=SEED,
            n_jobs=-1,
        )
        
        perm_dict = {
            "features": features,
            "importances_mean": perm_res.importances_mean.tolist(),
            "importances_std": perm_res.importances_std.tolist(),
            "scoring": "neg_mean_absolute_error",
            "n_repeats": 5,
            "cohort_size": len(X_perm),
            "shap_cohort_size": len(X),
            "representative_cohort_size": len(cohort),
            "cohort_fingerprint": cohort_fingerprint,
            "shap_fingerprint": shap_fingerprint
        }
        with open(out_dir / "permutation" / f"permutation_{cohort_name}.json", "w") as f:
            json.dump(perm_dict, f, indent=2)

if __name__ == "__main__":
    main()
