#!/usr/bin/env python3
"""
EnKF Daily Analysis Residual QC

Author
------
M. El Aabaribaoune (@um6p)
"""
__author__ = "M. El Aabaribaoune (@um6p)"

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

def process_exp(exp, ds_res, ds_inv, ds_inc, ds_ninv, ds_fv, ds_freq):
    print(f"\n================ {exp} ================")
    
    res = ds_res['daily_analysis_residual'].values
    inv = ds_inv['daily_innovation'].values
    inc = ds_inc['daily_signed_increment'].values
    ninv = ds_ninv['daily_normalized_innovation'].values
    fv = ds_fv['daily_forecast_variance'].values
    freq = ds_freq['observation_frequency'].values
    
    # Validation 1: Support consistency
    valid_land = ~np.isnan(freq)
    freq_1_mask = (freq == 1) & valid_land
    finite_res = ~np.isnan(res)
    
    print("SUPPORT CONSISTENCY:")
    print(f"  freq=1 but res nan: {np.sum(freq_1_mask & ~finite_res)}")
    print(f"  freq=0 but res finite: {np.sum((freq == 0) & finite_res)}")
    print(f"  inv mismatch: {np.sum(~np.isnan(inv) != finite_res)}")
    print(f"  ninv mismatch: {np.sum(~np.isnan(ninv) != finite_res)}")
    print(f"  fv mismatch: {np.sum(~np.isnan(fv) != finite_res)}")
    
    cond_res = res[freq_1_mask]
    cond_inv = inv[freq_1_mask]
    cond_inc = inc[freq_1_mask]
    cond_ninv = ninv[freq_1_mask]
    
    # 2. Count Conservation
    print("\nCOUNT CONSERVATION:")
    print(f"  finite count: {len(cond_res)}")
    
    # 3. Exact Zero Semantics
    neg = np.sum(cond_res < 0)
    zer = np.sum(cond_res == 0.0)
    pos = np.sum(cond_res > 0)
    print("\nEXACT ZERO SEMANTICS:")
    print(f"  negative: {neg}")
    print(f"  exact zero: {zer}")
    print(f"  positive: {pos}")
    print(f"  sum: {neg + zer + pos} == {len(cond_res)}")
    
    # 4. Distribution Identity
    print("\nDISTRIBUTION IDENTITY (assimilated pixel-days):")
    print(f"  min: {np.min(cond_res)}")
    print(f"  max: {np.max(cond_res)}")
    print(f"  mean: {np.mean(cond_res)}")
    print(f"  median: {np.median(cond_res)}")
    print(f"  std: {np.std(cond_res)}")
    print(f"  p01: {np.percentile(cond_res, 1)}")
    print(f"  p05: {np.percentile(cond_res, 5)}")
    print(f"  p25: {np.percentile(cond_res, 25)}")
    print(f"  p75: {np.percentile(cond_res, 75)}")
    print(f"  p95: {np.percentile(cond_res, 95)}")
    print(f"  p99: {np.percentile(cond_res, 99)}")
    
    print("\nFRACTIONS:")
    print(f"  residual < 0: {neg / len(cond_res):.6%}")
    print(f"  residual == 0: {zer / len(cond_res):.6%}")
    print(f"  residual > 0: {pos / len(cond_res):.6%}")

    # 5. Before vs After Mismatch
    abs_before = np.abs(cond_inv)
    abs_after = np.abs(cond_res)
    
    print("\nBEFORE VS AFTER MISMATCH:")
    print(f"  mean abs_before: {np.mean(abs_before)}")
    print(f"  median abs_before: {np.median(abs_before)}")
    print(f"  mean abs_after: {np.mean(abs_after)}")
    print(f"  median abs_after: {np.median(abs_after)}")
    
    red = abs_after < (abs_before - 1e-7)
    equ = np.abs(abs_after - abs_before) <= 1e-7
    inc_m = abs_after > (abs_before + 1e-7)
    print(f"  abs_after < abs_before: {np.sum(red) / len(cond_res):.6%}")
    print(f"  abs_after == abs_before: {np.sum(equ) / len(cond_res):.6%}")
    print(f"  abs_after > abs_before: {np.sum(inc_m) / len(cond_res):.6%}")
    
    # 6. Mismatch Reduction
    mismatch_red = abs_before - abs_after
    print("\nMISMATCH REDUCTION:")
    print(f"  mean: {np.mean(mismatch_red)}")
    print(f"  median: {np.median(mismatch_red)}")
    print(f"  p05: {np.percentile(mismatch_red, 5)}")
    print(f"  p25: {np.percentile(mismatch_red, 25)}")
    print(f"  p75: {np.percentile(mismatch_red, 75)}")
    print(f"  p95: {np.percentile(mismatch_red, 95)}")
    print(f"  > 0 fraction: {np.sum(mismatch_red > 1e-7) / len(cond_res):.6%}")
    print(f"  == 0 fraction: {np.sum(np.abs(mismatch_red) <= 1e-7) / len(cond_res):.6%}")
    print(f"  < 0 fraction: {np.sum(mismatch_red < -1e-7) / len(cond_res):.6%}")

    # 7. Observation-Space Update
    obs_update = cond_inv - cond_res
    print("\nOBSERVATION-SPACE UPDATE:")
    print(f"  min: {np.min(obs_update)}")
    print(f"  max: {np.max(obs_update)}")
    print(f"  mean: {np.mean(obs_update)}")
    print(f"  median: {np.median(obs_update)}")
    print(f"  std: {np.std(obs_update)}")
    
    # 8. Relation to Daily Signed Increment
    diff = np.abs(obs_update - cond_inc)
    p_up, _ = pearsonr(obs_update, cond_inc)
    s_up, _ = spearmanr(obs_update, cond_inc)
    print("\nRELATION TO DAILY SIGNED INCREMENT:")
    print(f"  Pearson: {p_up:.4f}")
    print(f"  Spearman: {s_up:.4f}")
    print(f"  mean abs diff: {np.mean(diff)}")
    print(f"  median abs diff: {np.median(diff)}")
    print(f"  max abs diff: {np.max(diff)}")
    print(f"  RMSE: {np.sqrt(np.mean(diff**2))}")
    
    # 9. Innovation vs Residual
    p_inv, _ = pearsonr(cond_inv, cond_res)
    s_inv, _ = spearmanr(cond_inv, cond_res)
    print("\nINNOVATION VS RESIDUAL:")
    print(f"  Pearson: {p_inv:.4f}")
    print(f"  Spearman: {s_inv:.4f}")
    
    p_abs_inv, _ = pearsonr(abs_before, abs_after)
    s_abs_inv, _ = spearmanr(abs_before, abs_after)
    print("  |Pearson|: ", p_abs_inv)
    print("  |Spearman|: ", s_abs_inv)
    
    # 10. Relation to Normalized Innovation
    print("\nRELATION TO NORMALIZED INNOVATION:")
    abs_ninv = np.abs(cond_ninv)
    classes = [
        ("|NI| < 1", abs_ninv < 1),
        ("1 <= |NI| < 2", (abs_ninv >= 1) & (abs_ninv < 2)),
        ("|NI| >= 2", abs_ninv >= 2)
    ]
    for label, mask in classes:
        print(f"  {label}:")
        if np.sum(mask) > 0:
            print(f"    sample count: {np.sum(mask)}")
            print(f"    mean |innovation|: {np.mean(abs_before[mask])}")
            print(f"    median |innovation|: {np.median(abs_before[mask])}")
            print(f"    mean |analysis_residual|: {np.mean(abs_after[mask])}")
            print(f"    median |analysis_residual|: {np.median(abs_after[mask])}")
            print(f"    median mismatch_reduction: {np.median(mismatch_red[mask])}")
    
    # 11. Residual-to-Innovation Ratio
    print("\nRESIDUAL-TO-INNOVATION RATIO (abs(innovation) >= 1e-4):")
    valid_ratio = abs_before >= 1e-4
    ratio = abs_after[valid_ratio] / abs_before[valid_ratio]
    if len(ratio) > 0:
        print(f"  median: {np.median(ratio)}")
        print(f"  p25: {np.percentile(ratio, 25)}")
        print(f"  p75: {np.percentile(ratio, 75)}")

def check_identity(exp, daily_ds):
    print(f"\n================ FULL-PERIOD EVENT-TO-DAILY IDENTITY ({exp}) ================")
    daily_res = daily_ds['daily_analysis_residual'].values
    daily_times = pd.DatetimeIndex(daily_ds.time.values)
    
    total_matched = 0
    max_diff = 0.0
    sum_diff = 0.0
    unequal_exact = 0
    unequal_1e8 = 0
    unequal_1e7 = 0
    sign_mismatch = 0
    
    for year in range(2016, 2021):
        ds_event = xr.open_dataset(f"data/interim/enkf/{exp.replace('-','_').lower()}/analysis_residual/analysis_residual_{year}.nc")
        ev_res = ds_event['analysis_residual'].values
        ev_times = ds_event.event_time.values
        ev_days = pd.DatetimeIndex(ev_times).floor('D')
        
        for i, ev_day in enumerate(ev_days):
            day_idx = np.where(daily_times == ev_day)[0]
            if len(day_idx) == 0: continue
            day_idx = day_idx[0]
            
            ev_slice = ev_res[i]
            daily_slice = daily_res[day_idx]
            
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
            sign_mismatch += np.sum(np.sign(ev_slice[mask]) != np.sign(daily_slice[mask]))
            
    mean_diff = sum_diff / total_matched if total_matched > 0 else 0
    print(f"Matched samples: {total_matched}")
    print(f"Max abs diff: {max_diff:.6e}")
    print(f"Mean abs diff: {mean_diff:.6e}")
    print(f"Unequal exact: {unequal_exact}")
    print(f"Unequal atol=1e-8: {unequal_1e8}")
    print(f"Unequal atol=1e-7: {unequal_1e7}")
    print(f"Sign mismatch: {sign_mismatch}")

def plot_all():
    out_dir = "reports/qc/daily_analysis_residual"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_res_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_analysis_residual", "daily_analysis_residual")
    ds_res_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_analysis_residual", "daily_analysis_residual")
    
    ds_inv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_innovation", "daily_innovation")
    ds_inv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_innovation", "daily_innovation")
    
    ds_inc_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_signed_increment", "daily_signed_increment")
    ds_inc_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_signed_increment", "daily_signed_increment")
    
    ds_ninv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_normalized_innovation", "daily_normalized_innovation")
    ds_ninv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_normalized_innovation", "daily_normalized_innovation")
    
    ds_fv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_forecast_variance", "daily_forecast_variance")
    ds_fv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_forecast_variance", "daily_forecast_variance")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_res_cdf, ds_inv_cdf, ds_inc_cdf, ds_ninv_cdf, ds_fv_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_res_nocdf, ds_inv_nocdf, ds_inc_nocdf, ds_ninv_nocdf, ds_fv_nocdf, ds_freq_nocdf)
    
    check_identity("DA-CDF", ds_res_cdf)
    check_identity("DA-NoCDF", ds_res_nocdf)
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_res_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_res_cdf['daily_analysis_residual'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage finite count: {len(valid_cdf)}")
    
    nocdf_outage_vals = ds_res_nocdf['daily_analysis_residual'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage finite count: {len(valid_nocdf)}")
    
    # ================ PLOTTING ================
    times_arr = ds_res_cdf.time.values
    extent = [ds_res_cdf.lon.values.min(), ds_res_cdf.lon.values.max(), ds_res_cdf.lat.values.min(), ds_res_cdf.lat.values.max()]
    
    cond_vals_cdf = ds_res_cdf['daily_analysis_residual'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    cond_vals_nocdf = ds_res_nocdf['daily_analysis_residual'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    
    # A. DISTRIBUTION
    plt.figure(figsize=(10, 6))
    bins = np.linspace(-0.25, 0.25, 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.title('Distribution of Daily Analysis Residual')
    plt.xlabel('Analysis Residual (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'residual_distribution.png'))
    plt.close()
    
    # B. DAILY TEMPORAL SUMMARY
    def get_means(ds_res, ds_inv, ds_freq):
        res = ds_res['daily_analysis_residual'].values
        inv = ds_inv['daily_innovation'].values
        freq = ds_freq['observation_frequency'].values
        
        c_mean = np.zeros(len(res))
        c_median = np.zeros(len(res))
        c_mean_abs = np.zeros(len(res))
        c_mean_red = np.zeros(len(res))
        n_upd = np.zeros(len(res))
        
        for i in range(len(res)):
            mask = freq[i] == 1
            n_upd[i] = np.sum(mask)
            if np.any(mask):
                c_mean[i] = np.nanmean(res[i][mask])
                c_median[i] = np.nanmedian(res[i][mask])
                c_mean_abs[i] = np.nanmean(np.abs(res[i][mask]))
                c_mean_red[i] = np.nanmean(np.abs(inv[i][mask]) - np.abs(res[i][mask]))
            else:
                c_mean[i] = np.nan
                c_median[i] = np.nan
                c_mean_abs[i] = np.nan
                c_mean_red[i] = np.nan
        return c_mean, c_median, c_mean_abs, c_mean_red, n_upd

    c_mean_cdf, c_median_cdf, c_mean_abs_cdf, c_mean_red_cdf, n_cdf = get_means(ds_res_cdf, ds_inv_cdf, ds_freq_cdf)
    c_mean_nocdf, c_median_nocdf, c_mean_abs_nocdf, c_mean_red_nocdf, n_nocdf = get_means(ds_res_nocdf, ds_inv_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(5, 1, figsize=(12, 20), sharex=True)
    
    axes[0].plot(times_arr, c_mean_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, c_mean_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Mean Residual')
    axes[0].legend()
    
    axes[1].plot(times_arr, c_median_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, c_median_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Median Residual')
    axes[1].legend()
    
    axes[2].plot(times_arr, c_mean_abs_cdf, label='DA-CDF', alpha=0.7)
    axes[2].plot(times_arr, c_mean_abs_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[2].set_title('Mean Absolute Residual')
    axes[2].legend()

    axes[3].plot(times_arr, c_mean_red_cdf, label='DA-CDF', alpha=0.7)
    axes[3].plot(times_arr, c_mean_red_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[3].set_title('Mean Mismatch Reduction')
    axes[3].legend()
    
    axes[4].plot(times_arr, n_cdf, label='DA-CDF', alpha=0.7)
    axes[4].plot(times_arr, n_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[4].set_title('Valid Count')
    axes[4].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_temporal_summary.png'))
    plt.close()
    
    # C. CONDITIONAL MEAN SIGNED MAP
    def get_cond_map(ds_res, ds_freq):
        vals = ds_res['daily_analysis_residual'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    c_map_cdf = get_cond_map(ds_res_cdf, ds_freq_cdf)
    c_map_nocdf = get_cond_map(ds_res_nocdf, ds_freq_nocdf)
    vmax_c = max(np.nanmax(np.abs(c_map_cdf)), np.nanmax(np.abs(c_map_nocdf)))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(c_map_cdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[0].set_title('DA-CDF Mean Signed Residual')
    im2 = axes[1].imshow(c_map_nocdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[1].set_title('DA-NoCDF Mean Signed Residual')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_mean_signed_map.png'))
    plt.close()

    # D. CONDITIONAL MEAN ABSOLUTE MAP
    def get_abs_map(ds_res, ds_freq):
        vals = np.abs(ds_res['daily_analysis_residual'].values)
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    a_map_cdf = get_abs_map(ds_res_cdf, ds_freq_cdf)
    a_map_nocdf = get_abs_map(ds_res_nocdf, ds_freq_nocdf)
    vmax_a = max(np.nanmax(a_map_cdf), np.nanmax(a_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(a_map_cdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_a)
    axes[0].set_title('DA-CDF Mean Absolute Residual')
    im2 = axes[1].imshow(a_map_nocdf, origin='lower', extent=extent, cmap='YlOrRd', vmin=0, vmax=vmax_a)
    axes[1].set_title('DA-NoCDF Mean Absolute Residual')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_mean_absolute_map.png'))
    plt.close()

    # E. MISMATCH-REDUCTION FRACTION MAP
    def get_red_frac_map(ds_res, ds_inv, ds_freq):
        res = np.abs(ds_res['daily_analysis_residual'].values)
        inv = np.abs(ds_inv['daily_innovation'].values)
        freq = ds_freq['observation_frequency'].values
        
        is_valid = freq == 1
        is_red = is_valid & (res < inv - 1e-7)
        
        valid_counts = np.sum(is_valid, axis=0)
        red_counts = np.sum(is_red, axis=0)
        
        frac = np.where(valid_counts > 0, red_counts / valid_counts, np.nan)
        return frac

    red_map_cdf = get_red_frac_map(ds_res_cdf, ds_inv_cdf, ds_freq_cdf)
    red_map_nocdf = get_red_frac_map(ds_res_nocdf, ds_inv_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(red_map_cdf, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1)
    axes[0].set_title('DA-CDF Fraction with Reduced Mismatch')
    im2 = axes[1].imshow(red_map_nocdf, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1)
    axes[1].set_title('DA-NoCDF Fraction with Reduced Mismatch')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'mismatch_reduction_fraction_map.png'))
    plt.close()

    # F. REPRESENTATIVE HIGH-SUPPORT DAYS
    def plot_rep_maps(ds_res, ds_inv, ds_freq, exp):
        freq = ds_freq['observation_frequency'].values
        res = ds_res['daily_analysis_residual'].values
        inv = ds_inv['daily_innovation'].values
        daily_support = np.sum(freq == 1, axis=(1,2))
        top_days_idx = np.argsort(daily_support)[-2:]
        
        for idx in top_days_idx:
            dt = pd.to_datetime(times_arr[idx]).strftime('%Y-%m-%d')
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            vmax = max(np.nanmax(np.abs(res[idx])), np.nanmax(np.abs(inv[idx])))
            
            im1 = axes[0].imshow(inv[idx], origin='lower', extent=extent, cmap='BrBG', vmin=-vmax, vmax=vmax)
            axes[0].set_title(f'{exp} Innovation: {dt}')
            
            im2 = axes[1].imshow(res[idx], origin='lower', extent=extent, cmap='BrBG', vmin=-vmax, vmax=vmax)
            axes[1].set_title(f'{exp} Residual: {dt}')
            
            fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
            plt.savefig(os.path.join(out_dir, f'rep_map_{exp.lower()}_{dt}.png'))
            plt.close()
            
    plot_rep_maps(ds_res_cdf, ds_inv_cdf, ds_freq_cdf, 'DA-CDF')
    plot_rep_maps(ds_res_nocdf, ds_inv_nocdf, ds_freq_nocdf, 'DA-NoCDF')

    # G. BEFORE VS AFTER HEXBIN
    def plot_before_after(cond_inv, cond_res, exp):
        plt.figure(figsize=(8, 8))
        plt.hexbin(cond_inv, cond_res, gridsize=50, cmap='plasma', mincnt=1)
        
        lim = max(np.max(np.abs(cond_inv)), np.max(np.abs(cond_res)))
        plt.plot([-lim, lim], [-lim, lim], 'w--', label='No observation-space correction reference')
        
        plt.xlim(-lim, lim)
        plt.ylim(-lim, lim)
        plt.title(f'{exp} Before vs After Mismatch')
        plt.xlabel('Daily Innovation')
        plt.ylabel('Daily Analysis Residual')
        plt.legend()
        plt.colorbar(label='Count')
        plt.savefig(os.path.join(out_dir, f'before_after_hexbin_{exp.lower()}.png'))
        plt.close()

    plot_before_after(ds_inv_cdf['daily_innovation'].values[(ds_freq_cdf['observation_frequency'].values == 1)],
                      ds_res_cdf['daily_analysis_residual'].values[(ds_freq_cdf['observation_frequency'].values == 1)],
                      'DA-CDF')
    plot_before_after(ds_inv_nocdf['daily_innovation'].values[(ds_freq_nocdf['observation_frequency'].values == 1)],
                      ds_res_nocdf['daily_analysis_residual'].values[(ds_freq_nocdf['observation_frequency'].values == 1)],
                      'DA-NoCDF')

    # H. OBSERVATION-SPACE UPDATE VS STATE INCREMENT
    def plot_obs_upd_vs_inc(cond_inv, cond_res, cond_inc, exp):
        obs_upd = cond_inv - cond_res
        plt.figure(figsize=(8, 8))
        plt.hexbin(obs_upd, cond_inc, gridsize=50, cmap='plasma', mincnt=1)
        
        lim = max(np.max(np.abs(obs_upd)), np.max(np.abs(cond_inc)))
        plt.plot([-lim, lim], [-lim, lim], 'w--', label='1:1 reference, not assumed identity')
        
        plt.xlim(-lim, lim)
        plt.ylim(-lim, lim)
        plt.title(f'{exp} Observation-Space Update vs Layer-1 Increment')
        plt.xlabel('Observation-Space Update')
        plt.ylabel('Daily Signed Increment')
        plt.legend()
        plt.colorbar(label='Count')
        plt.savefig(os.path.join(out_dir, f'obs_upd_vs_inc_{exp.lower()}.png'))
        plt.close()

    plot_obs_upd_vs_inc(ds_inv_cdf['daily_innovation'].values[(ds_freq_cdf['observation_frequency'].values == 1)],
                      ds_res_cdf['daily_analysis_residual'].values[(ds_freq_cdf['observation_frequency'].values == 1)],
                      ds_inc_cdf['daily_signed_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1)],
                      'DA-CDF')
    plot_obs_upd_vs_inc(ds_inv_nocdf['daily_innovation'].values[(ds_freq_nocdf['observation_frequency'].values == 1)],
                      ds_res_nocdf['daily_analysis_residual'].values[(ds_freq_nocdf['observation_frequency'].values == 1)],
                      ds_inc_nocdf['daily_signed_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1)],
                      'DA-NoCDF')

if __name__ == "__main__":
    plot_all()
