import os
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

"""
SMAP-XAI: Evapotranspiration QC Plotting

Purpose
-------
Preprocessing/QC visualization for canonical evapotranspiration.
Generates interannual maps, temporal mean maps, and spatial-mean time series 
for OPL, DA-NoCDF, and DA-CDF. Also generates DA vs OPL difference maps.

Inputs
------
Annual evapotranspiration NetCDF files.

Period
------
2016-2020

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def main():
    years = range(2016, 2021)
    exps = ["opl", "da_nocdf", "da_cdf"]
    
    out_dir = "reports/qc/et"
    os.makedirs(out_dir, exist_ok=True)
    
    print("--- LOADING ET DATA ---")
    data = {}
    for exp in exps:
        paths = [f"data/interim/noahmp/{exp}/et/et_{year}.nc" for year in years]
        data[exp] = xr.concat([xr.open_dataset(p) for p in paths], dim='time')
        
    # A. Daily spatial-mean ET time series
    print("Generating spatial mean time series...")
    fig, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)
    colors = {'opl': '#1f77b4', 'da_nocdf': '#ff7f0e', 'da_cdf': '#2ca02c'}
    labels = {'opl': 'OPL', 'da_nocdf': 'DA-NoCDF', 'da_cdf': 'DA-CDF'}
    
    for exp in exps:
        spatial_mean = data[exp]['et'].mean(dim=["lat", "lon"])
        spatial_mean.plot(ax=ax, color=colors[exp], label=labels[exp], linewidth=1.5, alpha=0.8)
        
    ax.set_title("Daily Spatial-Mean Evapotranspiration (2016-2020)")
    ax.set_ylabel("ET (mm day⁻¹)")
    ax.set_xlabel("Time")
    ax.legend()
    ax.grid(True, alpha=0.5)
    plt.savefig(f"{out_dir}/et_spatial_mean_timeseries_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # B. Temporal-mean ET maps
    print("Generating temporal-mean ET maps...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    
    boundaries = [0.0, 0.2, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
    cmap = plt.get_cmap('YlGnBu').copy()
    cmap.set_bad('white', alpha=0.0)
    norm = mcolors.BoundaryNorm(boundaries, cmap.N, extend='both')
    
    for i, exp in enumerate(exps):
        mean_daily = data[exp]['et'].mean(dim="time")
        ax = axes[i]
        im = mean_daily.plot(ax=ax, add_colorbar=False, cmap=cmap, norm=norm)
        ax.set_title(f"{labels[exp]} Mean ET")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='both')
    cbar.set_label("Evapotranspiration (mm day⁻¹)")
    plt.suptitle("Mean Daily Evapotranspiration (2016-2020)", fontsize=16)
    plt.savefig(f"{out_dir}/et_temporal_mean_maps_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # C. Temporal-mean ET difference maps (DA - OPL)
    print("Generating temporal-mean ET difference maps...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    
    diff_nocdf = data['da_nocdf']['et'].mean(dim="time") - data['opl']['et'].mean(dim="time")
    diff_cdf = data['da_cdf']['et'].mean(dim="time") - data['opl']['et'].mean(dim="time")
    
    diff_boundaries = [-1.0, -0.5, -0.2, -0.1, -0.05, 0.05, 0.1, 0.2, 0.5, 1.0]
    diff_cmap = plt.get_cmap('BrBG').copy()
    diff_cmap.set_bad('white', alpha=0.0)
    diff_norm = mcolors.BoundaryNorm(diff_boundaries, diff_cmap.N, extend='both')
    
    im_diff = diff_nocdf.plot(ax=axes[0], add_colorbar=False, cmap=diff_cmap, norm=diff_norm)
    axes[0].set_title("DA-NoCDF - OPL")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    
    diff_cdf.plot(ax=axes[1], add_colorbar=False, cmap=diff_cmap, norm=diff_norm)
    axes[1].set_title("DA-CDF - OPL")
    axes[1].set_xlabel("Longitude")
    axes[1].set_ylabel("Latitude")
    
    cbar_diff = fig.colorbar(im_diff, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='both')
    cbar_diff.set_label("$\Delta$ Evapotranspiration (mm day⁻¹)")
    plt.suptitle("Mean Daily Evapotranspiration Differences (2016-2020)", fontsize=16)
    plt.savefig(f"{out_dir}/et_temporal_mean_difference_maps_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()

    # D. Annual Domain-Average ET text dump
    print("\n--- ANNUAL DOMAIN-AVERAGE ET (mm/year) ---")
    for exp in exps:
        print(f"\n{labels[exp]}:")
        for year in years:
            ann_sum = data[exp]['et'].sel(time=str(year)).sum(dim='time', skipna=False)
            mean_ann = ann_sum.mean(skipna=True).values
            print(f"  {year}: {mean_ann:.2f}")

    print("\nAll figures successfully updated.")

if __name__ == "__main__":
    main()
