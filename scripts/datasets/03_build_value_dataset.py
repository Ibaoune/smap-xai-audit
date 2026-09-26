#!/usr/bin/env python3
"""
03_build_value_dataset.py
Author: M. El Aabaribaoune

Builds Block 3 — VALUE modeling datasets evaluating DA ET against GLEAM.
"""

__author__ = "M. El Aabaribaoune"

import os
import gc
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import xarray as xr
from calendar import monthrange

def exact_area(lat_s, lat_n, dlon):
    R = 6371.0
    return R**2 * np.radians(dlon) * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_s)))

def build_value_dataset(exp):
    print(f"BUILDING VALUE DATASET: {exp}")
    print("="*60)
    
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    da_base = f"data/interim/noahmp/{exp}"
    opl_base = "data/interim/noahmp/opl"
    met_base = "data/interim/noahmp/forcing"
    out_dir = f"data/processed/modeling/value/{exp}"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. BUILD OVERLAP MAPPING
    ds_noah = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_2016.nc")
    lat_noah = ds_noah.lat.values
    lon_noah = ds_noah.lon.values
    noah_valid_mask = np.isfinite(ds_noah['et'].isel(time=0).values)
    
    ds_g0 = xr.open_dataset(f"{base_dir}/data/processed/value/value_ae/{exp}/value_ae_2016.nc")
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
    
    final_common_mask = np.load(f"{base_dir}/data/processed/value/gleam/reference/final_common_mask.npy")
    mask_0 = final_common_mask[0]
    
    mapping = []
    for i in range(len(lat_gleam)):
        for j in range(len(lon_gleam)):
            if not mask_0[i, j]: continue
            
            glat_min = gleam_lat_min[i]
            glat_max = gleam_lat_max[i]
            glon_min = gleam_lon_min[j]
            glon_max = gleam_lon_max[j]
            
            target_area = exact_area(glat_min, glat_max, glon_max - glon_min)
            
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
            
            mapping.append({
                'g_i': i, 'g_j': j,
                'target_area': target_area,
                'valid_area': overlap_valid_area,
                'land_frac': overlap_valid_area / target_area,
                'weights': weights
            })
            
    num_valid = len(mapping)
    max_weights = max([len(m['weights']) for m in mapping])
    
    fast_map_gi = np.array([m['g_i'] for m in mapping])
    fast_map_gj = np.array([m['g_j'] for m in mapping])
    gleam_lats = lat_gleam[fast_map_gi]
    gleam_lons = lon_gleam[fast_map_gj]
    
    valid_noahmp_land_fraction = np.array([m['land_frac'] for m in mapping], dtype=np.float32)
    high_land_coverage = (valid_noahmp_land_fraction >= 0.99).astype(int)
    
    map_nl = np.zeros((num_valid, max_weights), dtype=int)
    map_nlon = np.zeros((num_valid, max_weights), dtype=int)
    map_w = np.zeros((num_valid, max_weights), dtype=np.float32)
    map_mask = np.zeros((num_valid, max_weights), dtype=bool)
    
    for idx, m in enumerate(mapping):
        for w_idx, w in enumerate(m['weights']):
            map_nl[idx, w_idx] = w['nl']
            map_nlon[idx, w_idx] = w['nlon']
            map_w[idx, w_idx] = w['area'] / m['valid_area']
            map_mask[idx, w_idx] = True
            
    def aggregate(native_array):
        gathered = native_array[map_nl, map_nlon]
        np.nan_to_num(gathered, copy=False, nan=0.0)
        gathered = gathered * map_mask
        return np.sum(gathered * map_w, axis=1)

    # 2. STATIC FEATURES
    print("Loading static features...")
    elev_ds = xr.open_dataset("data/processed/static/elevation/elevation.nc")['elevation'].values
    lc_ds = xr.open_dataset("data/processed/static/land_cover/land_cover_fraction.nc")
    st_ds = xr.open_dataset("data/processed/static/soil_texture/soil_texture_fraction.nc")
    
    static_cols = {}
    static_cols['elevation'] = aggregate(elev_ds)
    for c in range(1, 21):
        native = lc_ds['land_cover_fraction'].sel(land_cover_class=c).values
        static_cols[f'land_cover_fraction_{c}'] = aggregate(native)
    for c in range(1, 17):
        native = st_ds['soil_texture_fraction'].sel(texture_class=c).values
        static_cols[f'soil_texture_fraction_{c}'] = aggregate(native)
        
    years = [2016, 2017, 2018, 2019, 2020]
    
    def get_ds(year):
        ds = {
            'da_ssm': xr.open_dataset(f"{da_base}/ssm/ssm_{year}.nc")['ssm'].values,
            'da_rzsm': xr.open_dataset(f"data/processed/daily_model/{exp}/rzsm/rzsm_{year}.nc")['rzsm'].values,
            'da_et': xr.open_dataset(f"{da_base}/et/et_{year}.nc")['et'].values,
            'da_qs': xr.open_dataset(f"{da_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values,
            'da_qsb': xr.open_dataset(f"{da_base}/baseflow/baseflow_{year}.nc")['baseflow'].values,
            'opl_ssm': xr.open_dataset(f"{opl_base}/ssm/ssm_{year}.nc")['ssm'].values,
            'opl_rzsm': xr.open_dataset(f"data/processed/daily_model/opl/rzsm/rzsm_{year}.nc")['rzsm'].values,
            'opl_et': xr.open_dataset(f"{opl_base}/et/et_{year}.nc")['et'].values,
            'opl_qs': xr.open_dataset(f"{opl_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values,
            'opl_qsb': xr.open_dataset(f"{opl_base}/baseflow/baseflow_{year}.nc")['baseflow'].values,
            'obs_freq': xr.open_dataset(f"data/processed/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")['observation_frequency'].values,
            'inc_sign': xr.open_dataset(f"data/processed/daily_enkf/{exp}/daily_signed_increment/daily_signed_increment_{year}.nc")['daily_signed_increment'].values,
            'precip': xr.open_dataset(f"{met_base}/precipitation/precipitation_{year}.nc")['precipitation'].values,
            'tair': xr.open_dataset(f"{met_base}/air_temperature/air_temperature_{year}.nc")['air_temperature'].values,
            'delta_precip': xr.open_dataset(f"{da_base}/delta_precip_forcing/delta_precip_forcing_{year}.nc")['delta_precip_forcing'].values,
            'time': pd.to_datetime(xr.open_dataset(f"{da_base}/ssm/ssm_{year}.nc")['time'].values)
        }
        ds['inc_sign'] = np.where(ds['obs_freq'] == 1, ds['inc_sign'], 0.0)
        ds['inc_abs'] = np.abs(ds['inc_sign'])
        
        ds['delta_ssm'] = ds['da_ssm'] - ds['opl_ssm']
        ds['delta_rzsm'] = ds['da_rzsm'] - ds['opl_rzsm']
        ds['delta_et'] = ds['da_et'] - ds['opl_et']
        ds['delta_qs'] = ds['da_qs'] - ds['opl_qs']
        ds['delta_qsb'] = ds['da_qsb'] - ds['opl_qsb']
        
        v_ds = xr.open_dataset(f"data/processed/value/value_ae/{exp}/value_ae_{year}.nc")
        ds['value_ae'] = v_ds['value_ae'].values[:, fast_map_gi, fast_map_gj]
        ds['assimilated_fraction'] = v_ds['assimilated_fraction'].values[:, fast_map_gi, fast_map_gj]
        return ds

    prev_ds = None
    for y in years:
        print(f"Processing {y}...")
        curr_ds = get_ds(y)
        
        y_dir = f"{out_dir}/year={y}"
        os.makedirs(y_dir, exist_ok=True)
        
        if prev_ds is not None:
            hist_len = 7
            full = {}
            for k in curr_ds:
                if isinstance(curr_ds[k], np.ndarray):
                    full[k] = np.concatenate([prev_ds[k][-hist_len:], curr_ds[k]], axis=0)
                else:
                    full[k] = np.concatenate([prev_ds[k][-hist_len:], curr_ds[k]])
            start_idx = hist_len
        else:
            full = curr_ds
            start_idx = 0
            
        time_arr = full['time']
        
        for month in range(1, 13):
            curr_year_times = curr_ds['time']
            m_mask = (curr_year_times.month == month)
            if not m_mask.any(): continue
            
            m_indices = np.where(m_mask)[0]
            if y == 2016 and month == 1:
                m_indices = m_indices[m_indices >= 7]
                if len(m_indices) == 0: continue
                
            dfs = []
            for t_idx in m_indices:
                f_idx = t_idx + start_idx
                date = pd.Timestamp(curr_year_times[t_idx])
                
                t_slice_3d = slice(f_idx - 3, f_idx)
                t_slice_7d = slice(f_idx - 7, f_idx)
                
                # Dynamic aggregations
                inc_sign = aggregate(full['inc_sign'][f_idx])
                inc_abs = aggregate(full['inc_abs'][f_idx])
                inc_3d = aggregate(full['inc_sign'][t_slice_3d].sum(axis=0))
                inc_7d = aggregate(full['inc_sign'][t_slice_7d].sum(axis=0))
                abs_3d = aggregate(full['inc_abs'][t_slice_3d].sum(axis=0))
                abs_7d = aggregate(full['inc_abs'][t_slice_7d].sum(axis=0))
                
                # finite innovation history
                fin_frac = full['assimilated_fraction'][f_idx]
                fin_3d = full['assimilated_fraction'][t_slice_3d].mean(axis=0)
                fin_7d = full['assimilated_fraction'][t_slice_7d].mean(axis=0)
                
                df = pd.DataFrame({
                    'date': date,
                    'year': y,
                    'lat': gleam_lats,
                    'lon': gleam_lons,
                    'gleam_y_index': fast_map_gi,
                    'gleam_x_index': fast_map_gj,
                    'experiment': exp,
                    
                    'value_ae': full['value_ae'][f_idx],
                    
                    'source_signed_increment_t': inc_sign,
                    'source_absolute_increment_t': inc_abs,
                    'finite_innovation_fraction_t': fin_frac,
                    
                    'source_signed_increment_pre3d_sum': inc_3d,
                    'source_signed_increment_pre7d_sum': inc_7d,
                    'source_absolute_increment_pre3d_sum': abs_3d,
                    'source_absolute_increment_pre7d_sum': abs_7d,
                    'finite_innovation_fraction_pre3d_mean': fin_3d,
                    'finite_innovation_fraction_pre7d_mean': fin_7d,
                    
                    'ssm_opl_lag1': aggregate(full['opl_ssm'][f_idx-1]),
                    'rzsm_opl_lag1': aggregate(full['opl_rzsm'][f_idx-1]),
                    
                    'precip_t': aggregate(full['precip'][f_idx]),
                    'tair_t': aggregate(full['tair'][f_idx]),
                    'precip_lag1': aggregate(full['precip'][f_idx-1]),
                    'precip_pre3d_sum': aggregate(full['precip'][t_slice_3d].sum(axis=0)),
                    'precip_pre7d_sum': aggregate(full['precip'][t_slice_7d].sum(axis=0)),
                    'tair_lag1': aggregate(full['tair'][f_idx-1]),
                    'tair_pre3d_mean': aggregate(full['tair'][t_slice_3d].mean(axis=0)),
                    'tair_pre7d_mean': aggregate(full['tair'][t_slice_7d].mean(axis=0)),
                    
                    'delta_precip_forcing_t': aggregate(full['delta_precip'][f_idx]),
                    'delta_precip_forcing_pre3d_sum': aggregate(full['delta_precip'][t_slice_3d].sum(axis=0)),
                    'delta_precip_forcing_pre7d_sum': aggregate(full['delta_precip'][t_slice_7d].sum(axis=0)),
                    
                    'et_opl_lag1': aggregate(full['opl_et'][f_idx-1]),
                    'surface_runoff_opl_lag1': aggregate(full['opl_qs'][f_idx-1]),
                    'baseflow_opl_lag1': aggregate(full['opl_qsb'][f_idx-1]),
                    
                    'delta_ssm_lag1': aggregate(full['delta_ssm'][f_idx-1]),
                    'delta_rzsm_lag1': aggregate(full['delta_rzsm'][f_idx-1]),
                    'delta_et_lag1': aggregate(full['delta_et'][f_idx-1]),
                    'delta_surface_runoff_lag1': aggregate(full['delta_qs'][f_idx-1]),
                    'delta_baseflow_lag1': aggregate(full['delta_qsb'][f_idx-1]),
                    
                    'delta_rzsm_t': aggregate(full['delta_rzsm'][f_idx]),
                    'delta_et_t': aggregate(full['delta_et'][f_idx]),
                    
                    'valid_noahmp_land_fraction': valid_noahmp_land_fraction,
                    'high_land_coverage': high_land_coverage
                })
                
                # Temporal context
                df['month'] = date.month
                df['day_of_year'] = date.dayofyear
                days_in_year = 366 if date.is_leap_year else 365
                df['doy_sin'] = np.sin(2 * np.pi * date.dayofyear / days_in_year)
                df['doy_cos'] = np.cos(2 * np.pi * date.dayofyear / days_in_year)
                
                # Statics
                for k, v in static_cols.items(): df[k] = v
                
                dfs.append(df)
            
            if dfs:
                month_df = pd.concat(dfs, ignore_index=True)
                part_path = f"{y_dir}/part-{month:02d}.parquet"
                table = pa.Table.from_pandas(month_df)
                pq.write_table(table, part_path, compression='snappy')
                del month_df
                del dfs
                gc.collect()
                
        prev_ds = curr_ds
        
    print(f"Finished {exp}")

if __name__ == "__main__":
    build_value_dataset("da_cdf")
    build_value_dataset("da_nocdf")
