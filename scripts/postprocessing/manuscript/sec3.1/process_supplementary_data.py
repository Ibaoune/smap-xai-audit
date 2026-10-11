"""
Data Processing Pipeline for Manuscript Supplementary Figures S1–S3
===================================================================

This script prepares the underlying frozen diagnostic datasets for the three
supplementary figures supporting Section 3.1:

1. Figure S1 (Sample Matching Sensitivity):
   - CDF and NoCDF signed increments on native vs matched samples (1D arrays).
   - Numerical summary metrics (mean |increment|, medians, percentiles).
   - Exported to:
     * figures/manuscript/section_3_1/FigS1_distributions.npz
     * figures/manuscript/section_3_1/FigS1_source_data.csv

2. Figure S2 (Seasonal Matched-Sample Differences):
   - Multi-year seasonal means of matched signed increments (NoCDF - CDF) for DJF, MAM, JJA, SON.
   - Exported to:
     * figures/manuscript/section_3_1/FigS2_source_data.nc
     * figures/manuscript/section_3_1/FigS2_seasonal_summary.csv

3. Figure S3 (Water-Equivalent Surface-Layer Analysis Adjustment):
   - Monthly climatology of absolute adjustment and net balance.
   - Cumulative 2016–2020 absolute adjustment difference spatial grid.
   - Standardized domain cumulative water accounting metrics table.
   - Exported to:
     * figures/manuscript/section_3_1/FigS3_monthly_climatology.csv
     * figures/manuscript/section_3_1/FigS3_cumulative_map.nc
     * figures/manuscript/section_3_1/FigS3_water_accounting_summary.csv

4. Comprehensive QC Audit Report:
   - Exported to: figures/manuscript/section_3_1/FigS1_S3_qc_report.txt
"""

import os
from pathlib import Path
import xarray as xr
import pandas as pd
import numpy as np

def get_project_root() -> Path:
    """Resolve repository root directory robustly."""
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
    print(f"Loading elevation mask from {elev_path}...")
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull()
    total_land_pixels = int(valid_land.sum().item())
    print(f"Valid land pixels: {total_land_pixels}")
    
    # -------------------------------------------------------------------------
    # 2. Load 2016-2020 Daily Innovation & Increment Datasets
    # -------------------------------------------------------------------------
    print("Loading 2016–2020 daily EnKF datasets...")
    innov_cdf_list, innov_nocdf_list = [], []
    signed_cdf_list, signed_nocdf_list = [], []
    
    for y in years:
        p_ic = root / f'data/processed/daily_enkf/da_cdf/daily_innovation/daily_innovation_{y}.nc'
        p_inc = root / f'data/processed/daily_enkf/da_nocdf/daily_innovation/daily_innovation_{y}.nc'
        p_sc = root / f'data/processed/daily_enkf/da_cdf/daily_signed_increment/daily_signed_increment_{y}.nc'
        p_snc = root / f'data/processed/daily_enkf/da_nocdf/daily_signed_increment/daily_signed_increment_{y}.nc'
        
        innov_cdf_list.append(xr.open_dataset(p_ic)['daily_innovation'])
        innov_nocdf_list.append(xr.open_dataset(p_inc)['daily_innovation'])
        signed_cdf_list.append(xr.open_dataset(p_sc)['daily_signed_increment'])
        signed_nocdf_list.append(xr.open_dataset(p_snc)['daily_signed_increment'])
        
    innov_cdf = xr.concat(innov_cdf_list, dim='time')
    innov_nocdf = xr.concat(innov_nocdf_list, dim='time')
    signed_cdf = xr.concat(signed_cdf_list, dim='time')
    signed_nocdf = xr.concat(signed_nocdf_list, dim='time')
    
    # Sample masks
    mask_cdf_native = innov_cdf.notnull()
    mask_nocdf_native = innov_nocdf.notnull()
    mask_matched = mask_cdf_native & mask_nocdf_native
    
    count_cdf_nat = int(mask_cdf_native.sum().item())
    count_nocdf_nat = int(mask_nocdf_native.sum().item())
    count_matched = int(mask_matched.sum().item())
    
    print(f"CDF native sample:   {count_cdf_nat:,} pixel-days")
    print(f"NoCDF native sample: {count_nocdf_nat:,} pixel-days")
    print(f"Matched sample:      {count_matched:,} pixel-days")
    
    # -------------------------------------------------------------------------
    # 3. Process Figure S1 Data (Increment Distributions: Native vs Matched)
    # -------------------------------------------------------------------------
    print("\nProcessing Figure S1 1D distribution arrays...")
    def extract_clean_1d(da, mask):
        arr = da.where(mask).values.flatten()
        return arr[~np.isnan(arr)].astype(np.float32)
    
    cdf_nat_1d = extract_clean_1d(signed_cdf, mask_cdf_native)
    cdf_mat_1d = extract_clean_1d(signed_cdf, mask_matched)
    nocdf_nat_1d = extract_clean_1d(signed_nocdf, mask_nocdf_native)
    nocdf_mat_1d = extract_clean_1d(signed_nocdf, mask_matched)
    
    npz_s1_path = out_dir / 'FigS1_distributions.npz'
    np.savez_compressed(
        npz_s1_path,
        cdf_native=cdf_nat_1d,
        cdf_matched=cdf_mat_1d,
        nocdf_native=nocdf_nat_1d,
        nocdf_matched=nocdf_mat_1d
    )
    print(f"Saved: {npz_s1_path}")
    
    def get_summary_row(arr, exp_name, sample_type):
        abs_arr = np.abs(arr)
        return {
            'experiment': exp_name,
            'sample_type': sample_type,
            'count': len(arr),
            'mean_signed_m3m3': float(np.mean(arr)),
            'std_signed_m3m3': float(np.std(arr)),
            'median_signed_m3m3': float(np.median(arr)),
            'mean_absolute_m3m3': float(np.mean(abs_arr)),
            'median_absolute_m3m3': float(np.median(abs_arr)),
            'fraction_positive': float((arr > 0).mean()),
            'fraction_negative': float((arr < 0).mean()),
            'fraction_zero': float((arr == 0).mean()),
            'Q01': float(np.percentile(arr, 1.0)),
            'Q05': float(np.percentile(arr, 5.0)),
            'Q25': float(np.percentile(arr, 25.0)),
            'Q50': float(np.percentile(arr, 50.0)),
            'Q75': float(np.percentile(arr, 75.0)),
            'Q95': float(np.percentile(arr, 95.0)),
            'Q99': float(np.percentile(arr, 99.0))
        }
        
    df_s1 = pd.DataFrame([
        get_summary_row(cdf_nat_1d, 'DA_CDF', 'native'),
        get_summary_row(cdf_mat_1d, 'DA_CDF', 'matched'),
        get_summary_row(nocdf_nat_1d, 'DA_NoCDF', 'native'),
        get_summary_row(nocdf_mat_1d, 'DA_NoCDF', 'matched')
    ])
    csv_s1_path = out_dir / 'FigS1_source_data.csv'
    df_s1.to_csv(csv_s1_path, index=False)
    print(f"Saved: {csv_s1_path}")
    
    # -------------------------------------------------------------------------
    # 4. Process Figure S2 Data (Seasonal Matched Increment Differences)
    # -------------------------------------------------------------------------
    print("\nProcessing Figure S2 seasonal difference grids...")
    diff_matched = (signed_nocdf - signed_cdf).where(mask_matched)
    month = diff_matched.time.dt.month
    
    djf_diff = diff_matched.sel(time=month.isin([12, 1, 2])).mean(dim='time').where(valid_land)
    mam_diff = diff_matched.sel(time=month.isin([3, 4, 5])).mean(dim='time').where(valid_land)
    jja_diff = diff_matched.sel(time=month.isin([6, 7, 8])).mean(dim='time').where(valid_land)
    son_diff = diff_matched.sel(time=month.isin([9, 10, 11])).mean(dim='time').where(valid_land)
    
    ds_s2 = xr.Dataset({
        'diff_djf': djf_diff.assign_attrs(units='m3 m-3', long_name='DJF matched signed increment difference (NoCDF - CDF)'),
        'diff_mam': mam_diff.assign_attrs(units='m3 m-3', long_name='MAM matched signed increment difference (NoCDF - CDF)'),
        'diff_jja': jja_diff.assign_attrs(units='m3 m-3', long_name='JJA matched signed increment difference (NoCDF - CDF)'),
        'diff_son': son_diff.assign_attrs(units='m3 m-3', long_name='SON matched signed increment difference (NoCDF - CDF)')
    })
    nc_s2_path = out_dir / 'FigS2_source_data.nc'
    ds_s2.to_netcdf(nc_s2_path)
    print(f"Saved: {nc_s2_path}")
    
    def get_grid_stats(da, season_name):
        vals = da.values[~np.isnan(da.values)]
        return {
            'season': season_name,
            'n_valid_pixels': len(vals),
            'mean_m3m3': float(np.mean(vals)),
            'std_m3m3': float(np.std(vals)),
            'median_m3m3': float(np.median(vals)),
            'min_m3m3': float(np.min(vals)),
            'max_m3m3': float(np.max(vals)),
            'fraction_positive': float((vals > 0).mean()),
            'fraction_negative': float((vals < 0).mean()),
            'Q05': float(np.percentile(vals, 5)),
            'Q25': float(np.percentile(vals, 25)),
            'Q75': float(np.percentile(vals, 75)),
            'Q95': float(np.percentile(vals, 95))
        }
        
    df_s2 = pd.DataFrame([
        get_grid_stats(djf_diff, 'DJF'),
        get_grid_stats(mam_diff, 'MAM'),
        get_grid_stats(jja_diff, 'JJA'),
        get_grid_stats(son_diff, 'SON')
    ])
    csv_s2_path = out_dir / 'FigS2_seasonal_summary.csv'
    df_s2.to_csv(csv_s2_path, index=False)
    print(f"Saved: {csv_s2_path}")
    
    # -------------------------------------------------------------------------
    # 5. Process Figure S3 Data (Water-Equivalent Accounting)
    # -------------------------------------------------------------------------
    print("\nProcessing Figure S3 water-accounting datasets...")
    # Load pre-aggregated monthly time series and compute 12-month climatology
    monthly_path = root / 'analysis_water_accounting_monthly.csv'
    if not monthly_path.is_file():
        raise FileNotFoundError(f"Missing {monthly_path}. Please run process_water_accounting.py first.")
    
    df_monthly_raw = pd.read_csv(monthly_path)
    df_monthly_raw['month'] = pd.to_datetime(df_monthly_raw['time']).dt.month
    df_clim = df_monthly_raw.drop(columns=['time']).groupby('month').mean().reset_index()
    df_clim['month_name'] = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    
    csv_s3_clim_path = out_dir / 'FigS3_monthly_climatology.csv'
    df_clim.to_csv(csv_s3_clim_path, index=False)
    print(f"Saved: {csv_s3_clim_path}")
    
    # Load cumulative NetCDFs to construct cumulative difference map
    cum_cdf_path = root / 'analysis_water_accounting_pixel_cumulative_cdf.nc'
    cum_nocdf_path = root / 'analysis_water_accounting_pixel_cumulative_nocdf.nc'
    
    if not (cum_cdf_path.is_file() and cum_nocdf_path.is_file()):
        raise FileNotFoundError("Missing pixel cumulative NetCDFs. Please run process_water_accounting.py first.")
        
    cum_cdf = xr.open_dataset(cum_cdf_path)
    cum_nocdf = xr.open_dataset(cum_nocdf_path)
    
    diff_cum_abs = (cum_nocdf['W_absolute'] - cum_cdf['W_absolute']).where(valid_land)
    diff_cum_net = (cum_nocdf['W_net'] - cum_cdf['W_net']).where(valid_land)
    
    ds_s3_map = xr.Dataset({
        'diff_cum_absolute': diff_cum_abs.assign_attrs(units='mm', long_name='2016-2020 Cumulative absolute-adjustment difference (NoCDF - CDF)'),
        'diff_cum_net': diff_cum_net.assign_attrs(units='mm', long_name='2016-2020 Cumulative net-adjustment difference (NoCDF - CDF)')
    })
    nc_s3_path = out_dir / 'FigS3_cumulative_map.nc'
    ds_s3_map.to_netcdf(nc_s3_path)
    print(f"Saved: {nc_s3_path}")
    
    # Save standardized water-accounting summary CSV
    summary_raw_path = root / 'analysis_water_accounting_summary.csv'
    df_summary = pd.read_csv(summary_raw_path)
    csv_s3_sum_path = out_dir / 'FigS3_water_accounting_summary.csv'
    df_summary.to_csv(csv_s3_sum_path, index=False)
    print(f"Saved: {csv_s3_sum_path}")
    
    # -------------------------------------------------------------------------
    # 6. Generate Comprehensive Supplementary QC Audit Report
    # -------------------------------------------------------------------------
    qc_path = out_dir / 'FigS1_S3_qc_report.txt'
    with open(qc_path, 'w', encoding='utf-8') as f:
        f.write("======================================================================\n")
        f.write("QC AUDIT REPORT - SUPPLEMENTARY FIGURES S1–S3\n")
        f.write("======================================================================\n\n")
        
        f.write("1. FIGURE S1: INCREMENT DISTRIBUTION BY SAMPLE MATCHING\n")
        f.write(f"   - CDF Native pixel-days:       {len(cdf_nat_1d):,} | Mean |inc|: {np.mean(np.abs(cdf_nat_1d)):.5f} m3 m-3\n")
        f.write(f"   - CDF Matched pixel-days:      {len(cdf_mat_1d):,} | Mean |inc|: {np.mean(np.abs(cdf_mat_1d)):.5f} m3 m-3\n")
        f.write(f"   - NoCDF Native pixel-days:     {len(nocdf_nat_1d):,} | Mean |inc|: {np.mean(np.abs(nocdf_nat_1d)):.5f} m3 m-3\n")
        f.write(f"   - NoCDF Matched pixel-days:    {len(nocdf_mat_1d):,} | Mean |inc|: {np.mean(np.abs(nocdf_mat_1d)):.5f} m3 m-3\n\n")
        
        f.write("2. FIGURE S2: SEASONAL MATCHED INCREMENT DIFFERENCES (NoCDF - CDF)\n")
        for _, row in df_s2.iterrows():
            f.write(f"   - {row['season']}: Mean = {row['mean_m3m3']:+.5f} m3 m-3 | Range = [{row['min_m3m3']:+.4f}, {row['max_m3m3']:+.4f}] | Wetting frac = {row['fraction_positive']*100:.1f}%\n")
        f.write("\n")
        
        f.write("3. FIGURE S3: WATER-EQUIVALENT ACCOUNTING (CUMULATIVE 2016–2020)\n")
        f.write(f"   - CDF Positive (Wetting):      +{df_summary.loc[0, 'area_weighted_positive_mm']:.1f} mm\n")
        f.write(f"   - CDF Removal (Drying):        -{df_summary.loc[0, 'area_weighted_removal_mm']:.1f} mm\n")
        f.write(f"   - CDF Absolute (Activity):     +{df_summary.loc[0, 'area_weighted_absolute_mm']:.1f} mm\n")
        f.write(f"   - CDF Net (Balance):           {df_summary.loc[0, 'area_weighted_net_mm']:.1f} mm\n")
        f.write(f"   - NoCDF Positive (Wetting):    +{df_summary.loc[1, 'area_weighted_positive_mm']:.1f} mm\n")
        f.write(f"   - NoCDF Removal (Drying):      -{df_summary.loc[1, 'area_weighted_removal_mm']:.1f} mm\n")
        f.write(f"   - NoCDF Absolute (Activity):   +{df_summary.loc[1, 'area_weighted_absolute_mm']:.1f} mm\n")
        f.write(f"   - NoCDF Net (Balance):         {df_summary.loc[1, 'area_weighted_net_mm']:.1f} mm\n")
        f.write("======================================================================\n")
        
    print(f"Saved: {qc_path}")
    print("\nSupplementary data processing completed successfully.")

if __name__ == '__main__':
    main()
