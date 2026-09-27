import pandas as pd
import numpy as np
from smap_xai.modeling.metrics import ChunkedRegressionMetrics, compute_relative_skill

def evaluate_model(y_true: pd.Series, y_pred: pd.Series, baseline_metrics: dict) -> dict:
    metrics_calc = ChunkedRegressionMetrics()
    metrics_calc.update(y_true, y_pred)
    model_metrics = metrics_calc.compute()

    skill = compute_relative_skill(model_metrics, {"MAE": baseline_metrics["baseline_MAE"], "RMSE": baseline_metrics["baseline_RMSE"]})

    return {**model_metrics, **skill}

def load_baseline_metrics(dataset: str, experiment: str, target: str, baseline_reference: str, fold: str = "fold_3", workspace_root: str = ".", baseline_type: str = "temporal", support_mode: str = "native_support") -> dict:
    if support_mode == "matched_support":
        if dataset != "SOURCE":
            raise ValueError("Matched support baseline is only defined for SOURCE dataset.")

        path = f"{workspace_root}/reports/modeling/baselines/source_matched_support_metrics.csv"
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Exact matched baseline file not found: {path}")

        mask = (df["experiment"] == experiment)
        if not np.any(mask):
            raise ValueError(f"Matched baseline not found for experiment {experiment}")

        row = df[mask].iloc[0]

        if baseline_reference == "monthly_train_median":
            mae_col = "monthly_train_median_MAE"
            rmse_col = "monthly_train_median_RMSE"
        else:
            raise ValueError(f"Unknown matched baseline reference: {baseline_reference}")

        return {
            "baseline_reference": baseline_reference,
            "baseline_MAE": row[mae_col],
            "baseline_RMSE": row[rmse_col]
        }

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
