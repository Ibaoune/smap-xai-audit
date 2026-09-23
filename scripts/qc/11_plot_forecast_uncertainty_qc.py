#!/usr/bin/env python3
import os
import glob
import xarray as xr
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt

def load_all(dir_path):
    files = sorted(glob.glob(os.path.join(dir_path, "*.nc")))
    if not files: return xr.Dataset()
    return xr.concat([xr.open_dataset(f) for f in files], dim='event_time')

def main():
    cdf_dir = "data/interim/enkf/da_cdf/forecast_variance"
    nocdf_dir = "data/interim/enkf/da_nocdf/forecast_variance"
    
    out_dir = "reports/qc/forecast_uncertainty"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_cdf = load_all(cdf_dir)
    ds_nocdf = load_all(nocdf_dir)
    
    inv_cdf = ds_cdf['forecast_variance'].values
    inv_nocdf = ds_nocdf['forecast_variance'].values
    
    valid_cdf = inv_cdf[~np.isnan(inv_cdf)]
    valid_nocdf = inv_nocdf[~np.isnan(inv_nocdf)]
    
    # A. Distribution
    plt.figure(figsize=(10, 6))
    # use log scale for variance if needed, but let's try standard linear bins first
    # capping at 99th percentile for plot
    p99_cdf = np.percentile(valid_cdf, 99) if len(valid_cdf) > 0 else 0.01
    plt.hist(valid_cdf, bins=100, alpha=0.5, density=True, label='DA-CDF', range=(0, p99_cdf))
    plt.hist(valid_nocdf, bins=100, alpha=0.5, density=True, label='DA-NoCDF', range=(0, p99_cdf))
    plt.title('Forecast Variance (HPH^T) Distribution')
    plt.xlabel('Variance ((m3 m-3)2)')
    plt.ylabel('Density')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'variance_distribution.png'))
    plt.close()
    
    # B. Temporal summary
    mean_cdf = np.nanmean(inv_cdf, axis=(1, 2))
    median_cdf = np.nanmedian(inv_cdf, axis=(1, 2))
    valid_count = np.sum(~np.isnan(inv_cdf), axis=(1, 2))
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(ds_cdf['event_time'].values, mean_cdf, label='Mean', color='C0')
    ax1.plot(ds_cdf['event_time'].values, median_cdf, label='Median', color='C1')
    ax1.set_ylabel('Variance ((m3 m-3)2)')
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    ax2.plot(ds_cdf['event_time'].values, valid_count, label='Valid Obs Count', color='k', alpha=0.3, linewidth=1)
    ax2.set_ylabel('Valid Obs Count')
    
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper right')
    plt.title('Spatial Mean Forecast Variance Through Time (DA-CDF)')
    plt.savefig(os.path.join(out_dir, 'temporal_summary_cdf.png'))
    plt.close()
    
    # C. Representative events
    if len(ds_cdf.event_time) > 10:
        event_idx = [10, 200, 500]
        extent = [ds_cdf.lon.values.min(), ds_cdf.lon.values.max(), ds_cdf.lat.values.min(), ds_cdf.lat.values.max()]
        for idx in event_idx:
            ev_time = ds_cdf['event_time'].values[idx]
            data = ds_cdf['forecast_variance'].isel(event_time=idx).values
            
            plt.figure(figsize=(8, 6))
            vmax = np.nanpercentile(data, 95) if np.sum(~np.isnan(data)) > 0 else 0.001
            plt.imshow(data, origin='lower', cmap='viridis', vmin=0, vmax=vmax, extent=extent)
            plt.colorbar(label='Variance ((m3 m-3)2)', extend='max')
            plt.title(f'DA-CDF Forecast Variance: {ev_time}')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            time_str = str(ev_time).replace(':', '').replace('-', '').replace('T', '_')[:13]
            plt.savefig(os.path.join(out_dir, f'event_map_{time_str}.png'))
            plt.close()
            
    # D. 2016-2020 mean
    mean_map = np.nanmean(inv_cdf, axis=0)
    plt.figure(figsize=(8, 6))
    vmax = np.nanpercentile(mean_map, 95)
    plt.imshow(mean_map, origin='lower', cmap='viridis', vmin=0, vmax=vmax, extent=extent)
    plt.colorbar(label='Variance ((m3 m-3)2)', extend='max')
    plt.title('Temporal Mean Forecast Variance (DA-CDF 2016-2020)')
    plt.savefig(os.path.join(out_dir, 'mean_map_cdf.png'))
    plt.close()
    
    print("QC complete. Plots saved to", out_dir)

if __name__ == "__main__":
    main()
