#!/usr/bin/env python3
"""
SMAP-XAI Audit: Derive Canonical Value Target
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import numpy as np
import xarray as xr

sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
from smap_xai.preprocessing.value_metrics import compute_value_ae

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    years = [2016, 2017, 2018, 2019, 2020]
    
    out_dir = os.path.join(base_dir, "data/processed/value/value_ae")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "da_cdf"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "da_nocdf"), exist_ok=True)
    
    ref_dir = os.path.join(base_dir, "data/processed/value/gleam/reference")
    model_dir = os.path.join(base_dir, "data/processed/value/gleam/model_et")
    
    # Load authoritative mask
    final_common_mask = np.load(os.path.join(ref_dir, "final_common_mask.npy"))
    
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
            
            # Mask data directly before computations
            g_safe = np.where(mask_yr, g_et, np.nan)
            opl_safe = np.where(mask_yr, opl_et, np.nan)
            da_safe = np.where(mask_yr, da_et, np.nan)
            
            val_ae = compute_value_ae(opl_safe, da_safe, g_safe)
            
            ds_out = xr.Dataset(
                {
                    "value_ae": (["time", "lat", "lon"], val_ae),
                },
                coords={
                    "time": g_ds.time,
                    "lat": g_ds.lat,
                    "lon": g_ds.lon,
                },
                attrs={
                    "experiment": exp.upper().replace("_", "-"),
                    "definition": "|ET_OPL - ET_GLEAM| - |ET_DA - ET_GLEAM|",
                    "units": "mm/day",
                    "reference": "GLEAM v4.3a",
                    "positive_sign": "improved agreement relative to GLEAM",
                    "negative_sign": "degraded agreement relative to GLEAM",
                    "temporal_support": "daily"
                }
            )
            ds_out.to_netcdf(os.path.join(out_dir, exp, f"value_ae_{year}.nc"))
            
        t_start += t_len
        print(f"Processed {year}")

if __name__ == "__main__":
    main()
