#!/usr/bin/env python3
"""
03_audit_value_dataset.py
Author: M. El Aabaribaoune

Audits Block 3 — VALUE modeling datasets.
"""

__author__ = "M. El Aabaribaoune"

import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import yaml

def audit_value_dataset():
    print("==================================================")
    print("AUDITING VALUE DATASET")
    print("==================================================")
    
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    out_dir = f"{base_dir}/data/processed/modeling/value"
    
    exps = ['da_cdf', 'da_nocdf']
    
    total_size = {'da_cdf': 0, 'da_nocdf': 0}
    final_rows = {'da_cdf': 0, 'da_nocdf': 0}
    schema_cols = None
    
    dfs = {exp: [] for exp in exps}
    
    for exp in exps:
        print(f"\n--- AUDITING: {exp} ---")
        exp_dir = f"{out_dir}/{exp}"
        
        for year in range(2016, 2021):
            y_dir = f"{exp_dir}/year={year}"
            if not os.path.exists(y_dir): continue
            
            files = sorted(glob.glob(f"{y_dir}/*.parquet"))
            size_mb = sum([os.path.getsize(f) for f in files]) / (1024*1024)
            total_size[exp] += size_mb
            
            df_y = pd.read_parquet(y_dir)
            n_rows = len(df_y)
            final_rows[exp] += n_rows
            dfs[exp].append(df_y)
            
            print(f"Year {year}: {n_rows} rows, {len(files)} files, {size_mb:.2f} MB")
            
            if schema_cols is None:
                schema_cols = list(df_y.columns)
            else:
                assert list(df_y.columns) == schema_cols, "Schema mismatch!"
                
    df_cdf = pd.concat(dfs['da_cdf'], ignore_index=True)
    df_nocdf = pd.concat(dfs['da_nocdf'], ignore_index=True)
    
    print("\n--- SCHEMA CONSISTENCY ---")
    print("Schema consistent across all parts: True")
    print(f"Final column count: {len(schema_cols)}")
    
    print("\n--- SUPPORT AUDIT ---")
    raw_support = 4110 * 1827
    expected_modeling = 4110 * 1820
    print(f"Raw canonical target support: 4110 cells * 1827 days = {raw_support}")
    print(f"Expected modeling support: 4110 cells * 1820 days = {expected_modeling}")
    print(f"Rows removed due to 7-day history: {7 * 4110} (2016-01-01 through 2016-01-07)")
    print(f"Final rows (DA-CDF): {len(df_cdf)}")
    print(f"Final rows (DA-NoCDF): {len(df_nocdf)}")
    assert len(df_cdf) == expected_modeling, "Row count mismatch!"
    
    print("\n--- DUPLICATES / GRID AUDIT ---")
    dup_1 = df_cdf.duplicated(subset=['date', 'gleam_y_index', 'gleam_x_index']).sum()
    dup_2 = df_cdf.duplicated(subset=['date', 'lat', 'lon']).sum()
    print(f"Duplicates by (date, g_y, g_x): {dup_1}")
    print(f"Duplicates by (date, lat, lon): {dup_2}")
    
    map_size = df_cdf.groupby(['gleam_y_index', 'gleam_x_index']).size().reset_index()
    latlon_size = df_cdf.groupby(['lat', 'lon']).size().reset_index()
    print(f"Unique grid index pairs: {len(map_size)}")
    print(f"Unique lat/lon pairs: {len(latlon_size)}")
    assert len(map_size) == len(latlon_size) == 4110, "Mapping is not 1-to-1!"
    
    # check support equality
    cdf_keys = df_cdf[['date', 'gleam_y_index', 'gleam_x_index']].sort_values(['date', 'gleam_y_index', 'gleam_x_index']).reset_index(drop=True)
    nocdf_keys = df_nocdf[['date', 'gleam_y_index', 'gleam_x_index']].sort_values(['date', 'gleam_y_index', 'gleam_x_index']).reset_index(drop=True)
    assert cdf_keys.equals(nocdf_keys), "Support mismatch between CDF and NoCDF!"
    print("Exact same date/cell support in CDF and NoCDF: True")
    
    print("\n--- HIGH-LAND-COVERAGE SUPPORT AUDIT ---")
    n_primary = 4110
    high_land = df_cdf[df_cdf['high_land_coverage'] == 1]
    n_high = len(high_land.groupby(['gleam_y_index', 'gleam_x_index']))
    print(f"Number of primary cells: {n_primary}")
    print(f"Number of high-land-coverage cells: {n_high}")
    print(f"Rows in primary support: {len(df_cdf)}")
    print(f"Rows in high-land support: {len(high_land)}")
    
    print("\n--- MISSINGNESS ---")
    missing = df_cdf.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) == 0:
        print("No missing values (NaN/Inf) in the dataset.")
    else:
        print("Missing values found:")
        print(missing)
        
    print("\n--- ZERO-VARIANCE AUDIT ---")
    numeric_cols_cdf = df_cdf.select_dtypes(include=[np.number])
    zv_cdf = numeric_cols_cdf.columns[numeric_cols_cdf.std() == 0].tolist()
    
    numeric_cols_nocdf = df_nocdf.select_dtypes(include=[np.number])
    zv_nocdf = numeric_cols_nocdf.columns[numeric_cols_nocdf.std() == 0].tolist()
    zv_common = sorted(list(set(zv_cdf) & set(zv_nocdf)))
    print(f"DA-CDF zero-variance columns: {zv_cdf}")
    print(f"DA-NoCDF zero-variance columns: {zv_nocdf}")
    print(f"Common zero-variance columns: {zv_common}")
    
    # Update yaml
    yaml_path = f"{base_dir}/configs/datasets/value.yaml"
    with open(yaml_path, 'r') as f:
        cfg = yaml.safe_load(f)
    cfg['zero_variance_on_value_support']['features'] = zv_common
    with open(yaml_path, 'w') as f:
        yaml.dump(cfg, f, sort_keys=False)
        
    def print_stats(arr, name):
        n = len(arr)
        print(f"  N: {n}")
        print(f"  Min: {np.min(arr):.6f}")
        print(f"  Max: {np.max(arr):.6f}")
        print(f"  Mean: {np.mean(arr):.6f}")
        print(f"  Median: {np.median(arr):.6f}")
        print(f"  Std: {np.std(arr):.6f}")
        print(f"  p01: {np.percentile(arr, 1):.6f}")
        print(f"  p05: {np.percentile(arr, 5):.6f}")
        print(f"  p25: {np.percentile(arr, 25):.6f}")
        print(f"  p75: {np.percentile(arr, 75):.6f}")
        print(f"  p95: {np.percentile(arr, 95):.6f}")
        print(f"  p99: {np.percentile(arr, 99):.6f}")
        neg = np.sum(arr < 0)
        zero = np.sum(arr == 0)
        pos = np.sum(arr > 0)
        print(f"  Negative: {neg} ({neg/n*100:.2f}%)")
        print(f"  Exact Zero: {zero} ({zero/n*100:.2f}%)")
        print(f"  Positive: {pos} ({pos/n*100:.2f}%)")
        
    print("\n--- TARGET DISTRIBUTION QC ---")
    print("\nTarget: value_ae (DA-CDF)")
    print_stats(df_cdf['value_ae'].values, 'value_ae')
    
    print("\nTarget: value_ae (DA-NoCDF)")
    print_stats(df_nocdf['value_ae'].values, 'value_ae')
    
    print("\n--- HIGH-LAND-COVERAGE TARGET SENSITIVITY ---")
    print("\nTarget: value_ae (DA-CDF, High-Land)")
    hl_cdf = df_cdf[df_cdf['high_land_coverage'] == 1]['value_ae'].values
    print(f"  N: {len(hl_cdf)}")
    print(f"  Mean: {np.mean(hl_cdf):.6f}, Median: {np.median(hl_cdf):.6f}, Std: {np.std(hl_cdf):.6f}")
    print(f"  Positive: {np.sum(hl_cdf>0)/len(hl_cdf)*100:.2f}%")
    print(f"  Negative: {np.sum(hl_cdf<0)/len(hl_cdf)*100:.2f}%")
    
    print("\n--- FINITE-INNOVATION SUPPORT STRATIFICATION ---")
    print("\nTarget: value_ae (DA-CDF)")
    mask_0_cdf = df_cdf['finite_innovation_fraction_t'] == 0
    v0_cdf = df_cdf[mask_0_cdf]['value_ae'].values
    v1_cdf = df_cdf[~mask_0_cdf]['value_ae'].values
    
    print(f"  finite_innovation_fraction_t == 0 (N={len(v0_cdf)}):")
    print(f"    Mean: {np.mean(v0_cdf):.6f}, Median: {np.median(v0_cdf):.6f}")
    print(f"    Mean Abs: {np.mean(np.abs(v0_cdf)):.6f}")
    print(f"    p05: {np.percentile(v0_cdf, 5):.6f}, p95: {np.percentile(v0_cdf, 95):.6f}")
    print(f"    Positive: {np.sum(v0_cdf>0)/len(v0_cdf)*100:.2f}%")
    print(f"    Negative: {np.sum(v0_cdf<0)/len(v0_cdf)*100:.2f}%")
    
    print(f"  finite_innovation_fraction_t > 0 (N={len(v1_cdf)}):")
    print(f"    Mean: {np.mean(v1_cdf):.6f}, Median: {np.median(v1_cdf):.6f}")
    print(f"    Mean Abs: {np.mean(np.abs(v1_cdf)):.6f}")
    print(f"    p05: {np.percentile(v1_cdf, 5):.6f}, p95: {np.percentile(v1_cdf, 95):.6f}")
    print(f"    Positive: {np.sum(v1_cdf>0)/len(v1_cdf)*100:.2f}%")
    print(f"    Negative: {np.sum(v1_cdf<0)/len(v1_cdf)*100:.2f}%")
    
    print("\n--- FORCING-CONTROL QC ---")
    diff_t = np.abs(df_cdf['delta_precip_forcing_t'].values - df_nocdf['delta_precip_forcing_t'].values)
    diff_3d = np.abs(df_cdf['delta_precip_forcing_pre3d_sum'].values - df_nocdf['delta_precip_forcing_pre3d_sum'].values)
    diff_7d = np.abs(df_cdf['delta_precip_forcing_pre7d_sum'].values - df_nocdf['delta_precip_forcing_pre7d_sum'].values)
    print(f"Max absolute CDF-NoCDF difference (delta_precip_forcing_t): {np.max(diff_t)}")
    print(f"Max absolute CDF-NoCDF difference (pre3d_sum): {np.max(diff_3d)}")
    print(f"Max absolute CDF-NoCDF difference (pre7d_sum): {np.max(diff_7d)}")
    
    print("\n--- SOURCE SUPPORT QC ---")
    def print_frac_stats(arr, name):
        n = len(arr)
        print(f"\n{name}:")
        print(f"  min: {np.min(arr):.6f}")
        print(f"  max: {np.max(arr):.6f}")
        print(f"  mean: {np.mean(arr):.6f}")
        print(f"  median: {np.median(arr):.6f}")
        print(f"  p05: {np.percentile(arr, 5):.6f}")
        print(f"  p95: {np.percentile(arr, 95):.6f}")
        print(f"  fraction exactly zero: {np.sum(arr==0)/n:.4f}")
        print(f"  fraction > 0: {np.sum(arr>0)/n:.4f}")
        
    print_frac_stats(df_cdf['finite_innovation_fraction_t'].values, "DA-CDF finite_innovation_fraction_t")
    print_frac_stats(df_nocdf['finite_innovation_fraction_t'].values, "DA-NoCDF finite_innovation_fraction_t")
    
    print("\n--- TRANSFER-INFORMED FEATURES QC ---")
    print("delta_rzsm_t missing:", df_cdf['delta_rzsm_t'].isnull().sum())
    print("delta_et_t missing:", df_cdf['delta_et_t'].isnull().sum())
    
    print("\n--- LEAKAGE SCHEMA AUDIT ---")
    forbidden = ['et_gleam', 'et_opl_t', 'et_da_t', 'error_opl', 'error_da', 
                 'value_se', 'value_nae', 'value_refnorm', 'ratio', 'log_ratio']
    
    found = []
    for f in forbidden:
        for c in schema_cols:
            if f in c.lower():
                found.append(f"{f} in {c}")
    
    for c in schema_cols:
        if 'gleam' in c.lower() and c not in ['gleam_x_index', 'gleam_y_index']:
            found.append(f"gleam in {c}")
    assert len(found) == 0, "Leakage fields detected!"
    
    print("\n--- TARGET IDENTITY ---")
    ds_val = xr.open_dataset(f"{base_dir}/data/processed/value/value_ae/da_cdf/value_ae_2016.nc")
    c_val = ds_val['value_ae'].values
    
    fast_map_gi = df_cdf.loc[(df_cdf['year']==2016) & (df_cdf['date'] == pd.Timestamp('2016-01-08'))]['gleam_y_index'].values
    fast_map_gj = df_cdf.loc[(df_cdf['year']==2016) & (df_cdf['date'] == pd.Timestamp('2016-01-08'))]['gleam_x_index'].values
    
    # Just check 2016-01-08
    raw_slice = c_val[7, fast_map_gi, fast_map_gj]
    df_slice = df_cdf.loc[(df_cdf['year']==2016) & (df_cdf['date'] == pd.Timestamp('2016-01-08'))]['value_ae'].values
    max_err = np.max(np.abs(raw_slice - df_slice))
    print(f"Maximum absolute error on 2016-01-08 slice: {max_err}")
    
    print("\n--- FORMULA RECONSTRUCTION QC ---")
    # |ET_OPL - ET_GLEAM| - |ET_DA - ET_GLEAM|
    ds_o = xr.open_dataset(f"{base_dir}/data/processed/value/gleam/model_et/opl/et_on_gleam_2016.nc")
    ds_c = xr.open_dataset(f"{base_dir}/data/processed/value/gleam/model_et/da_cdf/et_on_gleam_2016.nc")
    ds_g = xr.open_dataset(f"{base_dir}/data/processed/value/gleam/reference/gleam_et_2016.nc")
    
    et_opl = ds_o['et'].values[7, fast_map_gi, fast_map_gj]
    et_da = ds_c['et'].values[7, fast_map_gi, fast_map_gj]
    et_gleam = ds_g['et_reference'].values[7, fast_map_gi, fast_map_gj]
    
    recon_value = np.abs(et_opl - et_gleam) - np.abs(et_da - et_gleam)
    recon_err = np.max(np.abs(recon_value - df_slice))
    print(f"Maximum value_ae formula reconstruction error (2016-01-08): {recon_err}")

if __name__ == "__main__":
    audit_value_dataset()
