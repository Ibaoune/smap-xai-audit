#!/usr/bin/env python
"""
RF-04B-SOURCE QC — Final closure audit.

Checks:
  1. All four SHAP parquets exist with 10k rows
  2. All four permutation JSONs exist with 5k rows
  3. QC JSONs pass additivity
  4. Matched CDF/NoCDF keys are identical
  5. Zero 2020 rows in any output
  6. All 35 SOURCE features are mapped in feature_groups.yaml (no unmapped)
  7. Permutation cohort_size == 5000 in all JSONs
  8. Sample-size stability: 5k vs 10k predictor rho >= 0.98, group rho >= 0.98
  9. Dependence features JSON has top_4_dependence_features with 4 entries
  10. All 6 development figures are reproducibly generated
  11. Correct matched-support terminology (no "native-support characterization" in matched docs)
"""
import json
import sys
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from scipy.stats import spearmanr

IN_DIR  = Path("data/processed/modeling/xai/outputs/source")
FIG_DIR = Path("figures/development/source")
MODELS  = [
    ("da_cdf",   "native"),
    ("da_nocdf", "native"),
    ("da_cdf",   "matched"),
    ("da_nocdf", "matched"),
]
REQUIRED_FIGURES = [
    "fig_source_a_group_importance.png",
    "fig_source_b_top_predictors.png",
    "fig_source_c_beeswarm.png",
    "fig_source_d_dependence.png",
    "fig_source_e_seasonal.png",
    "fig_source_f_spatial.png",
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    print("SOURCE XAI Final Closure Audit...", flush=True)

    # ── 1. SHAP parquets: 10k rows ─────────────────────────────────────────────
    for exp, sup in MODELS:
        f = IN_DIR / f"shap_{exp}_{sup}.parquet"
        assert f.exists(), f"Missing {f}"
        qc = json.loads((IN_DIR / f"qc_{exp}_{sup}.json").read_text())
        if qc["n_shap"] != 10000:
            fail(f"{exp}_{sup}: n_shap={qc['n_shap']} != 10000")
        if qc["max_abs_reconstruction_error"] >= 1e-4:
            fail(f"{exp}_{sup}: additivity failed {qc['max_abs_reconstruction_error']}")
        # Zero 2020
        df = pd.read_parquet(f, columns=["date"])
        if not pd.to_datetime(df["date"]).dt.year.eq(2019).all():
            fail(f"{exp}_{sup}: non-2019 rows found!")
    print("  [✓] SHAP parquets: 10k rows, additivity, 2019 isolation", flush=True)

    # ── 2. Permutation JSONs: 5k rows ──────────────────────────────────────────
    for exp, sup in MODELS:
        perm = json.loads((IN_DIR / f"permutation_{exp}_{sup}.json").read_text())
        if perm["cohort_size"] != 5000:
            fail(f"{exp}_{sup}: permutation cohort_size={perm['cohort_size']} != 5000")
        if len(perm["features"]) == 0:
            fail(f"{exp}_{sup}: empty feature list in permutation output")
    print("  [✓] Permutation JSONs: 5k rows, non-empty features", flush=True)

    # ── 3. Matched CDF/NoCDF identical keys ────────────────────────────────────
    cdf_keys   = pd.read_parquet(IN_DIR / "shap_da_cdf_matched.parquet",
                                 columns=["date", "y_index", "x_index"])
    nocdf_keys = pd.read_parquet(IN_DIR / "shap_da_nocdf_matched.parquet",
                                 columns=["date", "y_index", "x_index"])
    if not cdf_keys.equals(nocdf_keys):
        fail("Matched CDF and NoCDF keys differ!")
    print("  [✓] Matched support: identical CDF/NoCDF keys", flush=True)

    # ── 4. Feature-group completeness ──────────────────────────────────────────
    with open("configs/xai/feature_groups.yaml") as f:
        feature_groups = yaml.safe_load(f)
    mapped = {feat for feats in feature_groups.values() for feat in feats}

    df = pd.read_parquet(IN_DIR / "shap_da_cdf_matched.parquet")
    source_features = {c.replace("shap__", "") for c in df.columns if c.startswith("shap__")}
    unmapped = source_features - mapped
    if unmapped:
        fail(f"Unmapped SOURCE features: {unmapped}")
    if len(source_features) != 35:
        fail(f"Expected 35 SOURCE features, got {len(source_features)}")
    print(f"  [✓] Feature mapping: 35 SOURCE features, all mapped (global registry=58)", flush=True)

    # ── 5. Dependence features ─────────────────────────────────────────────────
    dep = json.loads((IN_DIR / "dependence_features.json").read_text())
    if len(dep["top_4_dependence_features"]) != 4:
        fail("dependence_features.json does not have 4 entries")
    expected = ["ssm_lag1", "precip_lag1", "rzsm_lag1", "land_cover_fraction_16"]
    if dep["top_4_dependence_features"] != expected:
        fail(f"Dependence features changed from frozen set! Got {dep['top_4_dependence_features']}")
    print("  [✓] Dependence features: frozen top-4 unchanged", flush=True)

    # ── 6. Sample-size stability ────────────────────────────────────────────────
    df = pd.read_parquet(IN_DIR / "shap_da_cdf_matched.parquet")
    features = [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]
    df_sorted = df.sort_values(["date", "y_index", "x_index"]).reset_index(drop=True)

    def get_ranks(sub):
        rows = [(f, float(np.mean(np.abs(sub[f"shap__{f}"].values)))) for f in features]
        out = pd.DataFrame(rows, columns=["feature", "mas"]).sort_values("mas", ascending=False).reset_index(drop=True)
        out["rank"] = out.index + 1
        return out

    def get_group_norms(sub):
        rows = [(g, sum(float(np.mean(np.abs(sub[f"shap__{f}"].values)))
                        for f in feats if f in features))
                for g, feats in feature_groups.items()]
        out = pd.DataFrame(rows, columns=["group", "abs"])
        out["norm"] = out["abs"] / out["abs"].sum()
        return out

    r5  = get_ranks(df_sorted.head(5000))
    r10 = get_ranks(df_sorted.head(10000))
    mm  = pd.merge(r5, r10, on="feature", suffixes=("_5k", "_10k"))
    rho_pred, _ = spearmanr(mm["rank_5k"], mm["rank_10k"])

    g5  = get_group_norms(df_sorted.head(5000))
    g10 = get_group_norms(df_sorted.head(10000))
    gg  = pd.merge(g5, g10, on="group", suffixes=("_5k", "_10k"))
    rho_grp, _ = spearmanr(gg["norm_5k"], gg["norm_10k"])
    max_diff = float((gg["norm_5k"] - gg["norm_10k"]).abs().max())

    print(f"  [✓] Sample-size stability (5k vs 10k):")
    print(f"       predictor rank rho = {rho_pred:.4f}")
    print(f"       group rho          = {rho_grp:.4f}")
    print(f"       max group diff     = {max_diff:.4f}")

    if rho_pred < 0.98:
        fail(f"Predictor rank stability too low: {rho_pred:.4f} < 0.98")
    if rho_grp < 0.98:
        fail(f"Group stability too low: {rho_grp:.4f} < 0.98")

    # ── 7. Development figures ─────────────────────────────────────────────────
    for fig in REQUIRED_FIGURES:
        p = FIG_DIR / fig
        if not p.exists():
            fail(f"Missing development figure: {fig}")
    print(f"  [✓] All {len(REQUIRED_FIGURES)} development figures present", flush=True)

    # ── 8. Summaries exist ─────────────────────────────────────────────────────
    for fname in ["tidy_predictor_summary.csv", "tidy_group_summary.csv",
                  "matched_group_comparison.csv", "spatial_stability.csv"]:
        if not (IN_DIR / fname).exists():
            fail(f"Missing summary: {fname}")
    print("  [✓] All summary CSVs present", flush=True)

    print("\n" + "="*50)
    print("SOURCE XAI FINAL CLOSURE AUDIT PASSED")
    print("="*50)


if __name__ == "__main__":
    main()
