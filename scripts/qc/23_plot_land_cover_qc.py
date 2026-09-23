#!/usr/bin/env python3
"""
Static Land Cover QC

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

def plot_land_cover_qc(proc_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    ds = xr.open_dataset(proc_file)
    lc = ds['land_cover_fraction'].values
    lat = ds['lat'].values
    lon = ds['lon'].values
    classes = ds['land_cover_class'].values
    
    extent = [lon.min(), lon.max(), lat.min(), lat.max()]
    
    # Calculate QC arrays
    sums_map = np.sum(lc, axis=0)
    dom_class = np.argmax(lc, axis=0) + 1 # class IDs are 1-20
    dom_frac = np.max(lc, axis=0)
    active_classes = np.sum(lc > 0, axis=0)
    
    # Valid land mask (using sum)
    valid_mask = ~np.isnan(sums_map)
    num_valid = np.sum(valid_mask)
    
    print("================ PER-CLASS STATISTICS ================")
    print("Canonical_ID | Source_Index | Finite | Non-zero | % > 0 | Min | Max | Mean | Median | P95 | Dom_Count | Dom_%")
    for i, c in enumerate(classes):
        cond = lc[i][valid_mask]
        non_zero = np.sum(cond > 0)
        
        c_id = c
        src_idx = i
        perc = non_zero/num_valid
        vmin = np.min(cond)
        vmax = np.max(cond)
        vmean = np.mean(cond)
        vmed = np.median(cond)
        vp95 = np.percentile(cond, 95)
        
        dom_count = np.sum(dom_class[valid_mask] == c)
        dom_perc = dom_count/num_valid
        
        print(f"{c_id:12d} | {src_idx:12d} | {num_valid:6d} | {non_zero:8d} | {perc:5.2%} | {vmin:.4f} | {vmax:.4f} | {vmean:.4f} | {vmed:.4f} | {vp95:.4f} | {dom_count:9d} | {dom_perc:5.2%}")
    
    print("\n================ MIXTURE STRUCTURE AND DOMINANT FRACTION ================")
    
    # Active class distribution
    act = active_classes[valid_mask]
    print("Active Classes per Pixel:")
    counts = []
    for k in range(1, 21):
        cnt = np.sum(act == k)
        if cnt > 0:
            print(f"  exactly {k} active class(es): {cnt}")
        counts.append(cnt)
    act_gt_3 = np.sum(act > 3)
    print(f"  >3 active classes: {act_gt_3}")
    print(f"  Total valid land pixels accounted for: {np.sum(counts)}")
    
    # Dominant fraction diagnostics
    df = dom_frac[valid_mask]
    print("\nDominant Fraction Statistics:")
    print(f"  max_fraction == 1.0: {np.sum(df == 1.0)}")
    print(f"  max_fraction >= 0.95: {np.sum(df >= 0.95)}")
    print(f"  max_fraction >= 0.90: {np.sum(df >= 0.90)}")
    print(f"  max_fraction >= 0.75: {np.sum(df >= 0.75)}")
    print(f"  max_fraction >= 0.50: {np.sum(df >= 0.50)}")
    print(f"  max_fraction < 0.50: {np.sum(df < 0.50)}")
    print(f"  min: {np.min(df):.4f}")
    print(f"  mean: {np.mean(df):.4f}")
    print(f"  median: {np.median(df):.4f}")
    print(f"  p05: {np.percentile(df, 5):.4f}")
    print(f"  p25: {np.percentile(df, 25):.4f}")
    print(f"  p75: {np.percentile(df, 75):.4f}")
    print(f"  p95: {np.percentile(df, 95):.4f}")
    
    # Ties and Dominant Count Conservation
    is_max = lc[:, valid_mask] == df
    tie_counts = np.sum(is_max, axis=0)
    ties = np.sum(tie_counts > 1)
    print(f"\nNumber of ties in maximum fraction: {ties}")
    print("  (Ties resolved deterministically by first/lowest source index via argmax)")
    
    total_dom = 0
    for c in classes:
        total_dom += np.sum(dom_class[valid_mask] == c)
    print(f"Sum of dominant-class counts: {total_dom}")
    print(f"Expected valid land: {num_valid}")
    print(f"Difference: {total_dom - num_valid}")
    
    # A. COMPOSITION SUM MAP
    plt.figure(figsize=(10, 8))
    im = plt.imshow(sums_map, origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1.2)
    plt.colorbar(im, label='Fraction Sum')
    plt.title('Land Cover Fraction Sum (Valid Land)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'composition_sum_map.png'))
    plt.close()
    
    # B. COMPOSITION ERROR MAP
    plt.figure(figsize=(10, 8))
    err_map = sums_map - 1.0
    im = plt.imshow(err_map, origin='lower', extent=extent, cmap='RdBu_r', vmin=-1e-4, vmax=1e-4)
    plt.colorbar(im, label='Sum - 1.0')
    plt.title('Land Cover Composition Error')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'composition_error_map.png'))
    plt.close()

    # C. DOMINANT LAND-COVER CLASS MAP
    plt.figure(figsize=(10, 8))
    dom_class_masked = np.where(valid_mask, dom_class, np.nan)
    im = plt.imshow(dom_class_masked, origin='lower', extent=extent, cmap='tab20', vmin=1, vmax=20)
    plt.colorbar(im, label='Land Cover Class ID (1-20)')
    plt.title('Dominant Land Cover Class')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'dominant_class_map.png'))
    plt.close()

    # D. DOMINANT FRACTION MAP
    plt.figure(figsize=(10, 8))
    im = plt.imshow(dom_frac, origin='lower', extent=extent, cmap='plasma', vmin=0, vmax=1)
    plt.colorbar(im, label='Dominant Fraction')
    plt.title('Dominant Land Cover Fraction')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'dominant_fraction_map.png'))
    plt.close()

    # E. ACTIVE-CLASS COUNT MAP
    plt.figure(figsize=(10, 8))
    act_class_masked = np.where(valid_mask, active_classes, np.nan)
    im = plt.imshow(act_class_masked, origin='lower', extent=extent, cmap='Pastel1', vmin=0, vmax=12)
    plt.colorbar(im, label='Number of Active Classes')
    plt.title('Number of Active Land Cover Classes')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(os.path.join(out_dir, 'active_class_map.png'))
    plt.close()
    
    # F. CLASS PREVALENCE FIGURE
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    mean_fracs = []
    dom_fracs = []
    class_labels = []
    
    for i, c in enumerate(classes):
        cond = lc[i][valid_mask]
        mean_fracs.append(np.mean(cond))
        dom_fracs.append(np.sum(dom_class[valid_mask] == c) / num_valid)
        class_labels.append(str(c))
        
    x = np.arange(len(classes))
    width = 0.35
    
    rects1 = ax1.bar(x - width/2, mean_fracs, width, label='Mean Fraction')
    rects2 = ax1.bar(x + width/2, dom_fracs, width, label='Dominant Fraction')
    
    ax1.set_ylabel('Proportion')
    ax1.set_title('Land Cover Class Prevalence (Valid Land)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(class_labels)
    ax1.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'class_prevalence.png'))
    plt.close()
    
    # G. PER-CLASS FRACTION MAPS (4x5 panel)
    fig, axes = plt.subplots(4, 5, figsize=(25, 16))
    axes = axes.flatten()
    
    for i, c in enumerate(classes):
        ax = axes[i]
        im = ax.imshow(lc[i], origin='lower', extent=extent, cmap='viridis', vmin=0, vmax=1)
        ax.set_title(f'Class {c}')
        ax.set_xticks([])
        ax.set_yticks([])
        
    fig.colorbar(im, ax=axes.tolist(), orientation='horizontal', fraction=0.05, pad=0.05, label='Fraction')
    plt.suptitle('Individual Land Cover Class Fractions')
    plt.savefig(os.path.join(out_dir, 'per_class_fraction_maps.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--proc_file', type=str, default='data/processed/static/land_cover/land_cover_fraction.nc')
    parser.add_argument('--out_dir', type=str, default='reports/qc/land_cover')
    args = parser.parse_args()
    
    plot_land_cover_qc(args.proc_file, args.out_dir)
