#!/usr/bin/env python3
"""
EnKF Daily Analysis Residual Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily EnKF analysis residual from the native event-based
analysis residual.

Definition
----------
y - H(x_a)
post-analysis diagnostic

NaN Semantics
-------------
NaN is used for valid land pixel-days without assimilation or grid cells 
outside canonical valid-land support.

Event-to-Day Mapping
--------------------
Unique valid event mapped to UTC calendar day.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp, year, in_dir, freq_dir, out_dir):
    in_file = os.path.join(in_dir, f'analysis_residual_{year}.nc')
    freq_file = os.path.join(freq_dir, f'observation_frequency_{year}.nc')
    
    if not (os.path.exists(in_file) and os.path.exists(freq_file)):
        print(f"Missing inputs for {year}")
        return

    # Load event-based analysis residual
    ds_in = xr.open_dataset(in_file)
    res_events = ds_in['analysis_residual'].values
    events = ds_in.event_time.values
    
    # Load daily observation frequency
    ds_freq = xr.open_dataset(freq_file)
    obs_freq = ds_freq['observation_frequency'].values
    daily_times = pd.DatetimeIndex(ds_freq.time.values)
    
    # Initialize daily array with NaN
    daily_res = np.full(obs_freq.shape, np.nan, dtype=np.float32)
    assigned = np.zeros(obs_freq.shape, dtype=bool)
    
    event_days = pd.DatetimeIndex(events).floor('D')
    
    for i, ev_day in enumerate(event_days):
        day_idx = np.where(daily_times == ev_day)[0]
        if len(day_idx) == 0:
            continue
        day_idx = day_idx[0]
        
        ev_slice = res_events[i]
        valid_pixels = ~np.isnan(ev_slice)
        
        if np.any(assigned[day_idx, valid_pixels]):
            raise ValueError(f"Multiple valid residuals map to the same pixel-day! Day: {ev_day}")
        
        daily_res[day_idx, valid_pixels] = ev_slice[valid_pixels]
        assigned[day_idx, valid_pixels] = True

    # Validate Support Consistency
    land_mask = ~np.isnan(obs_freq)
    obs_freq_1 = (obs_freq == 1) & land_mask
    obs_freq_0 = (obs_freq == 0) & land_mask
    
    finite_daily = ~np.isnan(daily_res)
    
    viol_1 = np.sum(obs_freq_1 & ~finite_daily)
    viol_0 = np.sum(obs_freq_0 & finite_daily)
    
    if viol_1 > 0 or viol_0 > 0:
        raise ValueError(f"Support consistency violation! freq=1 but nan: {viol_1}, freq=0 but finite: {viol_0}")
    
    daily_updated = np.sum(obs_freq_1)
    event_nonzero = np.sum(~np.isnan(res_events))
    print(f"[{year}] Support-count diff: {event_nonzero - daily_updated}")
    
    obs_rep = "CDF-matched representation" if exp == "DA-CDF" else "non-CDF-matched observation representation used by experiment"
    
    ds_out = xr.Dataset(
        {
            'daily_analysis_residual': (['time', 'lat', 'lon'], daily_res)
        },
        coords={
            'time': daily_times,
            'lat': ds_freq.lat.values,
            'lon': ds_freq.lon.values
        },
        attrs={
            'long_name': 'Daily SMAP EnKF soil-moisture analysis residual',
            'units': 'm3 m-3',
            'definition': 'assimilated observation minus analysis equivalent',
            'source_variable': 'analysis_residual',
            'source_support': 'native EnKF assimilation event',
            'daily_mapping': 'unique finite event mapped to UTC calendar day',
            'no_assimilation_semantics': 'NaN',
            'temporal_support': 'UTC calendar day',
            'analysis_stage': 'post-analysis',
            'xai_role': 'post-analysis diagnostic; not a pre-analysis increment predictor',
            'observation_representation': obs_rep
        }
    )
    
    out_file = os.path.join(out_dir, f'daily_analysis_residual_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'daily_analysis_residual': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', type=str, required=True)
    parser.add_argument('--in_dir', type=str, required=True)
    parser.add_argument('--freq_dir', type=str, required=True)
    parser.add_argument('--out_dir', type=str, required=True)
    parser.add_argument('--years', type=int, nargs='+', default=[2016, 2017, 2018, 2019, 2020])
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    for year in args.years:
        process_year(args.exp, year, args.in_dir, args.freq_dir, args.out_dir)

if __name__ == "__main__":
    main()
