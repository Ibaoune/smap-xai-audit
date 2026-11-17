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
    return xr.concat([xr.open_dataset(f) for f in files], dim='event_time')

def print_stats(v, name):
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

def process_exp(exp, ds_res, ds_inv, ds_ninnov, ds_var, ds_inc):
    print(f"\n================ {exp} ================")
    
    # Support
    t_r = pd.DatetimeIndex(ds_res.event_time.values)
    t_i = pd.DatetimeIndex(ds_inv.event_time.values)
    t_inc = pd.DatetimeIndex(ds_inc.event_time.values) if 'event_time' in ds_inc else t_r
    
    common = t_r.intersection(t_i).intersection(t_inc)
    print(f"Events (residual): {len(t_r)}")
    print(f"Intersection: {len(common)}")
    print(f"Residual-only: {len(t_r.difference(t_i))}")
    print(f"Innovation-only: {len(t_i.difference(t_r))}")
    print(f"Increment-only: {len(t_inc.difference(t_r)) if 'event_time' in ds_inc else 0}")
    
    # Arrays
    res = ds_res.sel(event_time=common)['analysis_residual'].values.flatten()
    inv = ds_inv.sel(event_time=common)['innovation'].values.flatten()
    if 'event_time' in ds_inc:
        inc = ds_inc.sel(event_time=common)['increment_signed'].values.flatten()
    else:
        inc = np.full_like(res, np.nan)
        
    ninnov = ds_ninnov.sel(event_time=common)['normalized_innovation'].values.flatten()
    
    val_r = ~np.isnan(res)
    val_i = ~np.isnan(inv)
    
    print(f"\nSupport Mismatch (residual vs innov): {np.sum(val_r != val_i)}")
    
    mask = val_r & val_i
    v_res = res[mask]
    v_inv = inv[mask]
    v_inc = inc[mask]
    v_ninnov = ninnov[mask]
    
    # Stats
    print_stats(v_res, "Analysis Residual")
    
    # Before vs After
    a_inv = np.abs(v_inv)
    a_res = np.abs(v_res)
    print("\nBefore vs After Assimilation Mismatch:")
    print(f"  mean |innovation|: {np.mean(a_inv):.6f}")
    print(f"  median |innovation|: {np.median(a_inv):.6f}")
    print(f"  mean |residual|: {np.mean(a_res):.6f}")
    print(f"  median |residual|: {np.median(a_res):.6f}")
    
    atol = 1e-7
    print(f"  |res| < |inv|: {np.sum(a_res < a_inv - atol) / len(v_res):.6f}")
    print(f"  |res| == |inv|: {np.sum(np.abs(a_res - a_inv) <= atol) / len(v_res):.6f}")
    print(f"  |res| > |inv|: {np.sum(a_res > a_inv + atol) / len(v_res):.6f}")
    
    mismatch_reduction = a_inv - a_res
    print("\nMismatch Reduction (|innov| - |res|):")
    print(f"  mean: {np.mean(mismatch_reduction):.6f}")
    print(f"  median: {np.median(mismatch_reduction):.6f}")
    print(f"  p05: {np.percentile(mismatch_reduction, 5):.6f}")
    print(f"  p95: {np.percentile(mismatch_reduction, 95):.6f}")
    print(f"  > 0 (reduced): {np.sum(mismatch_reduction > 0) / len(mismatch_reduction):.6f}")
    
    # Relation to signed increment
    if 'event_time' in ds_inc:
        expected_res = v_inv - v_inc
        diff = np.abs(expected_res - v_res)
        print("\nTest Relation to Signed Increment (res = innov - inc):")
        print(f"  max abs error: {np.max(diff):.3e}")
        print(f"  mean abs error: {np.mean(diff):.3e}")
        print(f"  RMSE: {np.sqrt(np.mean(diff**2)):.3e}")
        
    # Effective observation-space update
    obs_update = v_inv - v_res
    print("\nEffective observation-space update (innov - res):")
    print(f"  min: {np.min(obs_update):.6f}")
    print(f"  max: {np.max(obs_update):.6f}")
    print(f"  mean: {np.mean(obs_update):.6f}")
    print(f"  median: {np.median(obs_update):.6f}")
    
    # Correlations
    print("\nInnovation-Residual Relationship:")
    print(f"  Pearson: {pearsonr(v_inv, v_res)[0]:.4f}")
    print(f"  Spearman: {spearmanr(v_inv, v_res)[0]:.4f}")
    print(f"  Pearson (|inv| vs |res|): {pearsonr(a_inv, a_res)[0]:.4f}")
    
    # Normalized context
    print("\nNormalized Context:")
    for name, m in [('|ninnov| < 1', np.abs(v_ninnov) < 1), 
                    ('1 <= |ninnov| < 2', (np.abs(v_ninnov) >= 1) & (np.abs(v_ninnov) < 2)),
                    ('|ninnov| >= 2', np.abs(v_ninnov) >= 2)]:
        if np.sum(m) > 0:
            print(f"  {name}:")
            print(f"    mean |innov|: {np.mean(a_inv[m]):.6f}")
            print(f"    mean |res|: {np.mean(a_res[m]):.6f}")
            print(f"    median mismatch reduction: {np.median(mismatch_reduction[m]):.6f}")

def main():
    out_dir = "reports/qc/analysis_residual"
    os.makedirs(out_dir, exist_ok=True)
    
    ds_res_cdf = load_all("data/interim/enkf/da_cdf/analysis_residual", "analysis_residual")
    ds_inv_cdf = load_all("data/interim/enkf/da_cdf/innovation", "innovation")
    ds_ninnov_cdf = load_all("data/interim/enkf/da_cdf/normalized_innovation", "normalized_innovation")
    ds_var_cdf = load_all("data/interim/enkf/da_cdf/forecast_variance", "forecast_variance")
    ds_inc_cdf = load_all("data/interim/enkf/da_cdf/increment_signed", "increment_signed")
    
    ds_res_nocdf = load_all("data/interim/enkf/da_nocdf/analysis_residual", "analysis_residual")
    ds_inv_nocdf = load_all("data/interim/enkf/da_nocdf/innovation", "innovation")
    ds_ninnov_nocdf = load_all("data/interim/enkf/da_nocdf/normalized_innovation", "normalized_innovation")
    ds_var_nocdf = load_all("data/interim/enkf/da_nocdf/forecast_variance", "forecast_variance")
    ds_inc_nocdf = load_all("data/interim/enkf/da_nocdf/increment_signed", "increment_signed")
    
    process_exp('DA-CDF', ds_res_cdf, ds_inv_cdf, ds_ninnov_cdf, ds_var_cdf, ds_inc_cdf)
    process_exp('DA-NoCDF', ds_res_nocdf, ds_inv_nocdf, ds_ninnov_nocdf, ds_var_nocdf, ds_inc_nocdf)
    
    print("\n================ RAW-TO-INTERIM ================")
    raw_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output"
    if 'event_time' in ds_res_cdf:
        events = ds_res_cdf.sel(event_time=ds_res_cdf.event_time.dt.year == 2016).event_time.values
        sample_events = [events[10], events[400], events[-10]]
        for ev in sample_events:
            dt = pd.to_datetime(ev)
            ts = dt.strftime('%Y%m%d%H%M')
            pattern = f"{raw_dir}/{dt.year}-*/EnKF/{dt.year}*/LIS_DA_EnKF_{ts}_innov.a01.d01.nc"
            files = glob.glob(pattern)
            if files:
                ds_r = xr.open_dataset(files[0])
                r_val = ds_r['analysis_residual_01'].values
                r_val = np.where(r_val == -9999.0, np.nan, r_val)
                i_val = ds_res_cdf.sel(event_time=ev)['analysis_residual'].values
                
                mask = ~np.isnan(r_val) & ~np.isnan(i_val)
                diff = np.abs(r_val[mask] - i_val[mask])
                print(f"EVENT {ts}: max diff {np.max(diff) if len(diff)>0 else np.nan:.3e}, mean diff {np.mean(diff) if len(diff)>0 else np.nan:.3e}, mask mismatch {np.sum(np.isnan(r_val) != np.isnan(i_val))}")
                
    # 20. QUICKLOOKS
    v_cdf = ds_res_cdf['analysis_residual'].values.flatten()
    v_cdf = v_cdf[~np.isnan(v_cdf)]
    v_nocdf = ds_res_nocdf['analysis_residual'].values.flatten()
    v_nocdf = v_nocdf[~np.isnan(v_nocdf)]
    
    # A. DISTRIBUTION
    plt.figure(figsize=(10, 6))
    p99 = max(np.percentile(np.abs(v_cdf), 99), np.percentile(np.abs(v_nocdf), 99))
    plt.hist(v_cdf, bins=100, range=(-p99, p99), alpha=0.5, density=True, label='DA-CDF')
    plt.hist(v_nocdf, bins=100, range=(-p99, p99), alpha=0.5, density=True, label='DA-NoCDF')
    plt.title('Analysis Residual Distribution')
    plt.xlabel('Analysis Residual (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'distribution.png'))
    plt.close()
    
    # B. INNOVATION VS RESIDUAL
    for exp, ds_r, ds_i in [('DA-CDF', ds_res_cdf, ds_inv_cdf), ('DA-NoCDF', ds_res_nocdf, ds_inv_nocdf)]:
        common = np.intersect1d(ds_r.event_time.values, ds_i.event_time.values)
        inv = ds_i.sel(event_time=common)['innovation'].values.flatten()
        res = ds_r.sel(event_time=common)['analysis_residual'].values.flatten()
        mask = ~np.isnan(inv) & ~np.isnan(res)
        
        plt.figure(figsize=(8, 8))
        plt.hexbin(inv[mask], res[mask], gridsize=50, cmap='viridis', mincnt=1)
        plt.colorbar(label='Count')
        lims = [
            np.min([plt.xlim(), plt.ylim()]),
            np.max([plt.xlim(), plt.ylim()]),
        ]
        plt.plot(lims, lims, 'k--', alpha=0.75, zorder=0, label='No observation-space correction')
        plt.xlim(lims)
        plt.ylim(lims)
        plt.title(f'Innovation vs Analysis Residual ({exp})')
        plt.xlabel('Innovation (m3 m-3)')
        plt.ylabel('Analysis Residual (m3 m-3)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(out_dir, f'scatter_{exp.lower().replace("-", "_")}.png'))
        plt.close()

    # C. BEFORE / AFTER ABSOLUTE MISMATCH
    plt.figure(figsize=(10, 6))
    for exp, ds_r, ds_i in [('DA-CDF', ds_res_cdf, ds_inv_cdf), ('DA-NoCDF', ds_res_nocdf, ds_inv_nocdf)]:
        common = np.intersect1d(ds_r.event_time.values, ds_i.event_time.values)
        inv = np.abs(ds_i.sel(event_time=common)['innovation'].values.flatten())
        res = np.abs(ds_r.sel(event_time=common)['analysis_residual'].values.flatten())
        mask = ~np.isnan(inv) & ~np.isnan(res)
        
        plt.hist(inv[mask], bins=100, range=(0, p99), alpha=0.3, density=True, label=f'{exp} |Innov|')
        plt.hist(res[mask], bins=100, range=(0, p99), alpha=0.3, density=True, label=f'{exp} |Resid|')
    plt.title('Absolute Mismatch: Before vs After Assimilation')
    plt.xlabel('|Mismatch| (m3 m-3)')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'abs_mismatch_distributions.png'))
    plt.close()
    
    # D. TEMPORAL SUMMARY
    for exp, ds in [('cdf', ds_res_cdf), ('nocdf', ds_res_nocdf)]:
        val = ds['analysis_residual'].values
        mean_val = np.nanmean(val, axis=(1, 2))
        median_val = np.nanmedian(val, axis=(1, 2))
        mean_abs = np.nanmean(np.abs(val), axis=(1, 2))
        count = np.sum(~np.isnan(val), axis=(1, 2))
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(ds.event_time.values, mean_val, label='Mean signed')
        ax1.plot(ds.event_time.values, median_val, label='Median signed')
        ax1.plot(ds.event_time.values, mean_abs, label='Mean absolute')
        ax1.set_ylabel('Analysis Residual (m3 m-3)')
        ax2 = ax1.twinx()
        ax2.plot(ds.event_time.values, count, color='k', alpha=0.3, label='Valid Obs')
        ax2.set_ylabel('Valid Obs Count')
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper right')
        plt.title(f'Temporal Summary ({exp})')
        plt.savefig(os.path.join(out_dir, f'temporal_summary_{exp}.png'))
        plt.close()

    # E. REPRESENTATIVE EVENT MAPS
    extent = [ds_res_cdf.lon.values.min(), ds_res_cdf.lon.values.max(), ds_res_cdf.lat.values.min(), ds_res_cdf.lat.values.max()]
    if 'event_time' in ds_res_cdf:
        valid_counts = np.sum(~np.isnan(ds_res_cdf['analysis_residual'].values), axis=(1,2))
        best_idx = np.argmax(valid_counts)
        for idx in [500, best_idx]:
            ev = ds_res_cdf.event_time.values[idx]
            data = ds_res_cdf.isel(event_time=idx)['analysis_residual'].values
            
            plt.figure(figsize=(8, 6))
            vmax = np.nanpercentile(np.abs(data), 98)
            plt.imshow(data, origin='lower', extent=extent, cmap='BrBG', vmin=-vmax, vmax=vmax)
            plt.colorbar(label='Analysis Residual (m3 m-3)', extend='both')
            plt.title(f'DA-CDF Analysis Residual {str(ev)[:13]}')
            plt.savefig(os.path.join(out_dir, f'event_map_{str(ev)[:13].replace("-","").replace("T","_")}.png'))
            plt.close()
            
    # F. MISMATCH-REDUCTION MAP
    for exp, ds_r, ds_i in [('cdf', ds_res_cdf, ds_inv_cdf), ('nocdf', ds_res_nocdf, ds_inv_nocdf)]:
        inv = np.abs(ds_i['innovation'].values)
        res = np.abs(ds_r['analysis_residual'].values)
        
        reduced = (inv - res) > 1e-7
        val_mask = ~np.isnan(inv) & ~np.isnan(res)
        
        valid_counts = np.sum(val_mask, axis=0)
        frac = np.where(valid_counts > 0, np.sum(reduced & val_mask, axis=0) / valid_counts, np.nan)
        
        plt.figure(figsize=(8, 6))
        plt.imshow(frac, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1)
        plt.colorbar(label='Fraction')
        plt.title(f'Fraction of Assimilated Observations with Reduced\nObservation-Space Mismatch ({exp})')
        plt.savefig(os.path.join(out_dir, f'mismatch_reduction_map_{exp}.png'))
        plt.close()

if __name__ == "__main__":
    main()
