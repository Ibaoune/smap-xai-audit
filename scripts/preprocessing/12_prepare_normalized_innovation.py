#!/usr/bin/env python3
import os
import glob
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp_dir, out_dir, year):
    pattern = os.path.join(exp_dir, 'output', f'{year}-*', 'EnKF', f'{year}*', f'LIS_DA_EnKF_{year}*innov.a01.d01.nc')
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No files found for {year} in {exp_dir}")
        return
        
    print(f"Processing {len(files)} events for {year} in {exp_dir}...")
    
    datasets = []
    for f in files:
        basename = os.path.basename(f)
        ts_str = basename.split('_')[3]
        event_time = pd.to_datetime(ts_str, format='%Y%m%d%H%M')
        
        try:
            ds_raw = xr.open_dataset(f)
            var_name = 'ninnov_01'
            if var_name not in ds_raw.data_vars:
                continue
                
            data = ds_raw[var_name].values
            data = np.where(data == -9999.0, np.nan, data)
            
            ds_event = xr.Dataset(
                {
                    'normalized_innovation': (['lat', 'lon'], data)
                },
                coords={
                    'event_time': event_time
                },
                attrs={
                    'description': 'Normalized EnKF soil-moisture innovation',
                    'units': '1',
                    'source_variable': 'ninnov_01',
                    'definition': 'innovation / sqrt(forecast_variance + R)',
                    'observation_error_std': '0.04 m3 m-3',
                    'observation_error_variance': '0.0016 (m3 m-3)2',
                    'observation_type': 'SMAP NASA SPL3SMP_E',
                    'temporal_support': 'assimilation event',
                    'timestamp_convention': 'native EnKF assimilation timestamp'
                }
            )
            datasets.append(ds_event)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    if not datasets:
        return
        
    ds_annual = xr.concat(datasets, dim='event_time')
    
    try:
        ref_ds = xr.open_dataset('data/interim/noahmp/da_cdf/ssm/ssm_2016.nc')
        ds_annual = ds_annual.assign_coords({'lon': ref_ds.lon, 'lat': ref_ds.lat})
    except:
        pass
        
    out_file = os.path.join(out_dir, f'normalized_innovation_{year}.nc')
    ds_annual.to_netcdf(out_file, encoding={'normalized_innovation': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_dir', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--years', type=int, nargs='+', default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    for year in args.years:
        process_year(args.exp_dir, args.out_dir, year)

if __name__ == "__main__":
    main()
