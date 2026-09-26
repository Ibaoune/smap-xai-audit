import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta

def get_file_index(base_dir):
    """
    Builds a dictionary mapping canonical date (pd.Timestamp) to the actual LIS_HIST raw file path.
    Canonical date = Raw file timestamp - 1 day.
    """
    index = {}
    pattern = f"{base_dir}/**/*.d01.nc"
    files = glob.glob(pattern, recursive=True)
    for f in files:
        basename = os.path.basename(f)
        if basename.startswith("LIS_HIST_"):
            # LIS_HIST_YYYYMMDD0000.d01.nc
            date_str = basename.split("_")[2][:8]
            raw_ts = pd.to_datetime(date_str, format="%Y%m%d")
            canon_date = raw_ts - timedelta(days=1)
            index[canon_date] = f
    return index

def derive_da_precip_forcing_difference():
    print("="*60)
    print("DERIVING CANONICAL PRECIP-FORCING DIFFERENCE (DA - OPL)")
    print("="*60)
    
    base = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020"
    
    print("Building raw file index for OPL...")
    idx_opl = get_file_index(f"{base}/OPL_noirr_2016_2020/output")
    print("Building raw file index for DA-CDF...")
    idx_cdf = get_file_index(f"{base}/DA_cdf_noirr_2016_2020/output")
    print("Building raw file index for DA-NoCDF...")
    idx_nocdf = get_file_index(f"{base}/DA_nocdf_noirr_2016_2020/output")
    
    dates_req = pd.date_range(start="2016-01-01", end="2020-12-31", freq='D')
    print(f"Required canonical dates: {len(dates_req)}")
    
    # Verify complete canonical coverage
    missing_opl = [d for d in dates_req if d not in idx_opl]
    missing_cdf = [d for d in dates_req if d not in idx_cdf]
    missing_nocdf = [d for d in dates_req if d not in idx_nocdf]
    if missing_opl: print(f"Missing OPL: {len(missing_opl)}")
    if missing_cdf: print(f"Missing CDF: {len(missing_cdf)}")
    if missing_nocdf: print(f"Missing NoCDF: {len(missing_nocdf)}")
    
    if len(missing_opl) > 0 or len(missing_cdf) > 0 or len(missing_nocdf) > 0:
        raise ValueError("Missing dates in raw files! Coverage incomplete.")
        
    print("Complete coverage confirmed for 1827 dates.")
    
    # We need a reference dataset for lat/lon coordinates
    da_base = "data/interim/noahmp/da_cdf"
    ds_ssm_ref = xr.open_dataset(f"{da_base}/ssm/ssm_2016.nc")
    
    years = range(2016, 2021)
    
    # Initialize lists for full diagnostic arrays
    tair_diff_cdf_max = []
    tair_diff_nocdf_max = []
    
    for y in years:
        print(f"Processing year {y}...")
        y_dates = pd.date_range(start=f"{y}-01-01", end=f"{y}-12-31", freq='D')
        
        # We will create arrays (time, lat, lon)
        n_days = len(y_dates)
        n_lat = len(ds_ssm_ref.lat)
        n_lon = len(ds_ssm_ref.lon)
        
        delta_precip_cdf = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
        delta_precip_nocdf = np.zeros((n_days, n_lat, n_lon), dtype=np.float32)
        
        for i, d in enumerate(y_dates):
            f_opl = idx_opl[d]
            f_cdf = idx_cdf[d]
            f_nocdf = idx_nocdf[d]
            
            with xr.open_dataset(f_opl) as ds_o, xr.open_dataset(f_cdf) as ds_c, xr.open_dataset(f_nocdf) as ds_nc:
                p_opl = ds_o['TotalPrecip_tavg'].values * 86400.0 # mm/day
                p_cdf = ds_c['TotalPrecip_tavg'].values * 86400.0
                p_nocdf = ds_nc['TotalPrecip_tavg'].values * 86400.0
                
                t_opl = ds_o['Tair_f_tavg'].values
                t_cdf = ds_c['Tair_f_tavg'].values
                t_nocdf = ds_nc['Tair_f_tavg'].values
                
            delta_precip_cdf[i] = p_cdf - p_opl
            delta_precip_nocdf[i] = p_nocdf - p_opl
            
            # Record Tair diffs
            tair_diff_cdf_max.append(np.nanmax(np.abs(t_cdf - t_opl)))
            tair_diff_nocdf_max.append(np.nanmax(np.abs(t_nocdf - t_opl)))
            
        # Write canonical delta_precip_forcing to data/interim
        for exp, arr in zip(['da_cdf', 'da_nocdf'], [delta_precip_cdf, delta_precip_nocdf]):
            out_dir = f"data/interim/noahmp/{exp}/delta_precip_forcing"
            os.makedirs(out_dir, exist_ok=True)
            
            out_ds = xr.Dataset(
                {
                    "delta_precip_forcing": (["time", "lat", "lon"], arr)
                },
                coords={
                    "time": y_dates,
                    "lat": ds_ssm_ref.lat,
                    "lon": ds_ssm_ref.lon
                }
            )
            # Add attributes
            out_ds['delta_precip_forcing'].attrs['units'] = "mm/day"
            out_ds['delta_precip_forcing'].attrs['long_name'] = f"DA-minus-OPL precipitation forcing difference ({exp})"
            
            out_path = f"{out_dir}/delta_precip_forcing_{y}.nc"
            out_ds.to_netcdf(out_path, format="NETCDF4", engine="netcdf4")
            print(f"  Saved {out_path}")
            
    print("\n--- TAIR DIAGNOSTIC ---")
    print(f"DA-CDF Tair max abs difference: {np.max(tair_diff_cdf_max):.6e} K")
    print(f"DA-NoCDF Tair max abs difference: {np.max(tair_diff_nocdf_max):.6e} K")

if __name__ == "__main__":
    derive_da_precip_forcing_difference()
