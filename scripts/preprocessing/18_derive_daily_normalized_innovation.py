#!/usr/bin/env python3
"""
EnKF Daily Normalized Innovation Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily EnKF SMAP soil-moisture normalized innovation from the
native event-based normalized innovation.

daily_normalized_innovation = daily_innovation / sqrt(forecast_variance + R)
where R = 0.0016 (m3 m-3)^2

NaN Semantics
-------------
NaN is used for:
1. Valid land pixel-days without assimilation (observation_frequency == 0)
2. Grid cells outside canonical valid-land support

Event-to-Day Mapping
--------------------
Unique valid event mapped to UTC calendar day. Multiplicity > 1 triggers error.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp, year, in_dir, freq_dir, out_dir):
    in_file = os.path.join(in_dir, f'normalized_innovation_{year}.nc')
    freq_file = os.path.join(freq_dir, f'observation_frequency_{year}.nc')
    
    if not (os.path.exists(in_file) and os.path.exists(freq_file)):
        print(f"Missing inputs for {year}")
        return

    # Load event-based normalized innovation
    ds_in = xr.open_dataset(in_file)
    inv_events = ds_in['normalized_innovation'].values
    events = ds_in.event_time.values
    
    # Load daily observation frequency
    ds_freq = xr.open_dataset(freq_file)
    obs_freq = ds_freq['observation_frequency'].values
    daily_times = pd.DatetimeIndex(ds_freq.time.values)
    
    # Initialize daily array with NaN
    daily_inv = np.full(obs_freq.shape, np.nan, dtype=np.float32)
    assigned = np.zeros(obs_freq.shape, dtype=bool)
    
    # Map event times to daily indices
    event_days = pd.DatetimeIndex(events).floor('D')
    
    for i, ev_day in enumerate(event_days):
        day_idx = np.where(daily_times == ev_day)[0]
        if len(day_idx) == 0:
            continue
        day_idx = day_idx[0]
        
        ev_inv = inv_events[i]
        valid_pixels = ~np.isnan(ev_inv)
        
        if np.any(assigned[day_idx, valid_pixels]):
            raise ValueError(f"Multiple valid innovations map to the same pixel-day! Day: {ev_day}")
        
        daily_inv[day_idx, valid_pixels] = ev_inv[valid_pixels]
        assigned[day_idx, valid_pixels] = True

    # Validate Support Consistency
    land_mask = ~np.isnan(obs_freq)
    obs_freq_1 = (obs_freq == 1) & land_mask
    obs_freq_0 = (obs_freq == 0) & land_mask
    
    finite_daily = ~np.isnan(daily_inv)
    
    viol_1 = np.sum(obs_freq_1 & ~finite_daily)
    viol_0 = np.sum(obs_freq_0 & finite_daily)
    
    if viol_1 > 0 or viol_0 > 0:
        raise ValueError(f"Support consistency violation! freq=1 but nan: {viol_1}, freq=0 but finite: {viol_0}")
    
    # Count conservation
    daily_updated = np.sum(obs_freq_1)
    event_nonzero = np.sum(~np.isnan(inv_events))
    
    print(f"[{year}] Support-count diff: {event_nonzero - daily_updated} (events vs daily_obs=1)")
    
    ds_out = xr.Dataset(
        {
            'daily_normalized_innovation': (['time', 'lat', 'lon'], daily_inv)
        },
        coords={
            'time': daily_times,
            'lat': ds_freq.lat.values,
            'lon': ds_freq.lon.values
        },
        attrs={
            'long_name': 'Daily normalized SMAP EnKF soil-moisture innovation',
            'units': '1',
            'definition': 'innovation divided by sqrt(forecast_variance + observation_error_variance)',
            'source_variable': 'normalized_innovation',
            'observation_error_variance': '0.0016 (m3 m-3)^2',
            'source_support': 'native EnKF assimilation event',
            'daily_mapping': 'unique finite event mapped to UTC calendar day',
            'no_assimilation_semantics': 'NaN',
            'temporal_support': 'UTC calendar day',
            'xai_role': 'pre-analysis standardized mismatch predictor'
        }
    )
    
    out_file = os.path.join(out_dir, f'daily_normalized_innovation_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'daily_normalized_innovation': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"Saved {out_file}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', type=str, required=True, help='DA-CDF or DA-NoCDF')
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
