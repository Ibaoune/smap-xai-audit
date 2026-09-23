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

def process_exp(exp, ds_ninv, ds_inv, ds_abs, ds_freq):
    print(f"\n================ {exp} ================")
    
    vals_ninv = ds_ninv['daily_normalized_innovation'].values
    vals_inv = ds_inv['daily_innovation'].values
    vals_abs = ds_abs['daily_absolute_increment'].values
    freq = ds_freq['observation_frequency'].values
    
    valid_land = ~np.isnan(freq)
    finite_ninv = ~np.isnan(vals_ninv)
    
    # H. Support Consistency
    freq_1_mask = (freq == 1) & valid_land
    freq_0_mask = (freq == 0) & valid_land
    
    viol_1 = np.sum(freq_1_mask & ~finite_ninv)
    viol_0 = np.sum(freq_0_mask & finite_ninv)
    print(f"Support consistency violations: freq=1 but nan -> {viol_1}, freq=0 but finite -> {viol_0}")
    
    # K. Full-period statistics
    cond = vals_ninv[freq_1_mask]
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
    print(f"  fraction < 0: {np.sum(cond < 0) / len(cond)}")
    print(f"  fraction == 0: {np.sum(cond == 0) / len(cond)}")
    print(f"  fraction > 0: {np.sum(cond > 0) / len(cond)}")
    
    # L. Exceedance fractions
    abs_cond = np.abs(cond)
    print(f"  fraction |NI| > 1: {np.sum(abs_cond > 1) / len(cond)}")
    print(f"  fraction |NI| > 2: {np.sum(abs_cond > 2) / len(cond)}")
    print(f"  fraction |NI| > 3: {np.sum(abs_cond > 3) / len(cond)}")
    
    # S. Exact-zero consistency
    cond_inv = vals_inv[freq_1_mask]
    ninv_zero = (cond == 0.0)
    inv_zero = (cond_inv == 0.0)
    zero_mismatch = np.sum(ninv_zero != inv_zero)
    print(f"\nEXACT-ZERO CONSISTENCY:")
    print(f"  zero mismatches: {zero_mismatch}")
    
    # N. Innovation vs Normalized Innovation
    corr_p, _ = pearsonr(cond_inv, cond)
    corr_s, _ = spearmanr(cond_inv, cond)
    print("\nRELATION TO DAILY INNOVATION:")
    print(f"  Pearson: {corr_p:.4f}")
    print(f"  Spearman: {corr_s:.4f}")
    
    # O. |Normalized Innovation| vs Absolute Increment
    cond_abs = vals_abs[freq_1_mask]
    corr_abs_p_ninv, _ = pearsonr(abs_cond, cond_abs)
    corr_abs_s_ninv, _ = spearmanr(abs_cond, cond_abs)
    print("\n|NORMALIZED INNOVATION| VS ABSOLUTE INCREMENT:")
    print(f"  Pearson: {corr_abs_p_ninv:.4f}")
    print(f"  Spearman: {corr_abs_s_ninv:.4f}")
    
    # P. |Raw Innovation| vs Absolute Increment
    abs_cond_inv = np.abs(cond_inv)
    corr_abs_p_inv, _ = pearsonr(abs_cond_inv, cond_abs)
    corr_abs_s_inv, _ = spearmanr(abs_cond_inv, cond_abs)
    print("\n|RAW INNOVATION| VS ABSOLUTE INCREMENT:")
    print(f"  Pearson: {corr_abs_p_inv:.4f}")
    print(f"  Spearman: {corr_abs_s_inv:.4f}")

def check_identity(exp, daily_ds):
    print(f"\n================ FULL-PERIOD EVENT-TO-DAILY IDENTITY ({exp}) ================")
    daily_ninv = daily_ds['daily_normalized_innovation'].values
    daily_times = pd.DatetimeIndex(daily_ds.time.values)
    
    total_matched = 0
    max_diff = 0.0
    sum_diff = 0.0
    unequal_exact = 0
    unequal_1e8 = 0
    unequal_1e7 = 0
    sign_mismatch = 0
    
    for year in range(2016, 2021):
        ds_event = xr.open_dataset(f"data/interim/enkf/{exp.replace('-','_').lower()}/normalized_innovation/normalized_innovation_{year}.nc")
        ev_ninv = ds_event['normalized_innovation'].values
        ev_times = ds_event.event_time.values
        ev_days = pd.DatetimeIndex(ev_times).floor('D')
        
        for i, ev_day in enumerate(ev_days):
            day_idx = np.where(daily_times == ev_day)[0]
            if len(day_idx) == 0: continue
            day_idx = day_idx[0]
            
            ev_slice = ev_ninv[i]
            daily_slice = daily_ninv[day_idx]
            
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
            
            sign_ev = np.sign(ev_slice[mask])
            sign_da = np.sign(daily_slice[mask])
            sign_mismatch += np.sum(sign_ev != sign_da)
            
    mean_diff = sum_diff / total_matched if total_matched > 0 else 0
    print(f"Matched samples: {total_matched}")
    print(f"Max abs diff: {max_diff:.6e}")
    print(f"Mean abs diff: {mean_diff:.6e}")
    print(f"Unequal exact: {unequal_exact}")
    print(f"Unequal atol=1e-8: {unequal_1e8}")
    print(f"Unequal atol=1e-7: {unequal_1e7}")
    print(f"Sign mismatch: {sign_mismatch}")

def formula_reconstruction(exp):
    print(f"\n================ INDEPENDENT FORMULA RECONSTRUCTION ({exp}) ================")
    R = 0.0016
    total_matched = 0
    max_diff = 0.0
    sum_diff = 0.0
    unequal_exact = 0
    
    for year in range(2016, 2021):
        exp_low = exp.replace('-','_').lower()
        ds_ninv = xr.open_dataset(f"data/interim/enkf/{exp_low}/normalized_innovation/normalized_innovation_{year}.nc")
        ds_inv = xr.open_dataset(f"data/interim/enkf/{exp_low}/innovation/innovation_{year}.nc")
        ds_fv = xr.open_dataset(f"data/interim/enkf/{exp_low}/forecast_variance/forecast_variance_{year}.nc")
        
        ninv = ds_ninv['normalized_innovation'].values
        inv = ds_inv['innovation'].values
        fv = ds_fv['forecast_variance'].values
        
        mask = ~np.isnan(ninv)
        matched = np.sum(mask)
        if matched == 0: continue
        
        S = fv[mask] + R
        recon = inv[mask] / np.sqrt(S)
        orig = ninv[mask]
        
        diff = np.abs(recon - orig)
        
        total_matched += matched
        max_diff = max(max_diff, np.max(diff))
        sum_diff += np.sum(diff)
        unequal_exact += np.sum(recon != orig)
        
    mean_diff = sum_diff / total_matched if total_matched > 0 else 0
    print(f"innovation variance S = forecast_variance + {R}")
    print(f"innovation std = sqrt(S)")
    print(f"Matched samples: {total_matched}")
    print(f"Max abs diff: {max_diff:.6e}")
    print(f"Mean abs diff: {mean_diff:.6e}")
    print(f"Unequal exact: {unequal_exact}")

def main():
    out_dir = "reports/qc/daily_normalized_innovation"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_ninv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_normalized_innovation", "daily_normalized_innovation")
    ds_ninv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_normalized_innovation", "daily_normalized_innovation")
    
    ds_inv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_innovation", "daily_innovation")
    ds_inv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_innovation", "daily_innovation")
    
    ds_abs_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_absolute_increment", "daily_absolute_increment")
    ds_abs_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_absolute_increment", "daily_absolute_increment")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_ninv_cdf, ds_inv_cdf, ds_abs_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_ninv_nocdf, ds_inv_nocdf, ds_abs_nocdf, ds_freq_nocdf)
    
    check_identity("DA-CDF", ds_ninv_cdf)
    check_identity("DA-NoCDF", ds_ninv_nocdf)
    
    formula_reconstruction("DA-CDF")
    formula_reconstruction("DA-NoCDF")
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_ninv_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_ninv_cdf['daily_normalized_innovation'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage finite count: {len(valid_cdf)}")
    
    nocdf_outage_vals = ds_ninv_nocdf['daily_normalized_innovation'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage finite count: {len(valid_nocdf)}")
    
    # ================ PLOTTING ================
    times_arr = ds_ninv_cdf.time.values
    extent = [ds_ninv_cdf.lon.values.min(), ds_ninv_cdf.lon.values.max(), ds_ninv_cdf.lat.values.min(), ds_ninv_cdf.lat.values.max()]
    
    cond_vals_cdf = ds_ninv_cdf['daily_normalized_innovation'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    cond_vals_nocdf = ds_ninv_nocdf['daily_normalized_innovation'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    
    # A. DISTRIBUTION
    plt.figure(figsize=(10, 6))
    bins = np.linspace(-6, 6, 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    for v in [-3, -2, -1, 0, 1, 2, 3]:
        plt.axvline(v, color='black', lw=0.5, ls='--')
    plt.title('Distribution of Daily Normalized Innovation')
    plt.xlabel('Normalized Innovation')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'normalized_innovation_distribution.png'))
    plt.close()
    
    # B. TEMPORAL SUMMARY
    def get_means(ds_ninv, ds_freq):
        vals = ds_ninv['daily_normalized_innovation'].values
        freq = ds_freq['observation_frequency'].values
        
        c_mean = np.zeros(len(vals))
        c_median = np.zeros(len(vals))
        c_abs = np.zeros(len(vals))
        exc_frac = np.zeros(len(vals))
        n_upd = np.zeros(len(vals))
        
        for i in range(len(vals)):
            mask = freq[i] == 1
            n_upd[i] = np.sum(mask)
            if np.any(mask):
                c_mean[i] = np.nanmean(vals[i][mask])
                c_median[i] = np.nanmedian(vals[i][mask])
                c_abs[i] = np.nanmean(np.abs(vals[i][mask]))
                exc_frac[i] = np.sum(np.abs(vals[i][mask]) > 2) / n_upd[i]
            else:
                c_mean[i] = np.nan
                c_median[i] = np.nan
                c_abs[i] = np.nan
                exc_frac[i] = np.nan
        return c_mean, c_median, c_abs, exc_frac, n_upd

    c_mean_cdf, c_median_cdf, c_abs_cdf, exc_cdf, n_cdf = get_means(ds_ninv_cdf, ds_freq_cdf)
    c_mean_nocdf, c_median_nocdf, c_abs_nocdf, exc_nocdf, n_nocdf = get_means(ds_ninv_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(5, 1, figsize=(12, 18), sharex=True)
    axes[0].plot(times_arr, c_mean_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, c_mean_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Mean Signed')
    axes[0].axhline(0, color='black', lw=0.5, ls='--')
    axes[0].legend()
    
    axes[1].plot(times_arr, c_median_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, c_median_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Median')
    axes[1].axhline(0, color='black', lw=0.5, ls='--')
    axes[1].legend()
    
    axes[2].plot(times_arr, c_abs_cdf, label='DA-CDF', alpha=0.7)
    axes[2].plot(times_arr, c_abs_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[2].set_title('Mean Absolute')
    axes[2].legend()
    
    axes[3].plot(times_arr, exc_cdf, label='DA-CDF', alpha=0.7)
    axes[3].plot(times_arr, exc_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[3].set_title('Fraction |NI| > 2')
    axes[3].legend()
    
    axes[4].plot(times_arr, n_cdf, label='DA-CDF', alpha=0.7)
    axes[4].plot(times_arr, n_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[4].set_title('Valid Count')
    axes[4].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_temporal_summary.png'))
    plt.close()
    
    # C. CONDITIONAL MEAN SIGNED MAP
    def get_cond_map(ds_ninv, ds_freq):
        vals = ds_ninv['daily_normalized_innovation'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    c_map_cdf = get_cond_map(ds_ninv_cdf, ds_freq_cdf)
    c_map_nocdf = get_cond_map(ds_ninv_nocdf, ds_freq_nocdf)
    vmax_c = max(np.nanmax(np.abs(c_map_cdf)), np.nanmax(np.abs(c_map_nocdf)))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(c_map_cdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[0].set_title('DA-CDF Mean Signed NI')
    im2 = axes[1].imshow(c_map_nocdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[1].set_title('DA-NoCDF Mean Signed NI')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_mean_signed_map.png'))
    plt.close()

    # D. CONDITIONAL MEAN ABSOLUTE MAP
    def get_cond_abs_map(ds_ninv, ds_freq):
        vals = np.abs(ds_ninv['daily_normalized_innovation'].values)
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    ca_map_cdf = get_cond_abs_map(ds_ninv_cdf, ds_freq_cdf)
    ca_map_nocdf = get_cond_abs_map(ds_ninv_nocdf, ds_freq_nocdf)
    vmax_ca = max(np.nanmax(ca_map_cdf), np.nanmax(ca_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(ca_map_cdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_ca)
    axes[0].set_title('DA-CDF Mean Absolute NI')
    im2 = axes[1].imshow(ca_map_nocdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_ca)
    axes[1].set_title('DA-NoCDF Mean Absolute NI')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1)
    plt.savefig(os.path.join(out_dir, 'conditional_mean_absolute_map.png'))
    plt.close()
    
    # E. EXCEEDANCE MAP
    def get_exc_map(ds_ninv, ds_freq):
        vals = np.abs(ds_ninv['daily_normalized_innovation'].values)
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        exc = np.sum(cond_vals > 2, axis=0)
        tot = np.sum(freq == 1, axis=0)
        res = np.where(tot > 0, exc / tot, np.nan)
        return res
        
    e_map_cdf = get_exc_map(ds_ninv_cdf, ds_freq_cdf)
    e_map_nocdf = get_exc_map(ds_ninv_nocdf, ds_freq_nocdf)
    vmax_e = max(np.nanmax(e_map_cdf), np.nanmax(e_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(e_map_cdf, origin='lower', extent=extent, cmap='Reds', vmin=0, vmax=vmax_e)
    axes[0].set_title('DA-CDF Fraction |NI| > 2')
    im2 = axes[1].imshow(e_map_nocdf, origin='lower', extent=extent, cmap='Reds', vmin=0, vmax=vmax_e)
    axes[1].set_title('DA-NoCDF Fraction |NI| > 2')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Fraction of Assimilated Observations with |Normalized Innovation| > 2')
    plt.savefig(os.path.join(out_dir, 'exceedance_map.png'))
    plt.close()
    
    # F. REPRESENTATIVE DAILY MAPS
    def plot_rep_maps(ds_ninv, ds_freq, exp):
        freq = ds_freq['observation_frequency'].values
        vals = ds_ninv['daily_normalized_innovation'].values
        daily_support = np.sum(freq == 1, axis=(1,2))
        top_days_idx = np.argsort(daily_support)[-2:]
        
        for idx in top_days_idx:
            dt = pd.to_datetime(times_arr[idx]).strftime('%Y-%m-%d')
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(vals[idx], origin='lower', extent=extent, cmap='BrBG', vmin=-3, vmax=3)
            ax.set_title(f'{exp} Daily Normalized Innovation: {dt}')
            fig.colorbar(im, ax=ax, label='Normalized Innovation')
            plt.savefig(os.path.join(out_dir, f'rep_map_{exp.lower()}_{dt}.png'))
            plt.close()
            
    plot_rep_maps(ds_ninv_cdf, ds_freq_cdf, 'DA-CDF')
    plot_rep_maps(ds_ninv_nocdf, ds_freq_nocdf, 'DA-NoCDF')

    # G. NORMALIZED INNOVATION VS ABSOLUTE INCREMENT
    plt.figure(figsize=(8, 6))
    cond_abs_cdf = ds_abs_cdf['daily_absolute_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    plt.hexbin(np.abs(cond_vals_cdf), cond_abs_cdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-CDF |NI| vs Absolute Increment')
    plt.xlabel('|Daily Normalized Innovation|')
    plt.ylabel('Daily Absolute Increment')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'ninv_vs_abs_inc_cdf.png'))
    plt.close()
    
    plt.figure(figsize=(8, 6))
    cond_abs_nocdf = ds_abs_nocdf['daily_absolute_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    plt.hexbin(np.abs(cond_vals_nocdf), cond_abs_nocdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.title('DA-NoCDF |NI| vs Absolute Increment')
    plt.xlabel('|Daily Normalized Innovation|')
    plt.ylabel('Daily Absolute Increment')
    plt.colorbar(label='Count')
    plt.savefig(os.path.join(out_dir, 'ninv_vs_abs_inc_nocdf.png'))
    plt.close()

if __name__ == "__main__":
    main()
