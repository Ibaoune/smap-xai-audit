import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

"""
SMAP-XAI: Prepare Air Temperature Forcing

Purpose
-------
Preprocess the canonical daily near-surface air temperature predictor from 
the deterministic, unperturbed OPL LIS_HIST output.

Source
------
Experiment: OPL
Variable: Tair_f_tavg
Units: K
Temporal Support: 24-hour mean temperature (filename represents END of period)

Outputs
-------
Annual NetCDF files with canonical `air_temperature` variable.
Location: data/interim/noahmp/forcing/air_temperature/air_temperature_<year>.nc

Storage Decision
----------------
Air temperature is not stochastically perturbed in the DA experiments (unlike precipitation).
However, due to DA ensemble averaging (N=20) over identical values, tiny floating-point 
precision artifacts (~1e-5 K) appear in DA outputs. To retain the exact unperturbed 
environmental boundary conditions without arithmetic noise, the OPL representation 
is used as the single shared canonical forcing dataset.

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def process_temperature(year):
    import sys
    sys.path.append('src')
    from smap_xai.preprocessing.noahmp import discover_lis_hist_files, extract_noahmp_variable, construct_canonical_coords, validate_grid_consistency
    
    experiment = "OPL_noirr_2016_2020"
    base_in = f"/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/{experiment}"
    
    out_dir = "data/interim/noahmp/forcing/air_temperature"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Discovering LIS_HIST files for OPL year {year}...")
    files = discover_lis_hist_files(base_in, year)
    
    if len(files) not in [365, 366]:
        raise ValueError(f"Unexpected number of files discovered: {len(files)}")
        
    print(f"Discovered {len(files)} files.")
    
    ref_date, ref_path = files[0]
    ref_var, ref_ds = extract_noahmp_variable(ref_path, "Tair_f_tavg")
    ref_lat, ref_lon = construct_canonical_coords(ref_ds)
    
    times = []
    data_list = []
    
    for dt, path in files:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing expected file: {path}")
            
        var, ds = extract_noahmp_variable(path, "Tair_f_tavg")
        
        if not validate_grid_consistency(ds, ref_lat, ref_lon):
            raise ValueError(f"Grid mismatch found in file: {path}")
            
        times.append(dt)
        # Keep native units in Kelvin, extract as float32
        data_list.append(var.values.astype(np.float32))
        
    tair_array = np.stack(data_list, axis=0)
    
    ds_out = xr.Dataset(
        {'air_temperature': (['time', 'lat', 'lon'], tair_array)},
        coords={
            'time': pd.DatetimeIndex(times),
            'lat': ref_lat,
            'lon': ref_lon
        }
    )
    
    ds_out['air_temperature'].attrs['long_name'] = "Daily mean near-surface air temperature"
    ds_out['air_temperature'].attrs['units'] = "K"
    ds_out['air_temperature'].attrs['source_variable'] = "Tair_f_tavg"
    ds_out['air_temperature'].attrs['source_units'] = "K"
    ds_out['air_temperature'].attrs['temporal_support'] = "daily mean derived from 24-hour time-averaged forcing"
    ds_out['air_temperature'].attrs['timestamp_convention'] = "canonical date is one day before LIS_HIST filename timestamp"
    
    ds_out.attrs['forcing_source'] = "MERRA2 with GPM IMERG overlay"
    ds_out.attrs['source_experiment'] = "OPL deterministic/unperturbed forcing representation"
    ds_out.attrs['xai_role'] = "shared environmental meteorological predictor"
    ds_out.attrs['provenance'] = "extracted from standardized LIS/Noah-MP forcing output. OPL used to avoid floating-point arithmetic artifacts present in DA ensemble-averaging."
    
    out_path = os.path.join(out_dir, f"air_temperature_{year}.nc")
    encoding = {'air_temperature': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(-9999.0)}}
    ds_out.to_netcdf(out_path, encoding=encoding)
    
    print(f"Saved {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    
    process_temperature(args.year)
