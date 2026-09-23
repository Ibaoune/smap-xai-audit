#!/usr/bin/env python3
import os
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

def load_all(dir_path, var_name):
    files = sorted(glob.glob(os.path.join(dir_path, "*.nc")))
    if not files: return xr.Dataset()
    return xr.concat([xr.open_dataset(f) for f in files], dim='event_time')

def print_stats(ds, name):
    v = ds['normalized_innovation'].values.flatten()
    v = v[~np.isnan(v)]
    if len(v) == 0: return
    print(f"\n{name} Statistics:")
    print(f"  min: {np.min(v):.6f}")
    print(f"  max: {np.max(v):.6f}")
    print(f"  mean: {np.mean(v):.6f}")
    print(f"  median: {np.median(v):.6f}")
    print(f"  std: {np.std(v):.6f}")
    print(f"  p01: {np.percentile(v, 1):.6f}")
    print(f"  p05: {np.percentile(v, 5):.6f}")
    print(f"  p25: {np.percentile(v, 25):.6f}")
    print(f"  p75: {np.percentile(v, 75):.6f}")
    print(f"  p95: {np.percentile(v, 95):.6f}")
    print(f"  p99: {np.percentile(v, 99):.6f}")
    
    print(f"  < 0: {np.sum(v < 0) / len(v):.6f}")
    print(f"  == 0: {np.sum(v == 0) / len(v):.6f}")
    print(f"  > 0: {np.sum(v > 0) / len(v):.6f}")
    
    print(f"  |ninnov| > 1: {np.sum(np.abs(v) > 1) / len(v):.6f}")
    print(f"  |ninnov| > 2: {np.sum(np.abs(v) > 2) / len(v):.6f}")
    print(f"  |ninnov| > 3: {np.sum(np.abs(v) > 3) / len(v):.6f}")

def main():
    cdf_ninnov_dir = "data/interim/enkf/da_cdf/normalized_innovation"
    nocdf_ninnov_dir = "data/interim/enkf/da_nocdf/normalized_innovation"
    
    cdf_inv_dir = "data/interim/enkf/da_cdf/innovation"
    nocdf_inv_dir = "data/interim/enkf/da_nocdf/innovation"
    
    cdf_var_dir = "data/interim/enkf/da_cdf/forecast_variance"
    nocdf_var_dir = "data/interim/enkf/da_nocdf/forecast_variance"
    
    out_dir = "reports/qc/normalized_innovation"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_n_cdf = load_all(cdf_ninnov_dir, 'normalized_innovation')
    ds_n_nocdf = load_all(nocdf_ninnov_dir, 'normalized_innovation')
    
    # 5. EVENT SUPPORT / 6. SUPPORT MASK
    print("=== EVENT SUPPORT & MASK ===")
    for exp, ds_n, ds_i, ds_v in [('DA-CDF', ds_n_cdf, load_all(cdf_inv_dir, 'innovation'), load_all(cdf_var_dir, 'forecast_variance')),
                                  ('DA-NoCDF', ds_n_nocdf, load_all(nocdf_inv_dir, 'innovation'), load_all(nocdf_var_dir, 'forecast_variance'))]:
        print(f"\n{exp}:")
        if 'event_time' in ds_n and 'event_time' in ds_i and 'event_time' in ds_v:
            t_n = pd.DatetimeIndex(ds_n.event_time.values)
            t_i = pd.DatetimeIndex(ds_i.event_time.values)
            t_v = pd.DatetimeIndex(ds_v.event_time.values)
            print(f"  ninnov events: {len(t_n)}")
            print(f"  intersection: {len(t_n.intersection(t_i).intersection(t_v))}")
            print(f"  normalized-only: {len(t_n.difference(t_i))}")
            print(f"  innovation-only: {len(t_i.difference(t_n))}")
            print(f"  variance-only: {len(t_v.difference(t_n))}")
            
            # Mask
            common = t_n.intersection(t_i).intersection(t_v)
            v_n = ds_n.sel(event_time=common)['normalized_innovation'].values.flatten()
            v_i = ds_i.sel(event_time=common)['innovation'].values.flatten()
            v_v = ds_v.sel(event_time=common)['forecast_variance'].values.flatten()
            
            val_n = ~np.isnan(v_n)
            val_i = ~np.isnan(v_i)
            val_v = ~np.isnan(v_v)
            
            print(f"  mismatch ninnov vs innov: {np.sum(val_n != val_i)}")
            print(f"  mismatch ninnov vs var: {np.sum(val_n != val_v)}")
            
            print("\n  ZERO/MISSING SEMANTICS:")
            print(f"    Missing ninnov == missing innov: {np.all(val_n == val_i)}")
            zero_n = (v_n == 0) & val_n
            zero_i = (v_i == 0) & val_i
            print(f"    Zero ninnov == zero innov: {np.all(zero_n == zero_i)}")
            
            print("\n  CORRELATIONS:")
            mask = val_n & val_i & val_v
            a_n = np.abs(v_n[mask])
            a_i = np.abs(v_i[mask])
            a_v = v_v[mask]
            
            print(f"    corr(innov, ninnov): {pearsonr(v_i[mask], v_n[mask])[0]:.4f}")
            print(f"    corr(abs(innov), abs(ninnov)): {pearsonr(a_i, a_n)[0]:.4f}")
            print(f"    spearman(abs(ninnov), var): {spearmanr(a_n, a_v)[0]:.4f}")
            print(f"    spearman(abs(innov), var): {spearmanr(a_i, a_v)[0]:.4f}")
            
    
    # 13. STATISTICS
    print_stats(ds_n_cdf, 'DA-CDF')
    print_stats(ds_n_nocdf, 'DA-NoCDF')
    
    # RAW-TO-INTERIM (just read one raw file for 2016 for DA-CDF)
    raw_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output"
    if 'event_time' in ds_n_cdf:
        events = ds_n_cdf.sel(event_time=ds_n_cdf.event_time.dt.year == 2016).event_time.values[:3]
        for ev in events:
            dt = pd.to_datetime(ev)
            ts = dt.strftime('%Y%m%d%H%M')
            pattern = f"{raw_dir}/{dt.year}-*/EnKF/{dt.year}*/LIS_DA_EnKF_{ts}_innov.a01.d01.nc"
            files = glob.glob(pattern)
            if files:
                ds_r = xr.open_dataset(files[0])
                r_val = ds_r['ninnov_01'].values
                r_val = np.where(r_val == -9999.0, np.nan, r_val)
                i_val = ds_n_cdf.sel(event_time=ev)['normalized_innovation'].values
                
                mask = ~np.isnan(r_val) & ~np.isnan(i_val)
                diff = np.abs(r_val[mask] - i_val[mask])
                print(f"RAW-TO-INTERIM EVENT {ts}: max diff {np.max(diff) if len(diff)>0 else np.nan:.3e}, mean diff {np.mean(diff) if len(diff)>0 else np.nan:.3e}, mask mismatch {np.sum(np.isnan(r_val) != np.isnan(i_val))}")
                
    # 18. QUICKLOOKS
    v_cdf = ds_n_cdf['normalized_innovation'].values.flatten()
    v_cdf = v_cdf[~np.isnan(v_cdf)]
    v_nocdf = ds_n_nocdf['normalized_innovation'].values.flatten()
    v_nocdf = v_nocdf[~np.isnan(v_nocdf)]
    
    # A. DISTRIBUTION
    plt.figure(figsize=(10, 6))
    plt.hist(v_cdf, bins=100, range=(-5, 5), alpha=0.5, density=True, label='DA-CDF')
    plt.hist(v_nocdf, bins=100, range=(-5, 5), alpha=0.5, density=True, label='DA-NoCDF')
    for x in [-3, -2, -1, 0, 1, 2, 3]:
        plt.axvline(x, color='k', linestyle='--', alpha=0.3)
    plt.title('Normalized Innovation Distribution')
    plt.xlabel('Normalized Innovation')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'distribution.png'))
    plt.close()
    
    # B. TEMPORAL SUMMARY
    for exp, ds in [('cdf', ds_n_cdf), ('nocdf', ds_n_nocdf)]:
        n_val = ds['normalized_innovation'].values
        mean_val = np.nanmean(n_val, axis=(1, 2))
        median_val = np.nanmedian(n_val, axis=(1, 2))
        mean_abs_val = np.nanmean(np.abs(n_val), axis=(1, 2))
        count_val = np.sum(~np.isnan(n_val), axis=(1, 2))
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(ds.event_time.values, mean_val, label='Mean')
        ax1.plot(ds.event_time.values, median_val, label='Median')
        ax1.plot(ds.event_time.values, mean_abs_val, label='Mean Abs')
        ax1.set_ylabel('Normalized Innovation')
        ax2 = ax1.twinx()
        ax2.plot(ds.event_time.values, count_val, color='k', alpha=0.3, label='Valid Obs')
        ax2.set_ylabel('Valid Obs Count')
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper right')
        plt.title(f'Temporal Summary ({exp})')
        plt.savefig(os.path.join(out_dir, f'temporal_summary_{exp}.png'))
        plt.close()
        
    # C/D. REPRESENTATIVE EVENT MAPS
    extent = [ds_n_cdf.lon.values.min(), ds_n_cdf.lon.values.max(), ds_n_cdf.lat.values.min(), ds_n_cdf.lat.values.max()]
    if 'event_time' in ds_n_cdf:
        for idx in [500]:
            ev = ds_n_cdf.event_time.values[idx]
            data = ds_n_cdf.isel(event_time=idx)['normalized_innovation'].values
            
            plt.figure(figsize=(8, 6))
            plt.imshow(data, origin='lower', extent=extent, cmap='BrBG', vmin=-3, vmax=3)
            plt.colorbar(label='Normalized Innovation', extend='both')
            plt.title(f'DA-CDF Normalized Innovation {str(ev)[:13]}')
            plt.savefig(os.path.join(out_dir, f'event_map_{str(ev)[:13].replace("-","").replace("T","_")}.png'))
            plt.close()
            
    # E. EXCEEDANCE MAPS
    for exp, ds in [('cdf', ds_n_cdf), ('nocdf', ds_n_nocdf)]:
        val_mask = ~np.isnan(ds['normalized_innovation'].values)
        exc_2 = np.abs(ds['normalized_innovation'].values) > 2
        exc_3 = np.abs(ds['normalized_innovation'].values) > 3
        
        valid_counts = np.sum(val_mask, axis=0)
        frac_2 = np.where(valid_counts > 0, np.sum(exc_2 & val_mask, axis=0) / valid_counts, np.nan)
        frac_3 = np.where(valid_counts > 0, np.sum(exc_3 & val_mask, axis=0) / valid_counts, np.nan)
        
        plt.figure(figsize=(8, 6))
        plt.imshow(frac_2, origin='lower', extent=extent, cmap='Reds', vmin=0, vmax=0.1)
        plt.colorbar(label='Fraction')
        plt.title(f'Fraction of Assimilated Observations with |Normalized Innovation| > 2 ({exp})')
        plt.savefig(os.path.join(out_dir, f'exceedance_gt2_{exp}.png'))
        plt.close()

if __name__ == "__main__":
    main()
