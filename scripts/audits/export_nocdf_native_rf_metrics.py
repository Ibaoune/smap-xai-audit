#!/usr/bin/env python3
"""
export_nocdf_native_rf_metrics.py
=================================
Deterministic audit script extracting, validating and plotting the 2020
holdout evaluation metrics for Random Forest models trained strictly on
native DA-NoCDF support.

Strict provenance rules:
- Only 'da_nocdf' experiment.
- Only 'native_support' support mode (matched_support is forbidden).
- No dependency on legacy DA-CDF data or matched cohorts.
- Target physical units are explicitly documented and kept separate in error plots.

Outputs:
- tables/audit/nocdf_native_rf_2020_metrics.csv
- figures/audit/nocdf_native_rf_2020_metrics.pdf
- figures/audit/nocdf_native_rf_2020_metrics.png
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TARGET_METADATA = {
    "daily_absolute_increment": {
        "block": "SOURCE",
        "display_name": "SOURCE update magnitude",
        "unit": "m³ m⁻³",
        "unit_type": "soil_moisture",
        "description": "Daily surface soil moisture EnKF analysis increment magnitude (|analysis - forecast|)"
    },
    "delta_rzsm": {
        "block": "TRANSFER",
        "display_name": "RZSM anomaly",
        "unit": "m³ m⁻³",
        "unit_type": "soil_moisture",
        "description": "Daily root-zone soil moisture anomaly (DA-NoCDF - OPL)"
    },
    "delta_et": {
        "block": "TRANSFER",
        "display_name": "ET anomaly",
        "unit": "mm d⁻¹",
        "unit_type": "flux",
        "description": "Daily total evapotranspiration anomaly (DA-NoCDF - OPL)"
    },
    "delta_surface_runoff": {
        "block": "TRANSFER",
        "display_name": "Surface runoff anomaly",
        "unit": "mm d⁻¹",
        "unit_type": "flux",
        "description": "Daily surface runoff anomaly (DA-NoCDF - OPL)"
    },
    "delta_baseflow": {
        "block": "TRANSFER",
        "display_name": "Baseflow anomaly",
        "unit": "mm d⁻¹",
        "unit_type": "flux",
        "description": "Daily subsurface runoff / baseflow anomaly (DA-NoCDF - OPL)"
    },
    "value_ae": {
        "block": "VALUE",
        "display_name": "VALUE (ET error gain)",
        "unit": "mm d⁻¹",
        "unit_type": "flux",
        "description": "Daily ET absolute error reduction against GLEAM v4.3a (|OPL - GLEAM| - |DA - GLEAM|)"
    }
}

CANONICAL_TARGET_ORDER = [
    "daily_absolute_increment",
    "delta_rzsm",
    "delta_et",
    "delta_surface_runoff",
    "delta_baseflow",
    "value_ae"
]

def load_and_validate_metrics(workspace_root: Path) -> pd.DataFrame:
    metrics_path = workspace_root / "reports" / "modeling" / "final_2020" / "final_metrics_2020.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing holdout metrics at {metrics_path}")

    df = pd.read_csv(metrics_path)

    # STRICT AUDIT CONTROLS
    # 1. Filter strictly to da_nocdf and native_support
    df_nocdf = df[(df["experiment"] == "da_nocdf") & (df["support"] == "native_support")].copy()

    # 2. Assert no legacy CDF rows
    assert not (df_nocdf["experiment"] == "da_cdf").any(), "SECURITY VIOLATION: da_cdf detected in native NoCDF table!"
    assert not (df_nocdf["support"] == "matched_support").any(), "SECURITY VIOLATION: matched_support detected in native NoCDF table!"
    assert len(df_nocdf) == 6, f"Expected exactly 6 native NoCDF models, found {len(df_nocdf)}"

    # 3. Cross-reference with model metadata JSON files
    models_dir = workspace_root / "reports" / "modeling" / "models" / "final_refit_2016_2019"
    enriched_rows = []

    for _, row in df_nocdf.iterrows():
        block = row["block"].lower()
        target = row["target"]
        meta_path = models_dir / block / "da_nocdf" / target / "native_support" / "metadata.json"
        
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file missing for {block}/{target}: {meta_path}")

        with open(meta_path, "r") as f:
            meta = json.load(f)

        assert meta["diagnostic_block"] == row["block"], f"Block mismatch in metadata for {target}"
        assert meta["experiment"] == "da_nocdf", f"Experiment mismatch in metadata for {target}"
        assert meta["target"] == target, f"Target mismatch in metadata for {target}"
        assert meta["support_mode"] == "native_support", f"Support mode mismatch in metadata for {target}"

        t_meta = TARGET_METADATA[target]

        enriched = {
            "block": row["block"],
            "target": target,
            "display_name": t_meta["display_name"],
            "target_unit": t_meta["unit"],
            "unit_type": t_meta["unit_type"],
            "experiment": "da_nocdf",
            "support_mode": "native_support",
            "rf_configuration": row["model"],
            "test_year": 2020,
            "test_sample_count": int(row["N"]),
            "training_period": f"{meta['training_start']} to {meta['training_end']}",
            "training_sample_count": int(meta["n_training_rows"]),
            "training_active_pixels": int(meta["n_training_pixels"]),
            "n_features": int(meta["n_features"]),
            "feature_set": meta["feature_set"],
            "training_fingerprint": meta["training_support_fingerprint"],
            "git_freeze_commit": meta["freeze_commit"],
            "MAE": float(row["MAE"]),
            "RMSE": float(row["RMSE"]),
            "bias": float(row["bias"]),
            "R2": float(row["R2"]),
            "pearson_r": float(row["pearson_r"]),
            "baseline_name": row["baseline_name"],
            "baseline_MAE": float(row["baseline_MAE"]),
            "baseline_RMSE": float(row["baseline_RMSE"]),
            "MAE_skill": float(row["MAE_skill"]),
            "RMSE_skill": float(row["RMSE_skill"]),
            "target_description": t_meta["description"]
        }
        enriched_rows.append(enriched)

    df_res = pd.DataFrame(enriched_rows)
    # Order by canonical target order
    df_res["target_rank"] = df_res["target"].map(lambda t: CANONICAL_TARGET_ORDER.index(t))
    df_res = df_res.sort_values("target_rank").drop(columns=["target_rank"]).reset_index(drop=True)
    return df_res

def plot_diagnostics(df: pd.DataFrame, out_pdf: Path, out_png: Path):
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'figure.titlesize': 13,
        'pdf.fonttype': 42,
        'ps.fonttype': 42
    })

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Native DA-NoCDF Random Forest Performance — 2020 Independent Holdout", fontsize=13, fontweight='bold', y=0.98)

    labels = df["display_name"].tolist()
    y_pos = np.arange(len(labels))

    # Color palette
    color_r2 = "#1f77b4"
    color_corr = "#aec7e8"
    color_mae_sk = "#2ca02c"
    color_rmse_sk = "#98df8a"
    color_mae = "#d62728"
    color_rmse = "#ff9896"
    color_base = "#7f7f7f"

    # -------------------------------------------------------------
    # (a) Dimensionless performance metrics: R² and Pearson r
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    width = 0.35
    ax_a.barh(y_pos - width/2, df["R2"], width, label="R² score", color=color_r2, edgecolor='black', linewidth=0.5)
    ax_a.barh(y_pos + width/2, df["pearson_r"], width, label="Pearson correlation (r)", color=color_corr, edgecolor='black', linewidth=0.5)
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(labels)
    ax_a.set_xlabel("Dimensionless metric value")
    ax_a.set_title("(a) Correlation and variance explained (R² & Pearson r)", loc='left', fontweight='semibold')
    ax_a.set_xlim(0, 1.0)
    ax_a.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax_a.legend(loc='lower right', frameon=True)
    ax_a.invert_yaxis()

    # Annotate R² values
    for i, r2 in enumerate(df["R2"]):
        ax_a.text(r2 + 0.02, i - width/2, f"{r2:.3f}", va='center', fontsize=8, color="#08306b")

    # -------------------------------------------------------------
    # (b) Relative skill over monthly climatological baselines
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    ax_b.barh(y_pos - width/2, df["MAE_skill"], width, label="MAE Skill", color=color_mae_sk, edgecolor='black', linewidth=0.5)
    ax_b.barh(y_pos + width/2, df["RMSE_skill"], width, label="RMSE Skill", color=color_rmse_sk, edgecolor='black', linewidth=0.5)
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(labels)
    ax_b.set_xlabel("Skill score = 1 − Metric_RF / Metric_baseline")
    ax_b.set_title("(b) Relative skill score over climatological baseline", loc='left', fontweight='semibold')
    ax_b.set_xlim(0, 0.7)
    ax_b.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax_b.legend(loc='lower right', frameon=True)
    ax_b.invert_yaxis()

    for i, sk in enumerate(df["MAE_skill"]):
        ax_b.text(sk + 0.015, i - width/2, f"{sk:.3f}", va='center', fontsize=8, color="#00441b")

    # -------------------------------------------------------------
    # (c) Soil Moisture Error Metrics (m³ m⁻³) — SOURCE and RZSM only
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    df_sm = df[df["unit_type"] == "soil_moisture"].copy().reset_index(drop=True)
    sm_labels = [f"{r['display_name']}\n(N={r['test_sample_count']:,})" for _, r in df_sm.iterrows()]
    x_pos_sm = np.arange(len(df_sm))
    w_col = 0.22

    ax_c.bar(x_pos_sm - w_col, df_sm["MAE"], w_col, label="RF MAE", color=color_mae, edgecolor='black', linewidth=0.5)
    ax_c.bar(x_pos_sm, df_sm["RMSE"], w_col, label="RF RMSE", color=color_rmse, edgecolor='black', linewidth=0.5)
    ax_c.bar(x_pos_sm + w_col, df_sm["baseline_RMSE"], w_col, label="Baseline RMSE", color=color_base, edgecolor='black', linewidth=0.5, linestyle=':')

    ax_c.set_xticks(x_pos_sm)
    ax_c.set_xticklabels(sm_labels)
    ax_c.set_ylabel("Volumetric soil moisture error [m³ m⁻³]")
    ax_c.set_title("(c) Volumetric soil moisture targets error magnitude", loc='left', fontweight='semibold')
    ax_c.grid(True, axis='y', linestyle='--', alpha=0.5)
    ax_c.legend(loc='upper left', frameon=True)

    for i, (mae, rmse) in enumerate(zip(df_sm["MAE"], df_sm["RMSE"])):
        ax_c.text(i - w_col, mae + 0.0005, f"{mae:.4f}", ha='center', fontsize=8, color="#67000d")
        ax_c.text(i, rmse + 0.0005, f"{rmse:.4f}", ha='center', fontsize=8, color="#67000d")

    # -------------------------------------------------------------
    # (d) Flux & Water Balance Error Metrics (mm d⁻¹) — ET, Qs, Qsb, VALUE
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    df_flx = df[df["unit_type"] == "flux"].copy().reset_index(drop=True)
    flx_labels = [f"{r['display_name'].replace(' anomaly', '')}\n(N={r['test_sample_count']:,})" for _, r in df_flx.iterrows()]
    x_pos_flx = np.arange(len(df_flx))

    ax_d.bar(x_pos_flx - w_col, df_flx["MAE"], w_col, label="RF MAE", color=color_mae, edgecolor='black', linewidth=0.5)
    ax_d.bar(x_pos_flx, df_flx["RMSE"], w_col, label="RF RMSE", color=color_rmse, edgecolor='black', linewidth=0.5)
    ax_d.bar(x_pos_flx + w_col, df_flx["baseline_RMSE"], w_col, label="Baseline RMSE", color=color_base, edgecolor='black', linewidth=0.5, linestyle=':')

    ax_d.set_xticks(x_pos_flx)
    ax_d.set_xticklabels(flx_labels)
    ax_d.set_ylabel("Water flux / budget error [mm d⁻¹]")
    ax_d.set_title("(d) Hydrological flux & VALUE targets error magnitude", loc='left', fontweight='semibold')
    ax_d.grid(True, axis='y', linestyle='--', alpha=0.5)
    ax_d.legend(loc='upper right', frameon=True)

    for i, (mae, rmse) in enumerate(zip(df_flx["MAE"], df_flx["RMSE"])):
        ax_d.text(i - w_col, mae + 0.005, f"{mae:.3f}", ha='center', fontsize=8, color="#67000d")
        ax_d.text(i, rmse + 0.005, f"{rmse:.3f}", ha='center', fontsize=8, color="#67000d")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, dpi=300)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print(f"Saved diagnostic figure to:\n  {out_pdf}\n  {out_png}")

def main():
    parser = argparse.ArgumentParser(description="Export reproducible native NoCDF Random Forest evaluation metrics.")
    parser.add_argument("--workspace-root", type=str, default=".", help="Root directory of the repository")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    print(f"Workspace root: {workspace_root}")

    df_metrics = load_and_validate_metrics(workspace_root)

    out_csv = workspace_root / "tables" / "audit" / "nocdf_native_rf_2020_metrics.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_metrics.to_csv(out_csv, index=False)
    print(f"Saved verified NoCDF native metrics table to:\n  {out_csv}")

    out_pdf = workspace_root / "figures" / "audit" / "nocdf_native_rf_2020_metrics.pdf"
    out_png = workspace_root / "figures" / "audit" / "nocdf_native_rf_2020_metrics.png"
    plot_diagnostics(df_metrics, out_pdf, out_png)

    # Print summary table to stdout for audit verification
    print("\n" + "="*80)
    print("VERIFIED NATIVE NOCDF RANDOM FOREST 2020 METRICS SUMMARY:")
    print("="*80)
    display_cols = ["block", "target", "target_unit", "rf_configuration", "test_sample_count", "R2", "pearson_r", "MAE", "RMSE", "MAE_skill", "RMSE_skill"]
    print(df_metrics[display_cols].to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    main()
