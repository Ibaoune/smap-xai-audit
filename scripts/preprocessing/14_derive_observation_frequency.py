#!/usr/bin/env python3
"""
EnKF Daily Observation Frequency Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily observation frequency from the event-based EnKF innovation support.
Maps native EnKF assimilation event times to their UTC calendar day and counts
valid assimilated observations at each pixel.

Applies a static land mask to ensure unobserved valid land has frequency 0,
while non-land retains NaN.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp, year, in_dir, out_dir, land_mask, lat, lon):
    in_file = os.path.join(in_dir, f'innovation_{year}.nc')
    if not os.path.exists(in_file):
        print(f"Missing {in_file}")
        return

    ds_in = xr.open_dataset(in_file)
    inv = ds_in['innovation'].values
    events = ds_in.event_time.values
    
    # Identify finite (assimilated) pixels
    valid_assim = ~np.isnan(inv)
    
    # Group by calendar day
    event_days = pd.DatetimeIndex(events).floor('D')
    daily_counts = {}
    for i, day in enumerate(event_days):
        if day not in daily_counts:
            daily_counts[day] = np.zeros((121, 181), dtype=np.float32)
        daily_counts[day] += valid_assim[i].astype(np.float32)
        
    # Create full year daily index
    full_days = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='D')
    
    out_data = np.zeros((len(full_days), 121, 181), dtype=np.float32)
    for i, day in enumerate(full_days):
        if day in daily_counts:
            out_data[i] = daily_counts[day]
            
    # Apply land mask: set non-land to NaN
    # land_mask is boolean: True for land, False for non-land
    out_data[:, ~land_mask] = np.nan
    
    ds_out = xr.Dataset(
        {
            'observation_frequency': (['time', 'lat', 'lon'], out_data)
        },
        coords={
            'time': full_days,
            'lat': lat,
            'lon': lon
        },
        attrs={
            'long_name': 'Daily count of assimilated SMAP soil-moisture observations',
            'units': '1',
            'definition': 'Number of EnKF assimilation events with a valid assimilated observation at each pixel during the UTC calendar day',
            'source_support': 'isfinite(innovation)',
            'observation_type': 'SMAP NASA SPL3SMP_E',
            'temporal_support': 'UTC calendar day',
            'aggregation': 'count of native EnKF assimilation events',
            'source_experiment': exp
        }
    )
    
    out_file = os.path.join(out_dir, f'observation_frequency_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'observation_frequency': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}")
    
    # QC: Count conservation
    total_events = np.sum(valid_assim)
    total_daily = np.nansum(out_data)
    print(f"[{year}] Event-based valid: {total_events}, Daily aggregated valid: {total_daily}, Diff: {total_events - total_daily}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', type=str, required=True, help='DA-CDF or DA-NoCDF')
    parser.add_argument('--in_dir', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--years', type=int, nargs='+', default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Load canonical land mask
    ref_file = f"data/interim/noahmp/{args.exp.lower().replace('-', '_')}/ssm/ssm_2016.nc"
    if not os.path.exists(ref_file):
        raise FileNotFoundError(f"Missing land mask file: {ref_file}")
    
    ds_ref = xr.open_dataset(ref_file)
    ref_val = ds_ref['ssm'].isel(time=0).values
    land_mask = ~np.isnan(ref_val)
    lat = ds_ref.lat.values
    lon = ds_ref.lon.values
    masked_frac = np.sum(~land_mask) / land_mask.size
    print(f"Land mask loaded. Masked fraction: {masked_frac:.4f}")
    
    for year in args.years:
        process_year(args.exp, year, args.in_dir, args.out_dir, land_mask, lat, lon)

if __name__ == "__main__":
    main()
