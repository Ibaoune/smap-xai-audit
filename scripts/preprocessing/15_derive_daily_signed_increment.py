#!/usr/bin/env python3
"""
EnKF Daily Signed Analysis Increment Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives the daily signed EnKF Layer-1 soil-moisture analysis increment from the
native event-based increment_signed output.

Uses observation_frequency as the authoritative assimilation support. 
If observation_frequency == 1, assigns the unique event increment to the pixel-day.
If observation_frequency == 0, assigns 0.0 (no assimilation).
Preserves NaN for non-land model support.
Validates max daily multiplicity = 1.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

def process_year(exp, year, in_dir, freq_dir, out_dir):
    in_file = os.path.join(in_dir, f'increment_signed_{year}.nc')
    inv_file = in_file.replace('increment_signed', 'innovation')
    freq_file = os.path.join(freq_dir, f'observation_frequency_{year}.nc')
    
    if not (os.path.exists(in_file) and os.path.exists(freq_file) and os.path.exists(inv_file)):
        print(f"Missing inputs for {year}")
        return

    # Load event-based increments and innovation
    ds_in = xr.open_dataset(in_file)
    ds_inv = xr.open_dataset(inv_file)
    inc_var = 'increment' if 'increment' in ds_in.data_vars else 'increment_signed'
    inc_events = ds_in[inc_var].values
    inv_events = ds_inv['innovation'].values
    events = ds_in.event_time.values
    
    # Load daily observation frequency
    ds_freq = xr.open_dataset(freq_file)
    obs_freq = ds_freq['observation_frequency'].values
    daily_times = pd.DatetimeIndex(ds_freq.time.values)
    
    # Initialize daily signed increment array
    # Start with NaN (matches outside-canonical-support)
    daily_inc = np.full(obs_freq.shape, np.nan, dtype=np.float32)
    
    # Where valid land (obs_freq is finite), default to 0.0
    land_mask = ~np.isnan(obs_freq)
    daily_inc[land_mask] = 0.0
    
    # Track assigned pixel-days to prevent silent overwrite
    assigned = np.zeros(obs_freq.shape, dtype=bool)
    
    # Map event times to daily indices
    event_days = pd.DatetimeIndex(events).floor('D')
    
    # Iterate through events and map to daily array
    for i, ev_day in enumerate(event_days):
        # find corresponding day index
        day_idx = np.where(daily_times == ev_day)[0]
        if len(day_idx) == 0:
            continue
        day_idx = day_idx[0]
        
        # Valid increments for this event (based on innovation support)
        ev_inc = inc_events[i]
        ev_inv = inv_events[i]
        valid_pixels = ~np.isnan(ev_inv)
        
        # Check for multiple updates
        if np.any(assigned[day_idx, valid_pixels]):
            raise ValueError(f"Multiple valid increments map to the same pixel-day! Day: {ev_day}")
        
        # Assign valid increments
        daily_inc[day_idx, valid_pixels] = ev_inc[valid_pixels]
        assigned[day_idx, valid_pixels] = True

    # Validate zero semantics strictly
    # observation_frequency == 0 -> daily_inc == 0.0
    # observation_frequency == 1 -> daily_inc assigned
    obs_freq_0 = (obs_freq == 0) & land_mask
    obs_freq_1 = (obs_freq == 1) & land_mask
    
    violations_0 = np.sum((daily_inc[obs_freq_0] != 0.0) | np.isnan(daily_inc[obs_freq_0]))
    violations_1 = np.sum(~assigned[obs_freq_1])
    violations_nan = np.sum(~np.isnan(daily_inc[~land_mask]))
    
    if violations_0 > 0 or violations_1 > 0 or violations_nan > 0:
        raise ValueError(f"Zero semantics violations: 0-violations={violations_0}, 1-violations={violations_1}, NaN-violations={violations_nan}")
    
    # Count conservation
    daily_updated = np.sum(obs_freq_1)
    assigned_count = np.sum(assigned)
    event_nonzero = np.sum(~np.isnan(inv_events))
    
    print(f"[{year}] Support-count diff: {event_nonzero - daily_updated} (events vs daily_obs=1)")
    print(f"[{year}] Assigned-count diff: {assigned_count - daily_updated} (assigned vs daily_obs=1)")
    
    # Value conservation
    event_sum = np.nansum(inc_events, dtype=np.float64)
    daily_sum = np.sum(daily_inc[assigned], dtype=np.float64)
    val_diff = event_sum - daily_sum
    print(f"[{year}] Value conservation diff: {val_diff:.6e}")
    
    event_pos = np.nansum(inc_events[inc_events > 0], dtype=np.float64)
    daily_pos = np.sum(daily_inc[assigned & (daily_inc > 0)], dtype=np.float64)
    print(f"[{year}] Pos sum diff: {event_pos - daily_pos:.6e}")
    
    event_neg = np.nansum(inc_events[inc_events < 0], dtype=np.float64)
    daily_neg = np.sum(daily_inc[assigned & (daily_inc < 0)], dtype=np.float64)
    print(f"[{year}] Neg sum diff: {event_neg - daily_neg:.6e}")
    
    # Construct output dataset
    ds_out = xr.Dataset(
        {
            'daily_signed_increment': (['time', 'lat', 'lon'], daily_inc)
        },
        coords={
            'time': daily_times,
            'lat': ds_freq.lat.values,
            'lon': ds_freq.lon.values
        },
        attrs={
            'long_name': 'Daily signed EnKF Layer-1 soil-moisture analysis increment',
            'units': 'm3 m-3',
            'source_variable': 'increment_signed',
            'source_support': 'native EnKF assimilation events',
            'daily_mapping': 'unique valid assimilation event within UTC calendar day',
            'no_update_value': '0.0 on valid land',
            'missing_value_semantics': 'NaN outside canonical valid-land support',
            'layer': '0-10 cm',
            'temporal_support': 'UTC calendar day',
            'source_experiment': exp
        }
    )
    
    out_file = os.path.join(out_dir, f'daily_signed_increment_{year}.nc')
    ds_out.to_netcdf(out_file, encoding={'daily_signed_increment': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
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
