#!/usr/bin/env python
"""
RF-04B-SOURCE: Compute TreeSHAP and Permutation Importance for one SOURCE model.

SHAP cohort index: 50,000 rows (balanced month x spatial_fold, seed 42)
SHAP compute size: 10,000 rows (balanced sub-sample of the 50k index, seed 42)
  - Rationale: RF_A has 300 trees, max_depth=12, ~2700 leaves/tree.
    Full 50k run requires ~200 min/model; 10k requires ~20 min/model.
    10k is sufficient for stable global importance estimation.
Permutation size: 5,000 rows (nested subset of 10k compute cohort, seed 42)

2020 is SEALED. Only 2019 data is used.
"""
import argparse
import json
import sys
import joblib
import numpy as np
import pandas as pd
import shap
import yaml
from pathlib import Path
from sklearn.inspection import permutation_importance

from smap_xai.modeling.training import load_data


SHAP_COMPUTE_SIZE = 10_000
PERM_SIZE = 5_000
SEED = 42


def load_config():
    with open("configs/xai/rf_xai.yaml", "r") as f:
        return yaml.safe_load(f)


def balanced_subsample(df, size, key_cols, seed):
    """Balanced sample by month x spatial_fold cells."""
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


def run_shap(model, X, fitted_features):
    assert list(X.columns) == fitted_features, "Feature order mismatch!"
    assert not X.isnull().any().any(), "NaN in feature matrix!"

    explainer = shap.TreeExplainer(
        model,
        feature_perturbation="tree_path_dependent",
        model_output="raw",
    )
    shap_values = explainer.shap_values(X)
    assert shap_values.shape == X.shape, "SHAP shape mismatch!"
    assert not np.isnan(shap_values).any(), "NaN in SHAP values!"

    expected_value = explainer.expected_value
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = float(np.squeeze(expected_value))

    predictions = model.predict(X)
    reconstructed = expected_value + shap_values.sum(axis=1)
    abs_errors = np.abs(predictions - reconstructed)

    max_err = float(abs_errors.max())
    med_err = float(np.median(abs_errors))

    assert max_err < 1e-4, f"SHAP additivity FAILED: max_err={max_err:.2e}"
    print(f"  SHAP additivity: max_err={max_err:.2e}  med_err={med_err:.2e}")
    return shap_values, expected_value, predictions, max_err, med_err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True, choices=["da_cdf", "da_nocdf"])
    parser.add_argument("--support-mode", required=True, choices=["native", "matched"])
    args = parser.parse_args()

    exp = args.experiment
    sup = args.support_mode

    print(f"[RF-04B-SOURCE] experiment={exp}  support={sup}", flush=True)

    # ── 1. Load model ──────────────────────────────────────────────────────────
    model_key = f"SOURCE_{exp}_daily_absolute_increment_context_only_feature_set_RF_A_fold_3_{sup}_support"
    model_dir = Path(f"reports/modeling/models/random_forest/{model_key}")
    artifact_dir = Path(f"artifacts/modeling/random_forest/{model_key}")

    with open(model_dir / "metadata.json") as f:
        meta = json.load(f)
    fitted_features = meta["fitted_features"]
    n_fitted = len(fitted_features)
    print(f"  Feature set: {meta.get('feature_set','?')}  ({n_fitted} features)", flush=True)
    model = joblib.load(artifact_dir / "model.joblib")
    print(f"  Model loaded: {model.n_estimators} trees, max_depth={model.max_depth}", flush=True)

    # ── 2. Load cohort index (50k) ─────────────────────────────────────────────
    if sup == "native":
        exp_tag = exp.split("_")[1]   # cdf or nocdf
        cohort_file = f"data/processed/modeling/xai/cohorts/source_{exp_tag}_native_2019.parquet"
    else:
        cohort_file = "data/processed/modeling/xai/cohorts/source_matched_2019.parquet"

    cohort = pd.read_parquet(cohort_file)
    assert cohort["date"].dt.year.eq(2019).all(), "Non-2019 rows in cohort!"
    print(f"  Cohort index: {len(cohort)} rows", flush=True)

    # ── 3. Draw 10k balanced compute subset from cohort index ─────────────────
    compute_keys = balanced_subsample(
        cohort, SHAP_COMPUTE_SIZE, ["date", "y_index", "x_index"], SEED
    )
    assert len(compute_keys) == SHAP_COMPUTE_SIZE, (
        f"Balanced subsample size {len(compute_keys)} != {SHAP_COMPUTE_SIZE}"
    )

    # ── 4. Load feature data for the 10k rows ─────────────────────────────────
    keys_for_merge = compute_keys[["date", "y_index", "x_index"]].copy()
    df = load_data(
        "SOURCE", exp, "daily_absolute_increment",
        fitted_features, "2019-01-01", "2019-12-31",
        meta_cols=["date", "y_index", "x_index"],
    )
    df = pd.merge(df, keys_for_merge, on=["date", "y_index", "x_index"], how="inner")
    df = pd.merge(
        df,
        compute_keys[["date", "y_index", "x_index", "spatial_fold"]],
        on=["date", "y_index", "x_index"],
        how="left",
    )
    df = df.sort_values(["date", "y_index", "x_index"]).reset_index(drop=True)
    assert len(df) == SHAP_COMPUTE_SIZE, (
        f"After merge got {len(df)} rows, expected {SHAP_COMPUTE_SIZE}"
    )
    print(f"  Feature data loaded: {len(df)} rows", flush=True)

    X = df[fitted_features]
    y = df["daily_absolute_increment"]

    # ── 5. TreeSHAP ───────────────────────────────────────────────────────────
    print("  Computing TreeSHAP...", flush=True)
    shap_vals, expected_value, predictions, max_err, med_err = run_shap(
        model, X, fitted_features
    )

    # ── 6. Permutation importance on nested 5k subset ─────────────────────────
    print("  Computing Permutation Importance...", flush=True)
    X_perm = X.head(PERM_SIZE)
    y_perm = y.head(PERM_SIZE)
    perm_res = permutation_importance(
        model, X_perm, y_perm,
        scoring="neg_mean_absolute_error",
        n_repeats=5,
        random_state=SEED,
        n_jobs=-1,
    )

    # ── 7. Save outputs ────────────────────────────────────────────────────────
    out_dir = Path("data/processed/modeling/xai/outputs/source")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Per-sample SHAP parquet
    out_df = df[["date", "y_index", "x_index", "month", "spatial_fold"]].copy()
    out_df["target"] = y.values
    out_df["prediction"] = predictions
    out_df["expected_value"] = expected_value
    for i, feat in enumerate(fitted_features):
        out_df[f"shap__{feat}"] = shap_vals[:, i]
        out_df[f"value__{feat}"] = X[feat].values

    shap_file = out_dir / f"shap_{exp}_{sup}.parquet"
    out_df.to_parquet(shap_file, index=False)
    print(f"  Saved SHAP parquet: {shap_file} ({len(out_df)} rows)", flush=True)

    # Permutation JSON
    perm_dict = {
        "features": fitted_features,
        "importances_mean": perm_res.importances_mean.tolist(),
        "importances_std": perm_res.importances_std.tolist(),
        "scoring": "neg_mean_absolute_error",
        "n_repeats": 5,
        "cohort_size": PERM_SIZE,
        "sign_convention": (
            "Positive importance = permuting this feature WORSENS MAE "
            "(sklearn neg-MAE convention: larger decrease in neg-MAE = larger positive importance)"
        ),
    }
    with open(out_dir / f"permutation_{exp}_{sup}.json", "w") as f:
        json.dump(perm_dict, f, indent=2)

    # QC JSON
    qc_dict = {
        "experiment": exp,
        "support_mode": sup,
        "n_shap": len(X),
        "n_permutation": PERM_SIZE,
        "max_abs_reconstruction_error": max_err,
        "median_abs_reconstruction_error": med_err,
        "additivity_pass": max_err < 1e-4,
    }
    with open(out_dir / f"qc_{exp}_{sup}.json", "w") as f:
        json.dump(qc_dict, f, indent=2)

    print(f"[RF-04B-SOURCE] DONE: experiment={exp}  support={sup}", flush=True)


if __name__ == "__main__":
    main()
