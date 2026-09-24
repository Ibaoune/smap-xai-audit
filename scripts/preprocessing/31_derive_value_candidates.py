#!/usr/bin/env python3
"""
SMAP-XAI Audit: Derive Value Candidates
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import numpy as np
import xarray as xr
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
from smap_xai.preprocessing.value_metrics import (
    compute_value_ae, compute_value_se, compute_value_nae,
    compute_value_refnorm, compute_error_ratio, compute_log_error_ratio
)

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    years = [2016, 2017, 2018, 2019, 2020]
    
    out_dir = os.path.join(base_dir, "data/processed/value/candidates")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "da_cdf"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "da_nocdf"), exist_ok=True)
    
    ref_dir = os.path.join(base_dir, "data/processed/value/gleam/reference")
    model_dir = os.path.join(base_dir, "data/processed/value/gleam/model_et")
    
    # Load authoritative mask to ensure candidates only populate on valid cells
    final_common_mask = np.load(os.path.join(ref_dir, "final_common_mask.npy"))
    mask_day = final_common_mask[0]
    
    # Process by year to save memory
    t_start = 0
    for year in years:
        g_ds = xr.open_dataset(os.path.join(ref_dir, f"gleam_et_{year}.nc"))
        g_et = g_ds['et_reference'].values
        
        opl_ds = xr.open_dataset(os.path.join(model_dir, f"opl/et_on_gleam_{year}.nc"))
        opl_et = opl_ds['et'].values
        
        t_len = len(g_ds.time)
        mask_yr = final_common_mask[t_start:t_start+t_len]
        
        for exp in ['da_cdf', 'da_nocdf']:
            da_ds = xr.open_dataset(os.path.join(model_dir, f"{exp}/et_on_gleam_{year}.nc"))
            da_et = da_ds['et'].values
            
            # Mask data directly before computations to avoid infs on out-of-support
            g_safe = np.where(mask_yr, g_et, np.nan)
            opl_safe = np.where(mask_yr, opl_et, np.nan)
            da_safe = np.where(mask_yr, da_et, np.nan)
            
            # 1. value_ae
            val_ae = compute_value_ae(opl_safe, da_safe, g_safe)
            
            # 2. value_se
            val_se = compute_value_se(opl_safe, da_safe, g_safe)
            
            # 3. value_nae (test epsilon=1e-4 as primary)
            val_nae = compute_value_nae(opl_safe, da_safe, g_safe, epsilon=1e-4)
            
            # 4. value_refnorm (test epsilon_ref=0.05 as primary)
            val_refnorm = compute_value_refnorm(opl_safe, da_safe, g_safe, epsilon_ref=0.05)
            
            # 5. error_ratio and log_error_ratio
            ratio = compute_error_ratio(opl_safe, da_safe, g_safe, epsilon=1e-4)
            log_ratio = compute_log_error_ratio(opl_safe, da_safe, g_safe, epsilon=1e-4)
            
            # Create dataset
            ds_out = xr.Dataset(
                {
                    "value_ae": (["time", "lat", "lon"], val_ae),
                    "value_se": (["time", "lat", "lon"], val_se),
                    "value_nae": (["time", "lat", "lon"], val_nae),
                    "value_refnorm": (["time", "lat", "lon"], val_refnorm),
                    "error_ratio": (["time", "lat", "lon"], ratio),
                    "log_error_ratio": (["time", "lat", "lon"], log_ratio),
                },
                coords={
                    "time": g_ds.time,
                    "lat": g_ds.lat,
                    "lon": g_ds.lon,
                },
                attrs={"status": "candidate"}
            )
            ds_out.to_netcdf(os.path.join(out_dir, exp, f"candidates_{year}.nc"))
            
        t_start += t_len
        print(f"Processed {year}")

if __name__ == "__main__":
    main()
