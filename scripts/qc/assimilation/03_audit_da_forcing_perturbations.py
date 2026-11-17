"""
**Author:** M. El Aabaribaoune
Audit script for DA forcing perturbations (precipitation).
"""
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import pearsonr, spearmanr

def audit_forcing_perturbations():
    print("="*60)
    print("AUDITING DA FORCING PERTURBATIONS (2016-2020)")
    print("="*60)
    
    da_base_cdf = "data/interim/noahmp/da_cdf/delta_precip_forcing"
    da_base_nocdf = "data/interim/noahmp/da_nocdf/delta_precip_forcing"
    
    ds_ssm_ref = xr.open_dataset("data/interim/noahmp/da_cdf/ssm/ssm_2016.nc")
    valid_mask = np.isfinite(ds_ssm_ref['ssm'].isel(time=0).values)
    y_idx, x_idx = np.where(valid_mask)
    n_valid = len(y_idx)
    
    dp_cdf_list = []
    dp_nocdf_list = []
    dates_list = []
    
    for y in range(2016, 2021):
        ds_c = xr.open_dataset(f"{da_base_cdf}/delta_precip_forcing_{y}.nc")
        ds_nc = xr.open_dataset(f"{da_base_nocdf}/delta_precip_forcing_{y}.nc")
        
        arr_c = ds_c['delta_precip_forcing'].values
        arr_nc = ds_nc['delta_precip_forcing'].values
        
        for i, d in enumerate(ds_c.time.values):
            dates_list.append(d)
            dp_cdf_list.append(arr_c[i, y_idx, x_idx])
            dp_nocdf_list.append(arr_nc[i, y_idx, x_idx])
            
    dp_cdf = np.concatenate(dp_cdf_list)
    dp_nocdf = np.concatenate(dp_nocdf_list)
    
    def report_stats(arr, name):
        arr_clean = arr[~np.isnan(arr)]
        n = len(arr_clean)
        exact_zero = (arr_clean == 0).sum()
        print(f"\nStats for {name}:")
        print(f"  N: {n}")
        print(f"  min: {np.min(arr_clean):.6e}")
        print(f"  max: {np.max(arr_clean):.6e}")
        print(f"  mean: {np.mean(arr_clean):.6e}")
        print(f"  median: {np.median(arr_clean):.6e}")
        print(f"  std: {np.std(arr_clean):.6e}")
        print(f"  p01: {np.percentile(arr_clean, 1):.6e}")
        print(f"  p05: {np.percentile(arr_clean, 5):.6e}")
        print(f"  p95: {np.percentile(arr_clean, 95):.6e}")
        print(f"  p99: {np.percentile(arr_clean, 99):.6e}")
        print(f"  exact-zero fraction: {exact_zero/n:.4f}")
        print(f"  non-zero fraction: {1 - exact_zero/n:.4f}")
        
    report_stats(dp_cdf, "DA-CDF delta_precip_forcing")
    report_stats(dp_nocdf, "DA-NoCDF delta_precip_forcing")
    
    print("\n--- CDF vs NoCDF FORCING IDENTITY ---")
    diff = dp_cdf - dp_nocdf
    max_abs_diff = np.nanmax(np.abs(diff))
    print(f"max_abs(delta_precip_forcing_CDF - delta_precip_forcing_NoCDF) = {max_abs_diff:.6e}")
    
    print("\n--- RECOMPUTE TARGET ASSOCIATIONS ---")
    dates_full = np.repeat(dates_list, n_valid)
    y_full = np.tile(y_idx, len(dates_list))
    x_full = np.tile(x_idx, len(dates_list))
    
    df_raw_cdf = pd.DataFrame({'date': dates_full, 'y_index': y_full, 'x_index': x_full, 'delta_precip': dp_cdf})
    df_raw_nocdf = pd.DataFrame({'date': dates_full, 'y_index': y_full, 'x_index': x_full, 'delta_precip': dp_nocdf})
    
    def load_targets(exp):
        df_list = []
        for y in range(2016, 2021):
            df = pd.read_parquet(f"data/processed/modeling/transfer/{exp}/year={y}")
            df_list.append(df[['date', 'y_index', 'x_index', 'delta_rzsm', 'delta_et', 'delta_surface_runoff', 'delta_baseflow']])
        return pd.concat(df_list, ignore_index=True)
        
    print("Loading canonical targets...")
    df_cdf = load_targets('da_cdf')
    df_nocdf = load_targets('da_nocdf')
    
    # Merge and calculate
    df_merged_cdf = pd.merge(df_cdf, df_raw_cdf, on=['date', 'y_index', 'x_index'], how='inner')
    df_merged_nocdf = pd.merge(df_nocdf, df_raw_nocdf, on=['date', 'y_index', 'x_index'], how='inner')
    
    targets = ['delta_rzsm', 'delta_et', 'delta_surface_runoff', 'delta_baseflow']
    
    def rel(df_merged, name):
        df_clean = df_merged.dropna()
        print(f"\n{name} delta_precip_forcing_t vs targets (N={len(df_clean)}):")
        dp = df_clean['delta_precip'].values
        for t in targets:
            pr, _ = pearsonr(dp, df_clean[t].values)
            sp, _ = spearmanr(dp, df_clean[t].values)
            print(f"  {t:25} Pearson: {pr:+.4f}, Spearman: {sp:+.4f}")
            
    rel(df_merged_cdf, "DA-CDF")
    rel(df_merged_nocdf, "DA-NoCDF")

if __name__ == "__main__":
    audit_forcing_perturbations()
