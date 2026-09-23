#!/usr/bin/env python3
"""
Static Elevation QC

Author
------
M. El Aabaribaoune (@um6p)
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_elevation_qc(raw_file, proc_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # Load processed file
    ds = xr.open_dataset(proc_file)
    elev = ds['elevation'].values
    lat = ds['lat'].values
    lon = ds['lon'].values
    
    # Load source file to verify source-to-processed identity
    ds_raw = xr.open_dataset(raw_file)
    elev_raw = ds_raw['ELEVATION'].values
    
    finite_mask = ~np.isnan(elev)
    cond = elev[finite_mask]
    
    # Distribution identity
    print("================ PROCESSED LAND-ONLY STATISTICS ================")
    print(f"  min: {np.min(cond)}")
    print(f"  max: {np.max(cond)}")
    print(f"  mean: {np.mean(cond)}")
    print(f"  median: {np.median(cond)}")
    print(f"  std: {np.std(cond)}")
    print(f"  p01: {np.percentile(cond, 1)}")
    print(f"  p05: {np.percentile(cond, 5)}")
    print(f"  p25: {np.percentile(cond, 25)}")
    print(f"  p75: {np.percentile(cond, 75)}")
    print(f"  p95: {np.percentile(cond, 95)}")
    print(f"  p99: {np.percentile(cond, 99)}")
    
    neg = np.sum(cond < 0)
    zer = np.sum(cond == 0.0)
    pos = np.sum(cond > 0)
    print(f"\n  negative land elevations: {neg}")
    print(f"  exact-zero land elevations: {zer}")
    print(f"  positive land elevations: {pos}")
    
    # Identity
    diff = np.abs(cond - elev_raw[finite_mask])
    print("\n================ SOURCE-TO-PROCESSED IDENTITY ================")
    print(f"  Max absolute diff: {np.max(diff)}")
    print(f"  Mean absolute diff: {np.mean(diff)}")
    print(f"  Unequal exact: {np.sum(cond != elev_raw[finite_mask])}")
    print(f"  Unequal atol 1e-6: {np.sum(diff > 1e-6)}")
    
    # A. ELEVATION MAP
    plt.figure(figsize=(10, 8))
    extent = [lon.min(), lon.max(), lat.min(), lat.max()]
    im = plt.imshow(elev, origin='lower', extent=extent, cmap='terrain')
    plt.colorbar(im, label='Elevation (m)', extend='both')
    plt.title('Static Elevation (Canonical Noah-MP Grid)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'elevation_map.png'))
    plt.close()
    
    # B. ELEVATION DISTRIBUTION
    plt.figure(figsize=(8, 6))
    plt.hist(cond, bins=100, alpha=0.7, color='saddlebrown')
    plt.title('Distribution of Elevation on Valid Land')
    plt.xlabel('Elevation (m)')
    plt.ylabel('Count')
    plt.savefig(os.path.join(out_dir, 'elevation_distribution.png'))
    plt.close()
    
    # C. OPTIONAL HIGH-ELEVATION MAP
    # If the upper tail is compressed (e.g. above p95), we can plot with vmin/vmax focused on high values
    p95 = np.percentile(cond, 95)
    plt.figure(figsize=(10, 8))
    im = plt.imshow(elev, origin='lower', extent=extent, cmap='terrain', vmin=p95)
    plt.colorbar(im, label='Elevation (m)', extend='both')
    plt.title(f'High-Elevation Regions (> p95: {p95:.1f} m)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'high_elevation_map.png'))
    plt.close()
    
    # D. MASK QC
    plt.figure(figsize=(10, 8))
    im = plt.imshow(finite_mask, origin='lower', extent=extent, cmap='Greys_r')
    plt.title('Canonical Valid Land Mask')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'mask_qc.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_file', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc')
    parser.add_argument('--proc_file', type=str, default='data/processed/static/elevation/elevation.nc')
    parser.add_argument('--out_dir', type=str, default='reports/qc/elevation')
    args = parser.parse_args()
    
    plot_elevation_qc(args.raw_file, args.proc_file, args.out_dir)
