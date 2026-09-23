#!/usr/bin/env python3
"""
EnKF Innovation QC

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Generates diagnostic plots for the native EnKF innovation.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import glob
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import warnings

def load_all_years(directory):
    files = sorted(glob.glob(os.path.join(directory, "*.nc")))
    datasets = [xr.open_dataset(f) for f in files]
    ds = xr.concat(datasets, dim='event_time')
    return ds

def main():
    cdf_dir = "data/interim/enkf/da_cdf/innovation"
    nocdf_dir = "data/interim/enkf/da_nocdf/innovation"
    out_dir = "reports/qc/innovation"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_cdf = load_all_years(cdf_dir)
    ds_nocdf = load_all_years(nocdf_dir)
    
    inv_cdf = ds_cdf['innovation'].values
    inv_nocdf = ds_nocdf['innovation'].values
    
    valid_cdf = inv_cdf[~np.isnan(inv_cdf)]
    valid_nocdf = inv_nocdf[~np.isnan(inv_nocdf)]
    
    # 0. EVENT-BASED STATISTICS (FINITE, POSITIVE, NEGATIVE, EXACT ZERO)
    print("================ DA-CDF ===============")
    finite_cdf = len(valid_cdf)
    pos_cdf = np.sum(valid_cdf > 0)
    neg_cdf = np.sum(valid_cdf < 0)
    zero_cdf = np.sum(valid_cdf == 0.0)
    print(f"finite count: {finite_cdf}")
    print(f"negative count: {neg_cdf}")
    print(f"exact-zero count: {zero_cdf}")
    print(f"positive count: {pos_cdf}")
    assert neg_cdf + zero_cdf + pos_cdf == finite_cdf, "CDF count mismatch!"
    
    print("\n================ DA-NoCDF =============")
    finite_nocdf = len(valid_nocdf)
    pos_nocdf = np.sum(valid_nocdf > 0)
    neg_nocdf = np.sum(valid_nocdf < 0)
    zero_nocdf = np.sum(valid_nocdf == 0.0)
    print(f"finite count: {finite_nocdf}")
    print(f"negative count: {neg_nocdf}")
    print(f"exact-zero count: {zero_nocdf}")
    print(f"positive count: {pos_nocdf}")
    assert neg_nocdf + zero_nocdf + pos_nocdf == finite_nocdf, "NoCDF count mismatch!"
    print("\n")
    
    # A. INNOVATION DISTRIBUTION
    plt.figure(figsize=(10, 6))
    plt.hist(valid_cdf, bins=100, alpha=0.5, density=True, label='DA-CDF', range=(-0.15, 0.15))
    plt.hist(valid_nocdf, bins=100, alpha=0.5, density=True, label='DA-NoCDF', range=(-0.15, 0.15))
    plt.title('Innovation Distribution (Valid samples only)')
    plt.xlabel('Innovation (m3 m-3)')
    plt.ylabel('Density')
    plt.axvline(0, color='k', linestyle='--')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'innovation_distribution.png'))
    plt.close()
    
    # B. TEMPORAL SUMMARY
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_signed_cdf = np.nanmean(inv_cdf, axis=(1, 2))
        mean_abs_cdf = np.nanmean(np.abs(inv_cdf), axis=(1, 2))
        valid_count_cdf = np.sum(~np.isnan(inv_cdf), axis=(1, 2))
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(ds_cdf['event_time'].values, mean_signed_cdf, label='Mean Signed', color='C0', alpha=0.7)
    ax1.plot(ds_cdf['event_time'].values, mean_abs_cdf, label='Mean Absolute', color='C1', alpha=0.7)
    ax1.set_ylabel('Innovation (m3 m-3)')
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    ax2.plot(ds_cdf['event_time'].values, valid_count_cdf, label='Valid Obs Count', color='k', alpha=0.3, linewidth=1)
    ax2.set_ylabel('Valid Obs Count')
    
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper right')
    
    plt.title('Spatial Mean Innovation Through Time (DA-CDF)')
    plt.savefig(os.path.join(out_dir, 'temporal_summary_cdf.png'))
    plt.close()
    
    # C. REPRESENTATIVE EVENT MAPS
    event_idx = [10, 200, 500]
    extent = [ds_cdf.lon.values.min(), ds_cdf.lon.values.max(), ds_cdf.lat.values.min(), ds_cdf.lat.values.max()]
    
    for idx in event_idx:
        ev_time = ds_cdf['event_time'].values[idx]
        data = ds_cdf['innovation'].isel(event_time=idx).values
        
        plt.figure(figsize=(8, 6))
        vmax = 0.1
        plt.imshow(data, origin='lower', cmap='BrBG', vmin=-vmax, vmax=vmax, extent=extent)
        plt.colorbar(label='Innovation (m3 m-3)', extend='both')
        plt.title(f'DA-CDF Innovation Map: {ev_time}')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        time_str = str(ev_time).replace(':', '').replace('-', '').replace('T', '_')[:13]
        plt.savefig(os.path.join(out_dir, f'event_map_{time_str}.png'))
        plt.close()
        
    # D. OBSERVATION-SUPPORT MAP
    # Fraction of events with valid assimilated observation per pixel
    is_valid = ~np.isnan(inv_cdf)
    support_fraction = np.sum(is_valid, axis=0) / ds_cdf.event_time.size
    
    # Identify ocean mask (if a pixel is NEVER valid across all 4411 events, it's likely ocean)
    land_mask = np.sum(is_valid, axis=0) > 0
    support_fraction = np.where(land_mask, support_fraction, np.nan)
    
    plt.figure(figsize=(8, 6))
    plt.imshow(support_fraction, origin='lower', cmap='viridis', extent=extent)
    plt.colorbar(label='Support Fraction')
    plt.title('Fraction of Events with Valid Assimilated Observation (DA-CDF)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'observation_support_cdf.png'))
    plt.close()
    
    # E. INNOVATION VS INCREMENT
    inc_cdf_ds = xr.open_dataset('data/interim/enkf/da_cdf/increment_signed/increment_signed_2016.nc')
    inc_nocdf_ds = xr.open_dataset('data/interim/enkf/da_nocdf/increment_signed/increment_signed_2016.nc')
    
    inv_cdf_2016 = ds_cdf.sel(event_time=ds_cdf['event_time'].dt.year == 2016)['innovation'].values
    inv_nocdf_2016 = ds_nocdf.sel(event_time=ds_nocdf['event_time'].dt.year == 2016)['innovation'].values
    
    # Ensure they align by event time for the scatter plot
    common_cdf_times = np.intersect1d(ds_cdf.sel(event_time=ds_cdf['event_time'].dt.year == 2016)['event_time'].values, inc_cdf_ds['event_time'].values)
    
    v_inv_cdf = ds_cdf['innovation'].sel(event_time=common_cdf_times).values.flatten()
    v_inc_cdf = inc_cdf_ds['increment_signed'].sel(event_time=common_cdf_times).values.flatten()
    
    mask = (~np.isnan(v_inv_cdf)) & (~np.isnan(v_inc_cdf))
    v_inv_cdf = v_inv_cdf[mask]
    v_inc_cdf = v_inc_cdf[mask]
    
    plt.figure(figsize=(8, 8))
    plt.hexbin(v_inv_cdf, v_inc_cdf, gridsize=50, cmap='inferno', bins='log')
    plt.colorbar(label='log10(Count)')
    plt.xlabel('Innovation (m3 m-3)')
    plt.ylabel('Signed Increment (m3 m-3)')
    plt.title('DA-CDF: Innovation vs. Signed Increment (2016)')
    plt.plot([-0.2, 0.2], [-0.2, 0.2], 'k--', alpha=0.5)
    plt.grid(True)
    plt.savefig(os.path.join(out_dir, 'innov_vs_incr_cdf.png'))
    plt.close()
    
    print("QC complete. Plots saved to", out_dir)

if __name__ == "__main__":
    main()
