#!/usr/bin/env python3
"""
Derive Delta Baseflow

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Derives delta_baseflow = baseflow_DA - baseflow_OPL
for DA-CDF and DA-NoCDF experiments. Output represents the daily
DA-minus-OPL difference derived from the 24-h mean Noah-MP
Qsb_tavg flux and expressed in mm/day.

Important Note:
This is a subsurface-runoff/baseflow flux (Noah-MP Qsb_tavg), NOT routed 
streamflow, observed baseflow, groundwater storage, or groundwater-table depth.
The row-dependent structure in delta_baseflow is inherited from the DA Qsb/baseflow 
outputs and is consistent with the implementation-dependent numerical structure 
previously documented in the raw LIS flux diagnostics.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np

def derive_delta_baseflow(base_dir, out_base_dir):
    exps = ["da_cdf", "da_nocdf"]
    years = [2016, 2017, 2018, 2019, 2020]
    
    # Store aggregated counts
    agg_counts = {'opl': {'neg': 0, 'zero': 0, 'pos': 0}}
    for exp in exps:
        agg_counts[exp] = {'neg': 0, 'zero': 0, 'pos': 0}
        
    for exp in exps:
        out_dir = os.path.join(out_base_dir, f"{exp}/delta_baseflow")
        os.makedirs(out_dir, exist_ok=True)
        
        for year in years:
            print(f"\nProcessing {exp} for {year}...")
            
            p_opl = os.path.join(base_dir, f"data/interim/noahmp/opl/baseflow/baseflow_{year}.nc")
            p_da = os.path.join(base_dir, f"data/interim/noahmp/{exp}/baseflow/baseflow_{year}.nc")
            
            ds_opl = xr.open_dataset(p_opl)
            ds_da = xr.open_dataset(p_da)
            
            # 1. Identity Check
            assert np.all(ds_opl.time.values == ds_da.time.values), "Time mismatch"
            assert np.allclose(ds_opl.lat.values, ds_da.lat.values, atol=0), "Lat mismatch"
            assert np.allclose(ds_opl.lon.values, ds_da.lon.values, atol=0), "Lon mismatch"
            
            print(f"Max lat mismatch: {np.max(np.abs(ds_opl.lat.values - ds_da.lat.values))}")
            print(f"Max lon mismatch: {np.max(np.abs(ds_opl.lon.values - ds_da.lon.values))}")
            print(f"Date mismatch count: {np.sum(ds_opl.time.values != ds_da.time.values)}")
            
            val_opl = ds_opl['baseflow'].values
            val_da = ds_da['baseflow'].values
            
            # 2. Input statistics
            if exp == exps[0]:
                valid_opl = val_opl[~np.isnan(val_opl)]
                agg_counts['opl']['neg'] += np.sum(valid_opl < 0)
                agg_counts['opl']['zero'] += np.sum(valid_opl == 0)
                agg_counts['opl']['pos'] += np.sum(valid_opl > 0)
            
            valid_da = val_da[~np.isnan(val_da)]
            agg_counts[exp]['neg'] += np.sum(valid_da < 0)
            agg_counts[exp]['zero'] += np.sum(valid_da == 0)
            agg_counts[exp]['pos'] += np.sum(valid_da > 0)
            
            # 3. Calculate delta
            delta = (val_da - val_opl).astype(np.float32)
            
            # Mask based on support
            mask_opl = np.isnan(val_opl)
            mask_da = np.isnan(val_da)
            delta[mask_opl | mask_da] = np.nan
            
            # Missing data report
            canonical_land_mask = ~np.isnan(val_opl[0])
            for t_idx in range(len(ds_opl.time)):
                m_opl = np.isnan(val_opl[t_idx])
                m_da = np.isnan(val_da[t_idx])
                m_opl_land = m_opl & canonical_land_mask
                m_da_land = m_da & canonical_land_mask
                
                opl_miss = np.sum(m_opl_land)
                da_miss = np.sum(m_da_land)
                if opl_miss > 0 or da_miss > 0:
                    print(f"Missing baseflow on canonical land on {ds_opl.time.values[t_idx]} - OPL: {opl_miss}, DA: {da_miss}")

            # 4. Save
            ds_out = xr.Dataset(
                {
                    "delta_baseflow": (
                        ["time", "lat", "lon"],
                        delta,
                        {
                            "long_name": "Daily DA-minus-open-loop Noah-MP baseflow difference",
                            "units": "mm/day",
                            "definition": "baseflow_DA - baseflow_OPL",
                            "model_source": "Noah-MP Qsb_tavg",
                            "source_semantics": "subsurface-runoff/baseflow flux",
                            "conversion": "Qsb_tavg * 86400",
                            "averaging": "derived from daily 24-h mean Qsb_tavg flux",
                            "reference_experiment": "OPL_noirr_2016_2020",
                            "da_experiment": f"{exp}_noirr_2016_2020",
                            "temporal_support": "daily canonical model calendar",
                            "xai_role": "Transfer target",
                            "numerical_structure_note": "known row-dependent DA Qsb numerical structure documented separately"
                        }
                    )
                },
                coords={
                    "time": ds_opl.time,
                    "lat": ds_opl.lat,
                    "lon": ds_opl.lon
                }
            )
            
            out_path = os.path.join(out_dir, f"delta_baseflow_{year}.nc")
            ds_out.to_netcdf(out_path)
            print(f"Saved to {out_path}")

    print("\n--- Aggregated Source Baseflow Counts (2016-2020) ---")
    for key, counts in agg_counts.items():
        tot = counts['neg'] + counts['zero'] + counts['pos']
        print(f"{key.upper()} baseflow < 0 count: {counts['neg']}")
        print(f"{key.upper()} baseflow == 0 count: {counts['zero']} ({counts['zero']/tot:.2%})")
        print(f"{key.upper()} baseflow > 0 count: {counts['pos']} ({counts['pos']/tot:.2%})")
        print(f"Assertion: {key.upper()} total valid-land pixel-days == 29286810 -> {tot == 29286810}")
        assert tot == 29286810, f"Mismatch in {key.upper()} total count: {tot}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    args = parser.parse_args()
    
    out_base_dir = os.path.join(args.base_dir, 'data/processed/transfer')
    derive_delta_baseflow(args.base_dir, out_base_dir)
