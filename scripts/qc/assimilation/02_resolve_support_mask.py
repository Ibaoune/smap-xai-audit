import os
import numpy as np
import pandas as pd
import xarray as xr

def resolve_mask():
    base_interim = "data/interim/enkf"
    base_model = "data/interim/noahmp/da_cdf"
    
    # 1. Native audit mask (derived dynamically in previous step)
    # Load all years to recreate dynamic mask
    valid_mask_native = np.zeros((121, 181), dtype=bool)
    for y in [2016, 2017, 2018, 2019, 2020]:
        ds_cdf = xr.open_dataset(f"{base_interim}/da_cdf/innovation/innovation_{y}.nc")
        ds_nocdf = xr.open_dataset(f"{base_interim}/da_nocdf/innovation/innovation_{y}.nc")
        mask_y = np.isfinite(ds_nocdf['innovation'].values).any(axis=0) | np.isfinite(ds_cdf['innovation'].values).any(axis=0)
        valid_mask_native = valid_mask_native | mask_y
        
    print(f"Native audit mask active pixels: {valid_mask_native.sum()}")
    
    # Canonical mask (from Noah-MP static fields or any ssm field)
    ds_ssm = xr.open_dataset(f"{base_model}/ssm/ssm_2016.nc")
    valid_mask_canonical = np.isfinite(ds_ssm['ssm'].isel(time=0).values)
    print(f"Canonical land mask active pixels: {valid_mask_canonical.sum()}")
    
    intersect = valid_mask_native & valid_mask_canonical
    native_only = valid_mask_native & ~valid_mask_canonical
    canonical_only = valid_mask_canonical & ~valid_mask_native
    
    print(f"Intersection: {intersect.sum()}")
    print(f"Native-audit-only: {native_only.sum()}")
    print(f"Canonical-land-only: {canonical_only.sum()}")
    
    # 2. Recompute categories on 16030 mask
    both_count = 0
    cdf_only_count = 0
    nocdf_only_count = 0
    neither_count = 0
    
    # 4. Experiment-only timestamp contribution
    cdf_only_time_count = 0
    nocdf_only_time_count = 0
    
    for y in [2016, 2017, 2018, 2019, 2020]:
        ds_cdf = xr.open_dataset(f"{base_interim}/da_cdf/innovation/innovation_{y}.nc")
        ds_nocdf = xr.open_dataset(f"{base_interim}/da_nocdf/innovation/innovation_{y}.nc")
        
        t_cdf = pd.to_datetime(ds_cdf['event_time'].values)
        t_nocdf = pd.to_datetime(ds_nocdf['event_time'].values)
        
        common_t = np.intersect1d(t_cdf, t_nocdf)
        cdf_only_t = np.setdiff1d(t_cdf, t_nocdf)
        nocdf_only_t = np.setdiff1d(t_nocdf, t_cdf)
        
        # Common timestamps
        inn_cdf = ds_cdf['innovation'].sel(event_time=common_t).values
        inn_nocdf = ds_nocdf['innovation'].sel(event_time=common_t).values
        
        fin_cdf = np.isfinite(inn_cdf) & valid_mask_canonical[None, :, :]
        fin_nocdf = np.isfinite(inn_nocdf) & valid_mask_canonical[None, :, :]
        
        both_count += (fin_cdf & fin_nocdf).sum()
        cdf_only_count += (fin_cdf & ~fin_nocdf).sum()
        nocdf_only_count += (~fin_cdf & fin_nocdf).sum()
        neither_count += (~fin_cdf & ~fin_nocdf & valid_mask_canonical[None, :, :]).sum()
        
        # CDF-only timestamps
        if len(cdf_only_t) > 0:
            inn_cdf_only = ds_cdf['innovation'].sel(event_time=cdf_only_t).values
            cdf_only_time_count += (np.isfinite(inn_cdf_only) & valid_mask_canonical[None, :, :]).sum()
            
        # NoCDF-only timestamps
        if len(nocdf_only_t) > 0:
            inn_nocdf_only = ds_nocdf['innovation'].sel(event_time=nocdf_only_t).values
            nocdf_only_time_count += (np.isfinite(inn_nocdf_only) & valid_mask_canonical[None, :, :]).sum()

    print("\n--- RECOMPUTED ON CANONICAL 16030 LAND MASK ---")
    print(f"BOTH: {both_count}")
    print(f"CDF_ONLY: {cdf_only_count}")
    print(f"NOCDF_ONLY: {nocdf_only_count}")
    print(f"NEITHER: {neither_count}")
    
    # 3. Exact common-timestamp closure
    cdf_finite = both_count + cdf_only_count
    nocdf_finite = both_count + nocdf_only_count
    print(f"\nCDF finite at common timestamps = {cdf_finite}")
    print(f"NoCDF finite at common timestamps = {nocdf_finite}")
    
    # 4. Experiment-only timestamp contribution
    print(f"\nCDF-only-time contribution = {cdf_only_time_count}")
    print(f"NoCDF-only-time contribution = {nocdf_only_time_count}")
    
    total_cdf = cdf_finite + cdf_only_time_count
    total_nocdf = nocdf_finite + nocdf_only_time_count
    print(f"\nTotal CDF pre-lag daily support: {total_cdf}")
    print(f"Total NoCDF pre-lag daily support: {total_nocdf}")
    
    # 6. Quantify temporal vs shared-time spatial difference
    excess = total_nocdf - total_cdf
    excess_temporal = nocdf_only_time_count - cdf_only_time_count
    excess_spatial = nocdf_finite - cdf_finite
    
    print(f"\nTotal excess NoCDF finite support relative to CDF: {excess}")
    print(f"  Contribution from experiment-only timestamps: {excess_temporal} ({excess_temporal/excess*100:.1f}%)")
    print(f"  Net contribution from shared timestamps: {excess_spatial} ({excess_spatial/excess*100:.1f}%)")

if __name__ == "__main__":
    resolve_mask()
