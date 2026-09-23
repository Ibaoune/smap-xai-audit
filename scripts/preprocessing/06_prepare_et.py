import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd

"""
SMAP-XAI: Prepare Evapotranspiration

Purpose
-------
Preprocess the canonical daily evapotranspiration (ET) predictor/response 
from LIS_HIST output.

Source
------
Experiment: OPL, DA-NoCDF, DA-CDF
Variable: Evap_tavg
Units: kg m-2 s-1
Temporal Support: 24-hour mean flux (filename represents END of period)

Physical Meaning & Sign Convention
----------------------------------
`Evap_tavg` is total land-surface evapotranspiration. It includes bare soil 
evaporation, transpiration, canopy evaporation, and snow sublimation.
The sign convention is positive upward (flux from land to atmosphere). 
Negative values represent condensation/deposition (dew/frost) and are physically 
valid; they are preserved, not clipped.

Conversion
----------
et = Evap_tavg * 86400
New Units: mm day-1

Outputs
-------
Annual NetCDF files with canonical `et` variable.
Location: data/interim/noahmp/<experiment>/et/et_<year>.nc

Storage Decision
----------------
ET is a prognostic model response, explicitly dependent on the assimilation 
and perturbation logic. Therefore, it is stored separately for each experiment 
(unlike shared meteorological forcing).

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def process_et(experiment, year):
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
    
    out_dir = f"data/interim/noahmp/{experiment}/et"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Discovering LIS_HIST files for {experiment} year {year}...")
    files = discover_lis_hist_files(base_in, year)
    
    if len(files) not in [365, 366]:
        raise ValueError(f"Unexpected number of files discovered: {len(files)}")
        
    print(f"Discovered {len(files)} files.")
    
    ref_date, ref_path = files[0]
    ref_var, ref_ds = extract_noahmp_variable(ref_path, "Evap_tavg")
    ref_lat, ref_lon = construct_canonical_coords(ref_ds)
    
    times = []
    data_list = []
    
    for dt, path in files:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing expected file: {path}")
            
        var, ds = extract_noahmp_variable(path, "Evap_tavg")
        
        if not validate_grid_consistency(ds, ref_lat, ref_lon):
            raise ValueError(f"Grid mismatch found in file: {path}")
            
        times.append(dt)
        # Convert to mm day-1
        et_vals = (var.values * 86400.0).astype(np.float32)
        data_list.append(et_vals)
        
    et_array = np.stack(data_list, axis=0)
    
    ds_out = xr.Dataset(
        {'et': (['time', 'lat', 'lon'], et_array)},
        coords={
            'time': pd.DatetimeIndex(times),
            'lat': ref_lat,
            'lon': ref_lon
        }
    )
    
    ds_out['et'].attrs['long_name'] = "Daily evapotranspiration"
    ds_out['et'].attrs['units'] = "mm day-1"
    ds_out['et'].attrs['source_variable'] = "Evap_tavg"
    ds_out['et'].attrs['source_units'] = "kg m-2 s-1"
    ds_out['et'].attrs['conversion'] = "Evap_tavg * 86400"
    ds_out['et'].attrs['temporal_support'] = "daily total derived from 24-hour mean flux"
    ds_out['et'].attrs['timestamp_convention'] = "canonical date is one day before LIS_HIST filename timestamp"
    
    ds_out.attrs['source_experiment'] = experiment
    ds_out.attrs['xai_role'] = "baseline water-flux predictor and downstream assimilation response"
    
    out_path = os.path.join(out_dir, f"et_{year}.nc")
    encoding = {'et': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(-9999.0)}}
    ds_out.to_netcdf(out_path, encoding=encoding)
    
    print(f"Saved {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=str, required=True, choices=["opl", "da_nocdf", "da_cdf"])
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    
    process_et(args.experiment, args.year)
