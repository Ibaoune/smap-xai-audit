#!/usr/bin/env python
"""
RF-04B-VALUE: Compute TreeSHAP and Permutation Importance for one VALUE model.

VALUE-specific notes:
  - Grid identifiers: gleam_y_index, gleam_x_index  (GLEAM-native grid, NOT Noah-MP)
  - Target: value_ae = |ET_OPL - ET_GLEAM| - |ET_DA - ET_GLEAM|
  - Feature set: value_context_feature_set  (52 active predictors)
  - RF configuration: RF_B (n_est=300, max_depth=16, min_samples_leaf=5)
  - GLEAM is an external evaluation reference — NOT ground truth
  - Cohort checksum computed on gleam_y_index / gleam_x_index keys

Frozen compute settings:
  representative cohort = 50,000
  SHAP compute subset   = 10,000  (balanced month x spatial_fold, seed 42)
  permutation subset    =  5,000

2020 is SEALED.
"""
import argparse
import json
import joblib
import numpy as np
import pandas as pd
import shap
from pathlib import Path
from sklearn.inspection import permutation_importance

from smap_xai.modeling.training import load_data

EXPS   = ["da_cdf", "da_nocdf"]
TARGET = "value_ae"
SHAP_COMPUTE_SIZE = 10_000
PERM_SIZE         =  5_000
SEED              = 42
COHORT_CHECKSUM   = "fb68bb1122ffa6ee11490c122b239c7f"   # MD5 on sorted date+gleam_y+gleam_x (smap-xai-audit env, Python 3.11)
SPATIAL_ID_COLS   = ["gleam_y_index", "gleam_x_index"]   # VALUE uses GLEAM-native grid


def balanced_subsample(df, size, seed):
    """Balanced sample by month × spatial_fold (frozen RF-04A rule)."""
    cells     = df.groupby(["month", "spatial_fold"])
    n_cells   = df[["month", "spatial_fold"]].drop_duplicates().shape[0]
    per_cell  = size // n_cells
    remainder = size % n_cells
    parts = []
    for i, (_, g) in enumerate(cells):
        n = per_cell + (1 if i < remainder else 0)
        n = min(n, len(g))
        parts.append(g.sample(n=n, random_state=seed))
    return pd.concat(parts).sort_values(["date"] + SPATIAL_ID_COLS).reset_index(drop=True)


def verify_cohort_checksum(cohort):
    import hashlib
    keys = cohort.sort_values(["date"] + SPATIAL_ID_COLS)[["date"] + SPATIAL_ID_COLS].copy()
    keys["date_str"] = keys["date"].astype(str)
    cs = hashlib.md5(
        keys[["date_str"] + SPATIAL_ID_COLS].to_csv(index=False).encode()
    ).hexdigest()
    assert cs == COHORT_CHECKSUM, f"Cohort checksum mismatch: {cs} != {COHORT_CHECKSUM}"
    return cs


def _shap_worker(model, X_chunk):
    import shap
    explainer = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent", model_output="raw")
    return explainer.shap_values(X_chunk, check_additivity=False)


def run_shap(model, X, fitted_features):
    from joblib import Parallel, delayed
    import multiprocessing
    assert list(X.columns) == fitted_features, "Feature order mismatch!"
    assert not X.isnull().any().any(), "NaN in feature matrix!"
    
    # Parallelize over 16 chunks
    n_jobs = 16
    chunks = np.array_split(X, n_jobs)
    print(f"    Running SHAP on {n_jobs} cores in parallel...", flush=True)
    results = Parallel(n_jobs=n_jobs)(delayed(_shap_worker)(model, chunk) for chunk in chunks)
    shap_values = np.vstack(results)
    
    explainer = shap.TreeExplainer(
        model, feature_perturbation="tree_path_dependent", model_output="raw"
    )
    assert shap_values.shape == X.shape
    assert not np.isnan(shap_values).any(), "NaN in SHAP values!"
    ev = explainer.expected_value
    if isinstance(ev, (list, np.ndarray)):
        ev = float(np.squeeze(ev))
    preds  = model.predict(X)
    errors = np.abs(preds - (ev + shap_values.sum(axis=1)))
    max_err = float(errors.max())
    med_err = float(np.median(errors))
    assert max_err < 1e-4, f"SHAP additivity FAILED: max_err={max_err:.2e}"
    print(f"  SHAP additivity: max_err={max_err:.2e}  med_err={med_err:.2e}", flush=True)
    return shap_values, ev, preds, max_err, med_err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True, choices=EXPS)
    args = parser.parse_args()
    exp = args.experiment
    print(f"[RF-04B-VALUE] experiment={exp}  target={TARGET}", flush=True)

    # ── 1. Load model ──────────────────────────────────────────────────────────
    model_key = (
        f"VALUE_{exp}_{TARGET}_value_context_feature_set_RF_B_fold_3_native_support"
    )
    model_dir    = Path(f"reports/modeling/models/random_forest/{model_key}")
    artifact_dir = Path(f"artifacts/modeling/random_forest/{model_key}")

    with open(model_dir / "metadata.json") as f:
        meta = json.load(f)
    fitted_features = meta["fitted_features"]
    n_fitted        = len(fitted_features)
    feature_set     = meta.get("feature_set", "?")
    print(f"  Feature set: {feature_set}  ({n_fitted} features)", flush=True)

    model = joblib.load(artifact_dir / "model.joblib")
    print(
        f"  Model loaded: {model.n_estimators} trees  "
        f"max_depth={model.max_depth}  min_samples_leaf={model.min_samples_leaf}",
        flush=True,
    )

    # ── 2. Load and verify common cohort ──────────────────────────────────────
    cohort = pd.read_parquet(
        "data/processed/modeling/xai/cohorts/value_2019.parquet"
    )
    assert len(cohort) == 50_000, f"Expected 50k cohort, got {len(cohort)}"
    assert cohort["date"].dt.year.eq(2019).all(), "Non-2019 rows in cohort!"
    cs = verify_cohort_checksum(cohort)
    print(f"  Cohort checksum: {cs} ✓", flush=True)

    # ── 3. Draw 10k balanced compute subset ────────────────────────────────────
    compute_keys = balanced_subsample(cohort, SHAP_COMPUTE_SIZE, SEED)
    assert len(compute_keys) == SHAP_COMPUTE_SIZE

    # ── 4. Load feature data for the 10k rows ─────────────────────────────────
    df = load_data(
        "VALUE", exp, TARGET, fitted_features,
        "2019-01-01", "2019-12-31",
        meta_cols=["date"] + SPATIAL_ID_COLS,
    )
    merge_on = ["date"] + SPATIAL_ID_COLS
    # Drop any month/spatial_fold load_data may already carry — take from cohort instead
    for col in ["month", "spatial_fold"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    df = pd.merge(
        df,
        compute_keys[merge_on + ["month", "spatial_fold"]],
        on=merge_on,
        how="inner",
    )
    df = df.sort_values(["date"] + SPATIAL_ID_COLS).reset_index(drop=True)
    assert len(df) == SHAP_COMPUTE_SIZE, (
        f"After merge: {len(df)} rows != {SHAP_COMPUTE_SIZE}"
    )
    assert df["date"].dt.year.eq(2019).all(), "Non-2019 rows after merge!"
    print(f"  Feature data loaded: {len(df)} rows", flush=True)

    X = df[fitted_features]
    y = df[TARGET]

    # ── 5. TreeSHAP ───────────────────────────────────────────────────────────
    print("  Computing TreeSHAP...", flush=True)
    shap_vals, ev, preds, max_err, med_err = run_shap(model, X, fitted_features)

    # ── 6. Permutation importance ─────────────────────────────────────────────
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
    out_dir = Path("data/processed/modeling/xai/outputs/value")
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{exp}_{TARGET}"

    # Per-sample SHAP parquet (retain GLEAM-native grid identifiers)
    out_df = df[["date"] + SPATIAL_ID_COLS + ["month", "spatial_fold"]].copy()
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
    with open(out_dir / f"permutation_{tag}.json", "w") as f:
        json.dump(
            {
                "features":          fitted_features,
                "importances_mean":  perm_res.importances_mean.tolist(),
                "importances_std":   perm_res.importances_std.tolist(),
                "scoring":           "neg_mean_absolute_error",
                "n_repeats":         5,
                "cohort_size":       PERM_SIZE,
                "cohort_checksum":   cs,
            },
            f,
            indent=2,
        )

    # QC JSON
    with open(out_dir / f"qc_{tag}.json", "w") as f:
        json.dump(
            {
                "experiment":                        exp,
                "target":                            TARGET,
                "n_shap":                            int(len(X)),
                "n_permutation":                     PERM_SIZE,
                "cohort_checksum":                   cs,
                "max_abs_reconstruction_error":      max_err,
                "median_abs_reconstruction_error":   med_err,
                "additivity_pass":                   max_err < 1e-4,
                "rf_config":                         "RF_B",
                "n_estimators":                      model.n_estimators,
                "max_depth":                         model.max_depth,
                "min_samples_leaf":                  model.min_samples_leaf,
            },
            f,
            indent=2,
        )

    print(f"[RF-04B-VALUE] DONE: experiment={exp}", flush=True)


if __name__ == "__main__":
    main()
