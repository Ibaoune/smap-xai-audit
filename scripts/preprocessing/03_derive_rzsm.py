import os
import argparse
import xarray as xr
import numpy as np

"""
SMAP-XAI: Derive RZSM

Purpose
-------
Derives the canonical daily 0-100 cm root-zone soil moisture (rzsm).
Formula: rzsm = 0.10*ssm + 0.30*sm_layer2 + 0.60*sm_layer3
Layer 4 (100-200 cm) is explicitly excluded.

Inputs
------
Standardized interim NetCDF files for:
- ssm
- sm_layer2
- sm_layer3

Outputs
-------
Annual NetCDF files with `rzsm` variable.
Location: data/processed/daily_model/<experiment>/rzsm/rzsm_<year>.nc

Units
-----
m3 m-3

Assumptions
-----------
Inputs are already standardized, with matching grids and daily temporal support.

CLI Arguments
-------------
--experiment: opl, da_nocdf, or da_cdf
--year: YYYY

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

def derive_rzsm(experiment, year):
    base_in = "data/interim/noahmp"
    base_out = f"data/processed/daily_model/{experiment}/rzsm"
    os.makedirs(base_out, exist_ok=True)
    
    path_ssm = f"{base_in}/{experiment}/ssm/ssm_{year}.nc"
    path_l2 = f"{base_in}/{experiment}/sm_layer2/sm_layer2_{year}.nc"
    path_l3 = f"{base_in}/{experiment}/sm_layer3/sm_layer3_{year}.nc"
    
    ds_ssm = xr.open_dataset(path_ssm)
    ds_l2 = xr.open_dataset(path_l2)
    ds_l3 = xr.open_dataset(path_l3)
    
    # Pre-derivation alignment check
    assert ds_ssm['time'].equals(ds_l2['time']), "Time mismatch ssm vs l2"
    assert ds_ssm['time'].equals(ds_l3['time']), "Time mismatch ssm vs l3"
    assert ds_ssm['lat'].equals(ds_l2['lat']), "Lat mismatch ssm vs l2"
    assert ds_ssm['lat'].equals(ds_l3['lat']), "Lat mismatch ssm vs l3"
    assert ds_ssm['lon'].equals(ds_l2['lon']), "Lon mismatch ssm vs l2"
    assert ds_ssm['lon'].equals(ds_l3['lon']), "Lon mismatch ssm vs l3"
    assert ds_ssm['ssm'].shape == ds_l2['sm_layer2'].shape, "Shape mismatch ssm vs l2"
    assert ds_ssm['ssm'].shape == ds_l3['sm_layer3'].shape, "Shape mismatch ssm vs l3"
    
    mask_ssm = np.isnan(ds_ssm['ssm'].values)
    mask_l2 = np.isnan(ds_l2['sm_layer2'].values)
    mask_l3 = np.isnan(ds_l3['sm_layer3'].values)
    
    assert np.array_equal(mask_ssm, mask_l2), "Mask mismatch ssm vs l2"
    assert np.array_equal(mask_ssm, mask_l3), "Mask mismatch ssm vs l3"
    
    # Calculate RZSM
    rzsm_data = 0.10 * ds_ssm['ssm'] + 0.30 * ds_l2['sm_layer2'] + 0.60 * ds_l3['sm_layer3']
    rzsm_data = rzsm_data.astype(np.float32)
    
    ds_out = xr.Dataset(
        {'rzsm': (['time', 'lat', 'lon'], rzsm_data.values)},
        coords={
            'time': ds_ssm['time'],
            'lat': ds_ssm['lat'],
            'lon': ds_ssm['lon']
        }
    )
    
    # Set metadata
    ds_out['rzsm'].attrs['long_name'] = "Root-zone soil moisture, 0-100 cm"
    ds_out['rzsm'].attrs['units'] = "m3 m-3"
    ds_out['rzsm'].attrs['derivation'] = "0.10*ssm + 0.30*sm_layer2 + 0.60*sm_layer3"
    ds_out['rzsm'].attrs['depth'] = "0-100 cm"
    ds_out['rzsm'].attrs['temporal_support'] = "daily"
    ds_out.attrs['provenance'] = "Derived from standardized SMAP-XAI interim Noah-MP soil-moisture products."
    
    out_path = f"{base_out}/rzsm_{year}.nc"
    encoding = {'rzsm': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(-9999.0)}}
    ds_out.to_netcdf(out_path, encoding=encoding)
    print(f"Saved {out_path}")
    
    # Physical consistency check (convex average)
    min_val = np.minimum(np.minimum(ds_ssm['ssm'].values, ds_l2['sm_layer2'].values), ds_l3['sm_layer3'].values)
    max_val = np.maximum(np.maximum(ds_ssm['ssm'].values, ds_l2['sm_layer2'].values), ds_l3['sm_layer3'].values)
    
    valid = ~mask_ssm
    rzsm_valid = rzsm_data.values[valid]
    min_valid = min_val[valid]
    max_valid = max_val[valid]
    
    violations = np.sum((rzsm_valid < min_valid - 1e-6) | (rzsm_valid > max_valid + 1e-6))
    print(f"Convex-average violations: {violations}")
    assert violations == 0, "Physical consistency violated: rzsm outside input bounds"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=str, required=True, choices=["opl", "da_nocdf", "da_cdf"])
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    
    derive_rzsm(args.experiment, args.year)
