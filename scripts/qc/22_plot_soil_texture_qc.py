#!/usr/bin/env python3
"""
Static Soil Texture QC

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

def plot_soil_texture_qc(proc_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    ds = xr.open_dataset(proc_file)
    tex = ds['soil_texture_fraction'].values
    lat = ds['lat'].values
    lon = ds['lon'].values
    classes = ds['texture_class'].values
    
    extent = [lon.min(), lon.max(), lat.min(), lat.max()]
    
    # Calculate QC arrays
    sums_map = np.sum(tex, axis=0)
    dom_class = np.argmax(tex, axis=0) + 1 # class IDs are 1-16
    dom_frac = np.max(tex, axis=0)
    active_classes = np.sum(tex > 0, axis=0)
    
    # Valid land mask (using sum)
    valid_mask = ~np.isnan(sums_map)
    
    # Print per-class stats for all 16 classes
    print("================ PER-CLASS STATISTICS ================")
    for i, c in enumerate(classes):
        cond = tex[i][valid_mask]
        non_zero = np.sum(cond > 0)
        num_valid = len(cond)
        
        print(f"Class {c}:")
        print(f"  finite land count: {num_valid}")
        print(f"  non-zero land count: {non_zero}")
        print(f"  percent > 0: {non_zero/num_valid:.2%}")
        print(f"  min: {np.min(cond)}")
        print(f"  max: {np.max(cond)}")
        print(f"  mean: {np.mean(cond)}")
        print(f"  median: {np.median(cond)}")
        print(f"  p95: {np.percentile(cond, 95)}")
        
        dom_count = np.sum(dom_class[valid_mask] == c)
        print(f"  dominant-pixel count: {dom_count}")
        print(f"  dominant-pixel percentage: {dom_count/num_valid:.2%}")
        
        not_zero_or_one = np.sum((cond != 0) & (cond != 1))
        if not_zero_or_one > 0:
            print(f"  VIOLATION: {not_zero_or_one} values not exactly 0 or 1")
    
    print("\n================ ONE-HOT EXPLICIT VERIFICATION ================")
    tex_valid = tex[:, valid_mask]  # shape: (16, num_valid)
    
    # 1. sum over classes == 1 exactly
    sums_exact = np.sum(tex_valid, axis=0)
    viol_sum = np.sum(sums_exact != 1.0)
    
    # 2. count(classes == 1) == 1
    count_ones = np.sum(tex_valid == 1.0, axis=0)
    viol_ones = np.sum(count_ones != 1)
    
    # 3. count(classes != 0 and classes != 1) == 0
    not_binary = (tex_valid != 0.0) & (tex_valid != 1.0)
    viol_binary = np.sum(np.sum(not_binary, axis=0) > 0)
    
    zero_active = np.sum(count_ones == 0)
    multi_active = np.sum(count_ones > 1)
    
    print(f"pixels violating sum == 1: {viol_sum}")
    print(f"pixels with no active class: {zero_active}")
    print(f"pixels with >1 active class: {multi_active}")
    print(f"non-binary fraction values: {viol_binary}")
    
    print("\n================ DOMINANT CLASS CONSERVATION ================")
    total_dom = 0
    for c in classes:
        dom_count = np.sum(dom_class[valid_mask] == c)
        total_dom += dom_count
    print(f"Sum over ALL 16 classes: {total_dom}")
    print(f"Expected valid land: {np.sum(valid_mask)}")
    
    # A. FRACTION-SUM MAP
    plt.figure(figsize=(10, 8))
    im = plt.imshow(sums_map, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1.2)
    plt.colorbar(im, label='Fraction Sum')
    plt.title('Soil Texture Fraction Sum (Valid Land)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'fraction_sum_map.png'))
    plt.close()
    
    # B. FRACTION-SUM ERROR MAP
    plt.figure(figsize=(10, 8))
    err_map = sums_map - 1.0
    im = plt.imshow(err_map, origin='lower', extent=extent, cmap='RdBu_r', vmin=-1e-4, vmax=1e-4)
    plt.colorbar(im, label='Sum - 1.0')
    plt.title('Fraction Sum Error')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'fraction_sum_error_map.png'))
    plt.close()

    # C. DOMINANT TEXTURE CLASS MAP
    plt.figure(figsize=(10, 8))
    # Mask out dominant class where invalid
    dom_class_masked = np.where(valid_mask, dom_class, np.nan)
    im = plt.imshow(dom_class_masked, origin='lower', extent=extent, cmap='tab20', vmin=1, vmax=16)
    plt.colorbar(im, label='Texture Class ID (1-16)')
    plt.title('Dominant Soil Texture Class')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'dominant_texture_class_map.png'))
    plt.close()

    # D. DOMINANT FRACTION MAP
    plt.figure(figsize=(10, 8))
    im = plt.imshow(dom_frac, origin='lower', extent=extent, cmap='plasma', vmin=0, vmax=1)
    plt.colorbar(im, label='Dominant Fraction')
    plt.title('Dominant Soil Texture Fraction')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'dominant_fraction_map.png'))
    plt.close()

    # E. NUMBER OF ACTIVE CLASSES MAP
    plt.figure(figsize=(10, 8))
    act_class_masked = np.where(valid_mask, active_classes, np.nan)
    im = plt.imshow(act_class_masked, origin='lower', extent=extent, cmap='Pastel1', vmin=0, vmax=5)
    plt.colorbar(im, label='Number of Active Classes')
    plt.title('Number of Active Texture Classes')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'active_classes_map.png'))
    plt.close()
    
    # F. CLASS PREVALENCE BAR CHART
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    mean_fracs = []
    dom_fracs = []
    class_labels = []
    
    for i, c in enumerate(classes):
        cond = tex[i][valid_mask]
        mean_fracs.append(np.mean(cond))
        dom_fracs.append(np.sum(dom_class[valid_mask] == c) / len(cond))
        class_labels.append(str(c))
        
    x = np.arange(len(classes))
    width = 0.35
    
    rects1 = ax1.bar(x - width/2, mean_fracs, width, label='Mean Fraction')
    rects2 = ax1.bar(x + width/2, dom_fracs, width, label='Dominant Fraction')
    
    ax1.set_ylabel('Proportion')
    ax1.set_title('Soil Texture Class Prevalence (Valid Land)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(class_labels)
    ax1.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'class_prevalence.png'))
    plt.close()
    
    # G. PER-CLASS FRACTION MAP (4x4 panel)
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    axes = axes.flatten()
    
    for i, c in enumerate(classes):
        ax = axes[i]
        im = ax.imshow(tex[i], origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1)
        ax.set_title(f'Class {c}')
        ax.set_xticks([])
        ax.set_yticks([])
        
    fig.colorbar(im, ax=axes.tolist(), orientation='horizontal', fraction=0.05, pad=0.05, label='Fraction')
    plt.suptitle('Individual Soil Texture Class Fractions')
    plt.savefig(os.path.join(out_dir, 'per_class_fraction_map.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--proc_file', type=str, default='data/processed/static/soil_texture/soil_texture_fraction.nc')
    parser.add_argument('--out_dir', type=str, default='reports/qc/soil_texture')
    args = parser.parse_args()
    
    plot_soil_texture_qc(args.proc_file, args.out_dir)
