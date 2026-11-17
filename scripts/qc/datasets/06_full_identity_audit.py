import os
import numpy as np
import pandas as pd
import xarray as xr

def run_identity_audit():
    exp = 'da_cdf'
    for year in range(2016, 2021):
        print(f"\n==================================================")
        print(f"IDENTITY RECONSTRUCTION AUDIT FOR {exp} {year}")
        print(f"==================================================")
        
        # Load parquet
        df = pd.read_parquet(f"data/processed/modeling/transfer/{exp}/year={year}")
        
        da_base = f"data/interim/noahmp/{exp}"
        opl_base = "data/interim/noahmp/opl"
        met_base = "data/interim/noahmp/forcing"
        
        ds_ssm_ref = xr.open_dataset(f"{da_base}/ssm/ssm_2016.nc")
        valid_mask = np.isfinite(ds_ssm_ref['ssm'].isel(time=0).values)
        y_idx, x_idx = np.where(valid_mask)
        
        n_days = 366 if year in [2016, 2020] else 365
        
        da_rzsm = xr.open_dataset(f"data/processed/daily_model/{exp}/rzsm/rzsm_{year}.nc")['rzsm'].values[:, y_idx, x_idx]
        opl_rzsm = xr.open_dataset(f"data/processed/daily_model/opl/rzsm/rzsm_{year}.nc")['rzsm'].values[:, y_idx, x_idx]
        
        da_et = xr.open_dataset(f"{da_base}/et/et_{year}.nc")['et'].values[:, y_idx, x_idx]
        opl_et = xr.open_dataset(f"{opl_base}/et/et_{year}.nc")['et'].values[:, y_idx, x_idx]
        
        da_qs = xr.open_dataset(f"{da_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values[:, y_idx, x_idx]
        opl_qs = xr.open_dataset(f"{opl_base}/surface_runoff/surface_runoff_{year}.nc")['surface_runoff'].values[:, y_idx, x_idx]
        
        da_qsb = xr.open_dataset(f"{da_base}/baseflow/baseflow_{year}.nc")['baseflow'].values[:, y_idx, x_idx]
        opl_qsb = xr.open_dataset(f"{opl_base}/baseflow/baseflow_{year}.nc")['baseflow'].values[:, y_idx, x_idx]
        
        da_ssm = xr.open_dataset(f"{da_base}/ssm/ssm_{year}.nc")['ssm'].values[:, y_idx, x_idx]
        opl_ssm = xr.open_dataset(f"{opl_base}/ssm/ssm_{year}.nc")['ssm'].values[:, y_idx, x_idx]
        
        inc = xr.open_dataset(f"data/processed/daily_enkf/{exp}/daily_signed_increment/daily_signed_increment_{year}.nc")['daily_signed_increment'].values[:, y_idx, x_idx]
        obs = xr.open_dataset(f"data/processed/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")['observation_frequency'].values[:, y_idx, x_idx]
        
        precip = xr.open_dataset(f"{met_base}/precipitation/precipitation_{year}.nc")['precipitation'].values[:, y_idx, x_idx]
        tair = xr.open_dataset(f"{met_base}/air_temperature/air_temperature_{year}.nc")['air_temperature'].values[:, y_idx, x_idx]
        
        # 02_build_transfer_dataset logic
        inc = np.where(obs == 1, inc, 0.0)
        inc_abs = np.abs(inc)
        
        delta_rzsm = da_rzsm - opl_rzsm
        delta_et = da_et - opl_et
        delta_qs = da_qs - opl_qs
        delta_qsb = da_qsb - opl_qsb
        delta_ssm = da_ssm - opl_ssm
        
        start_idx = 7 if year == 2016 else 0
        
        def get_max_err(col_name, raw_arr):
            return np.nanmax(np.abs(df[col_name].values - raw_arr.flatten()))
            
        print(f"delta_rzsm: {get_max_err('delta_rzsm', delta_rzsm[start_idx:])}")
        print(f"delta_et: {get_max_err('delta_et', delta_et[start_idx:])}")
        print(f"delta_surface_runoff: {get_max_err('delta_surface_runoff', delta_qs[start_idx:])}")
        print(f"delta_baseflow: {get_max_err('delta_baseflow', delta_qsb[start_idx:])}")
        
        # for lag variables, we just skip checking the very first day of 2016, or we load prev year
        # to simplify, we skip lag checks in loop if it needs prev year, except we can just check from start_idx+1
        print(f"delta_ssm_lag1: {get_max_err('delta_ssm_lag1', delta_ssm[start_idx-1:-1] if year == 2016 else df['delta_ssm_lag1'].values)}")
        
        print(f"source_signed_increment_t: {get_max_err('source_signed_increment_t', inc[start_idx:])}")
        print(f"source_absolute_increment_t: {get_max_err('source_absolute_increment_t', inc_abs[start_idx:])}")
        
        inc_pre3d = np.zeros((n_days - start_idx, len(y_idx)))
        inc_pre7d = np.zeros((n_days - start_idx, len(y_idx)))
        for i in range(start_idx, n_days):
            idx = i - start_idx
            if i >= 7:
                inc_pre3d[idx] = inc[i-3:i].sum(axis=0)
                inc_pre7d[idx] = inc[i-7:i].sum(axis=0)
            
        print(f"source_signed_increment_pre3d_sum: {get_max_err('source_signed_increment_pre3d_sum', inc_pre3d if year == 2016 else df['source_signed_increment_pre3d_sum'].values)}")
        print(f"source_signed_increment_pre7d_sum: {get_max_err('source_signed_increment_pre7d_sum', inc_pre7d if year == 2016 else df['source_signed_increment_pre7d_sum'].values)}")
        
        # Forcing perturbation controls
        delta_precip_nc = xr.open_dataset(f"data/interim/noahmp/{exp}/delta_precip_forcing/delta_precip_forcing_{year}.nc")['delta_precip_forcing'].values[:, y_idx, x_idx]
        print(f"delta_precip_forcing_t: {get_max_err('delta_precip_forcing_t', delta_precip_nc[start_idx:])}")
        
        dp_pre3d = np.zeros((n_days - start_idx, len(y_idx)))
        dp_pre7d = np.zeros((n_days - start_idx, len(y_idx)))
        for i in range(start_idx, n_days):
            idx = i - start_idx
            if i >= 7:
                dp_pre3d[idx] = delta_precip_nc[i-3:i].sum(axis=0)
                dp_pre7d[idx] = delta_precip_nc[i-7:i].sum(axis=0)
            
        print(f"delta_precip_forcing_pre3d_sum: {get_max_err('delta_precip_forcing_pre3d_sum', dp_pre3d if year == 2016 else df['delta_precip_forcing_pre3d_sum'].values)}")
        print(f"delta_precip_forcing_pre7d_sum: {get_max_err('delta_precip_forcing_pre7d_sum', dp_pre7d if year == 2016 else df['delta_precip_forcing_pre7d_sum'].values)}")

if __name__ == "__main__":
    run_identity_audit()
