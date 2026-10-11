"""
Data Processing Pipeline for Manuscript Section 3.1 (Figure 3)
=============================================================

This script processes the 2016-2020 EnKF assimilation diagnostics for both
DA-CDF and DA-NoCDF experiments on the Morocco domain:

1. Computes the finite-diagnostic support masks:
   - CDF native support (finite daily innovations)
   - NoCDF native support (finite daily innovations)
   - Matched support (joint intersection of finite daily innovations)
2. Generates the spatial diagnostic-support frequency maps (Fig. 3a-c)
3. Computes the monthly diagnostic-support climatology (Fig. 3d)
4. Extracts the daily signed increments on exact matched support (Fig. 3e-h)
5. Exports NetCDF datasets, CSV statistical summaries, 1D compressed increment arrays,
   and a comprehensive numerical QC audit report.

Outputs:
  - figures/manuscript/section_3_1/Fig3_a_d_source_data.nc
  - figures/manuscript/section_3_1/Fig3_a_d_source_data.csv
  - figures/manuscript/section_3_1/Fig3_e_h_source_data.nc
  - figures/manuscript/section_3_1/Fig3_e_h_source_data.csv
  - figures/manuscript/section_3_1/matched_increments_1d.npz
  - figures/manuscript/section_3_1/matched_spatial_summary.csv
  - figures/manuscript/section_3_1/Fig3_qc_report.txt
"""

import os
from pathlib import Path
import xarray as xr
import pandas as pd
import numpy as np

def get_project_root() -> Path:
    """Resolve the repository root directory robustly."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'data').is_dir() and (parent / 'figures').is_dir():
            return parent
    return Path.cwd()

def main():
    root = get_project_root()
    out_dir = root / 'figures' / 'manuscript' / 'section_3_1'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Project root: {root}")
    print(f"Output directory: {out_dir}")
    
    years = [2016, 2017, 2018, 2019, 2020]
    
    # -------------------------------------------------------------------------
    # 1. Load Static Domain Mask
    # -------------------------------------------------------------------------
    elev_path = root / 'data' / 'processed' / 'static' / 'elevation' / 'elevation.nc'
    print(f"Loading elevation land mask from {elev_path}...")
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull()
    total_land_pixels = int(valid_land.sum().item())
    print(f"Total valid land pixels: {total_land_pixels}")
    
    # -------------------------------------------------------------------------
    # 2. Load 2016-2020 Daily EnKF Diagnostics
    # -------------------------------------------------------------------------
    innov_cdf_list = []
    innov_nocdf_list = []
    signed_cdf_list = []
    signed_nocdf_list = []
    
    for y in years:
        print(f"Loading year {y}...")
        p_ic = root / f'data/processed/daily_enkf/da_cdf/daily_innovation/daily_innovation_{y}.nc'
        p_inc = root / f'data/processed/daily_enkf/da_nocdf/daily_innovation/daily_innovation_{y}.nc'
        p_sc = root / f'data/processed/daily_enkf/da_cdf/daily_signed_increment/daily_signed_increment_{y}.nc'
        p_snc = root / f'data/processed/daily_enkf/da_nocdf/daily_signed_increment/daily_signed_increment_{y}.nc'
        
        ic = xr.open_dataset(p_ic)['daily_innovation']
        inc = xr.open_dataset(p_inc)['daily_innovation']
        sc = xr.open_dataset(p_sc)['daily_signed_increment']
        snc = xr.open_dataset(p_snc)['daily_signed_increment']
        
        innov_cdf_list.append(ic)
        innov_nocdf_list.append(inc)
        signed_cdf_list.append(sc)
        signed_nocdf_list.append(snc)
        
    print("Concatenating 2016-2020 time series...")
    innov_cdf = xr.concat(innov_cdf_list, dim='time')
    innov_nocdf = xr.concat(innov_nocdf_list, dim='time')
    signed_cdf = xr.concat(signed_cdf_list, dim='time')
    signed_nocdf = xr.concat(signed_nocdf_list, dim='time')
    
    n_days = int(innov_cdf.time.size)
    print(f"Total time steps (days): {n_days}")
    
    # -------------------------------------------------------------------------
    # 3. Define Native and Matched Diagnostic Support Masks
    # -------------------------------------------------------------------------
    mask_cdf_native = innov_cdf.notnull()
    mask_nocdf_native = innov_nocdf.notnull()
    mask_matched = mask_cdf_native & mask_nocdf_native
    
    cdf_count = int(mask_cdf_native.sum().item())
    nocdf_count = int(mask_nocdf_native.sum().item())
    matched_count = int(mask_matched.sum().item())
    unmatched_cdf = int((mask_cdf_native & ~mask_nocdf_native).sum().item())
    unmatched_nocdf = int((mask_nocdf_native & ~mask_cdf_native).sum().item())
    
    print("\n--- SUPPORT AUDIT ---")
    print(f"CDF native pixel-days:     {cdf_count:,}")
    print(f"NoCDF native pixel-days:   {nocdf_count:,}")
    print(f"Matched pixel-days:        {matched_count:,}")
    print(f"Unmatched CDF pixel-days:  {unmatched_cdf:,} ({unmatched_cdf / cdf_count * 100:.2f}%)")
    print(f"Unmatched NoCDF pixel-days:{unmatched_nocdf:,} ({unmatched_nocdf / nocdf_count * 100:.2f}%)")
    
    # -------------------------------------------------------------------------
    # 4. Generate Fig. 3a-d Source Datasets (Support Structure)
    # -------------------------------------------------------------------------
    print("\nGenerating Fig. 3a-d source datasets...")
    freq_cdf = (mask_cdf_native.sum(dim='time') / n_days * 100.0).where(valid_land)
    freq_nocdf = (mask_nocdf_native.sum(dim='time') / n_days * 100.0).where(valid_land)
    freq_diff = freq_nocdf - freq_cdf
    
    ds_3ad_nc = xr.Dataset({
        'freq_cdf': freq_cdf.assign_attrs(units='%', long_name='CDF finite EnKF diagnostic frequency'),
        'freq_nocdf': freq_nocdf.assign_attrs(units='%', long_name='NoCDF finite EnKF diagnostic frequency'),
        'freq_diff': freq_diff.assign_attrs(units='percentage points', long_name='Support difference (NoCDF - CDF)')
    })
    nc_3ad_path = out_dir / 'Fig3_a_d_source_data.nc'
    ds_3ad_nc.to_netcdf(nc_3ad_path)
    print(f"Saved: {nc_3ad_path}")
    
    # Monthly Support Climatology
    def calc_monthly_support(mask):
        month_series = mask.time.dt.month
        monthly_rates = []
        for m in range(1, 13):
            m_mask = mask.sel(time=(month_series == m))
            n_days_m = m_mask.time.size
            total_possible_m = n_days_m * total_land_pixels
            actual_m = int(m_mask.sum().item())
            rate_m = (actual_m / total_possible_m) * 100.0
            monthly_rates.append(rate_m)
        return monthly_rates

    month_cdf = calc_monthly_support(mask_cdf_native)
    month_nocdf = calc_monthly_support(mask_nocdf_native)
    month_matched = calc_monthly_support(mask_matched)
    
    df_monthly = pd.DataFrame({
        'month': range(1, 13),
        'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'cdf_native_percent': month_cdf,
        'nocdf_native_percent': month_nocdf,
        'matched_support_percent': month_matched
    })
    csv_3ad_path = out_dir / 'Fig3_a_d_source_data.csv'
    df_monthly.to_csv(csv_3ad_path, index=False)
    print(f"Saved: {csv_3ad_path}")
    
    # -------------------------------------------------------------------------
    # 5. Extract Matched Analysis Updates (Fig. 3e-h)
    # -------------------------------------------------------------------------
    print("\nExtracting matched increments on exact frozen support...")
    signed_cdf_matched = signed_cdf.where(mask_matched)
    signed_nocdf_matched = signed_nocdf.where(mask_matched)
    
    mean_cdf_matched = signed_cdf_matched.mean(dim='time').where(valid_land)
    mean_nocdf_matched = signed_nocdf_matched.mean(dim='time').where(valid_land)
    mean_diff_matched = (mean_nocdf_matched - mean_cdf_matched).where(valid_land)
    
    ds_3eh_nc = xr.Dataset({
        'mean_cdf_matched': mean_cdf_matched.assign_attrs(units='m3 m-3', long_name='CDF matched mean daily signed increment'),
        'mean_nocdf_matched': mean_nocdf_matched.assign_attrs(units='m3 m-3', long_name='NoCDF matched mean daily signed increment'),
        'mean_diff_matched': mean_diff_matched.assign_attrs(units='m3 m-3', long_name='Matched mean signed increment difference (NoCDF - CDF)')
    })
    nc_3eh_path = out_dir / 'Fig3_e_h_source_data.nc'
    ds_3eh_nc.to_netcdf(nc_3eh_path)
    print(f"Saved: {nc_3eh_path}")
    
    # 1D matched arrays
    arr_cdf_mat = signed_cdf_matched.values.flatten()
    arr_cdf_mat = arr_cdf_mat[~np.isnan(arr_cdf_mat)]
    
    arr_nocdf_mat = signed_nocdf_matched.values.flatten()
    arr_nocdf_mat = arr_nocdf_mat[~np.isnan(arr_nocdf_mat)]
    
    print(f"Extracted 1D arrays: CDF={len(arr_cdf_mat):,}, NoCDF={len(arr_nocdf_mat):,}")
    assert len(arr_cdf_mat) == matched_count, "CDF matched 1D count mismatch!"
    assert len(arr_nocdf_mat) == matched_count, "NoCDF matched 1D count mismatch!"
    
    npz_path = out_dir / 'matched_increments_1d.npz'
    np.savez_compressed(npz_path, cdf_mat=arr_cdf_mat, nocdf_mat=arr_nocdf_mat)
    print(f"Saved: {npz_path}")
    
    # -------------------------------------------------------------------------
    # 6. Compute Distribution and Spatial Summary Statistics
    # -------------------------------------------------------------------------
    def get_dist_stats(arr, name):
        abs_arr = np.abs(arr)
        return {
            'support': 'matched_support',
            'experiment': name,
            'N_pixel_days': len(arr),
            'mean_signed_m3m3': float(np.mean(arr)),
            'std_signed_m3m3': float(np.std(arr)),
            'median_signed_m3m3': float(np.median(arr)),
            'mean_absolute_m3m3': float(np.mean(abs_arr)),
            'median_absolute_m3m3': float(np.median(abs_arr)),
            'fraction_wetting_pos': float((arr > 0).mean()),
            'fraction_drying_neg': float((arr < 0).mean()),
            'fraction_zero': float((arr == 0).mean()),
            'Q005': float(np.percentile(arr, 0.5)),
            'Q01': float(np.percentile(arr, 1.0)),
            'Q05': float(np.percentile(arr, 5.0)),
            'Q25': float(np.percentile(arr, 25.0)),
            'Q50': float(np.percentile(arr, 50.0)),
            'Q75': float(np.percentile(arr, 75.0)),
            'Q95': float(np.percentile(arr, 95.0)),
            'Q99': float(np.percentile(arr, 99.0)),
            'Q995': float(np.percentile(arr, 99.5)),
            'Q95_absolute': float(np.percentile(abs_arr, 95.0)),
            'Q99_absolute': float(np.percentile(abs_arr, 99.0))
        }

    df_stats = pd.DataFrame([
        get_dist_stats(arr_cdf_mat, 'DA_CDF'),
        get_dist_stats(arr_nocdf_mat, 'DA_NoCDF')
    ])
    csv_3eh_path = out_dir / 'Fig3_e_h_source_data.csv'
    df_stats.to_csv(csv_3eh_path, index=False)
    print(f"Saved: {csv_3eh_path}")
    
    # Spatial Map Statistics
    def get_spatial_stats(da, name):
        vals = da.values[~np.isnan(da.values)]
        return {
            'metric': name,
            'mean': float(np.mean(vals)),
            'std': float(np.std(vals)),
            'median': float(np.median(vals)),
            'Q05': float(np.percentile(vals, 5)),
            'Q25': float(np.percentile(vals, 25)),
            'Q75': float(np.percentile(vals, 75)),
            'Q95': float(np.percentile(vals, 95)),
            'min': float(np.min(vals)),
            'max': float(np.max(vals)),
            'fraction_positive': float((vals > 0).mean()),
            'fraction_negative': float((vals < 0).mean())
        }

    df_spatial = pd.DataFrame([
        get_spatial_stats(mean_cdf_matched, 'Panel_f_CDF_matched_mean'),
        get_spatial_stats(mean_nocdf_matched, 'Panel_g_NoCDF_matched_mean'),
        get_spatial_stats(mean_diff_matched, 'Panel_h_Difference_NoCDF_minus_CDF')
    ])
    spatial_csv_path = out_dir / 'matched_spatial_summary.csv'
    df_spatial.to_csv(spatial_csv_path, index=False)
    print(f"Saved: {spatial_csv_path}")
    
    # -------------------------------------------------------------------------
    # 7. Generate Numerical QC Audit Report
    # -------------------------------------------------------------------------
    qc_path = out_dir / 'Fig3_qc_report.txt'
    with open(qc_path, 'w', encoding='utf-8') as f:
        f.write("======================================================================\n")
        f.write("QC AUDIT REPORT - MANUSCRIPT SECTION 3.1 (FIGURE 3)\n")
        f.write("======================================================================\n\n")
        f.write(f"Domain valid land pixels: {total_land_pixels}\n")
        f.write(f"Total time steps: {n_days} days (2016-01-01 to 2020-12-31)\n\n")
        f.write("1. DIAGNOSTIC SUPPORT COUNTS\n")
        f.write(f"   - CDF native support:      {cdf_count:,} pixel-days\n")
        f.write(f"   - NoCDF native support:    {nocdf_count:,} pixel-days\n")
        f.write(f"   - Exact matched support:   {matched_count:,} pixel-days\n")
        f.write(f"   - Unmatched CDF:           {unmatched_cdf:,} ({unmatched_cdf / cdf_count * 100:.2f}%)\n")
        f.write(f"   - Unmatched NoCDF:         {unmatched_nocdf:,} ({unmatched_nocdf / nocdf_count * 100:.2f}%)\n\n")
        f.write("2. MATCHED SIGNED INCREMENTS (DISTRIBUTION)\n")
        f.write(f"   - CDF mean signed:         {df_stats.loc[0, 'mean_signed_m3m3']:+.6f} m3 m-3\n")
        f.write(f"   - NoCDF mean signed:       {df_stats.loc[1, 'mean_signed_m3m3']:+.6f} m3 m-3\n")
        f.write(f"   - CDF mean absolute:       {df_stats.loc[0, 'mean_absolute_m3m3']:.6f} m3 m-3\n")
        f.write(f"   - NoCDF mean absolute:     {df_stats.loc[1, 'mean_absolute_m3m3']:.6f} m3 m-3\n")
        f.write(f"   - CDF drying fraction:     {df_stats.loc[0, 'fraction_drying_neg'] * 100:.2f}%\n")
        f.write(f"   - NoCDF wetting fraction:  {df_stats.loc[1, 'fraction_wetting_pos'] * 100:.2f}%\n\n")
        f.write("3. SPATIAL MAP METRICS (MATCHED SUPPORT)\n")
        f.write(f"   - Panel (f) CDF mean drying pixels:     {df_spatial.loc[0, 'fraction_negative'] * 100:.2f}%\n")
        f.write(f"   - Panel (g) NoCDF mean wetting pixels:   {df_spatial.loc[1, 'fraction_positive'] * 100:.2f}%\n")
        f.write(f"   - Panel (h) NoCDF > CDF difference:      {df_spatial.loc[2, 'fraction_positive'] * 100:.2f}%\n")
        f.write("======================================================================\n")
    print(f"Saved: {qc_path}")
    print("\nData processing complete successfully.")

if __name__ == '__main__':
    main()
