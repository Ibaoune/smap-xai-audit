#!/usr/bin/env python3
"""
EnKF Analysis Increment QC (Signed)

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Generates diagnostic plots for the signed analysis increment of Soil Moisture Layer 1.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import glob
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def load_all_years(directory):
    files = sorted(glob.glob(os.path.join(directory, "increment_signed_*.nc")))
    datasets = [xr.open_dataset(f) for f in files]
    ds = xr.concat(datasets, dim='event_time')
    return ds

def main():
    cdf_dir = "data/interim/enkf/da_cdf/increment_signed"
    nocdf_dir = "data/interim/enkf/da_nocdf/increment_signed"
    out_dir = os.environ.get("QC_OUT_DIR", f"reports/qc/analysis_increment")
    os.makedirs(out_dir, exist_ok=True)
    
    ds_cdf = load_all_years(cdf_dir)
    ds_nocdf = load_all_years(nocdf_dir)
    
    # A. EVENT-TIME DISTRIBUTION
    plt.figure(figsize=(10, 6))
    pd.Series(ds_cdf['event_time'].values).dt.to_period('M').value_counts().sort_index().plot(label='DA-CDF', color='C0')
    pd.Series(ds_nocdf['event_time'].values).dt.to_period('M').value_counts().sort_index().plot(label='DA-NoCDF', color='C1')
    plt.title('Assimilation Events Per Month')
    plt.ylabel('Event Count')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'event_time_distribution.png'))
    plt.close()

    # Get sample data for histograms and time series
    inc_cdf = ds_cdf['increment_signed'].values
    inc_nocdf = ds_nocdf['increment_signed'].values
    
    # Filter valid non-missing pixels
    valid_cdf = inc_cdf[~np.isnan(inc_cdf)]
    valid_nocdf = inc_nocdf[~np.isnan(inc_nocdf)]
    
    # B. INCREMENT DISTRIBUTION
    # For histograms, exclude 0.0 which dominates massively
    non_zero_cdf = valid_cdf[valid_cdf != 0.0]
    non_zero_nocdf = valid_nocdf[valid_nocdf != 0.0]
    
    plt.figure(figsize=(10, 6))
    plt.hist(non_zero_cdf, bins=100, alpha=0.5, density=True, label='DA-CDF', range=(-0.1, 0.1))
    plt.hist(non_zero_nocdf, bins=100, alpha=0.5, density=True, label='DA-NoCDF', range=(-0.1, 0.1))
    plt.title('Analysis Increment Distribution (Excluding exactly zero)')
    plt.xlabel('Signed Increment (m3 m-3)')
    plt.ylabel('Density')
    plt.axvline(0, color='k', linestyle='--')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'increment_distribution.png'))
    plt.close()
    
    # C. EVENT MAPS
    event_idx = [10, 200, 500]
    for idx in event_idx:
        ev_time = ds_cdf['event_time'].values[idx]
        data = ds_cdf['increment_signed'].isel(event_time=idx)
        
        plt.figure(figsize=(8, 6))
        vmax = 0.05
        data.plot(cmap='BrBG', vmin=-vmax, vmax=vmax, add_colorbar=True, 
                  cbar_kwargs={'label': 'Increment (m3 m-3)', 'extend': 'both'})
        plt.title(f'DA-CDF Increment Map: {ev_time}')
        time_str = str(ev_time).replace(':', '').replace('-', '').replace('T', '_')[:13]
        plt.savefig(os.path.join(out_dir, f'event_map_{time_str}.png'))
        plt.close()
        
    # D. TEMPORAL SUMMARY
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_signed_cdf = np.nanmean(inc_cdf, axis=(1, 2))
        mean_abs_cdf = np.nanmean(np.abs(inc_cdf), axis=(1, 2))
    
    plt.figure(figsize=(12, 6))
    plt.plot(ds_cdf['event_time'].values, mean_signed_cdf, label='Mean Signed', alpha=0.7)
    plt.plot(ds_cdf['event_time'].values, mean_abs_cdf, label='Mean Absolute', alpha=0.7)
    plt.title('Spatial Mean Increment Through Time (DA-CDF)')
    plt.ylabel('Increment (m3 m-3)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'temporal_summary_cdf.png'))
    plt.close()
    
    # E. OBSERVATION / UPDATE COVERAGE
    is_updated = (~np.isnan(inc_cdf)) & (inc_cdf != 0.0)
    update_fraction = np.sum(is_updated, axis=0) / ds_cdf.event_time.size
    
    land_mask = ~np.isnan(inc_cdf[0])
    update_fraction = np.where(land_mask, update_fraction, np.nan)
    
    plt.figure(figsize=(8, 6))
    extent = [ds_cdf.lon.values.min(), ds_cdf.lon.values.max(), ds_cdf.lat.values.min(), ds_cdf.lat.values.max()]
    plt.imshow(update_fraction, origin='lower', cmap='viridis', extent=extent)
    plt.colorbar(label='Update Fraction')
    plt.title('Fraction of Events with Non-Zero Increment (DA-CDF)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'update_coverage_cdf.png'))
    plt.close()

    print("QC complete. Plots saved to", out_dir)

if __name__ == "__main__":
    main()
