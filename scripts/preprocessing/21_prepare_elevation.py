#!/usr/bin/env python3
"""
Static Elevation Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Extracts static elevation from lis_input_NorthMor_5km.nc,
validates the grid against canonical SSM output, applies the
canonical valid-land mask, and saves the output without a time dimension.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def prepare_elevation(raw_file, ref_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load source static file
    ds_raw = xr.open_dataset(raw_file)
    elev_raw = ds_raw['ELEVATION'].values
    lat_raw = ds_raw['lat'].values
    lon_raw = ds_raw['lon'].values
    
    # Check orientation
    lat_increasing = lat_raw[1, 0] > lat_raw[0, 0]
    lon_increasing = lon_raw[0, 1] > lon_raw[0, 0]
    
    # Inspect ELEVFGRD as requested
    elevfgrd = ds_raw['ELEVFGRD'].values
    print("================ ELEVFGRD INSPECTION ================")
    print(f"Variable name: ELEVFGRD")
    print(f"Dimensions: {ds_raw['ELEVFGRD'].dims}")
    print(f"Shape: {elevfgrd.shape}")
    print(f"dtype: {elevfgrd.dtype}")
    print(f"Attributes: {ds_raw['ELEVFGRD'].attrs}")
    print(f"min: {np.nanmin(elevfgrd)}, max: {np.nanmax(elevfgrd)}")
    print(f"finite count: {np.sum(~np.isnan(elevfgrd))}, missing: {np.sum(np.isnan(elevfgrd))}")

    print("\n================ SOURCE ELEVATION AUDIT (ELEVATION) ================")
    print(f"Variable name: ELEVATION")
    print(f"Dimensions: {ds_raw['ELEVATION'].dims}")
    print(f"Shape: {elev_raw.shape}")
    print(f"dtype: {elev_raw.dtype}")
    print(f"Attributes: {ds_raw['ELEVATION'].attrs}")
    print(f"Latitude increasing: {lat_increasing}")
    print(f"Longitude increasing: {lon_increasing}")
    
    finite_raw = ~np.isnan(elev_raw)
    cond_raw = elev_raw[finite_raw]
    print("\n  -- RAW SOURCE STATISTICS (Unmasked) --")
    print(f"  finite count: {np.sum(finite_raw)}")
    print(f"  missing count: {np.sum(~finite_raw)}")
    print(f"  min: {np.nanmin(cond_raw)}")
    print(f"  max: {np.nanmax(cond_raw)}")
    print(f"  mean: {np.nanmean(cond_raw)}")
    print(f"  median: {np.nanmedian(cond_raw)}")
    print(f"  p01: {np.percentile(cond_raw, 1)}")
    print(f"  p05: {np.percentile(cond_raw, 5)}")
    print(f"  p25: {np.percentile(cond_raw, 25)}")
    print(f"  p75: {np.percentile(cond_raw, 75)}")
    print(f"  p95: {np.percentile(cond_raw, 95)}")
    print(f"  p99: {np.percentile(cond_raw, 99)}")
    print(f"  values < 0: {np.sum(cond_raw < 0)}")
    print(f"  values == 0: {np.sum(cond_raw == 0)}")
    print(f"  values > 0: {np.sum(cond_raw > 0)}")
    
    # 2. Load reference canonical daily file
    ds_ref = xr.open_dataset(ref_file)
    lat_ref_1d = ds_ref['lat'].values
    lon_ref_1d = ds_ref['lon'].values
    lon_ref, lat_ref = np.meshgrid(lon_ref_1d, lat_ref_1d)
    
    # 3. Grid Compatibility
    lat_diff = np.max(np.abs(lat_raw - lat_ref))
    lon_diff = np.max(np.abs(lon_raw - lon_ref))
    
    print("\n================ GRID COMPATIBILITY ================")
    print(f"Max absolute lat difference: {lat_diff:.6e}")
    print(f"Max absolute lon difference: {lon_diff:.6e}")
    if lat_diff > 1e-5 or lon_diff > 1e-5:
        raise ValueError("Source grid does not match canonical grid!")

    # 4. Canonical Land Mask
    # Get mask from daily_innovation (or similar) observation_frequency
    freq = ds_ref['observation_frequency'].values
    # Assuming freq has shape (time, lat, lon)
    # The valid land is wherever freq is not NaN (it is constant across time)
    land_mask = ~np.isnan(freq[0])
    
    num_valid = np.sum(land_mask)
    num_masked = np.sum(~land_mask)
    masked_frac = num_masked / land_mask.size
    
    print("\n================ CANONICAL LAND MASK ================")
    print(f"Valid land pixels: {num_valid}")
    print(f"Masked pixels: {num_masked}")
    print(f"Masked fraction: {masked_frac:.6f}")
    
    # 5. Apply Mask
    canonical_elev = np.where(land_mask, elev_raw, np.nan)
    
    finite_mask = ~np.isnan(canonical_elev)
    if not np.array_equal(finite_mask, land_mask):
        print("WARNING: Some valid land pixels have NaN elevation in source!")
        missing_on_land = np.sum(land_mask & np.isnan(elev_raw))
        print(f"Missing on valid land: {missing_on_land}")
    else:
        print("Mask consistency verified: isfinite(elevation) == canonical_valid_land_mask")

    # 6. Source-to-Processed Identity (on valid land)
    diff = np.abs(canonical_elev[land_mask] - elev_raw[land_mask])
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    unequal_exact = np.sum(canonical_elev[land_mask] != elev_raw[land_mask])
    unequal_1e6 = np.sum(diff > 1e-6)
    
    print("\n================ SOURCE-TO-PROCESSED IDENTITY ================")
    print(f"Max absolute diff: {max_diff}")
    print(f"Mean absolute diff: {mean_diff}")
    print(f"Unequal exact: {unequal_exact}")
    print(f"Unequal atol 1e-6: {unequal_1e6}")
    
    # 7. Coordinate Sanity
    min_idx = np.unravel_index(np.nanargmin(canonical_elev), canonical_elev.shape)
    max_idx = np.unravel_index(np.nanargmax(canonical_elev), canonical_elev.shape)
    
    print("\n================ COORDINATE SANITY CHECK ================")
    print(f"Min elevation: {canonical_elev[min_idx]} at ({lat_ref[min_idx]:.4f}, {lon_ref[min_idx]:.4f})")
    print(f"Max elevation: {canonical_elev[max_idx]} at ({lat_ref[max_idx]:.4f}, {lon_ref[max_idx]:.4f})")
    
    h, w = canonical_elev.shape
    rep_pts = {
        'NW': (h-1, 0),
        'NE': (h-1, w-1),
        'SW': (0, 0),
        'SE': (0, w-1),
        'Center': (h//2, w//2)
    }
    for k, (i, j) in rep_pts.items():
        val = canonical_elev[i,j]
        status = "masked" if np.isnan(val) else str(val)
        print(f"{k} portion [idx: {i},{j}]: Elev = {status} at ({lat_ref[i,j]:.4f}, {lon_ref[i,j]:.4f})")
        
    # 8. Output
    ds_out = xr.Dataset(
        {
            'elevation': (['lat', 'lon'], canonical_elev)
        },
        coords={
            'lat': lat_ref_1d,
            'lon': lon_ref_1d
        },
        attrs={
            'long_name': 'Surface elevation',
            'units': 'm',
            'source_file': os.path.basename(raw_file),
            'source_variable': 'ELEVATION',
            'temporal_support': 'static',
            'spatial_support': 'canonical Noah-MP valid-land grid',
            'masking': 'NaN outside canonical valid-land support',
            'xai_role': 'static physiographic predictor'
        }
    )
    
    out_file = os.path.join(out_dir, 'elevation.nc')
    ds_out.to_netcdf(out_file, encoding={'elevation': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"\nSaved {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_file', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc')
    parser.add_argument('--ref_file', type=str, default='data/processed/daily_enkf/da_cdf/observation_frequency/observation_frequency_2016.nc')
    parser.add_argument('--out_dir', type=str, default='data/processed/static/elevation')
    args = parser.parse_args()
    
    prepare_elevation(args.raw_file, args.ref_file, args.out_dir)
