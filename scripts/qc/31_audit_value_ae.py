#!/usr/bin/env python3
"""
SMAP-XAI Audit: Audit Canonical Value Target (Block 3)
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

def save_and_assert(fig, out_dir, filename):
    fpath = os.path.join(out_dir, filename)
    fig.savefig(fpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    assert os.path.exists(fpath) and os.path.getsize(fpath) > 0, f"Figure {filename} is empty!"
    print(f"Saved: {filename}")

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    years = [2016, 2017, 2018, 2019, 2020]
    exps = ['da_cdf', 'da_nocdf']
    
    c_dir = os.path.join(base_dir, "data/processed/value/value_ae")
    out_dir = os.path.join(base_dir, "reports/qc/value_ae")
    os.makedirs(out_dir, exist_ok=True)
    
    for f in glob.glob(os.path.join(out_dir, "*.png")): os.remove(f)
        
    print("==================================================")
    print("LOAD DATA AND SUPPORT DEFINITIONS")
    print("==================================================")
    ref_dir = os.path.join(base_dir, "data/processed/value/gleam/reference")
    model_dir = os.path.join(base_dir, "data/processed/value/gleam/model_et")
    
    mask_4110 = np.load(os.path.join(ref_dir, "final_common_mask.npy"))
    
    # 3871 mask approximate reconstruction
    ds_g0 = xr.open_dataset(os.path.join(ref_dir, f"gleam_et_{years[0]}.nc"))
    lat_gleam = ds_g0.lat.values; lon_gleam = ds_g0.lon.values
    ds_noah = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_2016.nc")
    lat_noah = ds_noah.lat.values; lon_noah = ds_noah.lon.values
    noah_valid_mask = np.isfinite(ds_noah['et'].isel(time=0).values)
    
    noah_lat_bounds = np.zeros(len(lat_noah) + 1); noah_lat_bounds[1:-1] = (lat_noah[:-1] + lat_noah[1:]) / 2.0; noah_lat_bounds[0] = lat_noah[0] - (lat_noah[1] - lat_noah[0]) / 2.0; noah_lat_bounds[-1] = lat_noah[-1] + (lat_noah[-1] - lat_noah[-2]) / 2.0
    noah_lon_bounds = np.zeros(len(lon_noah) + 1); noah_lon_bounds[1:-1] = (lon_noah[:-1] + lon_noah[1:]) / 2.0; noah_lon_bounds[0] = lon_noah[0] - (lon_noah[1] - lon_noah[0]) / 2.0; noah_lon_bounds[-1] = lon_noah[-1] + (lon_noah[-1] - lon_noah[-2]) / 2.0
    noah_lat_min = noah_lat_bounds[:-1]; noah_lat_max = noah_lat_bounds[1:]; noah_lon_min = noah_lon_bounds[:-1]; noah_lon_max = noah_lon_bounds[1:]
    
    gleam_lat_bounds = np.zeros(len(lat_gleam) + 1); gleam_lat_bounds[1:-1] = (lat_gleam[:-1] + lat_gleam[1:]) / 2.0; gleam_lat_bounds[0] = lat_gleam[0] - (lat_gleam[1] - lat_gleam[0]) / 2.0; gleam_lat_bounds[-1] = lat_gleam[-1] + (lat_gleam[-1] - lat_gleam[-2]) / 2.0
    gleam_lat_min = np.minimum(gleam_lat_bounds[:-1], gleam_lat_bounds[1:]); gleam_lat_max = np.maximum(gleam_lat_bounds[:-1], gleam_lat_bounds[1:])
    gleam_lon_bounds = np.zeros(len(lon_gleam) + 1); gleam_lon_bounds[1:-1] = (lon_gleam[:-1] + lon_gleam[1:]) / 2.0; gleam_lon_bounds[0] = lon_gleam[0] - (lon_gleam[1] - lon_gleam[0]) / 2.0; gleam_lon_bounds[-1] = lon_gleam[-1] + (lon_gleam[-1] - lon_gleam[-2]) / 2.0
    gleam_lon_min = np.minimum(gleam_lon_bounds[:-1], gleam_lon_bounds[1:]); gleam_lon_max = np.maximum(gleam_lon_bounds[:-1], gleam_lon_bounds[1:])
    
    R = 6371.0
    def exact_area(lat_s, lat_n, dlon): return R**2 * np.radians(dlon) * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_s)))
    
    mask_3871_spatial = np.zeros(mask_4110[0].shape, dtype=bool)
    for i in range(len(lat_gleam)):
        for j in range(len(lon_gleam)):
            if mask_4110[0, i, j]:
                glat_min = gleam_lat_min[i]; glat_max = gleam_lat_max[i]
                glon_min = gleam_lon_min[j]; glon_max = gleam_lon_max[j]
                target_area = exact_area(glat_min, glat_max, glon_max - glon_min)
                
                n_lat_idx = np.where((noah_lat_max > glat_min) & (noah_lat_min < glat_max))[0]
                n_lon_idx = np.where((noah_lon_max > glon_min) & (noah_lon_min < glon_max))[0]
                
                overlap_valid_area = 0.0
                for nl in n_lat_idx:
                    for nl_o in n_lon_idx:
                        ol_lat_min = max(glat_min, noah_lat_min[nl])
                        ol_lat_max = min(glat_max, noah_lat_max[nl])
                        ol_lon_min = max(glon_min, noah_lon_min[nl_o])
                        ol_lon_max = min(glon_max, noah_lon_max[nl_o])
                        if ol_lat_max > ol_lat_min and ol_lon_max > ol_lon_min:
                            if noah_valid_mask[nl, nl_o]:
                                overlap_valid_area += exact_area(ol_lat_min, ol_lat_max, ol_lon_max - ol_lon_min)
                
                if overlap_valid_area / target_area >= 0.99:
                    mask_3871_spatial[i, j] = True
                    
    mask_3871 = np.broadcast_to(mask_3871_spatial[np.newaxis, :, :], mask_4110.shape)
    
    data = {'da_cdf': {}, 'da_nocdf': {}}
    g_et = []; opl_et = []; da_et = {'da_cdf': [], 'da_nocdf': []}
    
    for year in years:
        g = xr.open_dataset(os.path.join(ref_dir, f"gleam_et_{year}.nc"))['et_reference'].values
        g_et.append(g)
        o = xr.open_dataset(os.path.join(model_dir, f"opl/et_on_gleam_{year}.nc"))['et'].values
        opl_et.append(o)
        
        for exp in exps:
            d = xr.open_dataset(os.path.join(model_dir, f"{exp}/et_on_gleam_{year}.nc"))['et'].values
            da_et[exp].append(d)
            
            cd = xr.open_dataset(os.path.join(c_dir, exp, f"value_ae_{year}.nc"))
            for var in ['value_ae', 'assimilated_fraction']:
                if var not in data[exp]: data[exp][var] = []
                data[exp][var].append(cd[var].values)
                
    g_et = np.concatenate(g_et, axis=0)
    opl_et = np.concatenate(opl_et, axis=0)
    times = pd.date_range("2016-01-01", "2020-12-31")
    
    for exp in exps:
        da_et[exp] = np.concatenate(da_et[exp], axis=0)
        for k in data[exp]:
            data[exp][k] = np.concatenate(data[exp][k], axis=0)
            
    print("==================================================")
    print("1. FULL value_ae DISTRIBUTION TABLE & CLOSURE")
    print("==================================================")
    for exp in exps:
        print(f"--- {exp} value_ae Distribution ---")
        v = data[exp]['value_ae'][mask_4110]
        nan_c = np.sum(np.isnan(v))
        inf_c = np.sum(np.isinf(v))
        fin_c = np.sum(np.isfinite(v))
        pos_c = np.sum(v > 0)
        neg_c = np.sum(v < 0)
        zer_c = np.sum(v == 0)
        tot = len(v)
        print(f"  Expected: {tot}, Finite: {fin_c}, NaN: {nan_c}, Inf: {inf_c}")
        print(f"  min: {np.min(v):.4f}, max: {np.max(v):.4f}, mean: {np.mean(v):.4f}, median: {np.median(v):.4f}, std: {np.std(v):.4f}")
        print(f"  p01: {np.percentile(v,1):.4f}, p05: {np.percentile(v,5):.4f}, p25: {np.percentile(v,25):.4f}, p75: {np.percentile(v,75):.4f}, p95: {np.percentile(v,95):.4f}, p99: {np.percentile(v,99):.4f}")
        print(f"  positive count: {pos_c} ({pos_c/tot*100:.1f}%), exact-zero count: {zer_c} ({zer_c/tot*100:.1f}%), negative count: {neg_c} ({neg_c/tot*100:.1f}%)")

    print("==================================================")
    print("2. ASSIMILATION-SUPPORT STRATIFICATION")
    print("==================================================")
    for exp in exps:
        af = data[exp]['assimilated_fraction'][mask_4110]
        v_ae = data[exp]['value_ae'][mask_4110]
        
        print(f"--- {exp} Assimilation Fraction Stratification ---")
        mask_a = (af == 0)
        mask_b = (af > 0)
        
        def rep_strat(name, m):
            v = v_ae[m]
            if len(v) == 0: return
            pos = np.sum(v>0)/len(v); neg = np.sum(v<0)/len(v)
            print(f"  {name}: N={len(v)}, mean={np.mean(v):.4f}, median={np.median(v):.4f}, pos={pos*100:.1f}%, neg={neg*100:.1f}%")
            
        rep_strat("A (af == 0)", mask_a)
        rep_strat("B (af > 0)", mask_b)

    print("==================================================")
    print("3. 2019 OUTAGE SUPPORT VERIFICATION")
    print("==================================================")
    outage = (times >= "2019-06-19") & (times <= "2019-07-23")
    for exp in exps:
        af_out = data[exp]['assimilated_fraction'][outage][mask_4110[outage]]
        v_out = data[exp]['value_ae'][outage][mask_4110[outage]]
        expected = len(af_out)
        actual_zero = np.sum(af_out == 0)
        print(f"--- {exp} Outage Verification ---")
        print(f"  Expected cell-days: {expected}, Actual zero-assimilation: {actual_zero}, Mismatch: {expected - actual_zero}")
        pos = np.sum(v_out>0)/len(v_out); neg = np.sum(v_out<0)/len(v_out)
        print(f"  mean: {np.mean(v_out):.4f}, median: {np.median(v_out):.4f}, pos: {pos*100:.1f}%, neg: {neg*100:.1f}%")

    print("==================================================")
    print("4. SEASONAL, YEARLY, AND SUPPORT SENSITIVITY")
    print("==================================================")
    months = times.month; years_s = times.year
    seasons = {'DJF': (months==12)|(months==1)|(months==2), 'MAM': (months>=3)&(months<=5), 'JJA': (months>=6)&(months<=8), 'SON': (months>=9)&(months<=11)}
    
    for exp in exps:
        print(f"--- {exp} Seasonal ---")
        for s, idx in seasons.items():
            v = data[exp]['value_ae'][idx][mask_4110[idx]]
            pos = np.sum(v>0)/len(v)
            print(f"  {s} (4110): N={len(v)}, mean={np.mean(v):.4f}, median={np.median(v):.4f}, pos={pos*100:.1f}%")
            
        print(f"--- {exp} Yearly ---")
        for y in range(2016, 2021):
            idx = (years_s == y)
            v = data[exp]['value_ae'][idx][mask_4110[idx]]
            pos = np.sum(v>0)/len(v)
            print(f"  {y}: N={len(v)}, mean={np.mean(v):.4f}, median={np.median(v):.4f}, pos={pos*100:.1f}%")
            
        print(f"--- {exp} 4110 vs 3871 Support Sensitivity ---")
        v_4110 = data[exp]['value_ae'][mask_4110]
        v_3871 = data[exp]['value_ae'][mask_3871]
        diff_mean = np.abs(np.mean(v_4110) - np.mean(v_3871))
        diff_median = np.abs(np.median(v_4110) - np.median(v_3871))
        pos_4 = np.sum(v_4110>0)/len(v_4110); pos_3 = np.sum(v_3871>0)/len(v_3871)
        print(f"  4110: mean={np.mean(v_4110):.4f}, median={np.median(v_4110):.4f}, pos={pos_4*100:.1f}%")
        print(f"  3871: mean={np.mean(v_3871):.4f}, median={np.median(v_3871):.4f}, pos={pos_3*100:.1f}%")
        print(f"  Absolute diffs: mean={diff_mean:.4e}, median={diff_median:.4e}, pos%={np.abs(pos_4-pos_3)*100:.2f}%")

    print("==================================================")
    print("5. BASELINE ERROR AND DELTA_ET DEPENDENCE")
    print("==================================================")
    e_o = np.abs((opl_et - g_et)[mask_4110])
    for exp in exps:
        v_ae = data[exp]['value_ae'][mask_4110]
        det = (da_et[exp] - opl_et)[mask_4110]
        
        p2, _ = pearsonr(np.abs(det), np.abs(v_ae)); s2, _ = spearmanr(np.abs(det), np.abs(v_ae))
        print(f"--- {exp} DA-minus-OPL ET response vs Value ---")
        print(f"  MAGNITUDE: Pearson={p2:.4f}, Spearman={s2:.4f}")
        
        p4, _ = pearsonr(e_o, np.abs(v_ae)); s4, _ = spearmanr(e_o, np.abs(v_ae))
        print(f"--- {exp} Baseline Error vs Value ---")
        print(f"  abs(e_OPL) vs abs(value_ae): Pearson={p4:.4f}, Spearman={s4:.4f}")

    print("==================================================")
    print("6. GENERATE ESSENTIAL FIGURES")
    print("==================================================")
    for exp in exps:
        v_ae = data[exp]['value_ae'][mask_4110]
        
        # 1. Distribution
        fig, ax = plt.subplots(); ax.hist(v_ae, bins=100); ax.set_title(f"value_ae Distribution ({exp})"); save_and_assert(fig, out_dir, f"value_ae_distribution_{exp}.png")
        
        # 2. Temporal
        daily = [np.mean(data[exp]['value_ae'][t][mask_4110[t]]) if np.sum(mask_4110[t]) > 0 else np.nan for t in range(len(times))]
        fig, ax = plt.subplots(); ax.plot(times, daily); ax.set_title(f"Daily Mean value_ae ({exp})"); save_and_assert(fig, out_dir, f"daily_value_ae_{exp}.png")
        
        # 3. Spatial
        spatial_mean = np.nanmean(np.where(mask_4110, data[exp]['value_ae'], np.nan), axis=0)
        fig, ax = plt.subplots(); im=ax.imshow(spatial_mean); plt.colorbar(im, ax=ax); save_and_assert(fig, out_dir, f"spatial_mean_value_ae_{exp}.png")
        
        # 4. Positive fraction
        spatial_pos = np.nanmean(np.where(mask_4110, data[exp]['value_ae']>0, np.nan), axis=0)
        fig, ax = plt.subplots(); im=ax.imshow(spatial_pos); plt.colorbar(im, ax=ax); save_and_assert(fig, out_dir, f"spatial_positive_fraction_{exp}.png")

    print("==================================================")
    print("DONE AUDIT")
    print("==================================================")

if __name__ == "__main__":
    main()
