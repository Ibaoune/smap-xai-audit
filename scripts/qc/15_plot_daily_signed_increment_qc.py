#!/usr/bin/env python3
import os
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

def load_all(dir_path, var_name):
    files = sorted(glob.glob(os.path.join(dir_path, "*.nc")))
    if not files: return xr.Dataset()
    return xr.concat([xr.open_dataset(f) for f in files], dim='time')

def process_exp(exp, ds, ds_freq):
    print(f"\n================ {exp} ================")
    
    vals = ds['daily_signed_increment'].values
    freq = ds_freq['observation_frequency'].values
    
    # Unconditional stats (all valid land pixel-days)
    valid_land = ~np.isnan(vals)
    uncond = vals[valid_land]
    
    print("UNCONDITIONAL (All valid land pixel-days):")
    print(f"  min: {np.min(uncond)}")
    print(f"  max: {np.max(uncond)}")
    print(f"  mean: {np.mean(uncond)}")
    print(f"  median: {np.median(uncond)}")
    print(f"  std: {np.std(uncond)}")
    print(f"  fraction < 0: {np.sum(uncond < 0) / len(uncond)}")
    print(f"  fraction == 0: {np.sum(uncond == 0) / len(uncond)}")
    print(f"  fraction > 0: {np.sum(uncond > 0) / len(uncond)}")
    
    # Conditional stats (only assimilated pixel-days)
    cond_mask = (freq == 1) & valid_land
    cond = vals[cond_mask]
    
    print("\nCONDITIONAL (Assimilated pixel-days only):")
    print(f"  min: {np.min(cond)}")
    print(f"  max: {np.max(cond)}")
    print(f"  mean: {np.mean(cond)}")
    print(f"  median: {np.median(cond)}")
    print(f"  std: {np.std(cond)}")
    print(f"  p05: {np.percentile(cond, 5)}")
    print(f"  p25: {np.percentile(cond, 25)}")
    print(f"  p75: {np.percentile(cond, 75)}")
    print(f"  p95: {np.percentile(cond, 95)}")
    print(f"  fraction < 0: {np.sum(cond < 0) / len(cond)}")
    print(f"  fraction > 0: {np.sum(cond > 0) / len(cond)}")

def main():
    out_dir = "reports/qc/daily_signed_increment"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_signed_increment", "daily_signed_increment")
    ds_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_signed_increment", "daily_signed_increment")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_nocdf, ds_freq_nocdf)
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_cdf['daily_signed_increment'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage valid non-zero count: {np.sum(valid_cdf != 0)}")
    
    nocdf_outage_vals = ds_nocdf['daily_signed_increment'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage valid non-zero count: {np.sum(valid_nocdf != 0)}")
    
    # EVENT-TO-DAILY IDENTITY TEST (DA-CDF)
    print("\n================ EVENT-TO-DAILY IDENTITY TEST (DA-CDF) ================")
    inv_cdf_2016 = xr.open_dataset("data/interim/enkf/da_cdf/increment_signed/increment_signed_2016.nc")
    inc_var = 'increment' if 'increment' in inv_cdf_2016.data_vars else 'increment_signed'
    inv_cdf_2016_events = inv_cdf_2016[inc_var].values
    inv_cdf_2016_times = inv_cdf_2016.event_time.values
    
    test_days = ['2016-01-05', '2016-07-01', '2016-12-10']
    for day_str in test_days:
        dt = pd.to_datetime(day_str)
        t_mask = (inv_cdf_2016_times >= dt) & (inv_cdf_2016_times < dt + pd.Timedelta(days=1))
        idx = np.where(t_mask)[0]
        
        if len(idx) == 0:
            print(f"{day_str}: No events")
            continue
            
        ev_inc = inv_cdf_2016_events[idx[0]]  # Assume first event for identity test
        daily_inc = ds_cdf.sel(time=day_str)['daily_signed_increment'].values
        
        mask = ~np.isnan(ev_inc)
        diff = np.abs(ev_inc[mask] - daily_inc[mask])
        print(f"{day_str}: max abs diff = {np.max(diff):.1e}, mean abs diff = {np.mean(diff):.1e}, unequal = {np.sum(diff > 0)}")

    # ================ PLOTTING ================
    
    times_arr = ds_cdf.time.values
    extent = [ds_cdf.lon.values.min(), ds_cdf.lon.values.max(), ds_cdf.lat.values.min(), ds_cdf.lat.values.max()]
    
    # A. DAILY DOMAIN MEAN
    def get_means(ds, ds_freq):
        vals = ds['daily_signed_increment'].values
        freq = ds_freq['observation_frequency'].values
        
        uncond_mean = np.nanmean(vals, axis=(1, 2))
        
        cond_mean = np.zeros(len(vals))
        for i in range(len(vals)):
            mask = freq[i] == 1
            if np.any(mask):
                cond_mean[i] = np.nanmean(vals[i][mask])
            else:
                cond_mean[i] = np.nan
        return uncond_mean, cond_mean

    uncond_cdf, cond_cdf = get_means(ds_cdf, ds_freq_cdf)
    uncond_nocdf, cond_nocdf = get_means(ds_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    axes[0].plot(times_arr, uncond_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, uncond_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Unconditional Domain Mean (All Valid Land)')
    axes[0].set_ylabel('Mean Increment')
    axes[0].legend()
    axes[0].axhline(0, color='black', lw=0.5, ls='--')
    
    axes[1].plot(times_arr, cond_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, cond_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Conditional Domain Mean (Updated Pixels Only)')
    axes[1].set_ylabel('Mean Increment')
    axes[1].legend()
    axes[1].axhline(0, color='black', lw=0.5, ls='--')
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_domain_mean.png'))
    plt.close()
    
    # B. UPDATED-PIXEL DISTRIBUTION
    cond_vals_cdf = ds_cdf['daily_signed_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1) & ~np.isnan(ds_cdf['daily_signed_increment'].values)]
    cond_vals_nocdf = ds_nocdf['daily_signed_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1) & ~np.isnan(ds_nocdf['daily_signed_increment'].values)]
    
    plt.figure(figsize=(10, 6))
    bins = np.linspace(min(np.min(cond_vals_cdf), np.min(cond_vals_nocdf)), max(np.max(cond_vals_cdf), np.max(cond_vals_nocdf)), 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.axvline(0, color='black', lw=1, ls='--')
    plt.title('Distribution of Signed Increments Conditional on Assimilation')
    plt.xlabel('Increment (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'updated_pixel_distribution.png'))
    plt.close()
    
    # C. TEMPORAL MEAN MAP
    mean_cdf = np.nanmean(ds_cdf['daily_signed_increment'].values, axis=0)
    mean_nocdf = np.nanmean(ds_nocdf['daily_signed_increment'].values, axis=0)
    
    vmax = max(np.nanmax(np.abs(mean_cdf)), np.nanmax(np.abs(mean_nocdf)))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(mean_cdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax, vmax=vmax)
    axes[0].set_title('DA-CDF Temporal Mean (Unconditional)')
    im2 = axes[1].imshow(mean_nocdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax, vmax=vmax)
    axes[1].set_title('DA-NoCDF Temporal Mean (Unconditional)')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Mean Increment (m3 m-3)')
    plt.savefig(os.path.join(out_dir, 'temporal_mean_map.png'))
    plt.close()
    
    # D. CONDITIONAL MEAN MAP
    def get_cond_mean(ds, ds_freq):
        vals = ds['daily_signed_increment'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    cond_mean_cdf = get_cond_mean(ds_cdf, ds_freq_cdf)
    cond_mean_nocdf = get_cond_mean(ds_nocdf, ds_freq_nocdf)
    
    vmax_cond = max(np.nanmax(np.abs(cond_mean_cdf)), np.nanmax(np.abs(cond_mean_nocdf)))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(cond_mean_cdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_cond, vmax=vmax_cond)
    axes[0].set_title('DA-CDF Mean Conditional on Assimilation')
    im2 = axes[1].imshow(cond_mean_nocdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_cond, vmax=vmax_cond)
    axes[1].set_title('DA-NoCDF Mean Conditional on Assimilation')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Mean Increment (m3 m-3)')
    plt.savefig(os.path.join(out_dir, 'conditional_mean_map.png'))
    plt.close()

if __name__ == "__main__":
    main()
