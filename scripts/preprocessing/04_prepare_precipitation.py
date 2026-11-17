import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

"""
SMAP-XAI: Prepare Precipitation Forcing

Purpose
-------
Preprocess the canonical daily precipitation predictor from the deterministic, 
unperturbed OPL LIS_HIST output. The raw TotalPrecip_tavg represents the 
environmental meteorological forcing without DA ensemble stochastic noise.

Source
------
Experiment: OPL
Variable: TotalPrecip_tavg
Units: kg m-2 s-1
Temporal Support: 24-hour mean flux (filename represents END of period)

Conversion
----------
precipitation = TotalPrecip_tavg * 86400
New Units: mm day-1

Outputs
-------
Annual NetCDF files with canonical `precipitation` variable.
Location: data/interim/noahmp/forcing/precipitation/precipitation_<year>.nc

Storage Decision
----------------
Only ONE shared forcing representation is stored because DA outputs contain 
undesirable stochastic perturbations, and the underlying environmental boundary 
conditions (MERRA2 + IMERG) are identical across all experiments.

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def process_precipitation(year):
    import sys
    sys.path.append('src')
    from smap_xai.preprocessing.noahmp import discover_lis_hist_files, parse_lis_hist_timestamp, extract_noahmp_variable, construct_canonical_coords, validate_grid_consistency
    
    experiment = "OPL_noirr_2016_2020"
    base_in = f"/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/{experiment}"
    
    out_dir = "data/interim/noahmp/forcing/precipitation"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Discovering LIS_HIST files for OPL year {year}...")
    files = discover_lis_hist_files(base_in, year)
    
    if len(files) not in [365, 366]:
        raise ValueError(f"Unexpected number of files discovered: {len(files)}")
        
    print(f"Discovered {len(files)} files.")
    
    # Process reference file to get grid
    ref_date, ref_path = files[0]
    ref_var, ref_ds = extract_noahmp_variable(ref_path, "TotalPrecip_tavg")
    ref_lat, ref_lon = construct_canonical_coords(ref_ds)
    
    times = []
    data_list = []
    
    for dt, path in files:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing expected file: {path}")
            
        var, ds = extract_noahmp_variable(path, "TotalPrecip_tavg")
        
        if not validate_grid_consistency(ds, ref_lat, ref_lon):
            raise ValueError(f"Grid mismatch found in file: {path}")
            
        times.append(dt)
        # Convert to mm day-1
        precip = (var.values * 86400.0).astype(np.float32)
        data_list.append(precip)
        
    precip_array = np.stack(data_list, axis=0)
    
    ds_out = xr.Dataset(
        {'precipitation': (['time', 'lat', 'lon'], precip_array)},
        coords={
            'time': pd.DatetimeIndex(times),
            'lat': ref_lat,
            'lon': ref_lon
        }
    )
    
    ds_out['precipitation'].attrs['long_name'] = "Daily total precipitation"
    ds_out['precipitation'].attrs['units'] = "mm day-1"
    ds_out['precipitation'].attrs['source_variable'] = "TotalPrecip_tavg"
    ds_out['precipitation'].attrs['source_units'] = "kg m-2 s-1"
    ds_out['precipitation'].attrs['conversion'] = "TotalPrecip_tavg * 86400"
    ds_out['precipitation'].attrs['temporal_support'] = "daily total derived from 24-hour mean precipitation flux"
    ds_out['precipitation'].attrs['timestamp_convention'] = "canonical date is one day before LIS_HIST filename timestamp"
    
    ds_out.attrs['forcing_source'] = "MERRA2 with GPM IMERG overlay"
    ds_out.attrs['source_experiment'] = "OPL deterministic/unperturbed forcing representation"
    ds_out.attrs['xai_role'] = "shared environmental meteorological predictor"
    ds_out.attrs['provenance'] = "extracted from standardized LIS/Noah-MP forcing output. DA-specific HIST precipitation intentionally not used because it reflects stochastic forcing perturbations."
    
    out_path = os.path.join(out_dir, f"precipitation_{year}.nc")
    encoding = {'precipitation': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(-9999.0)}}
    ds_out.to_netcdf(out_path, encoding=encoding)
    
    print(f"Saved {out_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    
    process_precipitation(args.year)
