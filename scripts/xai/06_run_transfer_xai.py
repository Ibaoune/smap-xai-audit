#!/usr/bin/env python
"""
RF-04B-TRANSFER: Compute TreeSHAP and Permutation Importance for one TRANSFER model.

Common cohort: transfer_2019.parquet  (50k index)
SHAP compute subset: 10,000 rows (balanced month x spatial_fold, seed 42)
Permutation subset : 5,000 rows (first 5k from compute cohort, sorted)

All 8 models share the SAME 50k cohort index and the SAME 10k compute subset.
This is required for direct target-to-target and CDF-vs-NoCDF comparison.

2020 is SEALED. Only 2019 data is used.
"""
import argparse
import json
import joblib
import numpy as np
import pandas as pd
import shap
import yaml
from pathlib import Path
from sklearn.inspection import permutation_importance

from smap_xai.modeling.training import load_data

TARGETS = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
SHAP_COMPUTE_SIZE = 10_000
PERM_SIZE         = 5_000
SEED              = 42
COHORT_CHECKSUM   = "616d94379a06cbcefd1c32a3bc5acf6f"


def balanced_subsample(df, size, seed):
    """Balanced sample by month x spatial_fold cells (frozen RF-04A rule)."""
    cells    = df.groupby(["month", "spatial_fold"])
    n_cells  = df[["month", "spatial_fold"]].drop_duplicates().shape[0]
    per_cell = size // n_cells
    remainder = size % n_cells
    parts = []
    for i, (_, g) in enumerate(cells):
        n = per_cell + (1 if i < remainder else 0)
        n = min(n, len(g))
        parts.append(g.sample(n=n, random_state=seed))
    return pd.concat(parts).sort_values(["date", "y_index", "x_index"]).reset_index(drop=True)


def verify_cohort_checksum(cohort):
    import hashlib
    keys = cohort.sort_values(["date", "y_index", "x_index"])[["date", "y_index", "x_index"]].copy()
    keys["date_str"] = keys["date"].astype(str)
    cs = hashlib.md5(keys[["date_str", "y_index", "x_index"]].to_csv(index=False).encode()).hexdigest()
    assert cs == COHORT_CHECKSUM, f"Cohort checksum mismatch: {cs} != {COHORT_CHECKSUM}"
    return cs


def run_shap(model, X, fitted_features):
    assert list(X.columns) == fitted_features, "Feature order mismatch!"
    assert not X.isnull().any().any(), "NaN in feature matrix!"
    explainer   = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent", model_output="raw")
    shap_values = explainer.shap_values(X)
    assert shap_values.shape == X.shape, "SHAP shape mismatch!"
    assert not np.isnan(shap_values).any(), "NaN in SHAP values!"
    ev = explainer.expected_value
    if isinstance(ev, (list, np.ndarray)):
        ev = float(np.squeeze(ev))
    preds = model.predict(X)
    errors = np.abs(preds - (ev + shap_values.sum(axis=1)))
    max_err = float(errors.max())
    med_err = float(np.median(errors))
    assert max_err < 1e-4, f"SHAP additivity FAILED: max_err={max_err:.2e}"
    print(f"  SHAP additivity: max_err={max_err:.2e}  med_err={med_err:.2e}", flush=True)
    return shap_values, ev, preds, max_err, med_err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True, choices=["da_cdf", "da_nocdf"])
    parser.add_argument("--target",     required=True, choices=TARGETS)
    args = parser.parse_args()

    exp = args.experiment
    tgt = args.target
    print(f"[RF-04B-TRANSFER] experiment={exp}  target={tgt}", flush=True)

    # ── 1. Load model ──────────────────────────────────────────────────────────
    model_key  = f"TRANSFER_{exp}_{tgt}_source_context_feature_set_RF_A_fold_3_native_support"
    model_dir  = Path(f"reports/modeling/models/random_forest/{model_key}")
    artifact_dir = Path(f"artifacts/modeling/random_forest/{model_key}")

    with open(model_dir / "metadata.json") as f:
        meta = json.load(f)
    fitted_features = meta["fitted_features"]
    n_fitted = len(fitted_features)
    print(f"  Feature set: {meta.get('feature_set','?')}  ({n_fitted} features)", flush=True)

    model = joblib.load(artifact_dir / "model.joblib")
    print(f"  Model loaded: {model.n_estimators} trees, max_depth={model.max_depth}", flush=True)

    # ── 2. Load and verify common cohort ──────────────────────────────────────
    cohort = pd.read_parquet("data/processed/modeling/xai/cohorts/transfer_2019.parquet")
    assert len(cohort) == 50000, f"Expected 50k cohort, got {len(cohort)}"
    assert cohort["date"].dt.year.eq(2019).all(), "Non-2019 rows in cohort!"
    cs = verify_cohort_checksum(cohort)
    print(f"  Cohort checksum: {cs} ✓", flush=True)

    # ── 3. Draw 10k balanced compute subset ────────────────────────────────────
    compute_keys = balanced_subsample(cohort, SHAP_COMPUTE_SIZE, SEED)
    assert len(compute_keys) == SHAP_COMPUTE_SIZE, f"Subsample size {len(compute_keys)} != {SHAP_COMPUTE_SIZE}"

    # ── 4. Load feature data for 10k rows ─────────────────────────────────────
    df = load_data(
        "TRANSFER", exp, tgt, fitted_features,
        "2019-01-01", "2019-12-31",
        meta_cols=["date", "y_index", "x_index"],
    )
    df = pd.merge(df, compute_keys[["date", "y_index", "x_index"]], on=["date", "y_index", "x_index"], how="inner")
    df = pd.merge(df, compute_keys[["date", "y_index", "x_index", "spatial_fold"]], on=["date", "y_index", "x_index"], how="left")
    df = df.sort_values(["date", "y_index", "x_index"]).reset_index(drop=True)
    assert len(df) == SHAP_COMPUTE_SIZE, f"After merge: {len(df)} rows != {SHAP_COMPUTE_SIZE}"
    print(f"  Feature data loaded: {len(df)} rows", flush=True)

    X = df[fitted_features]
    y = df[tgt]

    # ── 5. TreeSHAP ───────────────────────────────────────────────────────────
    print("  Computing TreeSHAP...", flush=True)
    shap_vals, ev, preds, max_err, med_err = run_shap(model, X, fitted_features)

    # ── 6. Permutation importance ─────────────────────────────────────────────
    print("  Computing Permutation Importance...", flush=True)
    X_perm = X.head(PERM_SIZE)
    y_perm = y.head(PERM_SIZE)
    perm_res = permutation_importance(
        model, X_perm, y_perm,
        scoring="neg_mean_absolute_error", n_repeats=5, random_state=SEED, n_jobs=-1,
    )

    # ── 7. Save outputs ────────────────────────────────────────────────────────
    out_dir = Path("data/processed/modeling/xai/outputs/transfer")
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{exp}_{tgt}"

    # Per-sample SHAP parquet
    out_df = df[["date", "y_index", "x_index", "month", "spatial_fold"]].copy()
    out_df["target"]         = y.values
    out_df["prediction"]     = preds
    out_df["expected_value"] = ev
    for i, feat in enumerate(fitted_features):
        out_df[f"shap__{feat}"]  = shap_vals[:, i]
        out_df[f"value__{feat}"] = X[feat].values

    shap_file = out_dir / f"shap_{tag}.parquet"
    out_df.to_parquet(shap_file, index=False)
    print(f"  Saved: {shap_file}", flush=True)

    # Permutation JSON
    perm_dict = {
        "features":           fitted_features,
        "importances_mean":   perm_res.importances_mean.tolist(),
        "importances_std":    perm_res.importances_std.tolist(),
        "scoring":            "neg_mean_absolute_error",
        "n_repeats":          5,
        "cohort_size":        PERM_SIZE,
        "cohort_checksum":    cs,
    }
    with open(out_dir / f"permutation_{tag}.json", "w") as f:
        json.dump(perm_dict, f, indent=2)

    # QC JSON
    qc = {
        "experiment":                    exp,
        "target":                        tgt,
        "n_shap":                        len(X),
        "n_permutation":                 PERM_SIZE,
        "cohort_checksum":               cs,
        "max_abs_reconstruction_error":  max_err,
        "median_abs_reconstruction_error": med_err,
        "additivity_pass":               max_err < 1e-4,
    }
    with open(out_dir / f"qc_{tag}.json", "w") as f:
        json.dump(qc, f, indent=2)

    print(f"[RF-04B-TRANSFER] DONE: experiment={exp}  target={tgt}", flush=True)


if __name__ == "__main__":
    main()
