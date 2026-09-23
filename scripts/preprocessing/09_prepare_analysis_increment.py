#!/usr/bin/env python3
"""
EnKF Analysis Increment Preprocessing (Soil Moisture Layer 1)

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Extracts the signed analysis increment for Soil Moisture Layer 1 from raw LIS EnKF files.
This script is strictly EVENT-BASED. It aggregates the raw files into annual
NetCDF files with an `event_time` dimension.

Sign convention:
    Positive: Analysis is wetter than forecast (xa > xf)
    Negative: Analysis is drier than forecast (xa < xf)
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import glob
import argparse
import numpy as np
import xarray as xr
import pandas as pd

def process_year(da_dir, year, out_dir):
    pattern = os.path.join(da_dir, 'output', f'{year}-*', 'EnKF', f'{year}*', f'LIS_DA_EnKF_{year}*incr.a01.d01.nc')
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No increment files found for {year} in {da_dir}")
        return
        
    event_times = []
    datasets = []
    
    # Pre-parse event times to ensure chronological order
    for f in files:
        basename = os.path.basename(f)
        time_str = basename.split('_')[3]
        event_time = pd.to_datetime(time_str, format='%Y%m%d%H%M')
        event_times.append(event_time)
        
    # Check for duplicates or out-of-order
    if len(event_times) != len(set(event_times)):
        raise ValueError(f"Duplicate event times detected in {year}")
        
    if event_times != sorted(event_times):
        raise ValueError(f"Event times are not strictly increasing in {year}")
        
    print(f"Processing {len(files)} events for {year}...")
    
    raw_var = 'anlys_incr_Soil Moisture Layer 1_01'
    
    for f, ev_time in zip(files, event_times):
        ds = xr.open_dataset(f)
        data = ds[raw_var].values.astype(np.float32)
        
        # Replace missing value (-9999.0) with NaN
        # Leave 0.0 as 0.0 (no observation/update)
        data = np.where(data == -9999.0, np.nan, data)
        
        ds_event = xr.Dataset(
            {
                'increment_signed': (['lat', 'lon'], data)
            },
            coords={
                'event_time': ev_time
            }
        )
        datasets.append(ds_event)
        ds.close()
        
    # Concatenate along event_time
    ds_annual = xr.concat(datasets, dim='event_time')
    
    # Add dummy lat/lon coordinates from OPL structure if needed,
    # but the prompt didn't specify inheriting OPL coordinates explicitly for this step.
    # We will just add the correct linspace for this domain.
    lat_vals = np.linspace(30.0, 36.0, 121)
    lon_vals = np.linspace(-10.0, -1.0, 181)
    ds_annual = ds_annual.assign_coords({'lat': lat_vals, 'lon': lon_vals})
    
    # Set attributes
    ds_annual['increment_signed'].attrs = {
        'long_name': 'Signed EnKF Analysis Increment for Soil Moisture Layer 1',
        'units': 'm3 m-3',
        'sign_convention': 'positive = analysis wetter than forecast',
        'layer': '0-10 cm'
    }
    
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f'increment_signed_{year}.nc')
    ds_annual.to_netcdf(out_file)
    print(f"Saved {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract signed analysis increment.")
    parser.add_argument("--exp_dir", required=True, help="Path to DA experiment directory")
    parser.add_argument("--out_dir", required=True, help="Path to save processed files")
    parser.add_argument("--years", nargs='+', default=['2016', '2017', '2018', '2019', '2020'])
    args = parser.parse_args()
    
    for y in args.years:
        process_year(args.exp_dir, y, args.out_dir)

if __name__ == "__main__":
    main()
