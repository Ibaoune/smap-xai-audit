#!/usr/bin/env python3
"""
EnKF Innovation Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Extracts event-based innovation fields from LIS DA EnKF outputs.
Preserves native assimilation timestamps.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import glob
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp_dir, out_dir, year):
    # Find all innov files for the given year
    pattern = os.path.join(exp_dir, 'output', f'{year}-*', 'EnKF', f'{year}*', f'LIS_DA_EnKF_{year}*innov.a01.d01.nc')
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No files found for {year} in {exp_dir}")
        return
        
    print(f"Processing {len(files)} events for {year}...")
    
    datasets = []
    for f in files:
        # LIS_DA_EnKF_YYYYMMDDHHMM_innov.a01.d01.nc
        basename = os.path.basename(f)
        ts_str = basename.split('_')[3]
        event_time = pd.to_datetime(ts_str, format='%Y%m%d%H%M')
        
        try:
            ds_raw = xr.open_dataset(f)
            # The variable is innov_01
            var_name = 'innov_01'
            if var_name not in ds_raw.data_vars:
                continue
                
            data = ds_raw[var_name].values
            
            # Extract coordinates from a reference LIS_HIST file because EnKF output often lacks lon/lat
            # We assume we can get it from the dataset or we use standard 121x181 grid
            
            # Replace -9999.0 with NaN
            data = np.where(data == -9999.0, np.nan, data)
            
            # Create a clean dataset for this event
            ds_event = xr.Dataset(
                {
                    'innovation': (['lat', 'lon'], data)
                },
                coords={
                    'event_time': event_time
                },
                attrs={
                    'description': 'EnKF soil-moisture innovation (y - H(xf))',
                    'units': 'm3 m-3'
                }
            )
            datasets.append(ds_event)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    if not datasets:
        return
        
    ds_annual = xr.concat(datasets, dim='event_time')
    
    # Try to add lon/lat if possible. In EnKF they usually don't exist in the file.
    # Let's borrow coordinates from interim SSM if available
    try:
        ref_ds = xr.open_dataset('data/interim/noahmp/da_cdf/ssm/ssm_2016.nc')
        ds_annual = ds_annual.assign_coords({'lon': ref_ds.lon, 'lat': ref_ds.lat})
    except:
        pass
        
    out_file = os.path.join(out_dir, f'innovation_{year}.nc')
    ds_annual.to_netcdf(out_file, encoding={'innovation': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess EnKF Innovation")
    parser.add_argument('--exp_dir', type=str, required=True, help="Path to raw experiment directory")
    parser.add_argument('--out_dir', type=str, required=True, help="Output directory")
    parser.add_argument('--years', type=int, nargs='+', default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    for year in args.years:
        process_year(args.exp_dir, args.out_dir, year)

if __name__ == "__main__":
    main()
