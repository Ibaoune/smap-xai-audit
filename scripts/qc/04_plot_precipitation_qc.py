import os
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

"""
SMAP-XAI: Precipitation QC Plotting

Purpose
-------
Preprocessing/QC visualization for canonical environmental precipitation forcing.
Generates interannual maps, temporal mean maps, and a spatial-mean time series.

Inputs
------
Annual precipitation NetCDF files extracted from deterministic OPL output.

Period
------
2016-2020

Outputs
-------
daily spatial-mean precipitation time series (2016-2020)
2016-2020 temporal-mean daily precipitation map
Annual domain-average precipitation maps (2016-2020)

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def main():
    years = range(2016, 2021)
    
    base_dir = "data/interim/noahmp/forcing/precipitation"
    out_dir = "reports/qc/precipitation"
    os.makedirs(out_dir, exist_ok=True)
    
    print("--- LOADING PRECIPITATION DATA ---")
    paths = [f"{base_dir}/precipitation_{year}.nc" for year in years]
    ds = xr.concat([xr.open_dataset(p) for p in paths], dim='time')
    
    # 1. 2016-2020 Mean Daily Precipitation Map
    print("Generating mean daily precipitation map...")
    mean_daily = ds['precipitation'].mean(dim="time")
    
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    
    boundaries = [0.0, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
    cmap = plt.get_cmap('Blues').copy()
    cmap.set_bad('white', alpha=0.0)
    norm = mcolors.BoundaryNorm(boundaries, cmap.N, extend='max')
    
    im = mean_daily.plot(ax=ax, add_colorbar=False, cmap=cmap, norm=norm)
    ax.set_title("Mean Daily Precipitation (2016-2020)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', shrink=0.8, extend='max')
    cbar.set_label("Precipitation (mm day⁻¹)")
    plt.savefig(f"{out_dir}/precipitation_temporal_mean_map_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # 2. Daily Spatial-Mean Precipitation Time Series
    print("Generating spatial mean time series...")
    plt.figure(figsize=(14, 5), constrained_layout=True)
    
    spatial_mean = ds['precipitation'].mean(dim=["lat", "lon"])
    spatial_mean.plot(color="#1f78b4", linewidth=1.5)
        
    plt.title("Daily Spatial-Mean Precipitation (2016-2020)")
    plt.ylabel("Precipitation (mm day⁻¹)")
    plt.xlabel("Time")
    plt.grid(True, alpha=0.5)
    plt.savefig(f"{out_dir}/precipitation_spatial_mean_timeseries_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # 3. Annual Domain-Average Precipitation Maps (2016-2020)
    print("Generating annual accumulated precipitation maps...")
    fig, axes = plt.subplots(1, 5, figsize=(20, 4), constrained_layout=True)
    
    ann_bounds = [0, 50, 100, 200, 300, 400, 500, 700, 1000]
    ann_cmap = plt.get_cmap('YlGnBu').copy()
    ann_cmap.set_bad('white', alpha=0.0)
    ann_norm = mcolors.BoundaryNorm(ann_bounds, ann_cmap.N, extend='max')
    
    for i, year in enumerate(years):
        ann_sum = ds['precipitation'].sel(time=str(year)).sum(dim='time', skipna=False)
        ax = axes[i]
        im_ann = ann_sum.plot(ax=ax, add_colorbar=False, cmap=ann_cmap, norm=ann_norm)
        ax.set_title(f"{year}")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
    cbar_ann = fig.colorbar(im_ann, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='max')
    cbar_ann.set_label("Annual Precipitation (mm year⁻¹)")
    plt.suptitle("Annual Accumulated Precipitation (2016–2020)", fontsize=16)
    plt.savefig(f"{out_dir}/precipitation_annual_accumulated_maps_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()

    print("All figures successfully updated.")

if __name__ == "__main__":
    main()
