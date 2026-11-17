#!/usr/bin/env python3
"""
02_build_transfer_dataset.py
Author: M. El Aabaribaoune

Builds Block 2 — TRANSFER modeling datasets explaining the downstream
DA-modified land trajectory propagation.
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

def build_transfer_dataset(exp):
    print(f"BUILDING TRANSFER DATASET: {exp}")
    print("="*60)
    
    # Paths
    da_base = f"data/interim/noahmp/{exp}"
    opl_base = "data/interim/noahmp/opl"
    met_base = "data/interim/noahmp/forcing"
    enkf_base = f"data/interim/enkf/{exp}"
    static_base = "data/interim/noahmp/static"
    
    out_dir = f"data/processed/modeling/transfer/{exp}"
    os.makedirs(out_dir, exist_ok=True)
    
    # Load statics
    print("Loading static features...")
    elev_ds = xr.open_dataset("data/processed/static/elevation/elevation.nc")
    lc_ds = xr.open_dataset("data/processed/static/land_cover/land_cover_fraction.nc")
    st_ds = xr.open_dataset("data/processed/static/soil_texture/soil_texture_fraction.nc")
    
    # Get spatial canonical mask (16030 active pixels)
    ds_ssm_ref = xr.open_dataset(f"{da_base}/ssm/ssm_2016.nc")
    valid_mask = np.isfinite(ds_ssm_ref['ssm'].isel(time=0).values)
    y_idx, x_idx = np.where(valid_mask)
    n_valid = len(y_idx)
    
    lat = ds_ssm_ref['lat'].values
    lon = ds_ssm_ref['lon'].values
    lat_valid = lat[y_idx]
    lon_valid = lon[x_idx]
    
    # Static columns matching
    df_coords = pd.DataFrame({'lat': lat_valid, 'lon': lon_valid, 'order': np.arange(len(lat_valid))})
    
    elev_df = elev_ds.to_dataframe().reset_index()
    df_coords = df_coords.merge(elev_df, on=['lat', 'lon'], how='left')
    
    lc_df = lc_ds.to_dataframe().reset_index()
    lc_df_pivot = lc_df.pivot(index=['lat', 'lon'], columns='land_cover_class', values='land_cover_fraction')
    lc_df_pivot.columns = [f'land_cover_fraction_{c}' for c in lc_df_pivot.columns]
    df_coords = df_coords.merge(lc_df_pivot.reset_index(), on=['lat', 'lon'], how='left')
    
    st_df = st_ds.to_dataframe().reset_index()
    st_df_pivot = st_df.pivot(index=['lat', 'lon'], columns='texture_class', values='soil_texture_fraction')
    st_df_pivot.columns = [f'soil_texture_fraction_{c}' for c in st_df_pivot.columns]
    df_coords = df_coords.merge(st_df_pivot.reset_index(), on=['lat', 'lon'], how='left')
    
    df_coords = df_coords.sort_values('order').reset_index(drop=True)
    
    elev_valid = df_coords['elevation'].values
    lc_vals = {f"land_cover_fraction_{i}": df_coords[f"land_cover_fraction_{i}"].values for i in range(1, 21)}
    st_vals = {f"soil_texture_fraction_{i}": df_coords[f"soil_texture_fraction_{i}"].values for i in range(1, 17)}
    
    # We will need to load history for t-1 through t-7. We process year by year, but we need December of previous year for January.
    # Since we only have 2016-2020, 2016 will start from 2016-01-08.
    
    years = [2016, 2017, 2018, 2019, 2020]
    
    def get_ds(year):
        # We need: DA (ssm, rzsm, et, qs, qsb), OPL (ssm, rzsm, et, qs, qsb), ENKF (inc signed, obs_freq), MET (precip, tair)
        ds = {
            'da_ssm': xr.open_dataset(f"{da_base}/ssm/ssm_{year}.nc")['ssm'].values[:, y_idx, x_idx],
            'da_rzsm': xr.open_dataset(f"data/processed/daily_model/{exp}/rzsm/rzsm_{year}.nc")['rzsm'].values[:, y_idx, x_idx],
            'da_et': xr.open_dataset(f"{da_base}/et/et_{year}.nc")['et'].values[:, y_idx, x_idx],
            'da_qs': xr.open_dataset(f"{da_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values[:, y_idx, x_idx],
            'da_qsb': xr.open_dataset(f"{da_base}/baseflow/baseflow_{year}.nc")['baseflow'].values[:, y_idx, x_idx],
            'opl_ssm': xr.open_dataset(f"{opl_base}/ssm/ssm_{year}.nc")['ssm'].values[:, y_idx, x_idx],
            'opl_rzsm': xr.open_dataset(f"data/processed/daily_model/opl/rzsm/rzsm_{year}.nc")['rzsm'].values[:, y_idx, x_idx],
            'opl_et': xr.open_dataset(f"{opl_base}/et/et_{year}.nc")['et'].values[:, y_idx, x_idx],
            'opl_qs': xr.open_dataset(f"{opl_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values[:, y_idx, x_idx],
            'opl_qsb': xr.open_dataset(f"{opl_base}/baseflow/baseflow_{year}.nc")['baseflow'].values[:, y_idx, x_idx],
            'obs_freq': xr.open_dataset(f"data/processed/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")['observation_frequency'].values[:, y_idx, x_idx],
            'inc_sign': xr.open_dataset(f"data/processed/daily_enkf/{exp}/daily_signed_increment/daily_signed_increment_{year}.nc")['daily_signed_increment'].values[:, y_idx, x_idx],
            'precip': xr.open_dataset(f"{met_base}/precipitation/precipitation_{year}.nc")['precipitation'].values[:, y_idx, x_idx],
            'tair': xr.open_dataset(f"{met_base}/air_temperature/air_temperature_{year}.nc")['air_temperature'].values[:, y_idx, x_idx],
            'delta_precip': xr.open_dataset(f"{da_base}/delta_precip_forcing/delta_precip_forcing_{year}.nc")['delta_precip_forcing'].values[:, y_idx, x_idx],
            'time': pd.to_datetime(xr.open_dataset(f"{da_base}/ssm/ssm_{year}.nc")['time'].values)
        }
        # Clean increment (set to 0 if obs_freq == 0 or nan)
        ds['inc_sign'] = np.where(ds['obs_freq'] == 1, ds['inc_sign'], 0.0)
        ds['inc_abs'] = np.abs(ds['inc_sign'])
        
        # Deltas
        ds['delta_ssm'] = ds['da_ssm'] - ds['opl_ssm']
        ds['delta_rzsm'] = ds['da_rzsm'] - ds['opl_rzsm']
        ds['delta_et'] = ds['da_et'] - ds['opl_et']
        ds['delta_qs'] = ds['da_qs'] - ds['opl_qs']
        ds['delta_qsb'] = ds['da_qsb'] - ds['opl_qsb']
        return ds

    prev_ds = None
    for y in years:
        print(f"Processing {y}...")
        curr_ds = get_ds(y)
        if curr_ds is None: continue
        
        y_dir = f"{out_dir}/year={y}"
        os.makedirs(y_dir, exist_ok=True)
        
        # Combine with previous year end for lag history if available
        if prev_ds is not None:
            # We need 7 days from previous year
            hist_len = 7
            full = {k: np.concatenate([prev_ds[k][-hist_len:], curr_ds[k]], axis=0) if isinstance(curr_ds[k], np.ndarray) else np.concatenate([prev_ds[k][-hist_len:], curr_ds[k]]) for k in curr_ds}
            start_idx = hist_len
        else:
            full = curr_ds
            start_idx = 0 # We lose first 7 days of 2016, but indices in full are unchanged
            
        time_arr = full['time']
        
        # Process in chunks (monthly) to avoid huge arrays
        for month in range(1, 13):
            # Find indices for this month in the current year
            # The curr_ds indices map to full indices by adding start_idx
            curr_year_times = curr_ds['time']
            m_mask = (curr_year_times.month == month)
            if not m_mask.any(): continue
            
            m_indices = np.where(m_mask)[0]
            # If 2016 Jan, we skip first 7 days
            if y == 2016 and month == 1:
                m_indices = m_indices[m_indices >= 7]
                if len(m_indices) == 0: continue
            
            # Create a dataframe for this month
            dfs = []
            for t_idx in m_indices:
                f_idx = t_idx + start_idx
                date = pd.Timestamp(curr_year_times[t_idx])
                
                # Slices for lags
                t_slice_3d = slice(f_idx - 3, f_idx)
                t_slice_7d = slice(f_idx - 7, f_idx)
                
                df = pd.DataFrame({
                    'date': date,
                    'year': y,
                    'lat': lat_valid,
                    'lon': lon_valid,
                    'y_index': y_idx,
                    'x_index': x_idx,
                    'experiment': exp,
                    
                    # TARGETS
                    'delta_rzsm': full['delta_rzsm'][f_idx],
                    'delta_et': full['delta_et'][f_idx],
                    'delta_surface_runoff': full['delta_qs'][f_idx],
                    'delta_baseflow': full['delta_qsb'][f_idx],
                    
                    # source_driver_current
                    'source_signed_increment_t': full['inc_sign'][f_idx],
                    'source_absolute_increment_t': full['inc_abs'][f_idx],
                    'observation_frequency': full['obs_freq'][f_idx],
                    
                    # source_driver_history
                    'source_signed_increment_pre3d_sum': full['inc_sign'][t_slice_3d].sum(axis=0),
                    'source_signed_increment_pre7d_sum': full['inc_sign'][t_slice_7d].sum(axis=0),
                    'source_absolute_increment_pre3d_sum': full['inc_abs'][t_slice_3d].sum(axis=0),
                    'source_absolute_increment_pre7d_sum': full['inc_abs'][t_slice_7d].sum(axis=0),
                    'finite_innovation_count_pre3d': full['obs_freq'][t_slice_3d].sum(axis=0),
                    'finite_innovation_count_pre7d': full['obs_freq'][t_slice_7d].sum(axis=0),
                })
                
                # Recency
                # 0 = finite innovation on day t
                # 1 = most recent on t-1, up to 7
                # 8 = no finite innovation in t ... t-7
                obs_window = full['obs_freq'][f_idx-7:f_idx+1] # shape (8, N)
                # Reverse it so index 0 is t, index 7 is t-7
                obs_window = obs_window[::-1, :]
                
                # argmax returns the first index with True. If all False, returns 0.
                has_obs = obs_window.any(axis=0)
                first_obs_idx = obs_window.argmax(axis=0)
                days_since = np.where(has_obs, first_obs_idx, 8)
                df['days_since_finite_innovation_7d'] = days_since
                
                # baseline_state
                df['ssm_opl_lag1'] = full['opl_ssm'][f_idx-1]
                df['rzsm_opl_lag1'] = full['opl_rzsm'][f_idx-1]
                
                # transfer_memory
                df['delta_ssm_lag1'] = full['delta_ssm'][f_idx-1]
                df['delta_rzsm_lag1'] = full['delta_rzsm'][f_idx-1]
                df['delta_et_lag1'] = full['delta_et'][f_idx-1]
                df['delta_surface_runoff_lag1'] = full['delta_qs'][f_idx-1]
                df['delta_baseflow_lag1'] = full['delta_qsb'][f_idx-1]
                
                # meteorology_current
                df['precip_t'] = full['precip'][f_idx]
                df['tair_t'] = full['tair'][f_idx]
                
                # forcing_perturbation_control
                df['delta_precip_forcing_t'] = full['delta_precip'][f_idx]
                df['delta_precip_forcing_pre3d_sum'] = full['delta_precip'][t_slice_3d].sum(axis=0)
                df['delta_precip_forcing_pre7d_sum'] = full['delta_precip'][t_slice_7d].sum(axis=0)
                
                # meteorology_antecedent
                df['precip_lag1'] = full['precip'][f_idx-1]
                df['precip_pre3d_sum'] = full['precip'][t_slice_3d].sum(axis=0)
                df['precip_pre7d_sum'] = full['precip'][t_slice_7d].sum(axis=0)
                df['tair_lag1'] = full['tair'][f_idx-1]
                df['tair_pre3d_mean'] = full['tair'][t_slice_3d].mean(axis=0)
                df['tair_pre7d_mean'] = full['tair'][t_slice_7d].mean(axis=0)
                
                # baseline_flux_lagged
                df['et_opl_lag1'] = full['opl_et'][f_idx-1]
                df['surface_runoff_opl_lag1'] = full['opl_qs'][f_idx-1]
                df['baseflow_opl_lag1'] = full['opl_qsb'][f_idx-1]
                
                # Temporal context
                df['month'] = date.month
                df['day_of_year'] = date.dayofyear
                days_in_year = 366 if date.is_leap_year else 365
                df['doy_sin'] = np.sin(2 * np.pi * date.dayofyear / days_in_year)
                df['doy_cos'] = np.cos(2 * np.pi * date.dayofyear / days_in_year)
                
                # Static
                df['elevation'] = elev_valid
                for i in range(1, 21): df[f'land_cover_fraction_{i}'] = lc_vals[f'land_cover_fraction_{i}']
                for i in range(1, 17): df[f'soil_texture_fraction_{i}'] = st_vals[f'soil_texture_fraction_{i}']
                
                dfs.append(df)
            
            if dfs:
                month_df = pd.concat(dfs, ignore_index=True)
                part_path = f"{y_dir}/part-{month:02d}.parquet"
                # Use pyarrow to save efficiently
                table = pa.Table.from_pandas(month_df)
                pq.write_table(table, part_path, compression='snappy')
                del month_df
                del dfs
                gc.collect()
        
        prev_ds = curr_ds
        
    print(f"Finished {exp}")

if __name__ == "__main__":
    build_transfer_dataset("da_cdf")
    build_transfer_dataset("da_nocdf")
