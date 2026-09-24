#!/usr/bin/env python3
"""
Derive Delta RZSM

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily DA-minus-open-loop root-zone soil-moisture response target
(delta_rzsm) for DA-CDF and DA-NoCDF experiments over 2016-2020.

Sign convention:
- positive means DA wetter than OPL
- negative means DA drier than OPL

Input:
- canonical OPL RZSM
- canonical DA RZSM

Output:
- delta_rzsm (time, lat, lon)

Support:
- All valid model pixel-days (1827 days, 16030 valid land pixels).
- Difference from event increment: this is a daily state-difference response
  with temporal memory, not an instantaneous surface EnKF update.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def process_year(year, exp, opl_dir, da_dir, out_dir):
    opl_file = os.path.join(opl_dir, f'rzsm_{year}.nc')
    da_file = os.path.join(da_dir, f'rzsm_{year}.nc')
    out_file = os.path.join(out_dir, f'delta_rzsm_{year}.nc')
    
    print(f"Processing {exp} for {year}...")
    
    ds_opl = xr.open_dataset(opl_file)
    ds_da = xr.open_dataset(da_file)
    
    # 1. Grid / Time Identity
    np.testing.assert_array_equal(ds_opl.time.values, ds_da.time.values)
    np.testing.assert_array_equal(ds_opl.lat.values, ds_da.lat.values)
    np.testing.assert_array_equal(ds_opl.lon.values, ds_da.lon.values)
    
    max_lat_diff = np.max(np.abs(ds_da.lat.values - ds_opl.lat.values))
    max_lon_diff = np.max(np.abs(ds_da.lon.values - ds_opl.lon.values))
    if max_lat_diff > 0 or max_lon_diff > 0:
        raise ValueError(f"Coordinate mismatch! lat diff: {max_lat_diff}, lon diff: {max_lon_diff}")
    
    # 2. Mask Semantics
    # Expected valid land is inherently in the ds_opl/ds_da NaN mask
    rzsm_opl = ds_opl['rzsm'].values
    rzsm_da = ds_da['rzsm'].values
    
    missing_opl = np.isnan(rzsm_opl)
    missing_da = np.isnan(rzsm_da)
    
    if not np.array_equal(missing_opl, missing_da):
        raise ValueError("Valid support mismatch between OPL and DA RZSM!")
        
    delta_rzsm = (rzsm_da - rzsm_opl).astype(np.float32)
    delta_rzsm[missing_opl] = np.nan
    
    ds_out = xr.Dataset(
        {
            "delta_rzsm": (
                ("time", "lat", "lon"),
                delta_rzsm,
                {
                    "long_name": "Daily DA-minus-open-loop root-zone soil-moisture difference",
                    "units": "m3 m-3",
                    "definition": "RZSM_DA - RZSM_OPL",
                    "root_zone_depth": "0-100 cm",
                    "rzsm_definition": "0.10*Layer1 + 0.30*Layer2 + 0.60*Layer3",
                    "reference_experiment": "OPL_noirr_2016_2020",
                    "da_experiment": exp,
                    "temporal_support": "daily canonical model calendar",
                    "xai_role": "Transfer target",
                    "sign_convention": "positive means DA wetter than OPL"
                },
            )
        },
        coords={
            "time": ds_opl.time,
            "lat": ds_opl.lat,
            "lon": ds_opl.lon,
        },
    )
    
    ds_out.to_netcdf(out_file)
    print(f"Saved {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', nargs='+', type=int, default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    opl_rzsm_dir = "data/processed/daily_model/opl/rzsm"
    da_exps = {
        "da_cdf": "data/processed/daily_model/da_cdf/rzsm",
        "da_nocdf": "data/processed/daily_model/da_nocdf/rzsm"
    }
    
    for exp, da_dir in da_exps.items():
        out_dir = f"data/processed/transfer/{exp}/delta_rzsm"
        os.makedirs(out_dir, exist_ok=True)
        for year in args.years:
            process_year(year, exp, opl_rzsm_dir, da_dir, out_dir)
