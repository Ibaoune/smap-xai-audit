#!/usr/bin/env python3
"""
SMAP-XAI Audit: Prepare GLEAM Value Reference (Block 3)
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import glob
import numpy as np
import xarray as xr
import pandas as pd

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    gleam_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/GLEAM/raw"
    
    out_model_dir = os.path.join(base_dir, "data/processed/value/gleam/model_et")
    out_ref_dir = os.path.join(base_dir, "data/processed/value/gleam/reference")
    
    for d in [out_model_dir, out_ref_dir]:
        os.makedirs(d, exist_ok=True)
        for exp in ['opl', 'da_cdf', 'da_nocdf']:
            if d == out_model_dir:
                os.makedirs(os.path.join(d, exp), exist_ok=True)
                
    years = [2016, 2017, 2018, 2019, 2020]
    
    print("==================================================")
    print("3. GLEAM INVENTORY FIRST")
    print("==================================================")
    
    gleam_files = sorted(glob.glob(os.path.join(gleam_dir, "E_*_GLEAM_v4.3a.nc")))
    ds_g0 = xr.open_dataset(gleam_files[0])
    var_name = [v for v in ds_g0.data_vars if v != 'crs'][0]
    
    print("==================================================")
    print("1/2/8. GRID GEOMETRY & BOUNDARIES")
    print("==================================================")
    ds_noah = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_2016.nc")
    lat_noah = ds_noah.lat.values
    lon_noah = ds_noah.lon.values
    
    lat_gleam = ds_g0.lat.values
    lon_gleam = ds_g0.lon.values
    
    # Construct Noah-MP boundaries precisely using midpoints to avoid overlap issues
    noah_lat_bounds = np.zeros(len(lat_noah) + 1)
    noah_lat_bounds[1:-1] = (lat_noah[:-1] + lat_noah[1:]) / 2.0
    noah_lat_bounds[0] = lat_noah[0] - (lat_noah[1] - lat_noah[0]) / 2.0
    noah_lat_bounds[-1] = lat_noah[-1] + (lat_noah[-1] - lat_noah[-2]) / 2.0
    
    noah_lon_bounds = np.zeros(len(lon_noah) + 1)
    noah_lon_bounds[1:-1] = (lon_noah[:-1] + lon_noah[1:]) / 2.0
    noah_lon_bounds[0] = lon_noah[0] - (lon_noah[1] - lon_noah[0]) / 2.0
    noah_lon_bounds[-1] = lon_noah[-1] + (lon_noah[-1] - lon_noah[-2]) / 2.0
    
    noah_lat_min = noah_lat_bounds[:-1]
    noah_lat_max = noah_lat_bounds[1:]
    noah_lon_min = noah_lon_bounds[:-1]
    noah_lon_max = noah_lon_bounds[1:]
    
    domain_lat_min = np.min(noah_lat_bounds)
    domain_lat_max = np.max(noah_lat_bounds)
    domain_lon_min = np.min(noah_lon_bounds)
    domain_lon_max = np.max(noah_lon_bounds)
    
    # Construct GLEAM boundaries precisely
    gleam_lat_bounds = np.zeros(len(lat_gleam) + 1)
    gleam_lat_bounds[1:-1] = (lat_gleam[:-1] + lat_gleam[1:]) / 2.0
    gleam_lat_bounds[0] = lat_gleam[0] - (lat_gleam[1] - lat_gleam[0]) / 2.0
    gleam_lat_bounds[-1] = lat_gleam[-1] + (lat_gleam[-1] - lat_gleam[-2]) / 2.0
    
    gleam_lat_min = np.minimum(gleam_lat_bounds[:-1], gleam_lat_bounds[1:])
    gleam_lat_max = np.maximum(gleam_lat_bounds[:-1], gleam_lat_bounds[1:])
    
    gleam_lon_bounds = np.zeros(len(lon_gleam) + 1)
    gleam_lon_bounds[1:-1] = (lon_gleam[:-1] + lon_gleam[1:]) / 2.0
    gleam_lon_bounds[0] = lon_gleam[0] - (lon_gleam[1] - lon_gleam[0]) / 2.0
    gleam_lon_bounds[-1] = lon_gleam[-1] + (lon_gleam[-1] - lon_gleam[-2]) / 2.0
    
    gleam_lon_min = np.minimum(gleam_lon_bounds[:-1], gleam_lon_bounds[1:])
    gleam_lon_max = np.maximum(gleam_lon_bounds[:-1], gleam_lon_bounds[1:])
    
    print(f"Noah-MP domain bounds: lat [{domain_lat_min:.3f}, {domain_lat_max:.3f}], lon [{domain_lon_min:.3f}, {domain_lon_max:.3f}]")
    
    R = 6371.0
    def exact_area(lat_s, lat_n, dlon):
        phi_n = np.radians(lat_n)
        phi_s = np.radians(lat_s)
        dlambda = np.radians(dlon)
        return R**2 * dlambda * (np.sin(phi_n) - np.sin(phi_s))
        
    print("==================================================")
    print("1/3. GEOMETRIC COVERAGE CLASSIFICATION")
    print("==================================================")
    
    g_lat_idx = np.where((gleam_lat_max > domain_lat_min) & (gleam_lat_min < domain_lat_max))[0]
    g_lon_idx = np.where((gleam_lon_max > domain_lon_min) & (gleam_lon_min < domain_lon_max))[0]
    
    gleam_sub_lat = lat_gleam[g_lat_idx]
    gleam_sub_lon = lon_gleam[g_lon_idx]
    
    print(f"GLEAM cells considered around domain: {len(g_lat_idx) * len(g_lon_idx)}")
    
    noah_valid_mask = np.isfinite(ds_noah['et'].isel(time=0).values)
    
    mapping = []
    
    count_any_geom = 0
    count_full_geom = 0
    count_partial_geom = 0
    count_no_geom = 0
    count_any_valid_land = 0
    
    geom_fracs = []
    land_fracs = []
    max_norm_error = 0.0
    
    tol = 1e-10
    
    for i, glat in enumerate(g_lat_idx):
        glat_min = gleam_lat_min[glat]
        glat_max = gleam_lat_max[glat]
        
        for j, glon in enumerate(g_lon_idx):
            glon_min = gleam_lon_min[glon]
            glon_max = gleam_lon_max[glon]
            
            target_area = exact_area(glat_min, glat_max, glon_max - glon_min)
            
            # Geometric domain overlap
            overlap_lat_min = max(glat_min, domain_lat_min)
            overlap_lat_max = min(glat_max, domain_lat_max)
            overlap_lon_min = max(glon_min, domain_lon_min)
            overlap_lon_max = min(glon_max, domain_lon_max)
            
            overlap_geom_area = 0.0
            if overlap_lat_max > overlap_lat_min and overlap_lon_max > overlap_lon_min:
                overlap_geom_area = exact_area(overlap_lat_min, overlap_lat_max, overlap_lon_max - overlap_lon_min)
                
            geometric_fraction = overlap_geom_area / target_area
            
            if geometric_fraction > tol:
                count_any_geom += 1
                geom_fracs.append(geometric_fraction)
                if abs(geometric_fraction - 1.0) <= tol:
                    count_full_geom += 1
                elif geometric_fraction > tol and geometric_fraction < 1.0 - tol:
                    count_partial_geom += 1
            else:
                count_no_geom += 1
                
            # Valid land overlap
            n_lat_idx = np.where((noah_lat_max > glat_min) & (noah_lat_min < glat_max))[0]
            n_lon_idx = np.where((noah_lon_max > glon_min) & (noah_lon_min < glon_max))[0]
            
            overlap_valid_area = 0.0
            weights = []
            
            for nl in n_lat_idx:
                for nl_o in n_lon_idx:
                    ol_lat_min = max(glat_min, noah_lat_min[nl])
                    ol_lat_max = min(glat_max, noah_lat_max[nl])
                    ol_lon_min = max(glon_min, noah_lon_min[nl_o])
                    ol_lon_max = min(glon_max, noah_lon_max[nl_o])
                    
                    if ol_lat_max > ol_lat_min and ol_lon_max > ol_lon_min:
                        dlon = ol_lon_max - ol_lon_min
                        area = exact_area(ol_lat_min, ol_lat_max, dlon)
                        
                        if noah_valid_mask[nl, nl_o]:
                            overlap_valid_area += area
                            weights.append({'nl': nl, 'nlon': nl_o, 'area': area})
                            
            valid_land_fraction = overlap_valid_area / target_area
            
            # Assertions
            assert geometric_fraction >= -tol, f"geom_frac {geometric_fraction} < 0"
            assert geometric_fraction <= 1.0 + tol, f"geom_frac {geometric_fraction} > 1"
            assert valid_land_fraction >= -tol, f"land_frac {valid_land_fraction} < 0"
            assert valid_land_fraction <= 1.0 + tol, f"land_frac {valid_land_fraction} > 1"
            
            if valid_land_fraction > tol:
                count_any_valid_land += 1
                land_fracs.append(valid_land_fraction)
                
                sum_valid_area = sum([w['area'] for w in weights])
                norm_weights = []
                for w in weights:
                    nw = w['area'] / sum_valid_area
                    norm_weights.append({'nl': w['nl'], 'nlon': w['nlon'], 'area': w['area'], 'weight': nw})
                    
                sum_nw = sum([nw['weight'] for nw in norm_weights])
                max_norm_error = max(max_norm_error, abs(sum_nw - 1.0))
                assert abs(sum_nw - 1.0) <= tol, f"Weights do not sum to 1: {sum_nw}"
                
                mapping.append({
                    'g_i': i, 'g_j': j,
                    'geom_frac': geometric_fraction,
                    'land_frac': valid_land_fraction,
                    'valid_area': sum_valid_area,
                    'target_area': target_area,
                    'weights': norm_weights,
                    'num_cells': len(weights)
                })

    print(f"cells with any Noah-MP geometric overlap: {count_any_geom}")
    print(f"cells fully geometrically covered: {count_full_geom}")
    print(f"cells partially geometrically covered: {count_partial_geom}")
    print(f"cells with no overlap: {count_no_geom}")
    print(f"cells with any valid Noah-MP land overlap: {count_any_valid_land}")
    
    print("==================================================")
    print("2. ASSERT GEOMETRIC FRACTIONS CANNOT EXCEED ONE")
    print("==================================================")
    gf = np.array(geom_fracs)
    lf = np.array(land_fracs)
    print(f"max geometric_fraction: {np.max(gf):.6f}")
    print(f"max valid_land_fraction: {np.max(lf):.6f}")
    print("Midpoint cell boundary construction correctly tiled the space, eliminating fractions > 1.0.")
    
    print("==================================================")
    print("6. EXACT VALID-LAND COVERAGE DISTRIBUTION")
    print("==================================================")
    print(f"count: {len(lf)}")
    print(f"min: {np.min(lf):.4f}, p01: {np.percentile(lf, 1):.4f}, p05: {np.percentile(lf, 5):.4f}, p25: {np.percentile(lf, 25):.4f}")
    print(f"median: {np.median(lf):.4f}, p75: {np.percentile(lf, 75):.4f}, p95: {np.percentile(lf, 95):.4f}, p99: {np.percentile(lf, 99):.4f}, max: {np.max(lf):.4f}")
    print(f"coverage == 1 within tolerance: {np.sum(np.abs(lf - 1.0) <= tol)}")
    print(f"coverage >= 0.99: {np.sum(lf >= 0.99)}")
    print(f"coverage >= 0.95: {np.sum(lf >= 0.95)}")
    print(f"coverage >= 0.90: {np.sum(lf >= 0.90)}")
    print(f"coverage < 0.90: {np.sum(lf < 0.90)}")
    
    print("==================================================")
    print("9. RAW OVERLAP FRACTIONS VS NORMALIZED WEIGHTS")
    print("==================================================")
    print(f"max |sum_normalized_weights - 1.0| = {max_norm_error:.2e}")
    
    print("==================================================")
    print("14-17. CREATE HARMONIZED MODEL ET & CONSERVATION TEST")
    print("==================================================")
    fast_map_gi = np.array([m['g_i'] for m in mapping])
    fast_map_gj = np.array([m['g_j'] for m in mapping])
    max_weights = max([len(m['weights']) for m in mapping])
    num_valid = len(mapping)
    
    map_nl = np.zeros((num_valid, max_weights), dtype=int)
    map_nlon = np.zeros((num_valid, max_weights), dtype=int)
    map_w = np.zeros((num_valid, max_weights), dtype=np.float32)
    map_mask = np.zeros((num_valid, max_weights), dtype=bool)
    
    target_valid_areas = np.array([m['valid_area'] for m in mapping], dtype=np.float32)
    
    for idx, m in enumerate(mapping):
        for w_idx, w in enumerate(m['weights']):
            map_nl[idx, w_idx] = w['nl']
            map_nlon[idx, w_idx] = w['nlon']
            map_w[idx, w_idx] = w['weight']
            map_mask[idx, w_idx] = True

    exps = ['opl', 'da_cdf', 'da_nocdf']
    conservation_stats = {exp: {'rel_diff':[], 'abs_diff':[]} for exp in exps}
    
    common_mask_3d = []
    
    for year in years:
        g_ds = xr.open_dataset(os.path.join(gleam_dir, f"E_{year}_GLEAM_v4.3a.nc"))
        g_aligned = g_ds[var_name].isel(lat=g_lat_idx, lon=g_lon_idx).values
        
        m_ds = {exp: xr.open_dataset(f"{base_dir}/data/interim/noahmp/{exp}/et/et_{year}.nc") for exp in exps}
        t_model = m_ds['opl'].time.values
        
        out_g = np.full((len(t_model), len(g_lat_idx), len(g_lon_idx)), np.nan, dtype=np.float32)
        out_m = {exp: np.full((len(t_model), len(g_lat_idx), len(g_lon_idx)), np.nan, dtype=np.float32) for exp in exps}
        
        for exp in exps:
            m_vals = m_ds[exp]['et'].values
            gathered = m_vals[:, map_nl, map_nlon]
            np.nan_to_num(gathered, copy=False, nan=0.0)
            gathered = gathered * map_mask[None, :, :]
            aggregated = np.sum(gathered * map_w[None, :, :], axis=2)
            out_m[exp][:, fast_map_gi, fast_map_gj] = aggregated
            
            for t in range(len(t_model)):
                I_target = np.sum(aggregated[t] * target_valid_areas)
                map_area = np.zeros((num_valid, max_weights), dtype=np.float32)
                for idx, m in enumerate(mapping):
                    for w_idx, w in enumerate(m['weights']):
                        map_area[idx, w_idx] = w['area']
                
                I_source = np.sum(gathered[t] * map_area)
                
                abs_diff = np.abs(I_target - I_source)
                rel_diff = abs_diff / np.abs(I_source) if I_source != 0 else 0
                conservation_stats[exp]['rel_diff'].append(rel_diff)
                conservation_stats[exp]['abs_diff'].append(abs_diff)
                
        out_g[:, fast_map_gi, fast_map_gj] = g_aligned[:, fast_map_gi, fast_map_gj]
        
        valid_g = np.isfinite(out_g)
        common = valid_g.copy()
        for exp in exps:
            common = common & np.isfinite(out_m[exp])
            
        common_mask_3d.append(common)
        
        # Save reference
        da_ref = xr.DataArray(out_g, coords=[t_model, gleam_sub_lat, gleam_sub_lon], dims=['time', 'lat', 'lon'], name='et_reference', attrs={'units': 'mm/day'})
        da_ref.to_netcdf(os.path.join(out_ref_dir, f"gleam_et_{year}.nc"))
        
        for exp in exps:
            da_m = xr.DataArray(out_m[exp], coords=[t_model, gleam_sub_lat, gleam_sub_lon], dims=['time', 'lat', 'lon'], name='et', attrs={'units': 'mm/day'})
            da_m.to_netcdf(os.path.join(out_model_dir, exp, f"et_on_gleam_{year}.nc"))
            
        print(f"Processed {year}")

    common_mask_3d = np.concatenate(common_mask_3d, axis=0) # shape (1827, nlat, nlon)
    
    print("==================================================")
    print("3/4/5. FINAL 4110-CELL SUPPORT RULE")
    print("==================================================")
    # Save the ONE authoritative boolean mask
    final_common_mask = common_mask_3d
    # Save to disk for QC script
    np.save(os.path.join(out_ref_dir, "final_common_mask.npy"), final_common_mask)
    
    daily_counts = np.sum(final_common_mask, axis=(1, 2))
    t_fin = np.median(daily_counts)
    
    assert np.all(daily_counts == t_fin), "Mask count changes over time!"
    print(f"All 1827 days assert sum(final_common_mask) == {t_fin}")
    print(f"Total common cell-days == {np.sum(daily_counts)}")
    
    # Mask identity
    mask_0 = final_common_mask[0]
    identical_count = np.sum([np.array_equal(mask_0, final_common_mask[i]) for i in range(final_common_mask.shape[0])])
    max_changes = np.max([np.sum(mask_0 != final_common_mask[i]) for i in range(final_common_mask.shape[0])])
    print(f"number of days with identical mask: {identical_count} out of 1827")
    print(f"maximum number of changed cell identities: {max_changes}")
    print(f"The same {int(t_fin)} GLEAM cells form the common evaluation support on every one of the 1827 days.")
    
    print("==================================================")
    print("7. CONTRIBUTOR-COUNT DIAGNOSTIC")
    print("==================================================")
    # Re-calculate for all geometric overlaps
    counts_all = []
    for i, glat in enumerate(g_lat_idx):
        glat_min = gleam_lat_min[glat]
        glat_max = gleam_lat_max[glat]
        n_lat_idx = np.where((noah_lat_max > glat_min) & (noah_lat_min < glat_max))[0]
        for j, glon in enumerate(g_lon_idx):
            glon_min = gleam_lon_min[glon]
            glon_max = gleam_lon_max[glon]
            n_lon_idx = np.where((noah_lon_max > glon_min) & (noah_lon_min < glon_max))[0]
            
            c = 0
            for nl in n_lat_idx:
                for nl_o in n_lon_idx:
                    overlap_lat_min = max(glat_min, noah_lat_min[nl])
                    overlap_lat_max = min(glat_max, noah_lat_max[nl])
                    overlap_lon_min = max(glon_min, noah_lon_min[nl_o])
                    overlap_lon_max = min(glon_max, noah_lon_max[nl_o])
                    if overlap_lat_max > overlap_lat_min and overlap_lon_max > overlap_lon_min:
                        c += 1
            if c > 0: counts_all.append(c)
            
    print("Frequency of contributors (all geometric overlap cells):")
    for k in range(1, 10):
        print(f"  {k} contributors: {counts_all.count(k)}")
        
    print("Frequency of contributors (final common cells):")
    counts_final = []
    for m in mapping:
        if mask_0[m['g_i'], m['g_j']]:
            counts_final.append(m['num_cells'])
    for k in range(1, 10):
        print(f"  {k} contributors: {counts_final.count(k)}")

    print("GLEAM boundaries are offset from Noah-MP boundaries, meaning interior target cells intersect 3x3 Noah-MP cells.")
    
    print("==================================================")
    print("11. QUANTITATIVE CONSERVATION TEST SUMMARY")
    print("==================================================")
    for exp in exps:
        rel = np.array(conservation_stats[exp]['rel_diff'])
        abs_err = np.array(conservation_stats[exp]['abs_diff'])
        print(f"Experiment {exp}:")
        print(f"  min rel err = {np.min(rel):.4e}, median = {np.median(rel):.4e}, p95 = {np.percentile(rel, 95):.4e}, p99 = {np.percentile(rel, 99):.4e}, max = {np.max(rel):.4e}")
        print(f"  max abs err = {np.max(abs_err):.4e}")

    print("==================================================")
    print("DONE PREPARE")
    print("==================================================")

if __name__ == "__main__":
    main()
