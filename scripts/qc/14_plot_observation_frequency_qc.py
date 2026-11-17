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

def process_exp(exp, ds, ds_inv):
    print(f"\n================ {exp} ================")
    
    # 1827-day completeness
    times = pd.DatetimeIndex(ds.time.values)
    print(f"Total days: {len(times)}")
    print(f"Date range: {times[0].strftime('%Y-%m-%d')} to {times[-1].strftime('%Y-%m-%d')}")
    
    # Annual counts
    for year in range(2016, 2021):
        if str(year) in ds_inv.event_time.dt.year.values:
            ev_mask = ds_inv.event_time.dt.year == year
            inv_y = ds_inv.sel(event_time=ev_mask)['innovation'].values
            ev_valid = np.sum(~np.isnan(inv_y))
            
            t_mask = ds.time.dt.year == year
            freq_y = ds.sel(time=t_mask)['observation_frequency'].values
            daily_valid = np.nansum(freq_y)
            print(f"[{year}] Event-based: {ev_valid}, Daily-agg: {daily_valid}, Diff: {ev_valid - daily_valid}")
            
    # Value range and fractions
    vals = ds['observation_frequency'].values
    vals_valid = vals[~np.isnan(vals)]
    
    if len(vals_valid) == 0: return
    
    print(f"\nFrequency statistics:")
    print(f"  min: {np.min(vals_valid)}")
    print(f"  max: {np.max(vals_valid)}")
    print(f"  mean: {np.mean(vals_valid):.6f}")
    print(f"  median: {np.median(vals_valid)}")
    
    counts = np.bincount(vals_valid.astype(int))
    for i in range(min(5, len(counts))):
        frac = counts[i] / len(vals_valid)
        label = f"== {i}" if i < 4 else ">= 4"
        if i == 4: frac = np.sum(counts[4:]) / len(vals_valid)
        print(f"  fraction {label}: {frac:.6f}")
        
    zero_days = np.sum(np.nansum(vals, axis=(1, 2)) == 0)
    print(f"  days with 0 observations domain-wide: {zero_days}")
    
    # Land coverage
    pixels_with_obs = np.sum(vals > 0, axis=(1, 2))
    valid_land_pixels = np.sum(~np.isnan(vals[0]))
    coverage_frac = pixels_with_obs / valid_land_pixels
    
    print(f"\nDaily land coverage:")
    print(f"  mean coverage fraction: {np.mean(coverage_frac):.6f}")
    print(f"  median coverage fraction: {np.median(coverage_frac):.6f}")
    
    # Multiple updates
    gt1_frac = np.sum(vals_valid > 1) / len(vals_valid[vals_valid > 0])
    print(f"\nMultiple updates (>1 per day, fraction of observed pixel-days): {gt1_frac:.6f}")
    
    # 2019 Outage
    if 2019 in times.year:
        before = (times >= '2019-05-01') & (times < '2019-06-19')
        during = (times >= '2019-06-19') & (times <= '2019-07-23')
        after = (times > '2019-07-23') & (times <= '2019-08-31')
        
        counts_daily = np.nansum(vals, axis=(1, 2))
        print(f"\n2019 Outage:")
        print(f"  Before (May 1 - Jun 18) mean daily total: {np.mean(counts_daily[before]):.1f}")
        print(f"  During (Jun 19 - Jul 23) mean daily total: {np.mean(counts_daily[during]):.1f}")
        print(f"  After (Jul 24 - Aug 31) mean daily total: {np.mean(counts_daily[after]):.1f}")

def main():
    out_dir = "reports/qc/observation_frequency"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_cdf = load_all("data/processed/daily_enkf/da_cdf/observation_frequency", "observation_frequency")
    ds_nocdf = load_all("data/processed/daily_enkf/da_nocdf/observation_frequency", "observation_frequency")
    
    # Need event-based innovation for count conservation checks
    inv_cdf = xr.concat([xr.open_dataset(f) for f in sorted(glob.glob("data/interim/enkf/da_cdf/innovation/*.nc"))], dim='event_time')
    inv_nocdf = xr.concat([xr.open_dataset(f) for f in sorted(glob.glob("data/interim/enkf/da_nocdf/innovation/*.nc"))], dim='event_time')
    
    process_exp('DA-CDF', ds_cdf, inv_cdf)
    process_exp('DA-NoCDF', ds_nocdf, inv_nocdf)
    
    # 10. EVENT-TO-DAY IDENTITY TEST
    print("\n================ EVENT-TO-DAY IDENTITY TEST (DA-CDF) ================")
    # Pick a few days: Jan 5, 2016, Jun 27, 2016 (no obs), Dec 28, 2016
    for date_str in ['2016-01-05', '2016-06-27', '2016-12-28']:
        dt = pd.to_datetime(date_str)
        t_mask = (inv_cdf.event_time >= dt) & (inv_cdf.event_time < dt + pd.Timedelta(days=1))
        inv_events = inv_cdf.sel(event_time=t_mask)['innovation'].values
        ev_counts = np.sum(~np.isnan(inv_events), axis=0) if len(inv_events) > 0 else np.zeros((121, 181))
        
        daily_freq = ds_cdf.sel(time=date_str)['observation_frequency'].values
        
        land_mask = ~np.isnan(daily_freq)
        ev_counts = ev_counts.astype(np.float32)
        ev_counts[~land_mask] = np.nan
        
        diff = np.abs(ev_counts[land_mask] - daily_freq[land_mask])
        print(f"Date {date_str}: events={len(inv_events)}, max diff={np.max(diff):.1f}, differing pixels={np.sum(diff > 0)}")
    
    # 18. QUICKLOOK QC
    
    # A. DAILY DOMAIN TOTAL
    counts_cdf = np.nansum(ds_cdf['observation_frequency'].values, axis=(1, 2))
    counts_nocdf = np.nansum(ds_nocdf['observation_frequency'].values, axis=(1, 2))
    
    plt.figure(figsize=(12, 6))
    plt.plot(ds_cdf.time.values, counts_cdf, label='DA-CDF', alpha=0.7)
    plt.plot(ds_nocdf.time.values, counts_nocdf, label='DA-NoCDF', alpha=0.7)
    plt.title('Total Assimilated Observations per Day')
    plt.ylabel('Count')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'daily_domain_total.png'))
    plt.close()
    
    # B. DAILY SPATIAL COVERAGE
    land_pixels = np.sum(~np.isnan(ds_cdf['observation_frequency'].values[0]))
    cov_cdf = np.sum(ds_cdf['observation_frequency'].values > 0, axis=(1, 2)) / land_pixels
    cov_nocdf = np.sum(ds_nocdf['observation_frequency'].values > 0, axis=(1, 2)) / land_pixels
    
    plt.figure(figsize=(12, 6))
    plt.plot(ds_cdf.time.values, cov_cdf, label='DA-CDF', alpha=0.7)
    plt.plot(ds_nocdf.time.values, cov_nocdf, label='DA-NoCDF', alpha=0.7)
    plt.title('Fraction of Valid Land Pixels with >=1 Observation')
    plt.ylabel('Fraction')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'daily_spatial_coverage.png'))
    plt.close()
    
    # C. TEMPORAL-MEAN MAP
    extent = [ds_cdf.lon.values.min(), ds_cdf.lon.values.max(), ds_cdf.lat.values.min(), ds_cdf.lat.values.max()]
    mean_cdf = np.nanmean(ds_cdf['observation_frequency'].values, axis=0)
    mean_nocdf = np.nanmean(ds_nocdf['observation_frequency'].values, axis=0)
    
    vmax = max(np.nanmax(mean_cdf), np.nanmax(mean_nocdf))
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(mean_cdf, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=vmax)
    axes[0].set_title('DA-CDF Mean Daily Obs Frequency')
    im2 = axes[1].imshow(mean_nocdf, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=vmax)
    axes[1].set_title('DA-NoCDF Mean Daily Obs Frequency')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Mean Count/Day')
    plt.savefig(os.path.join(out_dir, 'temporal_mean_map.png'))
    plt.close()
    
    # D. OBSERVATION-DAY FRACTION MAP
    days_gt0_cdf = np.sum(ds_cdf['observation_frequency'].values > 0, axis=0)
    valid_days_cdf = np.sum(~np.isnan(ds_cdf['observation_frequency'].values), axis=0)
    frac_cdf = np.where(valid_days_cdf > 0, days_gt0_cdf / valid_days_cdf, np.nan)
    
    days_gt0_nocdf = np.sum(ds_nocdf['observation_frequency'].values > 0, axis=0)
    valid_days_nocdf = np.sum(~np.isnan(ds_nocdf['observation_frequency'].values), axis=0)
    frac_nocdf = np.where(valid_days_nocdf > 0, days_gt0_nocdf / valid_days_nocdf, np.nan)
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    im1 = axes[0].imshow(frac_cdf, origin='lower', extent=extent, cmap='plasma', vmin=0, vmax=0.5)
    axes[0].set_title('DA-CDF')
    im2 = axes[1].imshow(frac_nocdf, origin='lower', extent=extent, cmap='plasma', vmin=0, vmax=0.5)
    axes[1].set_title('DA-NoCDF')
    fig.suptitle('Fraction of Days with >=1 Assimilated SMAP Observation')
    fig.colorbar(im1, ax=axes, orientation='horizontal', fraction=0.05, pad=0.1, label='Fraction')
    plt.savefig(os.path.join(out_dir, 'observation_day_fraction.png'))
    plt.close()
    
    # E. CDF - NoCDF SUPPORT DIFFERENCE
    diff_mean = mean_cdf - mean_nocdf
    
    plt.figure(figsize=(8, 6))
    vmax_diff = np.nanmax(np.abs(diff_mean))
    plt.imshow(diff_mean, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax_diff, vmax=vmax_diff)
    plt.colorbar(label='Difference (CDF - NoCDF)')
    plt.title('Difference in Mean Daily Obs Frequency (CDF - NoCDF)')
    plt.savefig(os.path.join(out_dir, 'support_difference_map.png'))
    plt.close()
    
    # F. DAILY COUNT HISTOGRAM
    vals_cdf = ds_cdf['observation_frequency'].values
    vals_cdf = vals_cdf[~np.isnan(vals_cdf)]
    vals_nocdf = ds_nocdf['observation_frequency'].values
    vals_nocdf = vals_nocdf[~np.isnan(vals_nocdf)]
    
    plt.figure(figsize=(10, 6))
    bins = np.arange(0, 10, 1) - 0.5
    plt.hist(vals_cdf, bins=bins, alpha=0.5, density=True, label='DA-CDF')
    plt.hist(vals_nocdf, bins=bins, alpha=0.5, density=True, label='DA-NoCDF')
    plt.xticks(range(10))
    plt.xlim(-0.5, 5.5)
    plt.title('Daily Count Histogram (Valid Land Pixel-Days)')
    plt.xlabel('Assimilated Observations per Day')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'daily_count_histogram.png'))
    plt.close()

if __name__ == "__main__":
    main()
