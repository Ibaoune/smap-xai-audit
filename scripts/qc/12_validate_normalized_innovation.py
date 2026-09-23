import os
import glob
import xarray as xr
import numpy as np

def validate(exp, year):
    print(f"--- {exp} {year} ---")
    f_ninnov = f"data/interim/enkf/{exp.lower().replace('-', '_')}/normalized_innovation/normalized_innovation_{year}.nc"
    f_innov = f"data/interim/enkf/{exp.lower().replace('-', '_')}/innovation/innovation_{year}.nc"
    f_var = f"data/interim/enkf/{exp.lower().replace('-', '_')}/forecast_variance/forecast_variance_{year}.nc"
    
    ds_n = xr.open_dataset(f_ninnov)
    ds_i = xr.open_dataset(f_innov)
    ds_v = xr.open_dataset(f_var)
    
    n_raw = ds_n['normalized_innovation'].values
    i_raw = ds_i['innovation'].values
    v_raw = ds_v['forecast_variance'].values
    
    denom = v_raw + 0.0016
    denom_valid = denom[~np.isnan(denom)]
    print(f"Denominator min: {np.min(denom_valid):.6f}, max: {np.max(denom_valid):.6f}")
    assert np.all(denom_valid > 0), "Found invalid denominator <= 0"
    
    std_innov = np.sqrt(denom)
    std_valid = std_innov[~np.isnan(std_innov)]
    print(f"Innov std min: {np.min(std_valid):.6f}, median: {np.median(std_valid):.6f}, max: {np.max(std_valid):.6f}")
    
    n_recon = i_raw / std_innov
    
    valid_mask = ~np.isnan(n_raw)
    
    diff = np.abs(n_raw[valid_mask] - n_recon[valid_mask])
    
    max_diff = np.max(diff) if len(diff) > 0 else np.nan
    mean_diff = np.mean(diff) if len(diff) > 0 else np.nan
    median_diff = np.median(diff) if len(diff) > 0 else np.nan
    rmse = np.sqrt(np.mean(diff**2)) if len(diff) > 0 else np.nan
    
    print(f"Max abs diff: {max_diff:.3e}")
    print(f"Mean abs diff: {mean_diff:.3e}")
    print(f"Median abs diff: {median_diff:.3e}")
    print(f"RMSE: {rmse:.3e}")
    
    print(f"Unequal > 1e-7: {np.sum(diff > 1e-7)}")
    print(f"Unequal > 1e-6: {np.sum(diff > 1e-6)}")
    print(f"Unequal > 1e-5: {np.sum(diff > 1e-5)}")
    
    # Missing masks
    mismatch = np.sum(np.isnan(n_raw) != np.isnan(n_recon))
    print(f"Missing mask mismatches: {mismatch}")
    return max_diff

def main():
    max_err = 0
    for exp in ['DA-CDF', 'DA-NoCDF']:
        for year in [2016, 2017, 2018, 2019, 2020]:
            err = validate(exp, year)
            if not np.isnan(err):
                max_err = max(max_err, err)
    print(f"WORST-CASE FULL-PERIOD RECONSTRUCTION ERROR: {max_err:.3e}")

if __name__ == "__main__":
    main()
