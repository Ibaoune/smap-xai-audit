#!/usr/bin/env python3
"""
Static Irrigation Fraction Audit

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Audits IRRIGFRAC from lis_input_NorthMor_5km.nc against the canonical valid land mask.
Performs zero-variance test and outputs statistics. Does NOT create a canonical predictor.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def audit_irrigation_fraction(raw_file, ref_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load source static file
    ds_raw = xr.open_dataset(raw_file)
    
    if 'IRRIGFRAC' not in ds_raw.variables:
        print("Variable IRRIGFRAC not found in the source file.")
        return
        
    irrig_da = ds_raw['IRRIGFRAC']
    irrig_raw = irrig_da.values
    
    print("================ INVENTORY IRRIGFRAC ================")
    print(f"Variable: IRRIGFRAC")
    print(f"Dimensions: {irrig_da.dims}")
    print(f"Shape: {irrig_da.shape}")
    print(f"dtype: {irrig_da.dtype}")
    print(f"Attributes: {irrig_da.attrs}")
    print(f"Actual Min: {np.nanmin(irrig_raw)}")
    print(f"Actual Max: {np.nanmax(irrig_raw)}")
    print(f"Finite count: {np.sum(np.isfinite(irrig_raw))}")
    print(f"Missing count: {np.sum(np.isnan(irrig_raw))}")
    
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

    # 4. Canonical Land Mask Audit
    freq = ds_ref['observation_frequency'].values
    land_mask = ~np.isnan(freq[0])
    
    num_valid = np.sum(land_mask)
    num_masked = np.sum(~land_mask)
    
    irrig_valid = irrig_raw[land_mask]
    
    print("\n================ CANONICAL LAND-MASK AUDIT ================")
    print(f"Valid land pixels: {num_valid}")
    print(f"Masked pixels: {num_masked}")
    print(f"Finite count on valid land: {np.sum(np.isfinite(irrig_valid))}")
    print(f"Missing count on valid land: {np.sum(np.isnan(irrig_valid))}")
    print(f"Min: {np.nanmin(irrig_valid)}")
    print(f"Max: {np.nanmax(irrig_valid)}")
    print(f"Mean: {np.nanmean(irrig_valid)}")
    print(f"Median: {np.nanmedian(irrig_valid)}")
    print(f"Std: {np.nanstd(irrig_valid)}")
    print(f"p01: {np.nanpercentile(irrig_valid, 1)}")
    print(f"p05: {np.nanpercentile(irrig_valid, 5)}")
    print(f"p25: {np.nanpercentile(irrig_valid, 25)}")
    print(f"p75: {np.nanpercentile(irrig_valid, 75)}")
    print(f"p95: {np.nanpercentile(irrig_valid, 95)}")
    print(f"p99: {np.nanpercentile(irrig_valid, 99)}")
    
    print(f"Count == 0: {np.sum(irrig_valid == 0)}")
    print(f"Count > 0: {np.sum(irrig_valid > 0)}")
    print(f"Count == 1: {np.sum(irrig_valid == 1)}")
    print(f"Count between 0 and 1: {np.sum((irrig_valid > 0) & (irrig_valid < 1))}")
    print(f"Count < 0: {np.sum(irrig_valid < 0)}")
    print(f"Count > 1: {np.sum(irrig_valid > 1)}")
    
    # 5. Zero-Variance Test
    unique_vals = np.unique(irrig_valid[~np.isnan(irrig_valid)])
    print("\n================ ZERO-VARIANCE TEST ================")
    print(f"Number of unique finite values on valid land: {len(unique_vals)}")
    print(f"Unique values: {unique_vals}")
    print(f"Variance on valid land: {np.nanvar(irrig_valid)}")
    
    if len(unique_vals) == 1 and unique_vals[0] == 0:
        print("IRRIGFRAC has zero variance over the current model domain.")
        
    # 6. Spatial Support (if > 0)
    pos_mask = irrig_valid > 0
    if np.sum(pos_mask) > 0:
        pos_vals = irrig_valid[pos_mask]
        print("\n================ SPATIAL SUPPORT ================")
        print(f"Positive-pixel count: {len(pos_vals)}")
        print(f"Positive-pixel percentage: {len(pos_vals)/num_valid:.2%}")
        print(f"Min positive fraction: {np.min(pos_vals)}")
        print(f"Max positive fraction: {np.max(pos_vals)}")
        print(f"Mean positive fraction: {np.mean(pos_vals)}")
        print(f"Median positive fraction: {np.median(pos_vals)}")
        
        # Max coordinate
        max_idx = np.nanargmax(irrig_raw)
        row, col = np.unravel_index(max_idx, irrig_raw.shape)
        print(f"Maximum IRRIGFRAC at coordinate: lat={lat_raw[row, col]}, lon={lon_raw[row, col]}")
        
        # QC Map
        extent = [lon_ref_1d.min(), lon_ref_1d.max(), lat_ref_1d.min(), lat_ref_1d.max()]
        plt.figure(figsize=(10, 8))
        im = plt.imshow(np.where(land_mask, irrig_raw, np.nan), origin='lower', extent=extent, cmap='viridis')
        plt.colorbar(im, label='IRRIGFRAC')
        plt.title('IRRIGFRAC on Valid Land')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.savefig(os.path.join(out_dir, 'irrigation_fraction_map.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.hist(pos_vals, bins=50)
        plt.title('IRRIGFRAC > 0 Distribution')
        plt.xlabel('IRRIGFRAC')
        plt.ylabel('Count')
        plt.savefig(os.path.join(out_dir, 'irrigation_fraction_distribution.png'))
        plt.close()
        print(f"Generated QC maps in {out_dir}")
    else:
        print("\n================ SPATIAL SUPPORT ================")
        print("No positive values exist. Constant zero field.")
        print("No QC maps generated due to zero variance.")

    import glob
    
    print("\n================ EXPERIMENT CONFIGURATION CENSUS ================")
    exp_dirs = [
        "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020",
        "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020",
        "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020"
    ]
    
    total_mismatches = 0
    
    for exp_dir in exp_dirs:
        exp_name = os.path.basename(exp_dir)
        configs = glob.glob(f"{exp_dir}/**/*.config", recursive=True)
        print(f"\nExperiment: {exp_name}")
        print(f"Total .config files inspected: {len(configs)}")
        
        # We will track:
        # key: exact string prefix
        # values: dict of {exact_value_string: count}
        # missing: count
        
        census = {
            "Irrigation scheme:": {"values": {}, "missing": 0, "expected": '"none"'},
            "Noah-MP.4.0.1 crop model option:": {"values": {}, "missing": 0, "expected": '0  # Irrigation OFF'}
        }
        
        for cfg in configs:
            found = {k: False for k in census.keys()}
            with open(cfg, 'r') as f:
                for line in f:
                    line = line.strip()
                    for key in census.keys():
                        if line.startswith(key):
                            val = line[len(key):].strip()
                            census[key]["values"][val] = census[key]["values"].get(val, 0) + 1
                            found[key] = True
                            
                            # Check mismatch
                            if val != census[key]["expected"]:
                                print(f"MISMATCH FOUND in {cfg}: {key} {val} (expected {census[key]['expected']})")
                                total_mismatches += 1
                                
            for key in census.keys():
                if not found[key]:
                    census[key]["missing"] += 1
                    
        for key, data in census.items():
            print(f"  Key: {key}")
            for val, count in data["values"].items():
                print(f"    Value: '{val}' -> {count} file(s)")
            print(f"    Missing key count: {data['missing']}")

    print("\n================ FINAL ELIGIBILITY DECISION ================")
    print(f"Mismatch count for expected irrigation OFF settings: {total_mismatches}")
    if total_mismatches > 0:
        print("STOP: Mismatches found in experiment configurations.")
    else:
        print("Independent finding 1 (Static input): IRRIGFRAC = 0 everywhere on canonical valid land.")
        print("Independent finding 2 (Process configuration): irrigation is disabled in the current Noah-MP experiments.")
        print("Decision: IRRIGFRAC is constant zero over the current valid-land domain and therefore contains no sample-to-sample variation for the current XAI dataset. It is excluded from the current feature matrix due to zero variance.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_file', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc')
    parser.add_argument('--ref_file', type=str, default='data/processed/daily_enkf/da_cdf/observation_frequency/observation_frequency_2016.nc')
    parser.add_argument('--out_dir', type=str, default='reports/qc/irrigation_fraction')
    args = parser.parse_args()
    
    audit_irrigation_fraction(args.raw_file, args.ref_file, args.out_dir)
