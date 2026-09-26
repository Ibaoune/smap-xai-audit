#!/usr/bin/env python3
"""
01_build_source_dataset.py
Author: M. El Aabaribaoune

Builds leakage-controlled machine-learning/XAI datasets explaining
the magnitude of the daily SMAP EnKF surface-soil-moisture update.
"""
import os
import sys
import numpy as np
import pandas as pd
import xarray as xr

def build_experiment_dataset(exp):
    base_dir = "data/processed"
    interim_enkf = f"data/interim/enkf/{exp}"
    interim_noahmp = f"data/interim/noahmp/{exp}"
    interim_forcing = "data/interim/noahmp/forcing"
    
    out_dir = f"data/processed/modeling/source/{exp}"
    os.makedirs(out_dir, exist_ok=True)
    
    # Load statics
    elev_ds = xr.open_dataset("data/processed/static/elevation/elevation.nc")
    lc_ds = xr.open_dataset("data/processed/static/land_cover/land_cover_fraction.nc")
    st_ds = xr.open_dataset("data/processed/static/soil_texture/soil_texture_fraction.nc")
    
    lats = elev_ds.lat.values
    lons = elev_ds.lon.values
    lon_to_x = {float(lon): x for x, lon in enumerate(lons)}
    lat_to_y = {float(lat): y for y, lat in enumerate(lats)}
    
    # Load all years first to safely compute lagged features across year boundaries
    ds_dict = {}
    for year in range(2016, 2021):
        print(f"Loading {exp} year {year}...")
        ds_abs = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/daily_absolute_increment/daily_absolute_increment_{year}.nc")
        ds_sig = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/daily_signed_increment/daily_signed_increment_{year}.nc")
        ds_obs = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")
        ds_inn = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/daily_innovation/daily_innovation_{year}.nc")
        ds_fvar = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/daily_forecast_variance/daily_forecast_variance_{year}.nc")
        ds_ninn = xr.open_dataset(f"{base_dir}/daily_enkf/{exp}/daily_normalized_innovation/daily_normalized_innovation_{year}.nc")
        
        ds_ssm = xr.open_dataset(f"{interim_noahmp}/ssm/ssm_{year}.nc")
        ds_rzsm = xr.open_dataset(f"{base_dir}/daily_model/{exp}/rzsm/rzsm_{year}.nc")
        
        ds_precip = xr.open_dataset(f"{interim_forcing}/precipitation/precipitation_{year}.nc")
        ds_tair = xr.open_dataset(f"{interim_forcing}/air_temperature/air_temperature_{year}.nc")
        
        ds_year = xr.merge([
            ds_abs, ds_sig, ds_obs, ds_inn, ds_fvar, ds_ninn,
            ds_ssm, ds_rzsm, ds_precip, ds_tair
        ])
        ds_dict[year] = ds_year
    
    # Concatenate along time for lagged computation
    ds_all = xr.concat(list(ds_dict.values()), dim="time")
    
    print(f"Computing lagged features for {exp}...")
    ds_all['ssm_lag1'] = ds_all['ssm'].shift(time=1)
    ds_all['rzsm_lag1'] = ds_all['rzsm'].shift(time=1)
    
    ds_all['precip_lag1'] = ds_all['precipitation'].shift(time=1)
    ds_all['precip_pre3d_sum'] = ds_all['precipitation'].rolling(time=3, min_periods=3).sum().shift(time=1)
    ds_all['precip_pre7d_sum'] = ds_all['precipitation'].rolling(time=7, min_periods=7).sum().shift(time=1)
    
    ds_all['tair_lag1'] = ds_all['air_temperature'].shift(time=1)
    ds_all['tair_pre3d_mean'] = ds_all['air_temperature'].rolling(time=3, min_periods=3).mean().shift(time=1)
    ds_all['tair_pre7d_mean'] = ds_all['air_temperature'].rolling(time=7, min_periods=7).mean().shift(time=1)
    
    # Temporal context
    ds_all['month'] = ds_all['time.month']
    ds_all['day_of_year'] = ds_all['time.dayofyear']
    
    def is_leap_year(year):
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    year_len = xr.DataArray([366 if is_leap_year(y) else 365 for y in ds_all['time.year'].values], dims=["time"])
    
    doy = ds_all['day_of_year']
    ds_all['doy_sin'] = np.sin(2 * np.pi * doy / year_len)
    ds_all['doy_cos'] = np.cos(2 * np.pi * doy / year_len)
    
    # Filter for observation_frequency == 1 and finite innovation
    print(f"Extracting valid SOURCE rows for {exp}...")
    
    for year in range(2016, 2021):
        ds_year_lagged = ds_all.sel(time=str(year))
        
        # Flatten to DataFrame
        df = ds_year_lagged.to_dataframe().reset_index()
        
        # Merge static fields manually by lat, lon
        df['y_index'] = df['lat'].map(lat_to_y).astype(np.int32)
        df['x_index'] = df['lon'].map(lon_to_x).astype(np.int32)
        
        # Filter for obs_freq == 1 and finite innovation
        df = df[(df['observation_frequency'] == 1) & (np.isfinite(df['daily_innovation']))]
        
        # Exclude if lagged features are NaN
        lag_cols = ['ssm_lag1', 'rzsm_lag1', 'precip_lag1', 'precip_pre3d_sum', 'precip_pre7d_sum', 
                    'tair_lag1', 'tair_pre3d_mean', 'tair_pre7d_mean']
        df = df.dropna(subset=lag_cols)
        
        if df.empty:
            continue
            
        # Add static fields properly
        df = pd.merge(df, elev_ds.to_dataframe().reset_index(), on=['lat', 'lon'], how='left')
        
        lc_df = lc_ds.to_dataframe().reset_index()
        lc_df_pivot = lc_df.pivot(index=['lat', 'lon'], columns='land_cover_class', values='land_cover_fraction')
        lc_df_pivot.columns = [f'land_cover_fraction_{c}' for c in lc_df_pivot.columns]
        df = pd.merge(df, lc_df_pivot.reset_index(), on=['lat', 'lon'], how='left')
        
        st_df = st_ds.to_dataframe().reset_index()
        st_df_pivot = st_df.pivot(index=['lat', 'lon'], columns='texture_class', values='soil_texture_fraction')
        st_df_pivot.columns = [f'soil_texture_fraction_{c}' for c in st_df_pivot.columns]
        df = pd.merge(df, st_df_pivot.reset_index(), on=['lat', 'lon'], how='left')
        
        # Add metadata
        df['experiment'] = exp.upper().replace('_', '-')
        df['date'] = df['time'].dt.date
        df['year'] = df['time'].dt.year
        
        # Select final columns
        cols = [
            "date", "year", "lat", "lon", "y_index", "x_index", "experiment", "observation_frequency",
            "daily_absolute_increment", "daily_signed_increment",
            "daily_innovation", "daily_forecast_variance", "daily_normalized_innovation",
            "ssm_lag1", "rzsm_lag1",
            "precip_lag1", "precip_pre3d_sum", "precip_pre7d_sum",
            "tair_lag1", "tair_pre3d_mean", "tair_pre7d_mean",
            "elevation", "month", "day_of_year", "doy_sin", "doy_cos"
        ] + list(lc_df_pivot.columns) + list(st_df_pivot.columns)
        
        # Rename for consistency
        df = df.rename(columns={
            "daily_innovation": "innovation",
            "daily_forecast_variance": "forecast_variance",
            "daily_normalized_innovation": "normalized_innovation"
        })
        cols = [c if c not in ["daily_innovation", "daily_forecast_variance", "daily_normalized_innovation"] else c.replace("daily_", "") for c in cols]
        
        df = df[cols]
        
        # Write to parquet
        year_dir = f"{out_dir}/year={year}"
        os.makedirs(year_dir, exist_ok=True)
        df.to_parquet(f"{year_dir}/part-00000.parquet", index=False)
        print(f"  {year}: {len(df)} rows written.")

if __name__ == "__main__":
    for exp in ["da_cdf", "da_nocdf"]:
        build_experiment_dataset(exp)
