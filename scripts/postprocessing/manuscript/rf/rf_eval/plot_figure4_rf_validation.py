#!/usr/bin/env python3
"""
plot_figure4_rf_validation.py
=============================
Renders publication-ready Figure 4 (standard regression metrics) for Random Forest evaluation.
Layout: Symmetric 2x2 horizontal grouped bar chart
- (a) 2019 temporal validation — R²
- (b) 2019 temporal validation — Pearson r
- (c) Independent 2020 holdout — R²
- (d) Independent 2020 holdout — Pearson r

Data sources:
figures/manuscript/rf/rf_eval/
- Figure4_2019_temporal_validation_metrics.csv
- Figure4_2020_holdout_metrics.csv

Aesthetic standards: Q1 hydrology / remote sensing journal style.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Matplotlib configuration
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'DejaVu Sans'
plt.rcParams['mathtext.it'] = 'DejaVu Sans:italic'
plt.rcParams['mathtext.bf'] = 'DejaVu Sans:bold'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

TARGET_ORDER = ["SOURCE", "RZSM", "ET", "Surface runoff", "Baseflow", "VALUE"]
COLOR_CDF = "#1f77b4"
COLOR_NOCDF = "#ff7f0e"

def resolve_paths(repo_root=None):
    if repo_root is None:
        current = Path.cwd()
        if (current / "figures" / "manuscript").exists():
            repo_root = current
        else:
            repo_root = Path(__file__).resolve().parents[5]
    data_dir = repo_root / "figures" / "manuscript" / "rf" / "rf_eval"
    return data_dir

def plot_figure4():
    data_dir = resolve_paths()
    csv_2019 = data_dir / "Figure4_2019_temporal_validation_metrics.csv"
    csv_2020 = data_dir / "Figure4_2020_holdout_metrics.csv"

    if not csv_2019.exists() or not csv_2020.exists():
        raise FileNotFoundError(f"Missing one or more source CSV files in {data_dir}. Run build_rf_eval_metrics.py first.")

    df_2019 = pd.read_csv(csv_2019)
    df_2020 = pd.read_csv(csv_2020)

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.2), dpi=500)
    plt.subplots_adjust(top=0.93, bottom=0.07, left=0.10, right=0.97, hspace=0.30, wspace=0.28)

    y_pos = np.arange(len(TARGET_ORDER))
    bar_height = 0.36

    # -------------------------------------------------------------
    # Helper to draw grouped horizontal bars and configure axes
    # -------------------------------------------------------------
    def draw_bars(ax, df, val_col):
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, linestyle='--', alpha=0.4, color='#b0b0b0')

        # Reference line at zero
        ax.axvline(0.0, color='black', linewidth=0.9, linestyle='-', zorder=2)

        for i, tgt in enumerate(TARGET_ORDER):
            # CDF
            cdf_row = df[(df["target"] == tgt) & (df["experiment"] == "CDF")]
            if not cdf_row.empty:
                v_cdf = cdf_row[val_col].iloc[0]
                ax.barh(i - bar_height/2, v_cdf, height=bar_height, color=COLOR_CDF,
                        edgecolor='white', linewidth=0.7, zorder=3)

            # NoCDF
            nocdf_row = df[(df["target"] == tgt) & (df["experiment"] == "NoCDF")]
            if not nocdf_row.empty:
                v_nocdf = nocdf_row[val_col].iloc[0]
                ax.barh(i + bar_height/2, v_nocdf, height=bar_height, color=COLOR_NOCDF,
                        edgecolor='white', linewidth=0.7, zorder=3)

        # Configure y-axis explicitly on every panel
        ax.set_yticks(y_pos)
        ax.set_yticklabels(TARGET_ORDER, fontsize=9.5, fontweight='medium')
        ax.invert_yaxis()  # Top to bottom: SOURCE to VALUE
        ax.set_ylim(len(TARGET_ORDER) - 0.45, -0.55)
        ax.tick_params(axis='both', which='major', labelsize=9)

    # -------------------------------------------------------------
    # Panel (a): 2019 temporal validation — R²
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    draw_bars(ax_a, df_2019, "r2")
    ax_a.set_title(r"(a) 2019 temporal validation — $R^2$", fontsize=11, fontweight='bold', loc='left', pad=8)
    ax_a.set_xlabel(r"Coefficient of determination ($R^2$)", fontsize=10, labelpad=5)
    ax_a.set_xlim(-0.05, 0.85)
    ax_a.set_xticks(np.arange(0.0, 0.81, 0.2))

    # -------------------------------------------------------------
    # Panel (b): 2019 temporal validation — Pearson r
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    draw_bars(ax_b, df_2019, "pearson_r")
    ax_b.set_title(r"(b) 2019 temporal validation — Pearson $r$", fontsize=11, fontweight='bold', loc='left', pad=8)
    ax_b.set_xlabel(r"Pearson correlation coefficient ($r$)", fontsize=10, labelpad=5)
    ax_b.set_xlim(0.0, 1.0)
    ax_b.set_xticks(np.arange(0.0, 1.01, 0.2))

    # -------------------------------------------------------------
    # Panel (c): Independent 2020 holdout — R²
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    draw_bars(ax_c, df_2020, "r2")
    ax_c.set_title(r"(c) Independent 2020 holdout — $R^2$", fontsize=11, fontweight='bold', loc='left', pad=8)
    ax_c.set_xlabel(r"Coefficient of determination ($R^2$)", fontsize=10, labelpad=5)
    ax_c.set_xlim(-0.05, 0.85)
    ax_c.set_xticks(np.arange(0.0, 0.81, 0.2))

    # -------------------------------------------------------------
    # Panel (d): Independent 2020 holdout — Pearson r
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    draw_bars(ax_d, df_2020, "pearson_r")
    ax_d.set_title(r"(d) Independent 2020 holdout — Pearson $r$", fontsize=11, fontweight='bold', loc='left', pad=8)
    ax_d.set_xlabel(r"Pearson correlation coefficient ($r$)", fontsize=10, labelpad=5)
    ax_d.set_xlim(0.0, 1.0)
    ax_d.set_xticks(np.arange(0.0, 1.01, 0.2))

    # -------------------------------------------------------------
    # Unified Figure Legend
    # -------------------------------------------------------------
    patch_cdf = mpatches.Patch(facecolor=COLOR_CDF, edgecolor='none', label='CDF')
    patch_nocdf = mpatches.Patch(facecolor=COLOR_NOCDF, edgecolor='none', label='NoCDF')
    fig.legend(handles=[patch_cdf, patch_nocdf], loc='upper center', bbox_to_anchor=(0.5, 0.985),
               ncol=2, frameon=True, facecolor='white', edgecolor='#e0e0e0',
               fontsize=10.5, handlelength=1.4, handleheight=0.9)

    # Export figure files
    out_png = data_dir / "Figure_4_RF_validation_standard_metrics.png"
    out_pdf = data_dir / "Figure_4_RF_validation_standard_metrics.pdf"

    fig.savefig(out_png, dpi=500, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)
    print(f"[✓] Successfully exported Figure 4:")
    print(f"    PNG: {out_png}")
    print(f"    PDF: {out_pdf}")

if __name__ == "__main__":
    plot_figure4()
