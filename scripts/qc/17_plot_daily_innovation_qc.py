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

def process_exp(exp, ds_inv, ds_signed, ds_abs, ds_freq):
    print(f"\n================ {exp} ================")
    
    vals_inv = ds_inv['daily_innovation'].values
    vals_signed = ds_signed['daily_signed_increment'].values
    vals_abs = ds_abs['daily_absolute_increment'].values
    freq = ds_freq['observation_frequency'].values
    
    valid_land = ~np.isnan(freq)
    finite_inv = ~np.isnan(vals_inv)
    
    # Support Consistency
    freq_1_mask = (freq == 1) & valid_land
    freq_0_mask = (freq == 0) & valid_land
    
    viol_1 = np.sum(freq_1_mask & ~finite_inv)
    viol_0 = np.sum(freq_0_mask & finite_inv)
    print(f"Support consistency violations: freq=1 but nan -> {viol_1}, freq=0 but finite -> {viol_0}")
    
    # Zero count
    cond = vals_inv[freq_1_mask]
    exact_zeros = np.sum(cond == 0.0)
    print(f"Exact zero count in innovation: {exact_zeros}")
    
    # Conditional stats
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
    
    # Relation to signed increment
    cond_signed = vals_signed[freq_1_mask]
    corr_p, _ = pearsonr(cond, cond_signed)
    corr_s, _ = spearmanr(cond, cond_signed)
    
    sign_agree = np.sum(np.sign(cond) == np.sign(cond_signed)) / len(cond)
    
    print("\nRELATION TO DAILY SIGNED INCREMENT:")
    print(f"  Pearson correlation: {corr_p:.4f}")
    print(f"  Spearman correlation: {corr_s:.4f}")
    print(f"  Sign-agreement fraction: {sign_agree:.4f}")
    
    # Relation to absolute increment
    cond_abs = vals_abs[freq_1_mask]
    corr_abs_p, _ = pearsonr(np.abs(cond), cond_abs)
    corr_abs_s, _ = spearmanr(np.abs(cond), cond_abs)
    print("\nRELATION TO DAILY ABSOLUTE INCREMENT:")
    print(f"  Pearson correlation (|inv| vs abs_inc): {corr_abs_p:.4f}")
    print(f"  Spearman correlation (|inv| vs abs_inc): {corr_abs_s:.4f}")

def main():
    out_dir = "reports/qc/daily_innovation"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_inv_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_innovation", "daily_innovation")
    ds_inv_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_innovation", "daily_innovation")
    
    ds_signed_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_signed_increment", "daily_signed_increment")
    ds_signed_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_signed_increment", "daily_signed_increment")
    
    ds_abs_cdf = load_all("data/processed/daily_enkf/da_cdf/daily_absolute_increment", "daily_absolute_increment")
    ds_abs_nocdf = load_all("data/processed/daily_enkf/da_nocdf/daily_absolute_increment", "daily_absolute_increment")
    
    ds_freq_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_freq_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    process_exp('DA-CDF', ds_inv_cdf, ds_signed_cdf, ds_abs_cdf, ds_freq_cdf)
    process_exp('DA-NoCDF', ds_inv_nocdf, ds_signed_nocdf, ds_abs_nocdf, ds_freq_nocdf)
    
    # 2019 OUTAGE VALIDATION
    print("\n================ 2019 OUTAGE VALIDATION ================")
    times = pd.DatetimeIndex(ds_inv_cdf.time.values)
    outage = (times >= '2019-06-19') & (times <= '2019-07-23')
    
    cdf_outage_vals = ds_inv_cdf['daily_innovation'].values[outage]
    valid_cdf = cdf_outage_vals[~np.isnan(cdf_outage_vals)]
    print(f"DA-CDF outage finite count: {len(valid_cdf)}")
    
    nocdf_outage_vals = ds_inv_nocdf['daily_innovation'].values[outage]
    valid_nocdf = nocdf_outage_vals[~np.isnan(nocdf_outage_vals)]
    print(f"DA-NoCDF outage finite count: {len(valid_nocdf)}")
    
    # FULL-PERIOD EVENT-TO-DAILY IDENTITY TEST
    def check_identity(exp, daily_ds):
        print(f"\n================ FULL-PERIOD EVENT-TO-DAILY IDENTITY ({exp}) ================")
        daily_inv = daily_ds['daily_innovation'].values
        daily_times = pd.DatetimeIndex(daily_ds.time.values)
        
        total_matched = 0
        max_diff = 0.0
        sum_diff = 0.0
        unequal_exact = 0
        unequal_1e8 = 0
        unequal_1e7 = 0
        sign_mismatch = 0
        
        for year in range(2016, 2021):
            ds_event = xr.open_dataset(f"data/interim/enkf/{exp.replace('-','_').lower()}/innovation/innovation_{year}.nc")
            ev_inv = ds_event['innovation'].values
            ev_times = ds_event.event_time.values
            ev_days = pd.DatetimeIndex(ev_times).floor('D')
            
            for i, ev_day in enumerate(ev_days):
                day_idx = np.where(daily_times == ev_day)[0]
                if len(day_idx) == 0: continue
                day_idx = day_idx[0]
                
                ev_slice = ev_inv[i]
                daily_slice = daily_inv[day_idx]
                
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
    
    check_identity("DA-CDF", ds_inv_cdf)
    check_identity("DA-NoCDF", ds_inv_nocdf)

    # ================ PLOTTING ================
    times_arr = ds_inv_cdf.time.values
    extent = [ds_inv_cdf.lon.values.min(), ds_inv_cdf.lon.values.max(), ds_inv_cdf.lat.values.min(), ds_inv_cdf.lat.values.max()]
    
    # A. DISTRIBUTION
    cond_vals_cdf = ds_inv_cdf['daily_innovation'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    cond_vals_nocdf = ds_inv_nocdf['daily_innovation'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    
    plt.figure(figsize=(10, 6))
    bins = np.linspace(min(np.min(cond_vals_cdf), np.min(cond_vals_nocdf)), max(np.max(cond_vals_cdf), np.max(cond_vals_nocdf)), 100)
    plt.hist(cond_vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(cond_vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.axvline(0, color='black', lw=1, ls='--')
    plt.title('Distribution of Daily Innovation Conditional on Assimilation')
    plt.xlabel('Innovation (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'innovation_distribution.png'))
    plt.close()
    
    # B. DAILY TEMPORAL SUMMARY
    def get_means(ds_inv, ds_freq):
        vals = ds_inv['daily_innovation'].values
        freq = ds_freq['observation_frequency'].values
        
        c_mean = np.zeros(len(vals))
        c_median = np.zeros(len(vals))
        c_abs = np.zeros(len(vals))
        n_upd = np.zeros(len(vals))
        
        for i in range(len(vals)):
            mask = freq[i] == 1
            n_upd[i] = np.sum(mask)
            if np.any(mask):
                c_mean[i] = np.nanmean(vals[i][mask])
                c_median[i] = np.nanmedian(vals[i][mask])
                c_abs[i] = np.nanmean(np.abs(vals[i][mask]))
            else:
                c_mean[i] = np.nan
                c_median[i] = np.nan
                c_abs[i] = np.nan
        return c_mean, c_median, c_abs, n_upd

    c_mean_cdf, c_median_cdf, c_abs_cdf, n_cdf = get_means(ds_inv_cdf, ds_freq_cdf)
    c_mean_nocdf, c_median_nocdf, c_abs_nocdf, n_nocdf = get_means(ds_inv_nocdf, ds_freq_nocdf)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
    axes[0].plot(times_arr, c_mean_cdf, label='DA-CDF', alpha=0.7)
    axes[0].plot(times_arr, c_mean_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[0].set_title('Mean Signed Innovation (Assimilated Pixels Only)')
    axes[0].axhline(0, color='black', lw=0.5, ls='--')
    axes[0].legend()
    
    axes[1].plot(times_arr, c_median_cdf, label='DA-CDF', alpha=0.7)
    axes[1].plot(times_arr, c_median_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[1].set_title('Median Innovation (Assimilated Pixels Only)')
    axes[1].axhline(0, color='black', lw=0.5, ls='--')
    axes[1].legend()
    
    axes[2].plot(times_arr, c_abs_cdf, label='DA-CDF', alpha=0.7)
    axes[2].plot(times_arr, c_abs_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[2].set_title('Mean Absolute Innovation (Assimilated Pixels Only)')
    axes[2].legend()
    
    axes[3].plot(times_arr, n_cdf, label='DA-CDF', alpha=0.7)
    axes[3].plot(times_arr, n_nocdf, label='DA-NoCDF', alpha=0.7)
    axes[3].set_title('Valid Count (Number of Updates)')
    axes[3].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daily_temporal_summary.png'))
    plt.close()
    
    # C. CONDITIONAL MEAN SIGNED MAP
    def get_cond_map(ds_inv, ds_freq):
        vals = ds_inv['daily_innovation'].values
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    c_map_cdf = get_cond_map(ds_inv_cdf, ds_freq_cdf)
    c_map_nocdf = get_cond_map(ds_inv_nocdf, ds_freq_nocdf)
    vmax_c = max(np.nanmax(np.abs(c_map_cdf)), np.nanmax(np.abs(c_map_nocdf)))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(c_map_cdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[0].set_title('DA-CDF Conditional Mean Signed Innovation')
    im2 = axes[1].imshow(c_map_nocdf, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_c, vmax=vmax_c)
    axes[1].set_title('DA-NoCDF Conditional Mean Signed Innovation')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Innovation (m3 m-3)')
    plt.savefig(os.path.join(out_dir, 'conditional_mean_signed_map.png'))
    plt.close()

    # D. CONDITIONAL MEAN ABSOLUTE MAP
    def get_cond_abs_map(ds_inv, ds_freq):
        vals = np.abs(ds_inv['daily_innovation'].values)
        freq = ds_freq['observation_frequency'].values
        cond_vals = np.where(freq == 1, vals, np.nan)
        return np.nanmean(cond_vals, axis=0)
        
    ca_map_cdf = get_cond_abs_map(ds_inv_cdf, ds_freq_cdf)
    ca_map_nocdf = get_cond_abs_map(ds_inv_nocdf, ds_freq_nocdf)
    vmax_ca = max(np.nanmax(ca_map_cdf), np.nanmax(ca_map_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(ca_map_cdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_ca)
    axes[0].set_title('DA-CDF Conditional Mean Absolute Innovation')
    im2 = axes[1].imshow(ca_map_nocdf, origin='lower', extent=extent, cmap='YlGnBu', vmin=0, vmax=vmax_ca)
    axes[1].set_title('DA-NoCDF Conditional Mean Absolute Innovation')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Absolute Innovation (m3 m-3)')
    plt.savefig(os.path.join(out_dir, 'conditional_mean_absolute_map.png'))
    plt.close()
    
    # E. REPRESENTATIVE DAILY MAPS
    def plot_rep_maps(ds_inv, ds_freq, exp):
        freq = ds_freq['observation_frequency'].values
        vals = ds_inv['daily_innovation'].values
        daily_support = np.sum(freq == 1, axis=(1,2))
        top_days_idx = np.argsort(daily_support)[-2:]
        
        for idx in top_days_idx:
            dt = pd.to_datetime(times_arr[idx]).strftime('%Y-%m-%d')
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(vals[idx], origin='lower', extent=extent, cmap='BrBG', vmin=-0.1, vmax=0.1)
            ax.set_title(f'{exp} Daily Innovation: {dt}')
            fig.colorbar(im, ax=ax, label='Innovation (m3 m-3)')
            plt.savefig(os.path.join(out_dir, f'rep_map_{exp.lower()}_{dt}.png'))
            plt.close()
            
    plot_rep_maps(ds_inv_cdf, ds_freq_cdf, 'DA-CDF')
    plot_rep_maps(ds_inv_nocdf, ds_freq_nocdf, 'DA-NoCDF')

    # F. INNOVATION VS SIGNED INCREMENT
    plt.figure(figsize=(8, 6))
    cond_signed_cdf = ds_signed_cdf['daily_signed_increment'].values[(ds_freq_cdf['observation_frequency'].values == 1)]
    plt.hexbin(cond_vals_cdf, cond_signed_cdf, gridsize=50, cmap='plasma', mincnt=1)
    # 1:1 line
    lims = [
        np.min([plt.xlim(), plt.ylim()]),  
        np.max([plt.xlim(), plt.ylim()]),  
    ]
    plt.plot(lims, lims, 'k--', alpha=0.75, zorder=0, label='1:1 reference (not expected relationship)')
    plt.title('DA-CDF Innovation vs Signed Increment')
    plt.xlabel('Daily Innovation')
    plt.ylabel('Daily Signed Increment')
    plt.colorbar(label='Count')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'innovation_vs_increment_cdf.png'))
    plt.close()
    
    plt.figure(figsize=(8, 6))
    cond_signed_nocdf = ds_signed_nocdf['daily_signed_increment'].values[(ds_freq_nocdf['observation_frequency'].values == 1)]
    plt.hexbin(cond_vals_nocdf, cond_signed_nocdf, gridsize=50, cmap='plasma', mincnt=1)
    plt.plot(lims, lims, 'k--', alpha=0.75, zorder=0, label='1:1 reference (not expected relationship)')
    plt.title('DA-NoCDF Innovation vs Signed Increment')
    plt.xlabel('Daily Innovation')
    plt.ylabel('Daily Signed Increment')
    plt.colorbar(label='Count')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'innovation_vs_increment_nocdf.png'))
    plt.close()

if __name__ == "__main__":
    main()
