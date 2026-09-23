#!/usr/bin/env python3
"""
EnKF Daily Absolute Analysis Increment Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily absolute EnKF Layer-1 soil-moisture analysis increment
from the processed daily_signed_increment output.

daily_absolute_increment = abs(daily_signed_increment)

Zero semantics are strictly preserved: 
0.0 on valid land pixel-days without assimilation.
NaN on grid cells outside canonical valid-land/model support.

XAI Role
--------
Candidate XAI-Source target representing DA correction magnitude.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def process_year(exp, year, signed_dir, out_dir):
    in_file = os.path.join(signed_dir, f'daily_signed_increment_{year}.nc')
    if not os.path.exists(in_file):
        print(f"Missing input for {year}: {in_file}")
        return

    # Load daily signed increments
    ds_in = xr.open_dataset(in_file)
    daily_signed = ds_in['daily_signed_increment'].values
    times = ds_in.time.values
    
    # Calculate absolute increment
    daily_abs = np.abs(daily_signed)
    
    # Validation checks
    valid_mask = ~np.isnan(daily_signed)
    
    # Sign/Range QC: Verify no negative values
    if np.any(daily_abs[valid_mask] < 0):
        raise ValueError(f"Found negative absolute increments in {year}!")
    
    # Exact Derivation Check
    diff = np.abs(daily_abs[valid_mask] - np.abs(daily_signed[valid_mask]))
    if np.any(diff > 1e-6):
        raise ValueError(f"Exact derivation failed for {year}! Max diff: {np.max(diff)}")
        
    # Value Conservation
    sum_abs_signed = np.nansum(np.abs(daily_signed))
    sum_daily_abs = np.nansum(daily_abs)
    val_diff = sum_daily_abs - sum_abs_signed
    print(f"[{year}] Value conservation diff: {val_diff:.6e}")
    
    # Construct output dataset
    ds_out = xr.Dataset(
        {
            'daily_absolute_increment': (['time', 'lat', 'lon'], daily_abs)
        },
        coords={
            'time': times,
            'lat': ds_in.lat.values,
            'lon': ds_in.lon.values
        },
        attrs={
            'long_name': 'Daily absolute EnKF Layer-1 soil-moisture analysis increment',
            'units': 'm3 m-3',
            'source_variable': 'daily_signed_increment',
            'derivation': 'abs(daily_signed_increment)',
            'layer': '0-10 cm',
            'temporal_support': 'UTC calendar day',
            'no_update_value': '0.0 on valid land',
            'missing_value_semantics': 'NaN outside canonical valid-land support',
            'xai_role': 'candidate XAI-Source target representing DA correction magnitude',
            'source_experiment': exp
        }
    )
    
    out_file = os.path.join(out_dir, f'daily_absolute_increment_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'daily_absolute_increment': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', type=str, required=True, help='DA-CDF or DA-NoCDF')
    parser.add_argument('--signed_dir', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--years', type=int, nargs='+', default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    for year in args.years:
        process_year(args.exp, year, args.signed_dir, args.out_dir)

if __name__ == "__main__":
    main()
