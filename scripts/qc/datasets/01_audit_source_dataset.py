#!/usr/bin/env python3
"""
01_audit_source_dataset.py
Author: M. El Aabaribaoune
QC script for the generated SOURCE modeling datasets.
"""
import os
import sys
import glob
import numpy as np
import pandas as pd

def audit_experiment(exp):
    print("="*60)
    print(f"AUDITING {exp}")
    print("="*60)
    
    base_dir = f"data/processed/modeling/source/{exp}"
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found.")
        return
        
    parquet_files = glob.glob(f"{base_dir}/year=*/*.parquet")
    dfs = []
    for f in parquet_files:
        _d = pd.read_parquet(f)
        _d['year'] = _d['year'].astype(int)
        dfs.append(_d)
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\n--- Rows per year ---")
    print(df['year'].value_counts().sort_index())
    
    print("\n--- Data Size ---")
    total_size = 0
    for year in range(2016, 2021):
        year_dir = f"{base_dir}/year={year}"
        if os.path.exists(year_dir):
            size = sum(os.path.getsize(os.path.join(year_dir, f)) for f in os.listdir(year_dir) if os.path.isfile(os.path.join(year_dir, f)))
            total_size += size
            print(f"  {year}: {size / (1024*1024):.2f} MB")
    print(f"  Total size: {total_size / (1024*1024):.2f} MB")
    
    print("\n--- Duplicate Key Audit ---")
    dup_count = df.duplicated(subset=['date', 'y_index', 'x_index']).sum()
    print(f"Duplicate date+y_index+x_index: {dup_count}")
    
    print("\n--- Update-Support Validation ---")
    obs_freq_violations = (df['observation_frequency'] != 1).sum()
    inn_violations = (~np.isfinite(df['innovation'])).sum()
    print(f"observation_frequency != 1: {obs_freq_violations}")
    print(f"innovation not finite: {inn_violations}")
    
    print("\n--- Target (daily_absolute_increment) ---")
    t = df['daily_absolute_increment']
    print(f"Finite: {np.isfinite(t).sum()}, NaN: {t.isna().sum()}, Inf: {np.isinf(t).sum()}")
    print(f"min: {t.min():.6f}, max: {t.max():.6f}")
    print(f"mean: {t.mean():.6f}, median: {t.median():.6f}, std: {t.std():.6f}")
    q = t.quantile([0.01, 0.05, 0.25, 0.75, 0.95, 0.99])
    print(f"p01: {q[0.01]:.6f}, p05: {q[0.05]:.6f}, p25: {q[0.25]:.6f}, p75: {q[0.75]:.6f}, p95: {q[0.95]:.6f}, p99: {q[0.99]:.6f}")
    
    print("\n--- Secondary Target (daily_signed_increment) ---")
    s = df['daily_signed_increment']
    print(f"Positive: {(s > 0).mean()*100:.2f}%, Zero: {(s == 0).mean()*100:.2f}%, Negative: {(s < 0).mean()*100:.2f}%")
    
    print("\n--- Feature Variance & Missingness QC ---")
    features = [c for c in df.columns if c not in ['date', 'year', 'experiment', 'observation_frequency', 'lat', 'lon', 'y_index', 'x_index', 'daily_absolute_increment', 'daily_signed_increment']]
    
    for f in features:
        col = df[f]
        n_nan = col.isna().sum()
        n_fin = np.isfinite(col).sum()
        v_mean = col.mean()
        v_std = col.std()
        v_min = col.min()
        v_max = col.max()
        if 'fraction' in f or 'month' in f or 'day' in f or 'sin' in f or 'cos' in f:
            v_uniq = col.nunique()
        else:
            v_uniq = 'N/A'
            
        print(f"{f}:")
        print(f"  Missing: {n_nan}, Finite: {n_fin}, Mean: {v_mean:.4f}, Std: {v_std:.4f}, Min: {v_min:.4f}, Max: {v_max:.4f}, Unique: {v_uniq}")
        if v_std == 0:
            print("  >>> FLAG: ZERO VARIANCE")
        elif v_std < 1e-4:
            print("  >>> FLAG: NEAR-ZERO VARIANCE")
            
if __name__ == "__main__":
    for exp in ["da_cdf", "da_nocdf"]:
        audit_experiment(exp)
