import os
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

"""
SMAP-XAI: RZSM QC Plotting

Purpose
-------
Preprocessing/QC visualization, not manuscript figures.
Calculates spatial means and temporal means to quickly compare the derived RZSM.

Inputs
------
Annual RZSM derived NetCDF files for:
    OPL
    DA-NoCDF
    DA-CDF

Period
------
2016-2020

Outputs
-------
daily spatial-mean comparison
temporal-mean RZSM maps
temporal-mean DA-minus-OPL difference maps

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def main():
    experiments = ["opl", "da_nocdf", "da_cdf"]
    exp_labels = {"opl": "OPL", "da_nocdf": "DA-NoCDF", "da_cdf": "DA-CDF"}
    years = range(2016, 2021)
    
    base_dir = "data/processed/daily_model"
    out_dir = "reports/qc/rzsm"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_dict = {}
    temporal_means = {}
    
    print("--- LOADING RZSM DATA ---")
    for exp in experiments:
        paths = [f"{base_dir}/{exp}/rzsm/rzsm_{year}.nc" for year in years]
        datasets = [xr.open_dataset(p) for p in paths]
        ds = xr.concat(datasets, dim='time')
        ds_dict[exp] = ds['rzsm']
        
        tm = ds['rzsm'].mean(dim="time")
        temporal_means[exp] = tm
        
        print(f"[{exp_labels[exp]}]")
        print(f"  temporal-mean rzsm spatial min: {float(tm.min()):.4f}")
        print(f"  temporal-mean rzsm spatial max: {float(tm.max()):.4f}")
        print(f"  overall 2016-2020 mean:         {float(ds['rzsm'].mean()):.4f}")
        
    diff_nocdf = temporal_means["da_nocdf"] - temporal_means["opl"]
    diff_cdf = temporal_means["da_cdf"] - temporal_means["opl"]
    
    print("--- DIFFERENCE STATISTICS ---")
    print("[DA-NoCDF - OPL]")
    print(f"  min: {float(diff_nocdf.min()):.4f}")
    print(f"  max: {float(diff_nocdf.max()):.4f}")
    print(f"  mean: {float(diff_nocdf.mean()):.4f}")
    print("[DA-CDF - OPL]")
    print(f"  min: {float(diff_cdf.min()):.4f}")
    print(f"  max: {float(diff_cdf.max()):.4f}")
    print(f"  mean: {float(diff_cdf.mean()):.4f}")
    
    print("Generating temporal mean maps...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    
    # Sensible bounds for RZSM based on observed ranges
    boundaries = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
    cmap = plt.get_cmap('YlGnBu').copy()
    cmap.set_bad('white', alpha=0.0)
    norm = mcolors.BoundaryNorm(boundaries, cmap.N, extend='max')
    
    for i, exp in enumerate(experiments):
        ax = axes[i]
        im = temporal_means[exp].plot(ax=ax, add_colorbar=False, cmap=cmap, norm=norm)
        ax.set_title(exp_labels[exp])
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='max')
    cbar.set_label("RZSM (m³ m⁻³)")
    plt.suptitle("Mean Root-Zone Soil Moisture (0-100 cm) (2016–2020)", fontsize=16)
    plt.savefig(f"{out_dir}/rzsm_temporal_mean_map_2016_2020_all_experiments.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    print("Generating difference maps...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    
    diff_bounds = [-0.12, -0.08, -0.04, -0.02, 0.00, 0.02, 0.04, 0.08, 0.12]
    cmap_diff = plt.get_cmap('BrBG').copy()
    cmap_diff.set_bad('white', alpha=0.0)
    norm_diff = mcolors.BoundaryNorm(diff_bounds, cmap_diff.N, extend='both')
    
    im1 = diff_nocdf.plot(ax=axes[0], add_colorbar=False, cmap=cmap_diff, norm=norm_diff)
    axes[0].set_title("DA-NoCDF − OPL")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    
    im2 = diff_cdf.plot(ax=axes[1], add_colorbar=False, cmap=cmap_diff, norm=norm_diff)
    axes[1].set_title("DA-CDF − OPL")
    axes[1].set_xlabel("Longitude")
    axes[1].set_ylabel("Latitude")
    
    cbar_diff = fig.colorbar(im1, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='both')
    cbar_diff.set_label("ΔRZSM (m³ m⁻³)")
    plt.suptitle("Mean RZSM Difference (2016–2020)", fontsize=16)
    plt.savefig(f"{out_dir}/rzsm_temporal_mean_difference_maps_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    print("Generating spatial mean time series...")
    plt.figure(figsize=(12, 6), constrained_layout=True)
    
    styles = {"opl": ("black", "-"), "da_nocdf": ("#d95f02", "--"), "da_cdf": ("#1b9e77", ":")}
    
    for exp in experiments:
        spatial_mean = ds_dict[exp].mean(dim=["lat", "lon"])
        color, ls = styles[exp]
        spatial_mean.plot(label=exp_labels[exp], color=color, linestyle=ls, linewidth=1.5)
        
    plt.title("Daily Spatial-Mean RZSM (2016–2020)")
    plt.ylabel("RZSM (m³ m⁻³)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.savefig(f"{out_dir}/rzsm_spatial_mean_timeseries_2016_2020_all_experiments.png", dpi=200, bbox_inches='tight')
    plt.close()

    print("\n--- VERTICAL SANITY CHECK ---")
    vars = ["ssm", "sm_layer2", "sm_layer3", "rzsm"]
    interim_dir = "data/interim/noahmp"
    
    for exp in experiments:
        print(f"[{exp_labels[exp]}]")
        for v in vars:
            if v == "rzsm":
                paths = [f"{base_dir}/{exp}/rzsm/rzsm_{year}.nc" for year in years]
            else:
                paths = [f"{interim_dir}/{exp}/{v}/{v}_{year}.nc" for year in years]
            ds = xr.concat([xr.open_dataset(p) for p in paths], dim='time')
            v_mean = float(ds[v].mean())
            print(f"  mean {v}: {v_mean:.4f}")

    print("All figures successfully updated.")

if __name__ == "__main__":
    main()
