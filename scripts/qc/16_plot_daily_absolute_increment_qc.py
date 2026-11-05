#!/usr/bin/env python3
import os
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr
import warnings

warnings.filterwarnings('ignore')

def load_all(dir_path, var_name):
    files = sorted(glob.glob(os.path.join(dir_path, "*.nc")))
    if not files: return xr.Dataset()
    return xr.concat([xr.open_dataset(f) for f in files], dim='time')

def process_exp(exp, ds_abs, ds_signed, ds_freq):
    print(f"\n================ {exp} ================")
    
    vals_abs = ds_abs['daily_absolute_increment'].values
    vals_signed = ds_signed['daily_signed_increment'].values
    freq = ds_freq['observation_frequency'].values
    
    valid_land = ~np.isnan(vals_abs)
    
    # Sign / Range QC
    neg_count = np.sum(vals_abs[valid_land] < 0)
    zero_count = np.sum(vals_abs[valid_land] == 0)
    pos_count = np.sum(vals_abs[valid_land] > 0)
    print("Sign / Range QC:")
    print(f"  negative count: {neg_count}")
    print(f"  zero count: {zero_count}")
    print(f"  positive count: {pos_count}")
    
    # Observation-frequency Consistency
    freq_0_mask = (freq == 0) & valid_land
    viol_0 = np.sum(vals_abs[freq_0_mask] != 0)
    freq_1_mask = (freq == 1) & valid_land
    viol_1 = np.sum(vals_abs[freq_1_mask] != np.abs(vals_signed[freq_1_mask]))
    viol_nan = np.sum(~np.isnan(vals_abs[~valid_land]))
    print(f"Consistency violations: freq=0 -> {viol_0}, freq=1 -> {viol_1}, nan -> {viol_nan}")
    
    # Unconditional stats
    uncond = vals_abs[valid_land]
    print("\nUNCONDITIONAL (All valid land pixel-days):")
    print(f"  min: {np.min(uncond)}")
    print(f"  max: {np.max(uncond)}")
    print(f"  mean: {np.mean(uncond)}")
    print(f"  median: {np.median(uncond)}")
    print(f"  std: {np.std(uncond)}")
    print(f"  p05: {np.percentile(uncond, 5)}")
    print(f"  p25: {np.percentile(uncond, 25)}")
    print(f"  p75: {np.percentile(uncond, 75)}")
    print(f"  p95: {np.percentile(uncond, 95)}")
    print(f"  p99: {np.percentile(uncond, 99)}")
    print(f"  fraction == 0: {np.sum(uncond == 0) / len(uncond)}")
    print(f"  fraction > 0: {np.sum(uncond > 0) / len(uncond)}")
    
    # Conditional stats
    cond = vals_abs[freq_1_mask]
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
    print(f"  p99: {np.percentile(cond, 99)}")
    
    # Relation to signed increment
    cond_signed = vals_signed[freq_1_mask]
    corr_pearson, _ = pearsonr(cond_signed, cond)
    corr_spearman, _ = spearmanr(cond_signed, cond)
    print("\nRelation to signed increment:")
    print(f"  Pearson Correlation (signed vs absolute on obs_freq=1): {corr_pearson:.4f}")
    print(f"  Spearman Correlation (signed vs absolute on obs_freq=1): {corr_spearman:.4f}")
    
    mean_abs_neg = np.mean(vals_abs[(freq == 1) & (vals_signed < 0)])
    mean_abs_pos = np.mean(vals_abs[(freq == 1) & (vals_signed > 0)])
    print(f"  mean absolute increment where signed < 0: {mean_abs_neg:.6f}")
    print(f"  mean absolute increment where signed > 0: {mean_abs_pos:.6f}")

    zeros_in_freq_1 = np.sum(cond == 0.0)
    print(f"  Zero absolute increments when obs_freq == 1: {zeros_in_freq_1}")

def main():
    out_dir = os.environ.get("QC_OUT_DIR", f"reports/qc/daily_absolute_increment")
    os.makedirs(out_dir, exist_ok=True)
    
    ds_abs_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_absolute_increment", "daily_absolute_increment")
    ds_abs_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_absolute_increment", "daily_absolute_increment")
    
    ds_signed_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_signed_increment", "daily_signed_increment")
    ds_signed_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_signed_increment", "daily_signed_increment")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_abs_cdf, ds_signed_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_abs_nocdf, ds_signed_nocdf, ds_freq_nocdf)
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_abs_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_abs_cdf['daily_absolute_increment'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage valid non-zero count: {np.sum(valid_cdf != 0)}")
    
    nocdf_outage_vals = ds_abs_nocdf['daily_absolute_increment'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage valid non-zero count: {np.sum(valid_nocdf != 0)}")

    # ================ PLOTTING ================
    times_arr = ds_abs_cdf.time.values
    extent = [ds_abs_cdf.lon.values.min(), ds_abs_cdf.lon.values.max(), ds_abs_cdf.lat.values.min(), ds_abs_cdf.lat.values.max()]
    
    # A. UPDATED-PIXEL DISTRIBUTION
    cond_vals_cdf = ds_abs_cdf['daily_absolute_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    cond_vals_nocdf = ds_abs_nocdf['daily_absolute_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    
    plt.figure(figsize=(10, 6))
    bins = np.linspace(0, max(np.max(cond_vals_cdf), np.max(cond_vals_nocdf)), 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.title('Distribution of Absolute Increments Conditional on Assimilation')
    plt.xlabel('Absolute Increment (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'updated_pixel_distribution.png'))
    plt.close()
    
    # B. DAILY MEAN TIME SERIES
    def get_means(ds_abs, ds_freq):
        vals = ds_abs['daily_absolute_increment'].values
        freq = ds_freq['observation_frequency'].values
        uncond_mean = np.nanmean(vals, axis=(1, 2))
        cond_mean = np.zeros(len(vals))
        tot_abs = np.zeros(len(vals))
        n_upd = np.zeros(len(vals))
        for i in range(len(vals)):
            mask = freq[i] == 1
            n_upd[i] = np.sum(mask)
            if np.any(mask):
                cond_mean[i] = np.nanmean(vals[i][mask])
                tot_abs[i] = np.nansum(vals[i][mask])
            else:
                cond_mean[i] = np.nan
                tot_abs[i] = 0.0
        return uncond_mean, cond_mean, tot_abs, n_upd

    u_cdf, c_cdf, tot_cdf, n_cdf = get_means(ds_abs_cdf, ds_freq_cdf)
    u_nocdf, c_nocdf, tot_nocdf, n_nocdf = get_means(ds_abs_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    axes[0].plot(times_arr, u_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, u_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Unconditional Mean Absolute Increment (All Valid Land)')
    axes[0].legend()
    
    axes[1].plot(times_arr, c_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, c_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Conditional Mean Absolute Increment (Updated Pixels Only)')
    axes[1].legend()
    
    axes[2].plot(times_arr, tot_cdf, label='DA-CDF', alpha=0.7)
    axes[2].plot(times_arr, tot_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[2].set_title('Total Absolute Increment (Diagnostic Sum, Not Water Volume)')
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_mean_timeseries.png'))
    plt.close()
    
    # C. UNCONDITIONAL TEMPORAL MEAN MAP
    mean_cdf = np.nanmean(ds_abs_cdf['daily_absolute_increment'].values, axis=0)
    mean_nocdf = np.nanmean(ds_abs_nocdf['daily_absolute_increment'].values, axis=0)
    vmax_u = max(np.nanmax(mean_cdf), np.nanmax(mean_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(mean_cdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_u)
    axes[0].set_title('DA-CDF Temporal Mean (Unconditional)')
    im2 = axes[1].imshow(mean_nocdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_u)
    axes[1].set_title('DA-NoCDF Temporal Mean (Unconditional)')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Mean Absolute Increment')
    plt.savefig(os.path.join(out_dir, 'unconditional_temporal_mean.png'))
    plt.close()
    
    # D. CONDITIONAL MEAN MAP
    def get_cond_mean(ds_abs, ds_freq):
        vals = ds_abs['daily_absolute_increment'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    c_mean_cdf = get_cond_mean(ds_abs_cdf, ds_freq_cdf)
    c_mean_nocdf = get_cond_mean(ds_abs_nocdf, ds_freq_nocdf)
    vmax_c = max(np.nanmax(c_mean_cdf), np.nanmax(c_mean_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(c_mean_cdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_c)
    axes[0].set_title('DA-CDF Conditional Mean (Assimilated Only)')
    im2 = axes[1].imshow(c_mean_nocdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_c)
    axes[1].set_title('DA-NoCDF Conditional Mean (Assimilated Only)')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Mean Absolute Increment')
    plt.savefig(os.path.join(out_dir, 'conditional_mean_map.png'))
    plt.close()
    
    # F. MAGNITUDE-VS-FREQUENCY DIAGNOSTIC
    freq_mean_cdf = np.nanmean(ds_freq_cdf['observation_frequency'].values, axis=0)
    freq_mean_nocdf = np.nanmean(ds_freq_nocdf['observation_frequency'].values, axis=0)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    # DA-CDF
    axes[0,0].imshow(freq_mean_cdf, origin='lower', extent=extent, cmap='plasma')
    axes[0,0].set_title('DA-CDF Mean Obs Frequency')
    axes[0,1].imshow(c_mean_cdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_c)
    axes[0,1].set_title('DA-CDF Conditional Mean Absolute Increment')
    # DA-NoCDF
    axes[1,0].imshow(freq_mean_nocdf, origin='lower', extent=extent, cmap='plasma')
    axes[1,0].set_title('DA-NoCDF Mean Obs Frequency')
    im = axes[1,1].imshow(c_mean_nocdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_c)
    axes[1,1].set_title('DA-NoCDF Conditional Mean Absolute Increment')
    
    fig.colorbar(im, ax=axes.ravel().tolist(), label='Absolute Increment')
    plt.savefig(os.path.join(out_dir, 'magnitude_vs_frequency.png'))
    plt.close()

    # E. REPRESENTATIVE DAILY MAPS
    def plot_rep_maps(ds_abs, ds_freq, exp):
        freq = ds_freq['observation_frequency'].values
        vals_abs = ds_abs['daily_absolute_increment'].values
        daily_support = np.sum(freq == 1, axis=(1,2))
        top_days_idx = np.argsort(daily_support)[-2:]
        times = ds_abs.time.values
        
        for idx in top_days_idx:
            dt = pd.to_datetime(times[idx]).strftime('%Y-%m-%d')
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(vals_abs[idx], origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=0.1)
            ax.set_title(f'{exp} Daily Absolute Increment: {dt}')
            fig.colorbar(im, ax=ax, label='Absolute Increment (m3 m-3)')
            plt.savefig(os.path.join(out_dir, f'rep_map_{exp.lower()}_{dt}.png'))
            plt.close()
            
    plot_rep_maps(ds_abs_cdf, ds_freq_cdf, 'DA-CDF')
    plot_rep_maps(ds_abs_nocdf, ds_freq_nocdf, 'DA-NoCDF')

if __name__ == "__main__":
    main()
