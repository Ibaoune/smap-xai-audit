#!/usr/bin/env python3
"""
EnKF Daily Forecast Variance Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily EnKF forecast observation-space variance from the native
event-based forecast variance (HPH^T).

Units
-----
(m3 m-3)^2

NaN Semantics
-------------
NaN is used for:
1. Valid land pixel-days without assimilation (observation_frequency == 0)
2. Grid cells outside canonical valid-land support
Zero is never used for imputation.

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
    in_file = os.path.join(in_dir, f'forecast_variance_{year}.nc')
    freq_file = os.path.join(freq_dir, f'observation_frequency_{year}.nc')
    
    if not (os.path.exists(in_file) and os.path.exists(freq_file)):
        print(f"Missing inputs for {year}")
        return

    # Load event-based forecast variance
    ds_in = xr.open_dataset(in_file)
    fv_events = ds_in['forecast_variance'].values
    events = ds_in.event_time.values
    
    # Load daily observation frequency
    ds_freq = xr.open_dataset(freq_file)
    obs_freq = ds_freq['observation_frequency'].values
    daily_times = pd.DatetimeIndex(ds_freq.time.values)
    
    # Initialize daily array with NaN
    daily_fv = np.full(obs_freq.shape, np.nan, dtype=np.float32)
    assigned = np.zeros(obs_freq.shape, dtype=bool)
    
    # Map event times to daily indices
    event_days = pd.DatetimeIndex(events).floor('D')
    
    for i, ev_day in enumerate(event_days):
        day_idx = np.where(daily_times == ev_day)[0]
        if len(day_idx) == 0:
            continue
        day_idx = day_idx[0]
        
        ev_fv = fv_events[i]
        valid_pixels = ~np.isnan(ev_fv)
        
        if np.any(assigned[day_idx, valid_pixels]):
            raise ValueError(f"Multiple valid forecast variances map to the same pixel-day! Day: {ev_day}")
        
        daily_fv[day_idx, valid_pixels] = ev_fv[valid_pixels]
        assigned[day_idx, valid_pixels] = True

    # Validate Support Consistency
    land_mask = ~np.isnan(obs_freq)
    obs_freq_1 = (obs_freq == 1) & land_mask
    obs_freq_0 = (obs_freq == 0) & land_mask
    
    finite_daily = ~np.isnan(daily_fv)
    
    viol_1 = np.sum(obs_freq_1 & ~finite_daily)
    viol_0 = np.sum(obs_freq_0 & finite_daily)
    
    if viol_1 > 0 or viol_0 > 0:
        raise ValueError(f"Support consistency violation! freq=1 but nan: {viol_1}, freq=0 but finite: {viol_0}")
    
    # Count conservation
    daily_updated = np.sum(obs_freq_1)
    event_nonzero = np.sum(~np.isnan(fv_events))
    
    print(f"[{year}] Support-count diff: {event_nonzero - daily_updated} (events vs daily_obs=1)")
    
    ds_out = xr.Dataset(
        {
            'daily_forecast_variance': (['time', 'lat', 'lon'], daily_fv)
        },
        coords={
            'time': daily_times,
            'lat': ds_freq.lat.values,
            'lon': ds_freq.lon.values
        },
        attrs={
            'long_name': 'Daily EnKF forecast observation-space soil-moisture variance',
            'units': '(m3 m-3)^2',
            'definition': 'HPH^T, forecast-error variance projected into observation space',
            'source_variable': 'forecast_variance',
            'raw_LIS_variable': 'forecast_sigma_01',
            'source_support': 'native EnKF assimilation event',
            'daily_mapping': 'unique finite event mapped to UTC calendar day',
            'no_assimilation_semantics': 'NaN',
            'observation_error_variance': '0.0016 (m3 m-3)^2',
            'temporal_support': 'UTC calendar day',
            'xai_role': 'pre-analysis observation-space forecast-variance predictor'
        }
    )
    
    out_file = os.path.join(out_dir, f'daily_forecast_variance_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'daily_forecast_variance': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
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
