import os
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

"""
SMAP-XAI: Air Temperature QC Plotting

Purpose
-------
Preprocessing/QC visualization for canonical environmental air temperature forcing.
Generates interannual maps, temporal mean maps, and a spatial-mean time series.

Inputs
------
Annual air_temperature NetCDF files extracted from deterministic OPL output.

Period
------
2016-2020

Outputs
-------
daily spatial-mean air temperature time series (2016-2020)
2016-2020 temporal-mean daily air temperature map
Annual domain-average air temperature maps (2016-2020)

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def main():
    years = range(2016, 2021)
    
    base_dir = "data/interim/noahmp/forcing/air_temperature"
    out_dir = "reports/qc/air_temperature"
    os.makedirs(out_dir, exist_ok=True)
    
    print("--- LOADING AIR TEMPERATURE DATA ---")
    paths = [f"{base_dir}/air_temperature_{year}.nc" for year in years]
    ds = xr.concat([xr.open_dataset(p) for p in paths], dim='time')
    
    # Convert to Celsius for visualization only
    ds_c = ds['air_temperature'] - 273.15
    
    # 1. 2016-2020 Mean Daily Air Temperature Map
    print("Generating mean daily air temperature map...")
    mean_daily = ds_c.mean(dim="time")
    
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    
    cmap = plt.get_cmap('plasma').copy()
    cmap.set_bad('white', alpha=0.0)
    
    # Using sensible discrete boundaries for Morocco temperature
    boundaries = np.arange(0, 32, 2)
    norm = plt.matplotlib.colors.BoundaryNorm(boundaries, cmap.N, extend='both')
    
    im = mean_daily.plot(ax=ax, add_colorbar=False, cmap=cmap, norm=norm)
    ax.set_title("Mean Daily Air Temperature (2016-2020)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', shrink=0.8, extend='both')
    cbar.set_label("Air Temperature (°C)")
    plt.savefig(f"{out_dir}/air_temperature_temporal_mean_map_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # 2. Daily Spatial-Mean Air Temperature Time Series
    print("Generating spatial mean time series...")
    plt.figure(figsize=(14, 5), constrained_layout=True)
    
    spatial_mean = ds_c.mean(dim=["lat", "lon"])
    spatial_mean.plot(color="#d95f02", linewidth=1.5)
        
    plt.title("Daily Spatial-Mean Air Temperature (2016-2020)")
    plt.ylabel("Air Temperature (°C)")
    plt.xlabel("Time")
    plt.grid(True, alpha=0.5)
    plt.savefig(f"{out_dir}/air_temperature_spatial_mean_timeseries_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    # 3. Annual Domain-Average Air Temperature Maps (2016-2020)
    print("Generating annual average air temperature maps...")
    fig, axes = plt.subplots(1, 5, figsize=(20, 4), constrained_layout=True)
    
    ann_bounds = np.arange(10, 30, 2)
    ann_cmap = plt.get_cmap('plasma').copy()
    ann_cmap.set_bad('white', alpha=0.0)
    ann_norm = plt.matplotlib.colors.BoundaryNorm(ann_bounds, ann_cmap.N, extend='both')
    
    for i, year in enumerate(years):
        ann_mean = ds_c.sel(time=str(year)).mean(dim='time', skipna=False)
        ax = axes[i]
        im_ann = ann_mean.plot(ax=ax, add_colorbar=False, cmap=ann_cmap, norm=ann_norm)
        ax.set_title(f"{year}")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
    cbar_ann = fig.colorbar(im_ann, ax=axes.ravel().tolist(), orientation='vertical', shrink=0.8, extend='both')
    cbar_ann.set_label("Annual Mean Temperature (°C)")
    plt.suptitle("Annual Mean Air Temperature (2016–2020)", fontsize=16)
    plt.savefig(f"{out_dir}/air_temperature_annual_mean_maps_2016_2020.png", dpi=200, bbox_inches='tight')
    plt.close()

    print("All figures successfully updated.")

if __name__ == "__main__":
    main()
