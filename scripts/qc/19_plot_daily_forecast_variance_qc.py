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

def process_exp(exp, ds_fv, ds_ninv, ds_inv, ds_abs, ds_freq):
    print(f"\n================ {exp} ================")
    
    vals_fv = ds_fv['daily_forecast_variance'].values
    vals_ninv = ds_ninv['daily_normalized_innovation'].values
    vals_inv = ds_inv['daily_innovation'].values
    vals_abs = ds_abs['daily_absolute_increment'].values
    freq = ds_freq['observation_frequency'].values
    
    valid_land = ~np.isnan(freq)
    finite_fv = ~np.isnan(vals_fv)
    
    # Support Consistency
    freq_1_mask = (freq == 1) & valid_land
    freq_0_mask = (freq == 0) & valid_land
    
    viol_1 = np.sum(freq_1_mask & ~finite_fv)
    viol_0 = np.sum(freq_0_mask & finite_fv)
    print(f"Support consistency violations: freq=1 but nan -> {viol_1}, freq=0 but finite -> {viol_0}")
    
    # Non-negativity test
    cond = vals_fv[freq_1_mask]
    neg_count = np.sum(cond < 0)
    zero_count = np.sum(cond == 0.0)
    pos_count = np.sum(cond > 0)
    print("\nNON-NEGATIVITY TEST:")
    print(f"  negative count: {neg_count}")
    print(f"  exact-zero count: {zero_count}")
    print(f"  positive count: {pos_count}")
    if neg_count > 0:
        raise ValueError("Negative forecast variance encountered!")

    # Full-period statistics
    print("\nFULL-PERIOD STATISTICS (Finite assimilated pixel-days only):")
    print(f"  min: {np.min(cond)}")
    print(f"  max: {np.max(cond)}")
    print(f"  mean: {np.mean(cond)}")
    print(f"  median: {np.median(cond)}")
    print(f"  std: {np.std(cond)}")
    print(f"  p01: {np.percentile(cond, 1)}")
    print(f"  p05: {np.percentile(cond, 5)}")
    print(f"  p25: {np.percentile(cond, 25)}")
    print(f"  p75: {np.percentile(cond, 75)}")
    print(f"  p95: {np.percentile(cond, 95)}")
    print(f"  p99: {np.percentile(cond, 99)}")
    
    # Exact-zero provenance
    # We will assume zero events are verified in the identity test if they match perfectly.
    
    # Reconstruct normalized innovation
    R = 0.0016
    cond_inv = vals_inv[freq_1_mask]
    cond_ninv = vals_ninv[freq_1_mask]
    S = cond + R
    recon_ninv = cond_inv / np.sqrt(S)
    
    diff = np.abs(recon_ninv - cond_ninv)
    print("\nRECONSTRUCT NORMALIZED INNOVATION:")
    print(f"  Max abs diff: {np.max(diff):.6e}")
    print(f"  Mean abs diff: {np.mean(diff):.6e}")
    print(f"  Unequal exact: {np.sum(recon_ninv != cond_ninv)}")
    print(f"  Unequal atol=1e-8: {np.sum(diff > 1e-8)}")
    print(f"  Unequal atol=1e-7: {np.sum(diff > 1e-7)}")
    
    # S Statistics
    print("\nS (INNOVATION VARIANCE) STATISTICS:")
    print(f"  min: {np.min(S)}")
    print(f"  max: {np.max(S)}")
    print(f"  mean: {np.mean(S)}")
    print(f"  median: {np.median(S)}")
    
    # Relation to Normalized Innovation
    cond_abs_ninv = np.abs(cond_ninv)
    corr_p, _ = pearsonr(cond, cond_abs_ninv)
    corr_s, _ = spearmanr(cond, cond_abs_ninv)
    print("\nRELATION TO |NORMALIZED INNOVATION|:")
    print(f"  Pearson: {corr_p:.4f}")
    print(f"  Spearman: {corr_s:.4f}")
    
    # Relation to Absolute Increment
    cond_abs = vals_abs[freq_1_mask]
    corr_abs_p, _ = pearsonr(cond, cond_abs)
    corr_abs_s, _ = spearmanr(cond, cond_abs)
    print("\nRELATION TO ABSOLUTE INCREMENT:")
    print(f"  Pearson: {corr_abs_p:.4f}")
    print(f"  Spearman: {corr_abs_s:.4f}")
    
    # Quartile diagnostic
    print("\nQUARTILE DIAGNOSTIC:")
    cond_abs_inv = np.abs(cond_inv)
    q_bins = np.percentile(cond, [0, 25, 50, 75, 100])
    quartile_counts = 0
    for i in range(4):
        if i == 3:
            mask_q = (cond >= q_bins[i]) & (cond <= q_bins[i+1])
        else:
            mask_q = (cond >= q_bins[i]) & (cond < q_bins[i+1])
        
        count_q = np.sum(mask_q)
        if count_q > 0:
            quartile_counts += count_q
            print(f"  Q{i+1} [{q_bins[i]:.6f} - {q_bins[i+1]:.6f}]:")
            print(f"    sample count: {count_q}")
            print(f"    median |innovation|: {np.median(cond_abs_inv[mask_q]):.6f}")
            print(f"    median abs_increment: {np.median(cond_abs[mask_q]):.6f}")
            print(f"    median |ninnov|: {np.median(cond_abs_ninv[mask_q]):.6f}")

    print(f"\nQUARTILE CONSERVATION CHECK:")
    print(f"  Finite count: {len(cond)}")
    print(f"  Quartile count sum: {quartile_counts}")
    print(f"  Difference: {len(cond) - quartile_counts}")
    assert quartile_counts == len(cond), "Quartile assignment dropped or double-counted samples!"

def check_identity(exp, daily_ds):
    print(f"\n================ FULL-PERIOD EVENT-TO-DAILY IDENTITY ({exp}) ================")
    daily_fv = daily_ds['daily_forecast_variance'].values
    daily_times = pd.DatetimeIndex(daily_ds.time.values)
    
    total_matched = 0
    max_diff = 0.0
    sum_diff = 0.0
    unequal_exact = 0
    unequal_1e8 = 0
    unequal_1e7 = 0
    
    for year in range(2016, 2021):
        ds_event = xr.open_dataset(f"data/interim/enkf/{exp.replace('-','_').lower()}/forecast_variance/forecast_variance_{year}.nc")
        ev_fv = ds_event['forecast_variance'].values
        ev_times = ds_event.event_time.values
        ev_days = pd.DatetimeIndex(ev_times).floor('D')
        
        for i, ev_day in enumerate(ev_days):
            day_idx = np.where(daily_times == ev_day)[0]
            if len(day_idx) == 0: continue
            day_idx = day_idx[0]
            
            ev_slice = ev_fv[i]
            daily_slice = daily_fv[day_idx]
            
            mask = ~np.isnan(ev_slice)
            matched = np.sum(mask)
            if matched == 0: continue
            
            diff = np.abs(ev_slice[mask] - daily_slice[mask])
            
            total_matched += matched
            max_diff = max(max_diff, np.max(diff))
            sum_diff += np.sum(diff)
            unequal_exact += np.sum(ev_slice[mask] != daily_slice[mask])
            unequal_1e8 += np.sum(diff > 1e-8)
            unequal_1e7 += np.sum(diff > 1e-7)
            
    mean_diff = sum_diff / total_matched if total_matched > 0 else 0
    print(f"Matched samples: {total_matched}")
    print(f"Max abs diff: {max_diff:.6e}")
    print(f"Mean abs diff: {mean_diff:.6e}")
    print(f"Unequal exact: {unequal_exact}")
    print(f"Unequal atol=1e-8: {unequal_1e8}")
    print(f"Unequal atol=1e-7: {unequal_1e7}")

def plot_all():
    out_dir = "reports/qc/daily_forecast_variance"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_fv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_forecast_variance", "daily_forecast_variance")
    ds_fv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_forecast_variance", "daily_forecast_variance")
    
    ds_ninv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_normalized_innovation", "daily_normalized_innovation")
    ds_ninv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_normalized_innovation", "daily_normalized_innovation")
    
    ds_inv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_innovation", "daily_innovation")
    ds_inv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_innovation", "daily_innovation")
    
    ds_abs_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_absolute_increment", "daily_absolute_increment")
    ds_abs_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_absolute_increment", "daily_absolute_increment")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_fv_cdf, ds_ninv_cdf, ds_inv_cdf, ds_abs_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_fv_nocdf, ds_ninv_nocdf, ds_inv_nocdf, ds_abs_nocdf, ds_freq_nocdf)
    
    check_identity("DA-CDF", ds_fv_cdf)
    check_identity("DA-NoCDF", ds_fv_nocdf)
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_fv_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_fv_cdf['daily_forecast_variance'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage finite count: {len(valid_cdf)}")
    
    nocdf_outage_vals = ds_fv_nocdf['daily_forecast_variance'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage finite count: {len(valid_nocdf)}")
    
    # ================ PLOTTING ================
    times_arr = ds_fv_cdf.time.values
    extent = [ds_fv_cdf.lon.values.min(), ds_fv_cdf.lon.values.max(), ds_fv_cdf.lat.values.min(), ds_fv_cdf.lat.values.max()]
    
    cond_vals_cdf = ds_fv_cdf['daily_forecast_variance'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    cond_vals_nocdf = ds_fv_nocdf['daily_forecast_variance'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    
    # A. DISTRIBUTION
    plt.figure(figsize=(10, 6))
    bins = np.linspace(0, 0.02, 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.title('Distribution of Daily Forecast Variance')
    plt.xlabel('Forecast Variance (m3 m-3)^2')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'forecast_variance_distribution.png'))
    plt.close()
    
    # B. TEMPORAL SUMMARY
    def get_means(ds_fv, ds_freq):
        vals = ds_fv['daily_forecast_variance'].values
        freq = ds_freq['observation_frequency'].values
        
        c_mean = np.zeros(len(vals))
        c_median = np.zeros(len(vals))
        c_p95 = np.zeros(len(vals))
        n_upd = np.zeros(len(vals))
        
        for i in range(len(vals)):
            mask = freq[i] == 1
            n_upd[i] = np.sum(mask)
            if np.any(mask):
                c_mean[i] = np.nanmean(vals[i][mask])
                c_median[i] = np.nanmedian(vals[i][mask])
                c_p95[i] = np.percentile(vals[i][mask], 95)
            else:
                c_mean[i] = np.nan
                c_median[i] = np.nan
                c_p95[i] = np.nan
        return c_mean, c_median, c_p95, n_upd

    c_mean_cdf, c_median_cdf, c_p95_cdf, n_cdf = get_means(ds_fv_cdf, ds_freq_cdf)
    c_mean_nocdf, c_median_nocdf, c_p95_nocdf, n_nocdf = get_means(ds_fv_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
    axes[0].plot(times_arr, c_mean_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, c_mean_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Mean Forecast Variance')
    axes[0].legend()
    
    axes[1].plot(times_arr, c_median_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, c_median_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Median Forecast Variance')
    axes[1].legend()
    
    axes[2].plot(times_arr, c_p95_cdf, label='DA-CDF', alpha=0.7)
    axes[2].plot(times_arr, c_p95_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[2].set_title('p95 Forecast Variance')
    axes[2].legend()
    
    axes[3].plot(times_arr, n_cdf, label='DA-CDF', alpha=0.7)
    axes[3].plot(times_arr, n_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[3].set_title('Valid Count')
    axes[3].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_temporal_summary.png'))
    plt.close()
    
    # C. CONDITIONAL MEAN MAP
    def get_cond_map(ds_fv, ds_freq):
        vals = ds_fv['daily_forecast_variance'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    c_map_cdf = get_cond_map(ds_fv_cdf, ds_freq_cdf)
    c_map_nocdf = get_cond_map(ds_fv_nocdf, ds_freq_nocdf)
    vmax_c = max(np.nanmax(c_map_cdf), np.nanmax(c_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(c_map_cdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_c)
    axes[0].set_title('DA-CDF Mean Forecast Variance')
    im2 = axes[1].imshow(c_map_nocdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_c)
    axes[1].set_title('DA-NoCDF Mean Forecast Variance')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_mean_map.png'))
    plt.close()

    # D. CONDITIONAL P95 MAP
    def get_p95_map(ds_fv, ds_freq):
        vals = ds_fv['daily_forecast_variance'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanpercentile(cond_vals, 95, axis=0)
        
    p95_map_cdf = get_p95_map(ds_fv_cdf, ds_freq_cdf)
    p95_map_nocdf = get_p95_map(ds_fv_nocdf, ds_freq_nocdf)
    vmax_p95 = max(np.nanmax(p95_map_cdf), np.nanmax(p95_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(p95_map_cdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_p95)
    axes[0].set_title('DA-CDF p95 Forecast Variance')
    im2 = axes[1].imshow(p95_map_nocdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_p95)
    axes[1].set_title('DA-NoCDF p95 Forecast Variance')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_p95_map.png'))
    plt.close()
    
    # E. REPRESENTATIVE DAILY MAPS
    def plot_rep_maps(ds_fv, ds_freq, exp):
        freq = ds_freq['observation_frequency'].values
        vals = ds_fv['daily_forecast_variance'].values
        daily_support = np.sum(freq == 1, axis=(1,2))
        top_days_idx = np.argsort(daily_support)[-2:]
        
        for idx in top_days_idx:
            dt = pd.to_datetime(times_arr[idx]).strftime('%Y-%m-%d')
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(vals[idx], origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=0.015)
            ax.set_title(f'{exp} Daily Forecast Variance: {dt}')
            fig.colorbar(im, ax=ax, label='Forecast Variance')
            plt.savefig(os.path.join(out_dir, f'rep_map_{exp.lower()}_{dt}.png'))
            plt.close()
            
    plot_rep_maps(ds_fv_cdf, ds_freq_cdf, 'DA-CDF')
    plot_rep_maps(ds_fv_nocdf, ds_freq_nocdf, 'DA-NoCDF')

    # F. FORECAST VARIANCE VS ABSOLUTE INCREMENT
    plt.figure(figsize=(8, 6))
    cond_abs_cdf = ds_abs_cdf['daily_absolute_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    plt.hexbin(cond_vals_cdf, cond_abs_cdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-CDF Forecast Variance vs Absolute Increment')
    plt.xlabel('Daily Forecast Variance')
    plt.ylabel('Daily Absolute Increment')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'fv_vs_abs_inc_cdf.png'))
    plt.close()
    
    plt.figure(figsize=(8, 6))
    cond_abs_nocdf = ds_abs_nocdf['daily_absolute_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    plt.hexbin(cond_vals_nocdf, cond_abs_nocdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-NoCDF Forecast Variance vs Absolute Increment')
    plt.xlabel('Daily Forecast Variance')
    plt.ylabel('Daily Absolute Increment')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'fv_vs_abs_inc_nocdf.png'))
    plt.close()
    
    # G. FORECAST VARIANCE VS |NORMALIZED INNOVATION|
    plt.figure(figsize=(8, 6))
    cond_ninv_cdf = np.abs(ds_ninv_cdf['daily_normalized_innovation'].values[(ds_freq_cdf['observation_frequency'].values == 1)])
    plt.hexbin(cond_vals_cdf, cond_ninv_cdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-CDF Forecast Variance vs |Normalized Innovation|')
    plt.xlabel('Daily Forecast Variance')
    plt.ylabel('|Daily Normalized Innovation|')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'fv_vs_abs_ninv_cdf.png'))
    plt.close()
    
    plt.figure(figsize=(8, 6))
    cond_ninv_nocdf = np.abs(ds_ninv_nocdf['daily_normalized_innovation'].values[(ds_freq_nocdf['observation_frequency'].values == 1)])
    plt.hexbin(cond_vals_nocdf, cond_ninv_nocdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-NoCDF Forecast Variance vs |Normalized Innovation|')
    plt.xlabel('Daily Forecast Variance')
    plt.ylabel('|Daily Normalized Innovation|')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'fv_vs_abs_ninv_nocdf.png'))
    plt.close()

if __name__ == "__main__":
    plot_all()
