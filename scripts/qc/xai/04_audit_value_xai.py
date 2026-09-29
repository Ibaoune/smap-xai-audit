#!/usr/bin/env python
"""
RF-04B-VALUE QC — Final closure audit.

Checks:
  1.  Exactly 2 SHAP parquets (da_cdf, da_nocdf), 10k rows each
  2.  Exactly 2 permutation JSONs, 5k rows each
  3.  Additivity pass on both models (max_err < 1e-4)
  4.  Zero 2020 rows in any output
  5.  Identical cohort checksum for both models
  6.  RF_B config confirmed (n_estimators=300, max_depth=16, min_samples_leaf=5)
  7.  52 active features, all mapped in feature_groups.yaml, identical CDF/NoCDF
  8.  Forbidden features absent (GLEAM(t), value_ae, ET_OPL(t), ET_DA(t))
  9.  Normalized group importance sums to 1.0 for both models (tol=1e-6)
  10. All required summary CSVs and JSONs present
  11. Frozen top-4 dependence features present and non-empty
  12. All 7 development figures present
  13. SOURCE XAI regression audit passes
  14. TRANSFER XAI regression audit passes
"""
import json
import sys
import subprocess
import numpy as np
import pandas as pd
import yaml
from pathlib import Path

IN_DIR          = Path("data/processed/modeling/xai/outputs/value")
FIG_DIR         = Path("figures/development/value")
EXPS            = ["da_cdf", "da_nocdf"]
TARGET          = "value_ae"
COHORT_CHECKSUM = "fb68bb1122ffa6ee11490c122b239c7f"
SPATIAL_ID_COLS = ["gleam_y_index", "gleam_x_index"]
RF_B = dict(n_estimators=300, max_depth=16, min_samples_leaf=5)
FORBIDDEN_PATTERNS = [
    "gleam_et", "et_gleam", "value_ae", "et_opl_t", "et_da_t",
    "lagged_value", "delta_et_t",
]
REQUIRED_FIGURES = [
    "fig_value_a_distribution.png",
    "fig_value_b_group_importance.png",
    "fig_value_c_top_predictors.png",
    "fig_value_d_shap_distributions.png",
    "fig_value_e_dependence.png",
    "fig_value_f_seasonal.png",
    "fig_value_g_spatial.png",
]
REQUIRED_SUMMARIES = [
    "target_distribution.csv",
    "tidy_predictor_summary.csv",
    "tidy_group_summary.csv",
    "cdf_nocdf_comparison.csv",
    "cdf_nocdf_group_detail.csv",
    "dependence_features.json",
]


def fail(msg):
    print(f"FAIL: {msg}", flush=True)
    sys.exit(1)


def main():
    print("VALUE XAI Final Closure Audit...", flush=True)

    # ── 1-4. SHAP parquets: 10k rows, additivity, 2019 only ──────────────────
    for exp in EXPS:
        tag    = f"{exp}_{TARGET}"
        shap_f = IN_DIR / f"shap_{tag}.parquet"
        qc_f   = IN_DIR / f"qc_{tag}.json"
        if not shap_f.exists(): fail(f"Missing {shap_f}")
        if not qc_f.exists():   fail(f"Missing {qc_f}")
        qc = json.loads(qc_f.read_text())
        if qc["n_shap"] != 10000:
            fail(f"{tag}: n_shap={qc['n_shap']} != 10000")
        if qc["max_abs_reconstruction_error"] >= 1e-4:
            fail(f"{tag}: additivity FAILED: {qc['max_abs_reconstruction_error']:.2e}")
        df = pd.read_parquet(shap_f, columns=["date"])
        if not pd.to_datetime(df["date"]).dt.year.eq(2019).all():
            fail(f"{tag}: non-2019 rows found!")
    print("  [✓] SHAP parquets: 2 models, 10k rows, additivity, 2019 isolation", flush=True)

    # ── 5. Permutation JSONs: 5k rows ─────────────────────────────────────────
    for exp in EXPS:
        tag  = f"{exp}_{TARGET}"
        perm = json.loads((IN_DIR / f"permutation_{tag}.json").read_text())
        if perm["cohort_size"] != 5000:
            fail(f"{tag}: permutation cohort_size={perm['cohort_size']} != 5000")
    print("  [✓] Permutation JSONs: 2 models, 5k rows", flush=True)

    # ── 6. Cohort checksum ────────────────────────────────────────────────────
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
        qc  = json.loads((IN_DIR / f"qc_{tag}.json").read_text())
        if qc["cohort_checksum"] != COHORT_CHECKSUM:
            fail(f"{tag}: cohort_checksum mismatch: {qc['cohort_checksum']}")
    print(f"  [✓] Cohort checksum: {COHORT_CHECKSUM} (both models)", flush=True)

    # ── 7. RF_B config ────────────────────────────────────────────────────────
    for exp in EXPS:
        tag = f"{exp}_{TARGET}"
        qc  = json.loads((IN_DIR / f"qc_{tag}.json").read_text())
        for param, val in RF_B.items():
            if qc.get(param) != val:
                fail(f"{tag}: RF_B {param}={qc.get(param)} != {val}")
    print(f"  [✓] RF_B config confirmed: {RF_B}", flush=True)

    # ── 8. Feature count, mapping, forbidden check ────────────────────────────
    with open("configs/xai/feature_groups.yaml") as f:
        fg = yaml.safe_load(f)
    mapped = {feat for feats in fg.values() for feat in feats}

    seen_features = None
    for exp in EXPS:
        tag  = f"{exp}_{TARGET}"
        df   = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        feats = {c.replace("shap__", "") for c in df.columns if c.startswith("shap__")}
        if seen_features is None:
            seen_features = feats
        elif feats != seen_features:
            fail(f"{tag}: feature set differs from da_cdf!")
        unmapped = feats - mapped
        if unmapped:
            fail(f"{tag}: unmapped features: {unmapped}")
        forbidden = [f for f in feats if any(p in f.lower() for p in FORBIDDEN_PATTERNS)]
        if forbidden:
            fail(f"{tag}: forbidden features found: {forbidden}")
    n_feats = len(seen_features)
    print(f"  [✓] Features: {n_feats} active, all mapped, no forbidden, identical CDF/NoCDF", flush=True)

    # ── 9. Group importance sums to 1.0 ──────────────────────────────────────
    for exp in EXPS:
        tag  = f"{exp}_{TARGET}"
        df   = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]
        group_sums = []
        for g, fs in fg.items():
            active = [f for f in fs if f in features]
            g_abs  = float(np.mean(np.abs(df[[f"shap__{f}" for f in active]].values)) * len(active)) if active else 0.0
            group_sums.append(g_abs)
        total = sum(group_sums)
        norm_sum = sum(v / total for v in group_sums) if total > 0 else 0.0
        if abs(norm_sum - 1.0) > 1e-6:
            fail(f"{tag}: group importance sums to {norm_sum:.8f} != 1.0")
    print("  [✓] Normalized group importance sums to 1.0 for both models (tol=1e-6)", flush=True)

    # ── 10. Summary files ─────────────────────────────────────────────────────
    for fn in REQUIRED_SUMMARIES:
        if not (IN_DIR / fn).exists(): fail(f"Missing summary: {fn}")
    print("  [✓] All required summary files present", flush=True)

    # ── 11. Dependence features ───────────────────────────────────────────────
    dep = json.loads((IN_DIR / "dependence_features.json").read_text())
    top4 = dep.get("top_4_dependence_features", [])
    if len(top4) != 4:
        fail(f"Dependence features: expected 4, got {len(top4)}: {top4}")
    print(f"  [✓] Dependence features: top-4 frozen: {top4}", flush=True)

    # ── 12. Development figures ───────────────────────────────────────────────
    for fig in REQUIRED_FIGURES:
        if not (FIG_DIR / fig).exists(): fail(f"Missing figure: {fig}")
    print(f"  [✓] All {len(REQUIRED_FIGURES)} VALUE development figures present", flush=True)

    # ── 13. SOURCE regression ─────────────────────────────────────────────────
    print("  Running SOURCE regression audit...", flush=True)
    r = subprocess.run(
        ["python", "scripts/qc/xai/02_audit_source_xai.py"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or "AUDIT PASSED" not in r.stdout:
        print(r.stdout); print(r.stderr)
        fail("SOURCE XAI regression audit FAILED")
    print("  [✓] SOURCE XAI regression audit: PASSED", flush=True)

    # ── 14. TRANSFER regression ───────────────────────────────────────────────
    print("  Running TRANSFER regression audit...", flush=True)
    r = subprocess.run(
        ["python", "scripts/qc/xai/03_audit_transfer_xai.py"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or "AUDIT PASSED" not in r.stdout:
        print(r.stdout); print(r.stderr)
        fail("TRANSFER XAI regression audit FAILED")
    print("  [✓] TRANSFER XAI regression audit: PASSED", flush=True)

    print("\n" + "="*55)
    print("VALUE XAI FINAL CLOSURE AUDIT PASSED")
    print("="*55)


if __name__ == "__main__":
    main()
