#!/usr/bin/env python3
"""
generate_figure_3_and_maps.py
-----------------------------
Generates corrected Figure 3 and standalone spatial maps in figures/cdf_v2/:
- Figure_3_assimilation_diagnostics.png & .pdf
  * Panel (a): Innovation availability for both CDF and NoCDF
  * Panel (b): Mean innovation NoCDF (RdBu_r: blue = negative / drying, red = positive)
  * Panel (c): Innovation distributions (CDF & NoCDF)
  * Panel (d): Mean signed increment NoCDF (RdBu_r, title without overlap)
  * Panel (e): Mean signed increment CDF (RdBu_r, title without overlap)
  * Panel (f): Seasonal increment magnitude (order: DJF, MAM, JJA, SON)
- map_mean_signed_increment.png & .pdf (CDF, NoCDF, NoCDF - CDF in RdBu_r)
- map_mean_innovation.png & .pdf (CDF, NoCDF, NoCDF - CDF in RdBu_r)
"""

import os
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['pdf.fonttype'] = 42

BASE_DIR = Path("data/processed/daily_enkf")
OUT_DIR = Path(os.environ.get("FIGURES_OUT_DIR", "figures/cdf_v2"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {"CDF": "#1f77b4", "NoCDF": "#ff7f0e"}

def load_var(exp, var_name):
    files = sorted(glob.glob(str(BASE_DIR / exp / var_name / "*.nc")))
    print(f"Loading {len(files)} files for {exp}/{var_name}...", flush=True)
    datasets = [xr.open_dataset(f) for f in files]
    return xr.concat(datasets, dim="time")

def main():
    print("=== Loading Datasets ===", flush=True)
    ds_nocdf_inn = load_var("da_nocdf", "daily_innovation")
    ds_cdf_inn = load_var("da_cdf", "daily_innovation")
    ds_nocdf_inc = load_var("da_nocdf", "daily_signed_increment")
    ds_cdf_inc = load_var("da_cdf", "daily_signed_increment")
    ds_nocdf_abs = load_var("da_nocdf", "daily_absolute_increment")
    ds_cdf_abs = load_var("da_cdf", "daily_absolute_increment")

    lon = ds_nocdf_inn.lon.values
    lat = ds_nocdf_inn.lat.values
    extent = [lon.min(), lon.max(), lat.min(), lat.max()]

    # =========================================================================
    # 1. GENERATE FIGURE 3
    # =========================================================================
    print("=== Plotting Figure 3 ===", flush=True)
    fig, axes = plt.subplots(2, 3, figsize=(16.5, 10.5))
    axes = axes.flatten()

    # (a) Availability for CDF and NoCDF
    axes[0].axis('off')
    ax_a1 = axes[0].inset_axes([0.0, 0.12, 0.46, 0.80])
    ax_a2 = axes[0].inset_axes([0.54, 0.12, 0.46, 0.80])

    count_nocdf = ds_nocdf_inn["daily_innovation"].count(dim="time").values
    count_cdf = ds_cdf_inn["daily_innovation"].count(dim="time").values
    vmax_count = max(np.nanmax(count_nocdf), np.nanmax(count_cdf))

    im_a1 = ax_a1.imshow(count_nocdf, extent=extent, origin='lower', cmap='viridis', vmin=0, vmax=vmax_count)
    ax_a1.set_title("NoCDF availability", fontsize=9.5, loc='center', pad=3)
    ax_a1.set_xlabel("Lon", fontsize=8.5, labelpad=2)
    ax_a1.set_ylabel("Lat", fontsize=8.5, labelpad=2)
    ax_a1.tick_params(labelsize=7.5)

    im_a2 = ax_a2.imshow(count_cdf, extent=extent, origin='lower', cmap='viridis', vmin=0, vmax=vmax_count)
    ax_a2.set_title("CDF availability", fontsize=9.5, loc='center', pad=3)
    ax_a2.set_xlabel("Lon", fontsize=8.5, labelpad=2)
    ax_a2.tick_params(labelsize=7.5)
    ax_a2.set_yticklabels([])

    axes[0].set_title(r"$\bf{(a)}$ Innovation availability (count)", loc='left', fontsize=11, pad=12)
    cbar_a = fig.colorbar(im_a2, ax=[ax_a1, ax_a2], orientation='horizontal', fraction=0.06, pad=0.18, shrink=0.88)
    cbar_a.set_label("Count of update days", fontsize=8.5)
    cbar_a.ax.tick_params(labelsize=7.5)

    # (b) Mean NoCDF innovation (RdBu_r: blue = negative / drying, red = positive)
    mean_nocdf_inn = ds_nocdf_inn["daily_innovation"].mean(dim="time").values
    im2 = axes[1].imshow(mean_nocdf_inn, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.05, vmax=0.05)
    axes[1].set_title(r"$\bf{(b)}$ Mean innovation (NoCDF)", loc='left', pad=10)
    cb2 = plt.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    cb2.set_label("[m³ m⁻³]", fontsize=9)
    cb2.ax.tick_params(labelsize=8.5)

    # (c) Innovation distributions
    nocdf_vals = ds_nocdf_inn["daily_innovation"].values.flatten()
    cdf_vals = ds_cdf_inn["daily_innovation"].values.flatten()
    nocdf_vals = nocdf_vals[~np.isnan(nocdf_vals)]
    cdf_vals = cdf_vals[~np.isnan(cdf_vals)]

    np.random.seed(42)
    s_cdf = np.random.choice(cdf_vals, min(len(cdf_vals), 25000), replace=False)
    s_nocdf = np.random.choice(nocdf_vals, min(len(nocdf_vals), 25000), replace=False)

    sns.kdeplot(s_cdf, label="CDF", color=PALETTE["CDF"], ax=axes[2], fill=True, alpha=0.3)
    sns.kdeplot(s_nocdf, label="NoCDF", color=PALETTE["NoCDF"], ax=axes[2], fill=True, alpha=0.3)
    axes[2].set_title(r"$\bf{(c)}$ Innovation distributions", loc='left', pad=10)
    axes[2].set_xlabel("Innovation [m³ m⁻³]")
    axes[2].legend()

    # (d) Mean signed increment NoCDF (RdBu_r: blue = negative, red = positive)
    mean_nocdf_inc = ds_nocdf_inc["daily_signed_increment"].mean(dim="time").values
    im4 = axes[3].imshow(mean_nocdf_inc, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.01, vmax=0.01)
    axes[3].set_title(r"$\bf{(d)}$ Mean analysis increment (NoCDF)", loc='left', pad=10)
    cb4 = plt.colorbar(im4, ax=axes[3], fraction=0.046, pad=0.04)
    cb4.set_label("[m³ m⁻³]", fontsize=9)
    cb4.ax.tick_params(labelsize=8.5)

    # (e) Mean signed increment CDF (RdBu_r: blue = negative, red = positive)
    mean_cdf_inc = ds_cdf_inc["daily_signed_increment"].mean(dim="time").values
    im5 = axes[4].imshow(mean_cdf_inc, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.01, vmax=0.01)
    axes[4].set_title(r"$\bf{(e)}$ Mean analysis increment (CDF)", loc='left', pad=10)
    cb5 = plt.colorbar(im5, ax=axes[4], fraction=0.046, pad=0.04)
    cb5.set_label("[m³ m⁻³]", fontsize=9)
    cb5.ax.tick_params(labelsize=8.5)

    # (f) Seasonal increment magnitude (order: DJF, MAM, JJA, SON)
    nocdf_seas = ds_nocdf_abs["daily_absolute_increment"].groupby("time.season").mean(dim=["time", "lat", "lon"]).to_dataframe().reset_index()
    cdf_seas = ds_cdf_abs["daily_absolute_increment"].groupby("time.season").mean(dim=["time", "lat", "lon"]).to_dataframe().reset_index()

    nocdf_seas["Experiment"] = "NoCDF"
    cdf_seas["Experiment"] = "CDF"
    seas_df = pd.concat([cdf_seas, nocdf_seas])
    season_order = ["DJF", "MAM", "JJA", "SON"]
    sns.barplot(data=seas_df, x="season", y="daily_absolute_increment", hue="Experiment", ax=axes[5], palette=PALETTE, order=season_order)
    axes[5].set_title(r"$\bf{(f)}$ Seasonal increment magnitude", loc='left', pad=8)
    axes[5].set_ylabel("Mean |increment| [m³ m⁻³]")
    axes[5].set_xlabel("")
    axes[5].legend()

    for ax in [axes[1], axes[3], axes[4]]:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    fig.subplots_adjust(hspace=0.35, wspace=0.28)
    fig_path = OUT_DIR / "Figure_3_assimilation_diagnostics"
    fig.savefig(f"{fig_path}.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(f"{fig_path}.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {fig_path}.png and .pdf", flush=True)

    # =========================================================================
    # 2. GENERATE map_mean_signed_increment.png & .pdf
    # =========================================================================
    print("=== Plotting map_mean_signed_increment ===", flush=True)
    fig_inc, axes_inc = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    
    # Panel 1: CDF mean increment
    im_c = axes_inc[0].imshow(mean_cdf_inc, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.01, vmax=0.01)
    axes_inc[0].set_title(r"$\bf{(a)}$ CDF mean signed increment", loc='left', fontsize=11)
    axes_inc[0].set_xlabel("Longitude")
    axes_inc[0].set_ylabel("Latitude")
    cb_c = plt.colorbar(im_c, ax=axes_inc[0], fraction=0.046, pad=0.04)
    cb_c.set_label("[m³ m⁻³]")

    # Panel 2: NoCDF mean increment
    im_n = axes_inc[1].imshow(mean_nocdf_inc, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.01, vmax=0.01)
    axes_inc[1].set_title(r"$\bf{(b)}$ NoCDF mean signed increment", loc='left', fontsize=11)
    axes_inc[1].set_xlabel("Longitude")
    cb_n = plt.colorbar(im_n, ax=axes_inc[1], fraction=0.046, pad=0.04)
    cb_n.set_label("[m³ m⁻³]")

    # Panel 3: Difference NoCDF - CDF
    diff_inc = mean_nocdf_inc - mean_cdf_inc
    im_d = axes_inc[2].imshow(diff_inc, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.015, vmax=0.015)
    axes_inc[2].set_title(r"$\bf{(c)}$ Difference: NoCDF − CDF", loc='left', fontsize=11)
    axes_inc[2].set_xlabel("Longitude")
    cb_d = plt.colorbar(im_d, ax=axes_inc[2], fraction=0.046, pad=0.04)
    cb_d.set_label("[m³ m⁻³]")

    fig_inc.suptitle("Mean Signed Analysis Increment (2016–2020) [Blue = Drying, Red = Wetting]", fontsize=13, y=0.98)
    fig_inc.tight_layout()
    inc_path = OUT_DIR / "map_mean_signed_increment"
    fig_inc.savefig(f"{inc_path}.png", dpi=300, bbox_inches='tight')
    fig_inc.savefig(f"{inc_path}.pdf", dpi=300, bbox_inches='tight')
    plt.close(fig_inc)
    print(f"Saved: {inc_path}.png and .pdf", flush=True)

    # =========================================================================
    # 3. GENERATE map_mean_innovation.png & .pdf
    # =========================================================================
    print("=== Plotting map_mean_innovation ===", flush=True)
    fig_inn, axes_inn = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    
    mean_cdf_inn = ds_cdf_inn["daily_innovation"].mean(dim="time").values

    # Panel 1: CDF mean innovation
    im_inn_c = axes_inn[0].imshow(mean_cdf_inn, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.04, vmax=0.04)
    axes_inn[0].set_title(r"$\bf{(a)}$ CDF mean innovation", loc='left', fontsize=11)
    axes_inn[0].set_xlabel("Longitude")
    axes_inn[0].set_ylabel("Latitude")
    cb_inn_c = plt.colorbar(im_inn_c, ax=axes_inn[0], fraction=0.046, pad=0.04)
    cb_inn_c.set_label("[m³ m⁻³]")

    # Panel 2: NoCDF mean innovation
    im_inn_n = axes_inn[1].imshow(mean_nocdf_inn, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.04, vmax=0.04)
    axes_inn[1].set_title(r"$\bf{(b)}$ NoCDF mean innovation", loc='left', fontsize=11)
    axes_inn[1].set_xlabel("Longitude")
    cb_inn_n = plt.colorbar(im_inn_n, ax=axes_inn[1], fraction=0.046, pad=0.04)
    cb_inn_n.set_label("[m³ m⁻³]")

    # Panel 3: Difference NoCDF - CDF
    diff_inn = mean_nocdf_inn - mean_cdf_inn
    im_inn_d = axes_inn[2].imshow(diff_inn, extent=extent, origin='lower', cmap='RdBu_r', vmin=-0.04, vmax=0.04)
    axes_inn[2].set_title(r"$\bf{(c)}$ Difference: NoCDF − CDF", loc='left', fontsize=11)
    axes_inn[2].set_xlabel("Longitude")
    cb_inn_d = plt.colorbar(im_inn_d, ax=axes_inn[2], fraction=0.046, pad=0.04)
    cb_inn_d.set_label("[m³ m⁻³]")

    fig_inn.suptitle("Mean Daily Innovation (2016–2020) [Blue = SMAP Drier than Model, Red = SMAP Wetter]", fontsize=13, y=0.98)
    fig_inn.tight_layout()
    inn_path = OUT_DIR / "map_mean_innovation"
    fig_inn.savefig(f"{inn_path}.png", dpi=300, bbox_inches='tight')
    fig_inn.savefig(f"{inn_path}.pdf", dpi=300, bbox_inches='tight')
    plt.close(fig_inn)
    print(f"Saved: {inn_path}.png and .pdf", flush=True)

if __name__ == "__main__":
    main()
