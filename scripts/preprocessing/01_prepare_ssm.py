"""
SMAP-XAI: SSM Preprocessing Driver

Purpose
-------
Standardize daily Noah-MP SSM. Parses raw LIS_HIST NetCDF files, concatenates 
them along a common temporal axis, executes strict spatial/temporal validation, 
and produces one unified interim file per year per experiment.

Source Variable
---------------
SoilMoist_tavg

Layer
-----
Layer 1 = 0-10 cm

Experiments
-----------
opl
da_nocdf
da_cdf

Period Support
--------------
Any requested year, currently validated for 2016-2020

Output
------
data/interim/noahmp/<experiment>/ssm/ssm_<year>.nc

Canonical Time
--------------
LIS filename timestamp - 1 day

No Operations
-------------
no unit conversion
no regridding
no interpolation
no smoothing
no clipping

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime

# Adjust the path so we can import from src
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from smap_xai.preprocessing.noahmp import (
    discover_lis_hist_files,
    parse_lis_hist_timestamp,
    extract_noahmp_variable,
    construct_canonical_coords,
    validate_grid_consistency
)

def main():
    parser = argparse.ArgumentParser(description="Prepare surface soil moisture (SSM) from Noah-MP outputs.")
    parser.add_argument("--experiment", type=str, default="opl", choices=["opl", "da_nocdf", "da_cdf"], help="Experiment name")
    parser.add_argument("--year", type=int, default=2016, help="Year to process")
    args = parser.parse_args()

    # Paths and configurations
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao"
    
    experiment_map = {
        "opl": "OPL_noirr_2016_2020",
        "da_nocdf": "DA_nocdf_noirr_2016_2020",
        "da_cdf": "DA_cdf_noirr_2016_2020"
    }
    
    experiment_dir = experiment_map.get(args.experiment)
    if experiment_dir is None:
        raise ValueError(f"Unknown experiment: {args.experiment}")
        
    experiment_root = os.path.join(base_dir, "NoahMP_Morocco", "experiments", "NorthMor", "matrix_2016_2020", experiment_dir)
    
    output_dir = os.path.join(base_dir, "smap-xai-audit", "data", "interim", "noahmp", args.experiment, "ssm")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"ssm_{args.year}.nc")

    # Discover files
    print(f"Discovering files for {args.experiment} {args.year}...")
    files = discover_lis_hist_files(experiment_root, args.year)
    
    valid_files = []
    missing_dates = []
    for date, fpath in files:
        if os.path.exists(fpath):
            valid_files.append((date, fpath))
        else:
            missing_dates.append(date)
            
    print(f"Found {len(valid_files)} valid LIS_HIST files.")
    if missing_dates:
        print(f"Missing {len(missing_dates)} files.")

    # Process files
    ssm_arrays = []
    times = []
    
    ref_lat = None
    ref_lon = None
    grid_errors = []
    read_errors = []
    duplicate_dates = []
    
    for date, fpath in valid_files:
        try:
            # Explicitly parse timestamp from filename to verify
            parsed_date = parse_lis_hist_timestamp(fpath)
            if parsed_date != date:
                print(f"Warning: parsed date {parsed_date} != expected canonical date {date}")
                
            if date in times:
                duplicate_dates.append(date)
                continue
                
            var, ds = extract_noahmp_variable(fpath, "SoilMoist_tavg", layer_idx=0) # layer 1 (0-10 cm)
            
            if ref_lat is None and ref_lon is None:
                ref_lat, ref_lon = construct_canonical_coords(ds)
            else:
                if not validate_grid_consistency(ds, ref_lat, ref_lon):
                    grid_errors.append(fpath)
                    continue
            
            # The variable might have nan as fill value (-9999.0)
            # xarray handles _FillValue automatically by replacing it with nan
            # var has dims (lat, lon) here, thanks to extract_noahmp_variable
            
            # Expand time dim
            var = var.expand_dims(time=[date])
            
            # Keep precision float32
            var = var.astype(np.float32)
            
            ssm_arrays.append(var)
            times.append(date)
            
        except Exception as e:
            import traceback
            print(f"Exception on file {fpath} for date {date}:")
            traceback.print_exc()
            read_errors.append((fpath, str(e)))
            break
            
    # Report source file coverage QC
    print(f"\n--- SOURCE FILE COVERAGE QC ---")
    print(f"Number of LIS_HIST files found for canonical year {args.year}: {len(valid_files)}")
    print(f"Duplicate canonical dates: {len(duplicate_dates)}")
    print(f"Missing canonical dates: {len(missing_dates)}")
    print(f"Files that cannot be read: {len(read_errors)}")
    print(f"Files with grid differing from reference: {len(grid_errors)}")

    if not ssm_arrays:
        print("No valid data processed. Exiting.")
        return

    # Concatenate along time
    print(f"\nConcatenating {len(ssm_arrays)} daily files...")
    ds_out = xr.concat(ssm_arrays, dim='time')
    ds_out.name = "ssm"
    
    # Assign canonical coords explicitly just to be safe
    ds_out = ds_out.assign_coords({"lat": ref_lat, "lon": ref_lon, "time": pd.DatetimeIndex(times)})
    
    # Convert to Dataset for output
    ds_final = xr.Dataset({"ssm": ds_out})
    
    # Metadata
    ds_final["ssm"].attrs = {
        "long_name": "Surface soil moisture, 0-10 cm",
        "units": "m3 m-3"
    }
    
    ds_final.attrs = {
        "source_experiment": args.experiment.upper(),
        "source_variable": "SoilMoist_tavg",
        "source_layer": "layer 1, 0-10 cm",
        "temporal_support": "daily 24-hour average",
        "timestamp_convention": "canonical date is one day before LIS_HIST filename timestamp"
    }
    
    # Save with lossless NetCDF compression
    # The encoding dtype is preserved as float32
    print(f"\nSaving to {output_path}...")
    encoding = {
        "ssm": {
            "zlib": True,
            "complevel": 4,
            "_FillValue": np.float32(-9999.0),
            "dtype": "float32"
        },
        "time": {
            "units": "days since 1970-01-01 00:00:00",
            "calendar": "standard"
        }
    }
    
    ds_final.to_netcdf(output_path, encoding=encoding)
    print("Done.\n")

    # Quality Control
    print(f"--- QUALITY CONTROL ---")
    
    # TEMPORAL QC
    times_arr = pd.DatetimeIndex(ds_final.time.values)
    first_date = times_arr.min().strftime('%Y-%m-%d')
    last_date = times_arr.max().strftime('%Y-%m-%d')
    n_timestamps = len(times_arr)
    all_unique = len(set(times_arr)) == n_timestamps
    
    # Check daily spacing exactly one day
    time_diffs = np.diff(times_arr)
    is_daily = np.all(time_diffs == np.timedelta64(1, 'D'))
    
    print("TEMPORAL QC:")
    print(f"  first canonical date = {first_date}")
    print(f"  last canonical date = {last_date}")
    print(f"  number of timestamps = {n_timestamps}")
    print(f"  all timestamps unique = {all_unique}")
    print(f"  daily spacing exactly one day = {is_daily}")
    if n_timestamps > 0 and is_daily:
        expected_days = (times_arr.max() - times_arr.min()).days + 1
        missing_calendar = expected_days - n_timestamps
        print(f"  missing calendar dates = {missing_calendar}")
    else:
        print(f"  missing calendar dates = Cannot determine (not daily or empty)")

    # SPATIAL QC
    n_time, n_lat, n_lon = ds_final["ssm"].shape
    lat_min, lat_max = float(ref_lat.min()), float(ref_lat.max())
    lon_min, lon_max = float(ref_lon.min()), float(ref_lon.max())
    lat_step = float(ref_lat[1] - ref_lat[0])
    lon_step = float(ref_lon[1] - ref_lon[0])
    
    print("\nSPATIAL QC:")
    print(f"  dimensions = {n_lat} x {n_lon}")
    print(f"  latitude range = {lat_min:.4f} to {lat_max:.4f}")
    print(f"  longitude range = {lon_min:.4f} to {lon_max:.4f}")
    print(f"  grid spacing = {lat_step:.4f} (lat), {lon_step:.4f} (lon)")
    print(f"  coordinate ordering = {ds_final['ssm'].dims}")
    print(f"  same grid in all {n_timestamps} source files = {len(grid_errors) == 0}")

    # VARIABLE QC
    ssm_vals = ds_final["ssm"].values
    dtype = ssm_vals.dtype
    
    # Calculate statistics ignoring NaNs
    valid_mask = ~np.isnan(ssm_vals)
    valid_vals = ssm_vals[valid_mask]
    
    if len(valid_vals) > 0:
        v_min = float(np.min(valid_vals))
        v_max = float(np.max(valid_vals))
        v_mean = float(np.mean(valid_vals))
    else:
        v_min, v_max, v_mean = np.nan, np.nan, np.nan
        
    n_nan = np.sum(~valid_mask)
    nan_frac = n_nan / ssm_vals.size
    
    n_lt_0 = np.sum(valid_vals < 0)
    n_gt_1 = np.sum(valid_vals > 1)
    
    print("\nVARIABLE QC:")
    print(f"  dtype = {dtype}")
    print(f"  minimum = {v_min}")
    print(f"  maximum = {v_max}")
    print(f"  mean = {v_mean}")
    print(f"  NaN count = {n_nan}")
    print(f"  NaN fraction = {nan_frac:.6f}")
    print(f"  values < 0 = {n_lt_0}")
    print(f"  values > 1 = {n_gt_1}")

if __name__ == "__main__":
    main()
