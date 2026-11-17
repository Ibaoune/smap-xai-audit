#!/usr/bin/env python3
"""
Derive Delta ET

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives delta_et = et_DA - et_OPL for DA-CDF and DA-NoCDF experiments.
Output represents the daily 24-h-mean evapotranspiration flux difference.
Known numerical row-wise structure from DA is preserved faithfully.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def derive_delta_et(base_dir, out_base_dir):
    exps = ["da_cdf", "da_nocdf"]
    years = [2016, 2017, 2018, 2019, 2020]
    
    # Store aggregated counts
    agg_counts = {'opl': {'neg': 0, 'zero': 0, 'pos': 0}}
    for exp in exps:
        agg_counts[exp] = {'neg': 0, 'zero': 0, 'pos': 0}
        
    for exp in exps:
        out_dir = os.path.join(out_base_dir, f"{exp}/delta_et")
        os.makedirs(out_dir, exist_ok=True)
        
        for year in years:
            print(f"\nProcessing {exp} for {year}...")
            
            p_opl = os.path.join(base_dir, f"data/interim/noahmp/opl/et/et_{year}.nc")
            p_da = os.path.join(base_dir, f"data/interim/noahmp/{exp}/et/et_{year}.nc")
            
            ds_opl = xr.open_dataset(p_opl)
            ds_da = xr.open_dataset(p_da)
            
            # 1. Identity Check
            assert np.all(ds_opl.time.values == ds_da.time.values), "Time mismatch"
            assert np.allclose(ds_opl.lat.values, ds_da.lat.values, atol=0), "Lat mismatch"
            assert np.allclose(ds_opl.lon.values, ds_da.lon.values, atol=0), "Lon mismatch"
            
            print(f"Max lat mismatch: {np.max(np.abs(ds_opl.lat.values - ds_da.lat.values))}")
            print(f"Max lon mismatch: {np.max(np.abs(ds_opl.lon.values - ds_da.lon.values))}")
            print(f"Date mismatch count: {np.sum(ds_opl.time.values != ds_da.time.values)}")
            
            et_opl = ds_opl['et'].values
            et_da = ds_da['et'].values
            
            # 2. Input ET statistics
            valid_opl = et_opl[~np.isnan(et_opl)]
            agg_counts['opl']['neg'] += np.sum(valid_opl < 0)
            agg_counts['opl']['zero'] += np.sum(valid_opl == 0)
            agg_counts['opl']['pos'] += np.sum(valid_opl > 0)
            
            valid_da = et_da[~np.isnan(et_da)]
            agg_counts[exp]['neg'] += np.sum(valid_da < 0)
            agg_counts[exp]['zero'] += np.sum(valid_da == 0)
            agg_counts[exp]['pos'] += np.sum(valid_da > 0)
            
            # 3. Calculate delta
            delta_et = (et_da - et_opl).astype(np.float32)
            
            # Mask based on support
            mask_opl = np.isnan(et_opl)
            mask_da = np.isnan(et_da)
            delta_et[mask_opl | mask_da] = np.nan
            
            # Missing data report
            canonical_land_mask = ~np.isnan(et_opl[0])
            for t_idx in range(len(ds_opl.time)):
                m_opl = np.isnan(et_opl[t_idx])
                m_da = np.isnan(et_da[t_idx])
                # Find if missing on canonical land
                m_opl_land = m_opl & canonical_land_mask
                m_da_land = m_da & canonical_land_mask
                
                opl_miss = np.sum(m_opl_land)
                da_miss = np.sum(m_da_land)
                if opl_miss > 0 or da_miss > 0:
                    print(f"Missing ET on canonical land on {ds_opl.time.values[t_idx]} - OPL: {opl_miss}, DA: {da_miss}")

            # 4. Save
            ds_out = xr.Dataset(
                {
                    "delta_et": (
                        ["time", "lat", "lon"],
                        delta_et,
                        {
                            "long_name": "Daily DA-minus-open-loop evapotranspiration difference",
                            "units": "mm/day",
                            "definition": "ET_DA - ET_OPL",
                            "et_source": "Noah-MP Evap_tavg",
                            "et_conversion": "Evap_tavg * 86400",
                            "averaging": "daily 24-h mean flux expressed in mm/day",
                            "reference_experiment": "OPL_noirr_2016_2020",
                            "da_experiment": f"{exp}_noirr_2016_2020",
                            "temporal_support": "daily canonical model calendar",
                            "xai_role": "Transfer target",
                            "numerical_structure_note": "known DA row-wise flux structure documented separately"
                        }
                    )
                },
                coords={
                    "time": ds_opl.time,
                    "lat": ds_opl.lat,
                    "lon": ds_opl.lon
                }
            )
            
            out_path = os.path.join(out_dir, f"delta_et_{year}.nc")
            ds_out.to_netcdf(out_path)
            print(f"Saved to {out_path}")

    print("\n--- Aggregated Source ET Counts (2016-2020) ---")
    for key, counts in agg_counts.items():
        print(f"{key.upper()} ET < 0 count: {counts['neg']}")
        print(f"{key.upper()} ET == 0 count: {counts['zero']}")
        print(f"{key.upper()} ET > 0 count: {counts['pos']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    args = parser.parse_args()
    
    out_base_dir = os.path.join(args.base_dir, 'data/processed/transfer')
    derive_delta_et(args.base_dir, out_base_dir)
