#!/usr/bin/env python
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import pyarrow.dataset as ds
from smap_xai.modeling.training import load_data
from smap_xai.modeling.metrics import ChunkedRegressionMetrics, compute_relative_skill

def compute_matched_support(workspace_root="."):
    print("Computing 2020 matched support...")
    cdf_dataset = ds.dataset(f"{workspace_root}/data/processed/modeling/source/da_cdf", format="parquet", ignore_prefixes=['.', '_', 'README.md'])
    cdf_keys = cdf_dataset.to_table(columns=["date", "y_index", "x_index"]).to_pandas()
    
    nocdf_dataset = ds.dataset(f"{workspace_root}/data/processed/modeling/source/da_nocdf", format="parquet", ignore_prefixes=['.', '_', 'README.md'])
    nocdf_keys = nocdf_dataset.to_table(columns=["date", "y_index", "x_index"]).to_pandas()
    
    cdf_keys["date"] = pd.to_datetime(cdf_keys["date"])
    nocdf_keys["date"] = pd.to_datetime(nocdf_keys["date"])
    
    # Filter to 2020 only
    cdf_keys = cdf_keys[(cdf_keys["date"] >= "2020-01-01") & (cdf_keys["date"] <= "2020-12-31")]
    nocdf_keys = nocdf_keys[(nocdf_keys["date"] >= "2020-01-01") & (nocdf_keys["date"] <= "2020-12-31")]
    
    matched = pd.merge(cdf_keys, nocdf_keys, on=["date", "y_index", "x_index"], how="inner")
    print(f"Matched 2020 rows: {len(matched)}")
    
    out_dir = Path(f"{workspace_root}/data/processed/modeling/splits")
    out_dir.mkdir(parents=True, exist_ok=True)
    matched.to_parquet(out_dir / "source_matched_support_2020.parquet", index=False)
    return matched

def fit_baseline(block, target, experiment, workspace_root="."):
    # Fit baseline on 2016-2019
    df_train = load_data(block, experiment, target, [], "2016-01-01", "2019-12-31", meta_cols=["date", target])
    df_train["month"] = pd.to_datetime(df_train["date"]).dt.month
    
    if block == "TRANSFER":
        monthly_stats = df_train.groupby("month")[target].mean().to_dict()
        baseline_name = "monthly_train_mean"
    else:
        monthly_stats = df_train.groupby("month")[target].median().to_dict()
        baseline_name = "monthly_train_median"
        
    return baseline_name, monthly_stats

def main():
    workspace = "."
    out_dir = Path(workspace) / "reports" / "modeling" / "final_2020"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Ensure matched support exists
    matched_keys = compute_matched_support(workspace)
    
    # 2. Iterate over all 14 RF-05 models
    models_dir = Path(workspace) / "reports" / "modeling" / "models" / "final_refit_2016_2019"
    meta_files = list(models_dir.rglob("metadata.json"))
    
    final_metrics = []
    target_dists = []
    
    for meta_path in meta_files:
        with open(meta_path) as f:
            meta = json.load(f)
            
        block = meta["diagnostic_block"]
        experiment = meta["experiment"]
        target = meta["target"]
        support = meta["support_mode"]
        features = meta["fitted_features"]
        
        print(f"Evaluating 2020 for {block} / {experiment} / {target} / {support} ...")
        
        # Load Model
        model = joblib.load(meta_path.parent / "model.joblib")
        
        # Load 2020 Data
        coord_cols = ["y_index", "x_index"] if block in ["SOURCE", "TRANSFER"] else ["gleam_y_index", "gleam_x_index"]
        df_test = load_data(block, experiment, target, features, "2020-01-01", "2020-12-31", meta_cols=["date"] + coord_cols, allow_2020=True)
        
        if support == "matched_support":
            df_test = pd.merge(df_test, matched_keys, on=["date", "y_index", "x_index"], how="inner")
            
        assert df_test["date"].min() >= pd.to_datetime("2020-01-01")
        assert df_test["date"].max() <= pd.to_datetime("2020-12-31")
        
        X_test = df_test[features]
        y_true = df_test[target].values
        
        # Target Distribution
        y_series = pd.Series(y_true)
        target_dists.append({
            "block": block,
            "experiment": experiment,
            "target": target,
            "support": support,
            "N": len(y_series),
            "mean": y_series.mean(),
            "median": y_series.median(),
            "std": y_series.std(),
            "p05": y_series.quantile(0.05),
            "p25": y_series.quantile(0.25),
            "p75": y_series.quantile(0.75),
            "p95": y_series.quantile(0.95),
            "fraction_lt_0": (y_series < 0).mean(),
            "fraction_eq_0": (y_series == 0).mean(),
            "fraction_gt_0": (y_series > 0).mean(),
        })
        
        # Predict RF
        y_pred = model.predict(X_test)
        
        # RF Metrics
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        bias = np.mean(y_pred - y_true)
        
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        pearson_r = np.corrcoef(y_true, y_pred)[0, 1] if np.std(y_true) > 0 and np.std(y_pred) > 0 else 0
        
        # Fit & Predict Baseline
        baseline_name, monthly_stats = fit_baseline(block, target, experiment, workspace)
        months = pd.to_datetime(df_test["date"]).dt.month
        y_base = months.map(monthly_stats).values
        
        base_mae = np.mean(np.abs(y_true - y_base))
        base_rmse = np.sqrt(np.mean((y_true - y_base)**2))
        
        mae_skill = 1 - (mae / base_mae) if base_mae > 0 else 0
        rmse_skill = 1 - (rmse / base_rmse) if base_rmse > 0 else 0
        
        final_metrics.append({
            "block": block,
            "experiment": experiment,
            "target": target,
            "support": support,
            "model": meta["rf_configuration"],
            "N": len(y_true),
            "MAE": mae,
            "RMSE": rmse,
            "bias": bias,
            "R2": r2,
            "pearson_r": pearson_r,
            "baseline_name": baseline_name,
            "baseline_MAE": base_mae,
            "baseline_RMSE": base_rmse,
            "MAE_skill": mae_skill,
            "RMSE_skill": rmse_skill,
        })
        
    df_metrics = pd.DataFrame(final_metrics)
    df_metrics.to_csv(out_dir / "final_metrics_2020.csv", index=False)
    print("Saved final_metrics_2020.csv")
    
    Path(out_dir / "target_distributions").mkdir(parents=True, exist_ok=True)
    df_dists = pd.DataFrame(target_dists)
    df_dists.to_csv(out_dir / "target_distributions" / "target_distributions_2020.csv", index=False)
    print("Saved target_distributions_2020.csv")

if __name__ == "__main__":
    main()
