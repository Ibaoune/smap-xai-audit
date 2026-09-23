import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

"""
SMAP-XAI: Prepare Surface Runoff

Purpose
-------
Preprocess the canonical daily surface runoff response from LIS_HIST output.

Source
------
Experiment: OPL, DA-NoCDF, DA-CDF
Variable: Qs_tavg
Units: kg m-2 s-1
Temporal Support: 24-hour mean flux (filename represents END of period)

Physical Meaning & Sign Convention
----------------------------------
`Qs_tavg` represents strictly surface runoff (overland flow). Subsurface runoff 
(baseflow) is distinctly captured by `Qsb_tavg`.
The sign convention is positive representing water leaving the land column 
via the surface. Negative values are generally non-physical for runoff in this model.

Conversion
----------
surface_runoff = Qs_tavg * 86400
New Units: mm day-1

Outputs
-------
Annual NetCDF files with canonical `surface_runoff` variable.
Location: data/interim/noahmp/<experiment>/surface_runoff/surface_runoff_<year>.nc

Storage Decision
----------------
Surface runoff is a prognostic model response, dependent on the assimilation 
and moisture state logic. Therefore, it is stored separately for each experiment.

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def process_surface_runoff(experiment, year):
    import sys
    sys.path.append('src')
    from smap_xai.preprocessing.noahmp import discover_lis_hist_files, extract_noahmp_variable, construct_canonical_coords, validate_grid_consistency
    
    # Map friendly experiment name to actual folder
    exp_map = {
        "opl": "OPL_noirr_2016_2020",
        "da_nocdf": "DA_nocdf_noirr_2016_2020",
        "da_cdf": "DA_cdf_noirr_2016_2020"
    }
    if experiment not in exp_map:
        raise ValueError(f"Unknown experiment: {experiment}")
        
    actual_exp = exp_map[experiment]
    base_in = f"/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/{actual_exp}"
    
    out_dir = f"data/interim/noahmp/{experiment}/surface_runoff"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Discovering LIS_HIST files for {experiment} year {year}...")
    files = discover_lis_hist_files(base_in, year)
    
    if len(files) not in [365, 366]:
        raise ValueError(f"Unexpected number of files discovered: {len(files)}")
        
    print(f"Discovered {len(files)} files.")
    
    ref_date, ref_path = files[0]
    ref_var, ref_ds = extract_noahmp_variable(ref_path, "Qs_tavg")
    ref_lat, ref_lon = construct_canonical_coords(ref_ds)
    
    times = []
    data_list = []
    
    for dt, path in files:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing expected file: {path}")
            
        var, ds = extract_noahmp_variable(path, "Qs_tavg")
        
        if not validate_grid_consistency(ds, ref_lat, ref_lon):
            raise ValueError(f"Grid mismatch found in file: {path}")
            
        times.append(dt)
        # Convert to mm day-1
        qs_vals = (var.values * 86400.0).astype(np.float32)
        data_list.append(qs_vals)
        
    qs_array = np.stack(data_list, axis=0)
    
    ds_out = xr.Dataset(
        {'surface_runoff': (['time', 'lat', 'lon'], qs_array)},
        coords={
            'time': pd.DatetimeIndex(times),
            'lat': ref_lat,
            'lon': ref_lon
        }
    )
    
    ds_out['surface_runoff'].attrs['long_name'] = "Daily surface runoff"
    ds_out['surface_runoff'].attrs['units'] = "mm day-1"
    ds_out['surface_runoff'].attrs['source_variable'] = "Qs_tavg"
    ds_out['surface_runoff'].attrs['source_units'] = "kg m-2 s-1"
    ds_out['surface_runoff'].attrs['conversion'] = "Qs_tavg * 86400"
    ds_out['surface_runoff'].attrs['temporal_support'] = "daily total derived from 24-hour mean flux"
    ds_out['surface_runoff'].attrs['timestamp_convention'] = "canonical date is one day before LIS_HIST filename timestamp"
    
    ds_out.attrs['source_experiment'] = experiment
    ds_out.attrs['xai_role'] = "baseline water-flux predictor and downstream assimilation response"
    
    out_path = os.path.join(out_dir, f"surface_runoff_{year}.nc")
    encoding = {'surface_runoff': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(-9999.0)}}
    ds_out.to_netcdf(out_path, encoding=encoding)
    
    print(f"Saved {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=str, required=True, choices=["opl", "da_nocdf", "da_cdf"])
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    
    process_surface_runoff(args.experiment, args.year)
