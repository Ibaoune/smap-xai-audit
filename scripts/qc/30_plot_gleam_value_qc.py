#!/usr/bin/env python3
"""
SMAP-XAI Audit: Plot GLEAM Value QC (Block 3)
Author: M. El Aabaribaoune (@um6p)
"""

import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    out_dir = os.path.join(base_dir, "reports/qc/value_gleam")
    os.makedirs(out_dir, exist_ok=True)
    
    print("==================================================")
    print("DELETE STALE PNGs BEFORE REGENERATING")
    print("==================================================")
    old_pngs = glob.glob(os.path.join(out_dir, "*.png"))
    for f in old_pngs:
        os.remove(f)
    print(f"Deleted {len(old_pngs)} stale PNGs.")
    
    years = [2016, 2017, 2018, 2019, 2020]
    exps = ['opl', 'da_cdf', 'da_nocdf']
    
    model_dir = os.path.join(base_dir, "data/processed/value/gleam/model_et")
    ref_dir = os.path.join(base_dir, "data/processed/value/gleam/reference")
    
    g_data = []
    m_data = {exp: [] for exp in exps}
    
    for year in years:
        g_ds = xr.open_dataset(os.path.join(ref_dir, f"gleam_et_{year}.nc"))
        g_data.append(g_ds['et_reference'].values)
        for exp in exps:
            m_ds = xr.open_dataset(os.path.join(model_dir, exp, f"et_on_gleam_{year}.nc"))
            m_data[exp].append(m_ds['et'].values)
            
    g_data = np.concatenate(g_data, axis=0)
    for exp in exps:
        m_data[exp] = np.concatenate(m_data[exp], axis=0)
        
    final_common_mask = np.load(os.path.join(ref_dir, "final_common_mask.npy"))
    total_cell_days = np.sum(final_common_mask)
    
    print("==================================================")
    print("4. COMMON-MASK ASSERTIONS & CLOSURE TABLE")
    print("==================================================")
    print("Dataset        cells/day     cell-days")
    
    def print_closure(name, data):
        c_v = data[final_common_mask]
        n_c = np.sum(c_v < 0)
        z_c = np.sum(c_v == 0)
        p_c = np.sum(c_v > 0)
        tot = n_c + z_c + p_c
        assert tot == total_cell_days, f"Closure failed for {name}: {tot} != {total_cell_days}"
        print(f"{name:<15} {tot/1827:<12.1f} {tot:<15}")
        return n_c, z_c, p_c
        
    n_g, z_g, p_g = print_closure("GLEAM", g_data)
    m_counts = {}
    for exp in exps:
        m_counts[exp] = print_closure(exp.upper(), m_data[exp])
        
    print_closure("COMMON", g_data)
    
    lat_gleam = g_ds.lat.values
    lon_gleam = g_ds.lon.values
    
    # Compute geographic extent for plotting
    # Assuming pixels are spaced by gleam_res = 0.1
    # lat is descending, lon is ascending
    lon_min = lon_gleam[0] - 0.05
    lon_max = lon_gleam[-1] + 0.05
    lat_min = lat_gleam[-1] - 0.05
    lat_max = lat_gleam[0] + 0.05
    map_extent = [lon_min, lon_max, lat_min, lat_max]
    
    gleam_res = 0.1
    R = 6371.0
    def exact_area(lat_min, lat_max, dlon):
        phi_n = np.radians(lat_max)
        phi_s = np.radians(lat_min)
        dlambda = np.radians(dlon)
        return R**2 * dlambda * (np.sin(phi_n) - np.sin(phi_s))
    
    lat_areas = exact_area(lat_gleam - gleam_res/2, lat_gleam + gleam_res/2, gleam_res)
    area_2d = np.broadcast_to(lat_areas[:, None], g_data[0].shape)
        
    print("==================================================")
    print("7. COMPLETE DISTRIBUTION TABLE")
    print("==================================================")
    def print_dist(name, vals, counts):
        v = vals[final_common_mask]
        neg, zer, pos = counts
        total = len(v)
        print(f"Dataset: {name}")
        print(f"  min: {np.min(v):.4f}, max: {np.max(v):.4f}")
        print(f"  mean: {np.mean(v):.4f}, median: {np.median(v):.4f}, std: {np.std(v):.4f}")
        print(f"  p01: {np.percentile(v, 1):.4f}, p05: {np.percentile(v, 5):.4f}, p25: {np.percentile(v, 25):.4f}, p75: {np.percentile(v, 75):.4f}, p95: {np.percentile(v, 95):.4f}, p99: {np.percentile(v, 99):.4f}")
        print(f"  negative: {neg} ({neg/total*100:.2f}%), zero: {zer} ({zer/total*100:.2f}%), positive: {pos} ({pos/total*100:.2f}%)")
        
    print_dist("GLEAM", g_data, (n_g, z_g, p_g))
    for exp in exps:
        print_dist(f"{exp}-on-GLEAM", m_data[exp], m_counts[exp])
        
    print("==================================================")
    print("5. COMPLETE MODEL-MINUS-GLEAM TABLE")
    print("==================================================")
    for exp in exps:
        diff = (m_data[exp] - g_data)[final_common_mask]
        print(f"Experiment: {exp} - GLEAM")
        print(f"  mean signed: {np.mean(diff):.4f}")
        print(f"  median signed: {np.median(diff):.4f}")
        print(f"  mean absolute: {np.mean(np.abs(diff)):.4f}")
        print(f"  median absolute: {np.median(np.abs(diff)):.4f}")
        print(f"  RMSD: {np.sqrt(np.mean(diff**2)):.4f}")
        
    print("==================================================")
    print("6. COMPLETE SEASONAL TABLE")
    print("==================================================")
    times = pd.date_range("2016-01-01", "2020-12-31")
    months = times.month
    seasons = {
        'DJF': (months == 12) | (months == 1) | (months == 2),
        'MAM': (months >= 3) & (months <= 5),
        'JJA': (months >= 6) & (months <= 8),
        'SON': (months >= 9) & (months <= 11)
    }
    
    for season, idx in seasons.items():
        print(f"Season: {season}")
        g_s = g_data[idx]
        mask_s = final_common_mask[idx]
        weights_s = area_2d[np.newaxis, :, :] * mask_s
        
        g_mean = np.nansum(g_s * weights_s) / np.sum(weights_s)
        print(f"  GLEAM mean: {g_mean:.4f}")
        for exp in exps:
            m_s = m_data[exp][idx]
            m_mean = np.nansum(m_s * weights_s) / np.sum(weights_s)
            diff = m_s - g_s
            bias = np.nansum(diff * weights_s) / np.sum(weights_s)
            mae = np.nansum(np.abs(diff) * weights_s) / np.sum(weights_s)
            print(f"  {exp} mean: {m_mean:.4f}, bias: {bias:.4f}, MAE: {mae:.4f}")
        
    print("==================================================")
    print("MONTHLY REGRESSION CHECK")
    print("==================================================")
    times_period = times.to_period("M")
    unique_months = times_period.unique()
    # Ensure x-axis for plotting are actual dates
    monthly_dates = unique_months.to_timestamp()
    
    g_monthly = []
    m_monthly = {exp: [] for exp in exps}
    
    for m in unique_months:
        idx = (times_period == m)
        g_d = g_data[idx]
        m_mask = final_common_mask[idx]
        w_d = area_2d[np.newaxis, :, :] * m_mask
        
        day_sums_g = np.nansum(g_d * w_d, axis=(1,2)) / np.sum(w_d, axis=(1,2))
        g_monthly.append(np.sum(day_sums_g))
        
        for exp in exps:
            m_d = m_data[exp][idx]
            day_sums_m = np.nansum(m_d * w_d, axis=(1,2)) / np.sum(w_d, axis=(1,2))
            m_monthly[exp].append(np.sum(day_sums_m))
            
    g_monthly = np.array(g_monthly)
    for exp in exps:
        m_m = np.array(m_monthly[exp])
        pearson = np.corrcoef(m_m, g_monthly)[0,1]
        rmsd = np.sqrt(np.mean((m_m - g_monthly)**2))
        bias = np.mean(m_m - g_monthly)
        print(f"Experiment: {exp} vs GLEAM")
        print(f"  Pearson R: {pearson:.4f}, RMSD: {rmsd:.4f}, bias: {bias:.4f}")

    print("==================================================")
    print("9. PLOTTING & VISUAL QC ASSERTIONS")
    print("==================================================")
    
    def save_and_assert(fig, filename):
        # We assert non-blank logic in specific contexts instead of globally
        fpath = os.path.join(out_dir, filename)
        fig.savefig(fpath, dpi=150, bbox_inches='tight')
        plt.close(fig)
        assert os.path.exists(fpath) and os.path.getsize(fpath) > 0, f"Figure {filename} failed to save or is empty!"
        print(f"Validated & saved: {filename}")

    # Generate 1: et_distribution.png
    # Deterministic subsampling because >7.5 million values per dataset
    np.random.seed(42)
    sample_size = 500000
    common_idx = np.where(final_common_mask.flatten())[0]
    subsample_idx = np.random.choice(common_idx, size=min(sample_size, len(common_idx)), replace=False)
    
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(g_data.flatten()[subsample_idx], bins=100, alpha=0.5, label='GLEAM', density=True)
    ax.hist(m_data['opl'].flatten()[subsample_idx], bins=100, alpha=0.5, label='OPL', density=True)
    ax.hist(m_data['da_cdf'].flatten()[subsample_idx], bins=100, alpha=0.5, label='DA-CDF', density=True)
    ax.hist(m_data['da_nocdf'].flatten()[subsample_idx], bins=100, alpha=0.5, label='DA-NoCDF', density=True)
    
    ax.set_title(f"ET Distribution on Common Support (Subsampled {sample_size})")
    ax.set_xlabel("ET [mm/day]")
    ax.set_ylabel("Density")
    ax.legend()
    assert len(ax.patches) > 0, "No distribution patches found!"
    # Ensure 4 datasets are represented in legend
    assert len(ax.get_legend().get_texts()) >= 4, "Missing legend entries in distribution plot!"
    save_and_assert(fig, "et_distribution.png")

    # Generate 2: monthly_domain_series.png
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(monthly_dates, g_monthly, label="GLEAM", color="black", linewidth=2)
    ax.plot(monthly_dates, m_monthly['opl'], label="OPL", color="blue")
    ax.plot(monthly_dates, m_monthly['da_cdf'], label="DA-CDF", color="red")
    ax.plot(monthly_dates, m_monthly['da_nocdf'], label="DA-NoCDF", color="green")
    
    ax.set_title("Monthly Area-Weighted Domain ET Sum")
    ax.set_ylabel("ET [mm/month]")
    ax.set_xlabel("Date")
    ax.legend()
    assert len(ax.lines) >= 4, "Monthly domain series does not have 4 lines!"
    save_and_assert(fig, "monthly_domain_series.png")

    # Generate 3: daily_domain_mean.png
    g_daily = []
    for t in range(len(times)):
        mask = final_common_mask[t]
        weights = area_2d * mask
        g_daily.append(np.nansum(g_data[t] * weights) / np.sum(weights))
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(times, g_daily, label="GLEAM", color="black")
    ax.set_title("Daily Spherical-Area Weighted Mean ET")
    ax.set_ylabel("ET [mm/day]")
    ax.set_xlabel("Date")
    ax.legend()
    assert len(ax.lines) >= 1, "Daily domain series is blank!"
    save_and_assert(fig, "daily_domain_mean.png")

    # Generate 4: daily_valid_cell_count.png
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(times, np.sum(final_common_mask, axis=(1,2)))
    ax.set_ylim(0, 5000)
    ax.set_title("Daily Valid Cell Count")
    ax.set_ylabel("Count")
    assert len(ax.lines) >= 1, "Daily valid cell count is blank!"
    save_and_assert(fig, "daily_valid_cell_count.png")

    # Map assertion helper
    def assert_map(ax):
        has_images = len(ax.images) > 0 or len(ax.collections) > 0
        assert has_images, "Map panel is empty!"
        assert ax.get_xlim() != (0.0, 1.0), "Map has default xlim"
        assert ax.get_ylim() != (0.0, 1.0), "Map has default ylim"
        # Since lat is descending in GLEAM, imshow will have y inverted relative to extent
        # We verify variance
        if len(ax.images) > 0:
            arr = ax.images[0].get_array()
            assert np.nanstd(arr) > 0, "Map pixel variance is zero!"

    # Temporal means
    g_mean = np.nanmean(np.where(final_common_mask, g_data, np.nan), axis=0)
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(g_mean, extent=map_extent, aspect='auto', origin='upper')
    plt.colorbar(im, ax=ax, label="ET [mm/day]")
    ax.set_title("Temporal Mean GLEAM")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    assert_map(ax)
    save_and_assert(fig, "temporal_mean_gleam.png")

    for exp in exps:
        m_mean = np.nanmean(np.where(final_common_mask, m_data[exp], np.nan), axis=0)
        fig, ax = plt.subplots(figsize=(8,6))
        im = ax.imshow(m_mean, extent=map_extent, aspect='auto', origin='upper')
        plt.colorbar(im, ax=ax, label="ET [mm/day]")
        ax.set_title(f"Temporal Mean {exp.upper()}")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        assert_map(ax)
        save_and_assert(fig, f"temporal_mean_{exp}.png")
        
        fig, ax = plt.subplots(figsize=(8,6))
        im = ax.imshow(m_mean - g_mean, extent=map_extent, aspect='auto', origin='upper', cmap='RdBu', vmin=-1, vmax=1)
        plt.colorbar(im, ax=ax, label="Difference [mm/day]")
        ax.set_title(f"Mean Difference {exp.upper()} - GLEAM")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        assert_map(ax)
        save_and_assert(fig, f"mean_difference_{exp}_vs_gleam.png")

    # Selected maps: 4 panels each
    dates_to_plot = ["2016-01-15", "2016-04-15", "2016-07-15", "2016-10-15", "2016-02-29"]
    for d in dates_to_plot:
        idx = np.where(times == pd.to_datetime(d))[0][0]
        
        fig, axes = plt.subplots(2, 2, figsize=(14,10))
        axs = axes.flatten()
        
        vmin = 0
        vmax = np.nanmax([np.nanmax(np.where(final_common_mask[idx], g_data[idx], np.nan)),
                          np.nanmax(np.where(final_common_mask[idx], m_data['opl'][idx], np.nan)),
                          np.nanmax(np.where(final_common_mask[idx], m_data['da_cdf'][idx], np.nan)),
                          np.nanmax(np.where(final_common_mask[idx], m_data['da_nocdf'][idx], np.nan))])
        
        data_list = [g_data[idx], m_data['opl'][idx], m_data['da_cdf'][idx], m_data['da_nocdf'][idx]]
        names = ["GLEAM", "OPL-on-GLEAM", "DA-CDF-on-GLEAM", "DA-NoCDF-on-GLEAM"]
        
        for i, ax in enumerate(axs):
            d_arr = np.where(final_common_mask[idx], data_list[i], np.nan)
            im = ax.imshow(d_arr, extent=map_extent, aspect='auto', origin='upper', vmin=vmin, vmax=vmax)
            ax.set_title(f"{names[i]} ({d})")
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            assert_map(ax)
            
        fig.subplots_adjust(right=0.85)
        cbar_ax = fig.add_axes([0.88, 0.15, 0.03, 0.7])
        fig.colorbar(im, cax=cbar_ax, label="ET [mm/day]")
        
        assert len(axs) == 4, "Comparison figure does not have 4 panels!"
        save_and_assert(fig, f"map_comparison_{d}.png")
        
    # Common support
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(final_common_mask[0], extent=map_extent, aspect='auto', origin='upper')
    ax.set_title("Common Support Mask")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    assert_map(ax)
    save_and_assert(fig, "common_support.png")
    
    # Grid alignment
    fig, ax = plt.subplots(figsize=(8,6))
    lon_grid, lat_grid = np.meshgrid(lon_gleam, lat_gleam)
    ax.plot(lon_grid.flatten(), lat_grid.flatten(), 'k.', markersize=1)
    ax.set_title("Grid Alignment")
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max) # lat_min and lat_max are properly set
    assert len(ax.lines) > 0, "Grid alignment is empty!"
    save_and_assert(fig, "grid_alignment.png")

    print("==================================================")
    print("DONE PLOT")
    print("==================================================")

if __name__ == "__main__":
    main()
