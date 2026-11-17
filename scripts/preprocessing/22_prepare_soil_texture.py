#!/usr/bin/env python3
"""
Static Soil Texture Preprocessing

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Extracts static fractional soil texture from lis_input_NorthMor_5km.nc,
validates the class/fraction semantics, applies the canonical valid-land mask,
and saves the canonical output.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def prepare_soil_texture(raw_file, ref_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load source static file
    ds_raw = xr.open_dataset(raw_file)
    
    # Identify variables containing 'TEXT', 'SOIL', 'TEX'
    candidates = [v for v in ds_raw.variables if any(k in v.upper() for k in ['TEXT', 'SOIL', 'TEX'])]
    print("================ INVENTORY ALL SOIL-TEXTURE CANDIDATES ================")
    for var in candidates:
        print(f"Variable: {var}")
        print(f"  Dimensions: {ds_raw[var].dims}")
        print(f"  Shape: {ds_raw[var].shape}")
        print(f"  dtype: {ds_raw[var].dtype}")
        print(f"  Attributes: {ds_raw[var].attrs}")
        print(f"  Min: {np.nanmin(ds_raw[var].values)}")
        print(f"  Max: {np.nanmax(ds_raw[var].values)}")
        print("  ---")
        
    # The selected variable is TEXTURE
    tex_raw = ds_raw['TEXTURE'].values
    print("\n================ EXACT TEXTURE DATA MODEL ================")
    print(f"Selected variable: TEXTURE")
    print(f"Dimension order: {ds_raw['TEXTURE'].dims}")
    print("Logical structure: stack of 16 class fractions (soiltypes, north_south, east_west).")
    
    # 2. Load reference canonical daily file
    ds_ref = xr.open_dataset(ref_file)
    lat_ref_1d = ds_ref['lat'].values
    lon_ref_1d = ds_ref['lon'].values
    lon_ref, lat_ref = np.meshgrid(lon_ref_1d, lat_ref_1d)
    
    lat_raw = ds_raw['lat'].values
    lon_raw = ds_raw['lon'].values
    
    # 3. Grid Compatibility
    lat_diff = np.max(np.abs(lat_raw - lat_ref))
    lon_diff = np.max(np.abs(lon_raw - lon_ref))
    
    print("\n================ GRID COMPATIBILITY ================")
    print(f"Max absolute lat difference: {lat_diff:.6e}")
    print(f"Max absolute lon difference: {lon_diff:.6e}")
    if lat_diff > 1e-5 or lon_diff > 1e-5:
        raise ValueError("Source grid does not match canonical grid!")

    # 4. Source Fraction Audit (Unmasked)
    sums_raw = np.sum(tex_raw, axis=0)
    print("\n================ SOURCE FRACTION AUDIT ================")
    print("Convention: [0,1] with sum ≈ 1")
    print(f"Per-pixel sum distribution (Unmasked):")
    print(f"  min: {np.nanmin(sums_raw)}")
    print(f"  max: {np.nanmax(sums_raw)}")
    print(f"  mean: {np.nanmean(sums_raw)}")
    print(f"  median: {np.nanmedian(sums_raw)}")
    print(f"  p01: {np.percentile(sums_raw, 1)}")
    print(f"  p05: {np.percentile(sums_raw, 5)}")
    print(f"  p95: {np.percentile(sums_raw, 95)}")
    print(f"  p99: {np.percentile(sums_raw, 99)}")
    print(f"  sum ≈ 1 count: {np.sum(np.abs(sums_raw - 1) < 1e-5)}")
    
    # 5. Canonical Land Mask
    freq = ds_ref['observation_frequency'].values
    land_mask = ~np.isnan(freq[0])
    
    num_valid = np.sum(land_mask)
    num_masked = np.sum(~land_mask)
    print("\n================ CANONICAL LAND MASK ================")
    print(f"Valid land pixels: {num_valid}")
    print(f"Masked pixels: {num_masked}")
    
    # 6. Apply Mask
    # Expand land_mask to 3D: (16, 121, 181)
    land_mask_3d = np.broadcast_to(land_mask, tex_raw.shape)
    canonical_tex = np.where(land_mask_3d, tex_raw, np.nan)
    
    # Check for missing on valid land
    missing_on_land = np.sum(land_mask_3d & np.isnan(tex_raw))
    print(f"Missing on valid land count: {missing_on_land}")
    if missing_on_land > 0:
        raise ValueError("Missing texture values found within canonical valid land mask!")
        
    # 7. Fraction Validity (on canonical land)
    print("\n================ FRACTION VALIDITY ================")
    cond_tex = canonical_tex[:, land_mask] # Shape: (16, num_valid)
    print(f"Count with fraction < 0: {np.sum(cond_tex < 0)}")
    print(f"Count with fraction > 1: {np.sum(cond_tex > 1)}")
    
    cond_sums = np.sum(cond_tex, axis=0)
    print(f"Count sum differs from 1 by > 1e-6: {np.sum(np.abs(cond_sums - 1) > 1e-6)}")
    print(f"Count sum differs from 1 by > 1e-5: {np.sum(np.abs(cond_sums - 1) > 1e-5)}")
    print(f"Count sum differs from 1 by > 1e-4: {np.sum(np.abs(cond_sums - 1) > 1e-4)}")
    
    # 8. Mixture Structure
    active_classes = np.sum(cond_tex > 0, axis=0)
    max_fractions = np.max(cond_tex, axis=0)
    print("\n================ PIXEL MIXTURE STRUCTURE ================")
    for i in range(1, 17):
        count = np.sum(active_classes == i)
        if count > 0:
            print(f"Pixels with exactly {i} active classes: {count} ({count/num_valid:.2%})")
            
    print(f"\nPixels with max_fraction == 1: {np.sum(max_fractions == 1)}")
    print(f"Pixels with max_fraction >= 0.9: {np.sum(max_fractions >= 0.9)}")
    print(f"Pixels with max_fraction >= 0.75: {np.sum(max_fractions >= 0.75)}")
    print(f"Pixels with max_fraction >= 0.5: {np.sum(max_fractions >= 0.5)}")
    print(f"Pixels with max_fraction < 0.5: {np.sum(max_fractions < 0.5)}")
    
    # 9. Dominant-Class QC
    dominant_class = np.argmax(cond_tex, axis=0)
    print("\n================ DOMINANT-CLASS QC ================")
    for i in range(16):
        count = np.sum(dominant_class == i)
        if count > 0:
            print(f"Class {i+1} dominant count: {count} ({count/num_valid:.2%})")
            
    # Check for ties
    is_max = cond_tex == max_fractions
    tie_counts = np.sum(is_max, axis=0)
    print(f"Number of ties: {np.sum(tie_counts > 1)}")
    
    # 10. Source-to-Processed Identity
    print("\n================ SOURCE-TO-PROCESSED IDENTITY ================")
    diff = np.abs(cond_tex - tex_raw[:, land_mask])
    print(f"Max absolute diff: {np.max(diff)}")
    print(f"Mean absolute diff: {np.mean(diff)}")
    print(f"Unequal exact count: {np.sum(diff > 0)}")
    
    # 11. Composition-Sum Validation
    sums_map = np.sum(canonical_tex, axis=0)
    print("\n================ COMPOSITION-SUM VALIDATION ================")
    valid_sums = sums_map[land_mask]
    print(f"min: {np.min(valid_sums)}")
    print(f"max: {np.max(valid_sums)}")
    print(f"mean: {np.mean(valid_sums)}")
    print(f"median: {np.median(valid_sums)}")
    print(f"maximum |sum - 1|: {np.max(np.abs(valid_sums - 1))}")
    
    # 12. Output
    ds_out = xr.Dataset(
        {
            'soil_texture_fraction': (['texture_class', 'lat', 'lon'], canonical_tex)
        },
        coords={
            'texture_class': np.arange(1, 17, dtype=np.int32),
            'lat': lat_ref_1d,
            'lon': lon_ref_1d
        },
        attrs={
            'long_name': 'Soil texture class area fraction',
            'units': '1',
            'source_file': os.path.basename(raw_file),
            'source_variable': 'TEXTURE',
            'temporal_support': 'static',
            'spatial_support': 'canonical Noah-MP valid-land grid',
            'composition': 'fractions across texture_class sum approximately to 1 on valid land',
            'masking': 'NaN outside canonical valid-land support',
            'xai_role': 'static soil-texture compositional predictor'
        }
    )
    
    out_file = os.path.join(out_dir, 'soil_texture_fraction.nc')
    ds_out.to_netcdf(out_file, encoding={'soil_texture_fraction': {'dtype': 'float32', 'zlib': True, 'complevel': 4}})
    print(f"\nSaved {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_file', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc')
    parser.add_argument('--ref_file', type=str, default='data/processed/daily_enkf/da_cdf/observation_frequency/observation_frequency_2016.nc')
    parser.add_argument('--out_dir', type=str, default='data/processed/static/soil_texture')
    args = parser.parse_args()
    
    prepare_soil_texture(args.raw_file, args.ref_file, args.out_dir)
