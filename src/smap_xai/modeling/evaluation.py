import pandas as pd
import numpy as np
from smap_xai.modeling.metrics import ChunkedRegressionMetrics, compute_relative_skill

def evaluate_model(y_true: pd.Series, y_pred: pd.Series, baseline_metrics: dict) -> dict:
    metrics_calc = ChunkedRegressionMetrics()
    metrics_calc.update(y_true, y_pred)
    model_metrics = metrics_calc.compute()
    
    skill = compute_relative_skill(model_metrics, {"MAE": baseline_metrics["baseline_MAE"], "RMSE": baseline_metrics["baseline_RMSE"]})
    
    return {**model_metrics, **skill}

def load_baseline_metrics(dataset: str, experiment: str, target: str, baseline_reference: str, fold: str = "fold_3", workspace_root: str = ".", baseline_type: str = "temporal") -> dict:
    if baseline_type == "temporal":
        df = pd.read_csv(f"{workspace_root}/reports/modeling/baselines/temporal_baseline_metrics.csv")
        mask = (df["dataset"] == dataset) & (df["experiment"] == experiment) & (df["target"] == target) & (df["baseline"] == baseline_reference) & (df["fold"] == fold)
    elif baseline_type == "spatial":
        df = pd.read_csv(f"{workspace_root}/reports/modeling/baselines/spatial_baseline_metrics.csv")
        mask = (df["dataset"] == dataset) & (df["experiment"] == experiment) & (df["target"] == target) & (df["baseline"] == baseline_reference) & (df["fold"] == fold)
    else:
        raise ValueError(f"Unknown baseline_type {baseline_type}")
    if not np.any(mask):
        raise ValueError(f"Baseline {baseline_reference} not found for {dataset} {experiment} {target} {fold}")
    row = df[mask].iloc[0]
    return {
        "baseline_reference": baseline_reference,
        "baseline_MAE": row["MAE"],
        "baseline_RMSE": row["RMSE"]
    }
