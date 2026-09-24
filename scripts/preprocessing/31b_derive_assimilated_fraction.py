#!/usr/bin/env python3
"""
SMAP-XAI Audit: Derive Assimilated Fraction on GLEAM Support
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import glob
import numpy as np
import xarray as xr

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    gleam_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/GLEAM/raw"
    
    out_dir = os.path.join(base_dir, "data/processed/value/candidates")
    os.makedirs(out_dir, exist_ok=True)
    
    years = [2016, 2017, 2018, 2019, 2020]
    
    # 1. GRID GEOMETRY (Copied from 30)
    gleam_files = sorted(glob.glob(os.path.join(gleam_dir, "E_*_GLEAM_v4.3a.nc")))
    ds_g0 = xr.open_dataset(gleam_files[0])
    
    ds_noah = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_2016.nc")
    lat_noah = ds_noah.lat.values
    lon_noah = ds_noah.lon.values
    
    lat_gleam = ds_g0.lat.values
    lon_gleam = ds_g0.lon.values
    
    noah_lat_bounds = np.zeros(len(lat_noah) + 1)
    noah_lat_bounds[1:-1] = (lat_noah[:-1] + lat_noah[1:]) / 2.0
    noah_lat_bounds[0] = lat_noah[0] - (lat_noah[1] - lat_noah[0]) / 2.0
    noah_lat_bounds[-1] = lat_noah[-1] + (lat_noah[-1] - lat_noah[-2]) / 2.0
    noah_lon_bounds = np.zeros(len(lon_noah) + 1)
    noah_lon_bounds[1:-1] = (lon_noah[:-1] + lon_noah[1:]) / 2.0
    noah_lon_bounds[0] = lon_noah[0] - (lon_noah[1] - lon_noah[0]) / 2.0
    noah_lon_bounds[-1] = lon_noah[-1] + (lon_noah[-1] - lon_noah[-2]) / 2.0
    noah_lat_min = noah_lat_bounds[:-1]; noah_lat_max = noah_lat_bounds[1:]
    noah_lon_min = noah_lon_bounds[:-1]; noah_lon_max = noah_lon_bounds[1:]
    domain_lat_min = np.min(noah_lat_bounds); domain_lat_max = np.max(noah_lat_bounds)
    domain_lon_min = np.min(noah_lon_bounds); domain_lon_max = np.max(noah_lon_bounds)
    
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
    
    R = 6371.0
    def exact_area(lat_s, lat_n, dlon): return R**2 * np.radians(dlon) * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_s)))
    
    g_lat_idx = np.where((gleam_lat_max > domain_lat_min) & (gleam_lat_min < domain_lat_max))[0]
    g_lon_idx = np.where((gleam_lon_max > domain_lon_min) & (gleam_lon_min < domain_lon_max))[0]
    
    noah_valid_mask = np.isfinite(ds_noah['et'].isel(time=0).values)
    
    mapping = []
    tol = 1e-10
    
    print("Building weights...")
    for i, glat in enumerate(g_lat_idx):
        glat_min = gleam_lat_min[glat]
        glat_max = gleam_lat_max[glat]
        for j, glon in enumerate(g_lon_idx):
            glon_min = gleam_lon_min[glon]
            glon_max = gleam_lon_max[glon]
            
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
                        area = exact_area(ol_lat_min, ol_lat_max, ol_lon_max - ol_lon_min)
                        if noah_valid_mask[nl, nl_o]:
                            overlap_valid_area += area
                            weights.append({'nl': nl, 'nlon': nl_o, 'area': area})
            
            if overlap_valid_area > tol:
                mapping.append({
                    'g_i': i, 'g_j': j,
                    'valid_area': overlap_valid_area,
                    'weights': weights
                })
                
    fast_map_gi = np.array([m['g_i'] for m in mapping])
    fast_map_gj = np.array([m['g_j'] for m in mapping])
    max_weights = max([len(m['weights']) for m in mapping])
    num_valid = len(mapping)
    
    map_nl = np.zeros((num_valid, max_weights), dtype=int)
    map_nlon = np.zeros((num_valid, max_weights), dtype=int)
    map_area = np.zeros((num_valid, max_weights), dtype=np.float32)
    map_mask = np.zeros((num_valid, max_weights), dtype=bool)
    target_valid_areas = np.array([m['valid_area'] for m in mapping], dtype=np.float32)
    
    for idx, m in enumerate(mapping):
        for w_idx, w in enumerate(m['weights']):
            map_nl[idx, w_idx] = w['nl']
            map_nlon[idx, w_idx] = w['nlon']
            map_area[idx, w_idx] = w['area']
            map_mask[idx, w_idx] = True
            
    exps = ['da_cdf', 'da_nocdf']
    
    for year in years:
        for exp in exps:
            obs_ds = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")
            obs_vals = obs_ds['observation_frequency'].values
            
            # Map values
            gathered = obs_vals[:, map_nl, map_nlon]
            np.nan_to_num(gathered, copy=False, nan=0.0)
            gathered = gathered * map_mask[None, :, :]
            
            # assimilated_fraction = sum(valid overlap area where obs_freq >= 1) / target_valid_areas
            assimilated_area = np.sum((gathered >= 1) * map_area[None, :, :], axis=2)
            assimilated_fraction = assimilated_area / target_valid_areas
            
            out_af = np.full((len(obs_ds.time), len(g_lat_idx), len(g_lon_idx)), np.nan, dtype=np.float32)
            out_af[:, fast_map_gi, fast_map_gj] = assimilated_fraction
            
            # Save it alongside candidates
            c_file = os.path.join(out_dir, exp, f"candidates_{year}.nc")
            ds_c = xr.open_dataset(c_file)
            
            # Avoid appending if already exists, recreate dataset or just add variable
            if 'assimilated_fraction' not in ds_c:
                ds_c['assimilated_fraction'] = (["time", "lat", "lon"], out_af)
                ds_c.to_netcdf(c_file + ".tmp")
                ds_c.close()
                os.replace(c_file + ".tmp", c_file)
            else:
                ds_c.close()
                
        print(f"Processed {year}")

if __name__ == "__main__":
    main()
