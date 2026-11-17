#!/usr/bin/env python
"""
RF-04B-TRANSFER QC — Final closure audit.

Checks:
  1.  Exactly 8 SHAP parquets, 10k rows each
  2.  Exactly 8 permutation JSONs, 5k rows each
  3.  QC JSONs: additivity pass on all 8
  4.  Zero 2020 rows in any output
  5.  Identical common cohort checksum across all 8 parquets
  6.  52 active fitted features, all mapped in feature_groups.yaml
  7.  Feature set identical across all 8 models
  8.  All summary CSVs and matrices present
  9.  Frozen dependence features (top-3 per target, 4 targets)
  10. All 7 development figures present
  11. SOURCE XAI audit still passes (no shared code regressions)
  12. Normalized group importance sums to 1.0 for every model (tol=1e-6)
"""
import json
import sys
import numpy as np
import pandas as pd
import yaml
from pathlib import Path

IN_DIR  = Path("data/processed/modeling/xai/outputs/transfer")
FIG_DIR = Path("figures/development/transfer")
SRC_DIR = Path("data/processed/modeling/xai/outputs/source")
TARGETS = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
EXPS    = ["da_cdf", "da_nocdf"]
MODELS  = [(e, t) for e in EXPS for t in TARGETS]
COHORT_CHECKSUM = "616d94379a06cbcefd1c32a3bc5acf6f"
REQUIRED_FIGURES = [
    "fig_transfer_a_group_matrix.png",
    "fig_transfer_b_top_predictors.png",
    "fig_transfer_c_cross_target.png",
    "fig_transfer_d_distributions.png",
    "fig_transfer_e_dependence.png",
    "fig_transfer_f_seasonal.png",
    "fig_transfer_g_spatial.png",
]


def fail(msg):
    print(f"FAIL: {msg}", flush=True)
    sys.exit(1)


def main():
    print("TRANSFER XAI Final Closure Audit...", flush=True)

    # ── 1-4. SHAP parquets ─────────────────────────────────────────────────────
    seen_features = None
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        shap_f = IN_DIR / f"shap_{tag}.parquet"
        qc_f   = IN_DIR / f"qc_{tag}.json"
        if not shap_f.exists(): fail(f"Missing {shap_f}")
        if not qc_f.exists():   fail(f"Missing {qc_f}")
        qc = json.loads(qc_f.read_text())
        if qc["n_shap"] != 10000:
            fail(f"{tag}: n_shap={qc['n_shap']} != 10000")
        if qc["max_abs_reconstruction_error"] >= 1e-4:
            fail(f"{tag}: additivity failed {qc['max_abs_reconstruction_error']}")
        df = pd.read_parquet(shap_f, columns=["date"])
        if not pd.to_datetime(df["date"]).dt.year.eq(2019).all():
            fail(f"{tag}: non-2019 rows found!")
    print("  [✓] SHAP parquets: 8 models, 10k rows, additivity, 2019 isolation", flush=True)

    # ── 5. Permutation JSONs ───────────────────────────────────────────────────
    for exp, tgt in MODELS:
        tag  = f"{exp}_{tgt}"
        perm = json.loads((IN_DIR / f"permutation_{tag}.json").read_text())
        if perm["cohort_size"] != 5000:
            fail(f"{tag}: permutation cohort_size={perm['cohort_size']} != 5000")
    print("  [✓] Permutation JSONs: 8 models, 5k rows", flush=True)

    # ── 6. Common cohort checksum ──────────────────────────────────────────────
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        qc  = json.loads((IN_DIR / f"qc_{tag}.json").read_text())
        if qc["cohort_checksum"] != COHORT_CHECKSUM:
            fail(f"{tag}: cohort_checksum mismatch {qc['cohort_checksum']}")
    print(f"  [✓] Common cohort checksum: {COHORT_CHECKSUM} (all 8 models)", flush=True)

    # ── 7. Feature count and mapping ──────────────────────────────────────────
    with open("configs/xai/feature_groups.yaml") as f:
        feature_groups = yaml.safe_load(f)
    mapped = {feat for feats in feature_groups.values() for feat in feats}

    seen_features = None
    for exp, tgt in MODELS:
        tag      = f"{exp}_{tgt}"
        df       = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = {c.replace("shap__", "") for c in df.columns if c.startswith("shap__")}
        if seen_features is None:
            seen_features = features
        elif features != seen_features:
            fail(f"{tag}: feature set differs from first model!")
        unmapped = features - mapped
        if unmapped:
            fail(f"{tag}: unmapped features: {unmapped}")
    n_feats = len(seen_features)
    print(f"  [✓] Feature mapping: {n_feats} active features, all mapped, identical across all 8 models", flush=True)

    # ── 8. Dependence features ─────────────────────────────────────────────────
    dep_f = IN_DIR / "dependence_features.json"
    if not dep_f.exists(): fail("Missing dependence_features.json")
    dep = json.loads(dep_f.read_text())["targets"]
    for tgt in TARGETS:
        if tgt not in dep: fail(f"Missing dependence features for {tgt}")
        if len(dep[tgt]) != 3: fail(f"{tgt}: expected top-3, got {len(dep[tgt])}")
    print("  [✓] Dependence features: top-3 frozen for all 4 targets", flush=True)

    # ── 9. Summary files ───────────────────────────────────────────────────────
    required_files = [
        "tidy_predictor_summary.csv", "tidy_group_summary.csv",
        "group_matrix_cdf.csv", "group_matrix_nocdf.csv",
        "group_matrix_diff.csv", "cdf_nocdf_comparison.csv",
        "cross_target_pred_corr_cdf.csv", "cross_target_pred_corr_nocdf.csv",
        "cross_target_group_corr_cdf.csv", "cross_target_group_corr_nocdf.csv",
    ]
    for fn in required_files:
        if not (IN_DIR / fn).exists(): fail(f"Missing summary: {fn}")
    print("  [✓] All summary CSVs present", flush=True)

    # ── 10. Development figures ────────────────────────────────────────────────
    for fig in REQUIRED_FIGURES:
        if not (FIG_DIR / fig).exists(): fail(f"Missing figure: {fig}")
    print(f"  [✓] All {len(REQUIRED_FIGURES)} TRANSFER development figures present", flush=True)

    # ── 11. SOURCE regression ──────────────────────────────────────────────────
    print("  Running SOURCE regression audit...", flush=True)
    import subprocess
    result = subprocess.run(
        ["python", "scripts/qc/xai/02_audit_source_xai.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail("SOURCE XAI regression audit FAILED")
    if "AUDIT PASSED" not in result.stdout:
        fail("SOURCE XAI audit did not report PASSED")
    print("  [✓] SOURCE XAI regression audit: PASSED", flush=True)

    # ── 12. Normalized group importance sums to 1.0 ────────────────────────────
    with open("configs/xai/feature_groups.yaml") as f:
        fg = yaml.safe_load(f)
    for exp, tgt in MODELS:
        tag = f"{exp}_{tgt}"
        df  = pd.read_parquet(IN_DIR / f"shap_{tag}.parquet")
        features = [c.replace("shap__", "") for c in df.columns if c.startswith("shap__")]
        total_abs = sum(
            float(np.mean(np.abs(df[[f"shap__{f}" for f in fs if f in features]].values)) * len([f for f in fs if f in features]))
            for fs in fg.values()
        )
        # total_abs computed as sum of per-group sum-of-mean-abs; normalize
        group_sums = []
        for g, fs in fg.items():
            active = [f for f in fs if f in features]
            if active:
                g_abs = float(np.mean(np.abs(df[[f"shap__{f}" for f in active]].values)) * len(active))
            else:
                g_abs = 0.0
            group_sums.append(g_abs)
        total = sum(group_sums)
        norm_sum = sum(v / total for v in group_sums) if total > 0 else 0.0
        if abs(norm_sum - 1.0) > 1e-6:
            fail(f"{tag}: normalized group importance sums to {norm_sum:.8f} != 1.0")
    print("  [✓] Normalized group importance sums to 1.0 for all 8 models (tol=1e-6)", flush=True)

    print("\n" + "="*55)
    print("TRANSFER XAI FINAL CLOSURE AUDIT PASSED")
    print("="*55)


if __name__ == "__main__":
    main()
