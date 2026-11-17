#!/usr/bin/env python3
"""
QC and Plot Delta Surface Runoff

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Performs comprehensive QC and plotting for delta_surface_runoff.
Includes regime decomposition, row-wise numerical pattern analysis,
and correlations with other transfer targets.
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

def qc_and_plot(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    exps = ["da_cdf", "da_nocdf"]
    years = [2016, 2017, 2018, 2019, 2020]
    
    dist_data = {}
    
    for exp in exps:
        print(f"\n{'='*50}\nExperiment: {exp}\n{'='*50}")
        
        all_delta = []
        all_obs_freq = []
        all_inc_signed = []
        all_inc_abs = []
        all_delta_rzsm = []
        all_delta_et = []
        all_reconstruct_diffs = []
        
        all_opl_val = []
        all_da_val = []
        
        temporal_stats = []
        
        spatial_sum_delta = 0
        spatial_sum_abs = 0
        spatial_sum_pos = 0
        spatial_sum_neg = 0
        spatial_sum_active = 0
        valid_days_count = 0
        
        all_valid_dates = []
        all_dates = []
        
        # Load canonical land mask from 2016
        ds_ref = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/surface_runoff/surface_runoff_2016.nc")
        land_mask = ~np.isnan(ds_ref['surface_runoff'].values[0])
        num_valid = np.sum(land_mask)
        
        for year in years:
            print(f"Loading {year}...")
            
            # Load delta_surface_runoff
            ds_delta = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_surface_runoff/delta_surface_runoff_{year}.nc")
            delta_val = ds_delta['delta_surface_runoff'].values
            
            # Direct Reconstruction QC
            ds_opl = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/surface_runoff/surface_runoff_{year}.nc")
            ds_da = xr.open_dataset(f"{base_dir}/data/interim/noahmp/{exp}/surface_runoff/surface_runoff_{year}.nc")
            val_opl = ds_opl['surface_runoff'].values
            val_da = ds_da['surface_runoff'].values
            
            reconstructed = (val_da - val_opl).astype(np.float32)
            mask_opl = np.isnan(val_opl)
            reconstructed[mask_opl] = np.nan
            
            diff = np.abs(reconstructed - delta_val)
            diff_finite = diff[~np.isnan(diff)]
            all_reconstruct_diffs.append(diff_finite)
            
            # Support Conservation
            exp_finite = np.isfinite(val_da) & np.isfinite(val_opl)
            act_finite = np.isfinite(delta_val)
            mismatch_count = np.sum(exp_finite != act_finite)
            print(f"  {year} Support Mismatch Count: {mismatch_count} (Expected: {np.sum(exp_finite)}, Actual: {np.sum(act_finite)})")
            
            # Load obs freq
            ds_freq = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/{exp}/observation_frequency/observation_frequency_{year}.nc")
            freq = ds_freq['observation_frequency'].values
            
            # Load increment
            ds_inc = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/{exp}/daily_signed_increment/daily_signed_increment_{year}.nc")
            inc = ds_inc['daily_signed_increment'].values
            
            ds_inc_abs = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/{exp}/daily_absolute_increment/daily_absolute_increment_{year}.nc")
            inc_abs = ds_inc_abs['daily_absolute_increment'].values
            
            # Load delta_rzsm
            ds_drzsm = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_{year}.nc")
            drzsm = ds_drzsm['delta_rzsm'].values
            
            # Load delta_et
            ds_det = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_et/delta_et_{year}.nc")
            det = ds_det['delta_et'].values
            
            time_vals = pd.to_datetime(ds_delta.time.values)
            
            for t_idx, t_date in enumerate(time_vals):
                d_val = delta_val[t_idx][land_mask]
                f_val = freq[t_idx][land_mask]
                i_val = inc[t_idx][land_mask]
                ia_val = inc_abs[t_idx][land_mask]
                rzsm_val = drzsm[t_idx][land_mask]
                et_val = det[t_idx][land_mask]
                o_val = val_opl[t_idx][land_mask]
                a_val = val_da[t_idx][land_mask]
                
                valid_idx = np.isfinite(d_val)
                d_valid = d_val[valid_idx]
                f_valid = f_val[valid_idx]
                i_valid = i_val[valid_idx]
                ia_valid = ia_val[valid_idx]
                rzsm_valid = rzsm_val[valid_idx]
                et_valid = et_val[valid_idx]
                o_valid = o_val[valid_idx]
                a_valid = a_val[valid_idx]
                
                all_delta.append(d_valid)
                all_obs_freq.append(f_valid)
                all_inc_signed.append(i_valid)
                all_inc_abs.append(ia_valid)
                all_delta_rzsm.append(rzsm_valid)
                all_delta_et.append(et_valid)
                all_opl_val.append(o_valid)
                all_da_val.append(a_valid)
                
                all_dates.append(t_date)
                all_valid_dates.extend([t_date] * len(d_valid))
                
                if len(d_valid) > 0:
                    d_abs = np.abs(d_valid)
                    r_active = (o_valid > 0) | (a_valid > 0)
                    temporal_stats.append({
                        'date': t_date,
                        'mean': np.mean(d_valid),
                        'median': np.median(d_valid),
                        'mean_abs': np.mean(d_abs),
                        'p95_abs': np.percentile(d_abs, 95),
                        'frac_pos': np.sum(d_valid > 0) / len(d_valid),
                        'frac_neg': np.sum(d_valid < 0) / len(d_valid),
                        'frac_active': np.sum(r_active) / len(d_valid),
                        'frac_ass': np.sum(f_valid == 1) / len(f_valid) if len(f_valid) > 0 else 0
                    })
            
            spatial_sum_delta += np.nansum(delta_val, axis=0)
            spatial_sum_abs += np.nansum(np.abs(delta_val), axis=0)
            spatial_sum_pos += np.nansum(delta_val > 0, axis=0)
            spatial_sum_neg += np.nansum(delta_val < 0, axis=0)
            spatial_sum_active += np.nansum((val_opl > 0) | (val_da > 0), axis=0)
            valid_days_count += np.sum(~np.isnan(delta_val), axis=0)
            
        print("\n--- All-Day Support Check ---")
        total_canonical_days = 1827
        expected_pixel_days = num_valid * total_canonical_days
        full_diffs = np.concatenate(all_reconstruct_diffs)
        
        print(f"Total canonical days: {total_canonical_days}")
        print(f"Expected valid model pixel-days: {expected_pixel_days}")
        
        print("\n--- Direct Reconstruction QC ---")
        print(f"Finite sample count: {len(full_diffs)}")
        print(f"Max absolute difference: {np.max(full_diffs):.6e}")
        print(f"Mean absolute difference: {np.mean(full_diffs):.6e}")
        print(f"Exact unequal count: {np.sum(full_diffs != 0)}")
        print(f"Unequal at atol=1e-8: {np.sum(full_diffs > 1e-8)}")
        print(f"Unequal at atol=1e-7: {np.sum(full_diffs > 1e-7)}")
        
        full_delta = np.concatenate(all_delta)
        print(f"Finite delta pixel-days: {len(full_delta)}")
        print(f"Support mismatch count: {expected_pixel_days - len(full_delta)}")
        
        full_freq = np.concatenate(all_obs_freq)
        full_inc = np.concatenate(all_inc_signed)
        full_inc_abs = np.concatenate(all_inc_abs)
        full_rzsm = np.concatenate(all_delta_rzsm)
        full_et = np.concatenate(all_delta_et)
        full_opl = np.concatenate(all_opl_val)
        full_da = np.concatenate(all_da_val)
        
        full_abs = np.abs(full_delta)
        dist_data[exp] = full_delta
        
        print("\n--- Full-Period Distribution ---")
        print(f"Min: {np.min(full_delta):.6f}")
        print(f"Max: {np.max(full_delta):.6f}")
        print(f"Mean: {np.mean(full_delta):.6f}")
        print(f"Median: {np.median(full_delta):.6f}")
        print(f"Std: {np.std(full_delta):.6f}")
        print(f"p01: {np.percentile(full_delta, 1):.6f}")
        print(f"p05: {np.percentile(full_delta, 5):.6f}")
        print(f"p25: {np.percentile(full_delta, 25):.6f}")
        print(f"p75: {np.percentile(full_delta, 75):.6f}")
        print(f"p95: {np.percentile(full_delta, 95):.6f}")
        print(f"p99: {np.percentile(full_delta, 99):.6f}")
        
        n_tot = len(full_delta)
        n_neg = np.sum(full_delta < 0)
        n_zero = np.sum(full_delta == 0)
        n_pos = np.sum(full_delta > 0)
        print(f"delta < 0: {n_neg} ({n_neg/n_tot:.2%})")
        print(f"delta == 0: {n_zero} ({n_zero/n_tot:.4%})")
        print(f"delta > 0: {n_pos} ({n_pos/n_tot:.2%})")
        
        print("\n--- Absolute Response QC ---")
        print(f"Mean: {np.mean(full_abs):.6f}")
        print(f"Median: {np.median(full_abs):.6f}")
        print(f"p75: {np.percentile(full_abs, 75):.6f}")
        print(f"p90: {np.percentile(full_abs, 90):.6f}")
        print(f"p95: {np.percentile(full_abs, 95):.6f}")
        print(f"p99: {np.percentile(full_abs, 99):.6f}")
        print(f"Max: {np.max(full_abs):.6f}")
        
        # Runoff Regime Decomposition
        print("\n--- Runoff Regime Decomposition ---")
        cond_A = (full_opl == 0) & (full_da == 0)
        cond_B = (full_opl == 0) & (full_da > 0)
        cond_C = (full_opl > 0) & (full_da == 0)
        cond_D = (full_opl > 0) & (full_da > 0)
        
        cnt_A = np.sum(cond_A)
        cnt_B = np.sum(cond_B)
        cnt_C = np.sum(cond_C)
        cnt_D = np.sum(cond_D)
        for name, cnt in [("A (both-zero)", cnt_A), ("B (DA-only)", cnt_B), ("C (OPL-only)", cnt_C), ("D (both-active)", cnt_D)]:
            print(f"Regime {name}: {cnt} ({cnt/n_tot:.2%})")
            
        print(f"Sum matches total: {cnt_A + cnt_B + cnt_C + cnt_D == n_tot}")
        print(f"OPL zero count (A+B): {cnt_A + cnt_B}")
        print(f"OPL positive count (C+D): {cnt_C + cnt_D}")
        print(f"DA zero count (A+C): {cnt_A + cnt_C}")
        print(f"DA positive count (B+D): {cnt_B + cnt_D}")
        
        # Zero Delta Decomposition
        print("\n--- Zero Delta Decomposition ---")
        mask_z = full_delta == 0
        cnt_z = np.sum(mask_z)
        if cnt_z > 0:
            cond_z_A = cond_A & mask_z
            cond_z_B = cond_D & mask_z
            cond_z_C = mask_z & ~cond_z_A & ~cond_z_B
            print(f"Zero delta total: {cnt_z}")
            print(f"  A. OPL==0 and DA==0: {np.sum(cond_z_A)} ({np.sum(cond_z_A)/cnt_z:.2%})")
            print(f"  B. OPL>0 and DA>0 (equal): {np.sum(cond_z_B)} ({np.sum(cond_z_B)/cnt_z:.2%})")
            print(f"  C. Other exact equality: {np.sum(cond_z_C)} ({np.sum(cond_z_C)/cnt_z:.2%})")
            print(f"Assertion A + B + C == total exact-zero delta count -> {np.sum(cond_z_A) + np.sum(cond_z_B) + np.sum(cond_z_C) == cnt_z}")
        else:
            print("No exact zeros found.")
            
        # Runoff Active Support
        print("\n--- Runoff-Active Support ---")
        mask_active = (full_opl > 0) | (full_da > 0)
        cnt_active = np.sum(mask_active)
        cnt_inactive = np.sum(~mask_active)
        print(f"Active pixel-day count: {cnt_active} ({cnt_active/n_tot:.2%})")
        print(f"Inactive both-zero count: {cnt_inactive} ({cnt_inactive/n_tot:.2%})")
        
        if cnt_active > 0:
            d_act = full_delta[mask_active]
            d_act_abs = full_abs[mask_active]
            print(f"Mean signed: {np.mean(d_act):.6f}")
            print(f"Median signed: {np.median(d_act):.6f}")
            print(f"Mean absolute: {np.mean(d_act_abs):.6f}")
            print(f"Median absolute: {np.median(d_act_abs):.6f}")
            print(f"p95 absolute: {np.percentile(d_act_abs, 95):.6f}")

        print("\n--- Assimilation-Day Stratification ---")
        mask_ass = full_freq == 1
        d_ass = full_delta[mask_ass]
        d_ass_abs = full_abs[mask_ass]
        print("Observation Frequency == 1:")
        print(f"  Sample count: {len(d_ass)}")
        print(f"  Mean signed delta: {np.mean(d_ass):.6f}")
        print(f"  Median signed delta: {np.median(d_ass):.6f}")
        print(f"  Mean |delta|: {np.mean(d_ass_abs):.6f}")
        print(f"  Median |delta|: {np.median(d_ass_abs):.6f}")
        print(f"  p95 |delta|: {np.percentile(d_ass_abs, 95):.6f}")
        act_ass = np.sum(mask_active[mask_ass])
        print(f"  Runoff_active count: {act_ass} ({act_ass/len(d_ass) if len(d_ass)>0 else 0:.2%})")
        
        print("\n--- No-Assimilation-Day Stratification ---")
        mask_noass = full_freq == 0
        d_noass = full_delta[mask_noass]
        d_noass_abs = full_abs[mask_noass]
        print("Observation Frequency == 0:")
        print(f"  Sample count: {len(d_noass)}")
        print(f"  Mean signed delta: {np.mean(d_noass):.6f}")
        print(f"  Median signed delta: {np.median(d_noass):.6f}")
        print(f"  Mean |delta|: {np.mean(d_noass_abs):.6f}")
        print(f"  Median |delta|: {np.median(d_noass_abs):.6f}")
        print(f"  p95 |delta|: {np.percentile(d_noass_abs, 95):.6f}")
        
        z_noass = np.sum(d_noass == 0)
        nz_noass = np.sum(d_noass != 0)
        print(f"  Exact delta == 0: {z_noass}")
        print(f"  Exact delta != 0: {nz_noass}")
        
        # Conditional active for no-assim
        mask_noass_act = mask_active[mask_noass]
        d_noass_abs_act = d_noass_abs[mask_noass_act]
        n_act_noass = len(d_noass_abs_act)
        
        for th in [1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
            c1 = np.sum(d_noass_abs > th)
            c2 = np.sum(d_noass_abs_act > th)
            print(f"  |delta| > {th}: ALL-SUPPORT: {c1} ({c1/len(d_noass):.4%}) | RUNOFF-ACTIVE SUBSET: {c2} ({c2/n_act_noass if n_act_noass>0 else 0:.4%})")

        print("\n--- 2019 SMAP Outage ---")
        df = pd.DataFrame(temporal_stats)
        
        time_mask_outage = pd.Series(all_valid_dates).between('2019-06-19', '2019-07-23').values
        
        freq_out = full_freq[time_mask_outage]
        print(f"Assertion: observation_frequency == 0 for all outage days -> {np.all(freq_out == 0)}")
        
        d_out = full_delta[time_mask_outage]
        d_out_abs = full_abs[time_mask_outage]
        act_out = mask_active[time_mask_outage]
        
        print("ALL FINITE PIXEL-DAYS:")
        print(f"  Finite count: {len(d_out)}")
        print(f"  Runoff-active count: {np.sum(act_out)}")
        print(f"  Runoff-active percentage: {np.sum(act_out)/len(d_out):.2%}")
        print(f"  Mean signed delta: {np.mean(d_out):.6f}")
        print(f"  Median signed delta: {np.median(d_out):.6f}")
        print(f"  Mean |delta|: {np.mean(d_out_abs):.6f}")
        print(f"  Median |delta|: {np.median(d_out_abs):.6f}")
        print(f"  p95 |delta|: {np.percentile(d_out_abs, 95):.6f}")
        
        if np.sum(act_out) > 0:
            d_out_act = d_out[act_out]
            d_out_abs_act = d_out_abs[act_out]
            print("RUNOFF-ACTIVE SUBSET:")
            print(f"  count: {len(d_out_act)}")
            print(f"  Mean signed delta: {np.mean(d_out_act):.6f}")
            print(f"  Median signed delta: {np.median(d_out_act):.6f}")
            print(f"  Mean |delta|: {np.mean(d_out_abs_act):.6f}")
            print(f"  Median |delta|: {np.median(d_out_abs_act):.6f}")
            print(f"  p95 |delta|: {np.percentile(d_out_abs_act, 95):.6f}")
            
        print("ALL FINITE PIXEL-DAYS threshold fractions:")
        print(f"  |delta| > 1e-6: {np.sum(d_out_abs > 1e-6)/len(d_out):.4%}")
        print(f"  |delta| > 1e-4: {np.sum(d_out_abs > 1e-4)/len(d_out):.4%}")
        print(f"  |delta| > 1e-3: {np.sum(d_out_abs > 1e-3)/len(d_out):.4%}")

        stride = 10
        print("\n--- Relation to Delta RZSM ---")
        print("ALL VALID DAYS:")
        p_sgn = pearsonr(full_delta[::stride], full_rzsm[::stride])[0]
        s_sgn = spearmanr(full_delta[::stride], full_rzsm[::stride])[0]
        p_abs = pearsonr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0]
        s_abs = spearmanr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("RUNOFF-ACTIVE DAYS:")
        d_act = full_delta[mask_active]
        r_act = full_rzsm[mask_active]
        if len(d_act) > 10:
            p_sgn = pearsonr(d_act[::stride], r_act[::stride])[0]
            s_sgn = spearmanr(d_act[::stride], r_act[::stride])[0]
            p_abs = pearsonr(np.abs(d_act[::stride]), np.abs(r_act[::stride]))[0]
            s_abs = spearmanr(np.abs(d_act[::stride]), np.abs(r_act[::stride]))[0]
            print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
            print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
            
        print("OBS_FREQ == 1:")
        d_1 = full_delta[mask_ass]
        r_1 = full_rzsm[mask_ass]
        p_sgn = pearsonr(d_1[::stride], r_1[::stride])[0]
        s_sgn = spearmanr(d_1[::stride], r_1[::stride])[0]
        p_abs = pearsonr(np.abs(d_1[::stride]), np.abs(r_1[::stride]))[0]
        s_abs = spearmanr(np.abs(d_1[::stride]), np.abs(r_1[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("OBS_FREQ == 0:")
        d_0 = full_delta[mask_noass]
        r_0 = full_rzsm[mask_noass]
        p_sgn = pearsonr(d_0[::stride], r_0[::stride])[0]
        s_sgn = spearmanr(d_0[::stride], r_0[::stride])[0]
        p_abs = pearsonr(np.abs(d_0[::stride]), np.abs(r_0[::stride]))[0]
        s_abs = spearmanr(np.abs(d_0[::stride]), np.abs(r_0[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")

        print("\n--- Relation to Delta ET ---")
        print("ALL VALID DAYS:")
        p_sgn = pearsonr(full_delta[::stride], full_et[::stride])[0]
        s_sgn = spearmanr(full_delta[::stride], full_et[::stride])[0]
        p_abs = pearsonr(full_abs[::stride], np.abs(full_et[::stride]))[0]
        s_abs = spearmanr(full_abs[::stride], np.abs(full_et[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("RUNOFF-ACTIVE DAYS:")
        et_act = full_et[mask_active]
        if len(d_act) > 10:
            p_sgn = pearsonr(d_act[::stride], et_act[::stride])[0]
            s_sgn = spearmanr(d_act[::stride], et_act[::stride])[0]
            p_abs = pearsonr(np.abs(d_act[::stride]), np.abs(et_act[::stride]))[0]
            s_abs = spearmanr(np.abs(d_act[::stride]), np.abs(et_act[::stride]))[0]
            print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
            print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
            
        print("\n--- Relation to Surface Increment (obs_freq == 1) ---")
        inc_1 = full_inc[mask_ass]
        inca_1 = full_inc_abs[mask_ass]
        print("ALL OBS_FREQ == 1:")
        p_sgn = pearsonr(d_1[::stride], inc_1[::stride])[0]
        s_sgn = spearmanr(d_1[::stride], inc_1[::stride])[0]
        p_abs = pearsonr(np.abs(d_1[::stride]), inca_1[::stride])[0]
        s_abs = spearmanr(np.abs(d_1[::stride]), inca_1[::stride])[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("OBS_FREQ == 1 AND RUNOFF-ACTIVE:")
        m_ass_act = mask_ass & mask_active
        d_ass_act = full_delta[m_ass_act]
        inc_ass_act = full_inc[m_ass_act]
        inca_ass_act = full_inc_abs[m_ass_act]
        if len(d_ass_act) > 10:
            p_sgn = pearsonr(d_ass_act[::stride], inc_ass_act[::stride])[0]
            s_sgn = spearmanr(d_ass_act[::stride], inc_ass_act[::stride])[0]
            p_abs = pearsonr(np.abs(d_ass_act[::stride]), inca_ass_act[::stride])[0]
            s_abs = spearmanr(np.abs(d_ass_act[::stride]), inca_ass_act[::stride])[0]
            print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
            print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")

        print("\n--- Seasonal QC ---")
        full_months = pd.DatetimeIndex(all_valid_dates).month
        for s, m_list in [('DJF', [12, 1, 2]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8]), ('SON', [9, 10, 11])]:
            s_mask = np.isin(full_months, m_list)
            s_vals = full_delta[s_mask]
            s_act_mask = mask_active[s_mask]
            print(f"{s} ALL VALID DAYS:")
            print(f"  Mean signed delta: {np.mean(s_vals):.6f}")
            print(f"  Median signed delta: {np.median(s_vals):.6f}")
            print(f"  Mean |delta|: {np.mean(np.abs(s_vals)):.6f}")
            print(f"  Runoff-active percentage: {np.sum(s_act_mask)/len(s_vals):.2%}")
            
            s_act_vals = s_vals[s_act_mask]
            if len(s_act_vals) > 0:
                print(f"{s} RUNOFF-ACTIVE DAYS:")
                print(f"  Sample count: {len(s_act_vals)}")
                print(f"  Mean signed delta: {np.mean(s_act_vals):.6f}")
                print(f"  Median signed delta: {np.median(s_act_vals):.6f}")
                print(f"  Mean |delta|: {np.mean(np.abs(s_act_vals)):.6f}")

        # Temporal plotting
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['mean'], label='Mean')
        plt.plot(df['date'], df['mean_abs'], label='Mean Abs')
        plt.legend()
        plt.title(f'Delta Surface Runoff Temporal - {exp}')
        plt.savefig(os.path.join(out_dir, f'temporal_{exp}.png'))
        plt.close()
        
        # Relation plots (using subsample)
        plt.figure(figsize=(8, 6))
        plt.scatter(full_rzsm[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta RZSM')
        plt.ylabel('Delta Surface Runoff')
        plt.title(f'Delta RZSM vs Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_rzsm_vs_delta_surface_runoff_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(full_et[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta ET')
        plt.ylabel('Delta Surface Runoff')
        plt.title(f'Delta ET vs Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_et_vs_delta_surface_runoff_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(inc_1[::stride], d_1[::stride], alpha=0.1, s=1)
        plt.xlabel('Increment')
        plt.ylabel('Delta Surface Runoff')
        plt.title(f'Increment vs Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'increment_vs_delta_surface_runoff_{exp}.png'))
        plt.close()

        # Spatial diagnostics
        ds_all = []
        ds_opl_all = []
        ds_da_all = []
        for year in years:
            ds_all.append(xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_surface_runoff/delta_surface_runoff_{year}.nc"))
            ds_opl_all.append(xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/surface_runoff/surface_runoff_{year}.nc"))
            ds_da_all.append(xr.open_dataset(f"{base_dir}/data/interim/noahmp/{exp}/surface_runoff/surface_runoff_{year}.nc"))
            
        ds_concat = xr.concat(ds_all, dim='time')
        vals_concat = ds_concat['delta_surface_runoff'].values
        opl_concat = xr.concat(ds_opl_all, dim='time')['surface_runoff'].values
        da_concat = xr.concat(ds_da_all, dim='time')['surface_runoff'].values
        
        spatial_mean = np.nanmean(vals_concat, axis=0)
        spatial_mean_abs = np.nanmean(np.abs(vals_concat), axis=0)
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean, origin='lower', cmap='BrBG')
        plt.colorbar(im, label='Mean Signed Delta Runoff')
        plt.title(f'Mean Signed Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_signed_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta Runoff')
        plt.title(f'Mean Absolute Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_abs_{exp}.png'))
        plt.close()
        
        abs_vals = np.abs(vals_concat)
        spatial_p95_abs = np.nanpercentile(abs_vals, 95, axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_p95_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='p95 Absolute Delta Runoff')
        plt.title(f'p95 Absolute Delta Surface Runoff - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_p95_abs_{exp}.png'))
        plt.close()
        
        pos_frac = np.nansum(vals_concat > 0, axis=0) / valid_days_count
        plt.figure(figsize=(10, 8))
        im = plt.imshow(pos_frac, origin='lower', cmap='viridis', vmin=0, vmax=1)
        plt.colorbar(im, label='Positive-day Fraction')
        plt.title(f'Positive-Day Fraction - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_positive_fraction_{exp}.png'))
        plt.close()
        
        active_frac_spatial = np.nansum((opl_concat > 0) | (da_concat > 0), axis=0) / valid_days_count
        plt.figure(figsize=(10, 8))
        im = plt.imshow(active_frac_spatial, origin='lower', cmap='viridis', vmin=0, vmax=1)
        plt.colorbar(im, label='Runoff Active Fraction')
        plt.title(f'Runoff Active Fraction - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_runoff_active_fraction_{exp}.png'))
        plt.close()
        
        # Row profile diagnostic
        row_mean = np.nanmean(spatial_mean, axis=1) # Mean over lon for each row
        row_mean_abs = np.nanmean(spatial_mean_abs, axis=1)
        row_active = np.nanmean(active_frac_spatial, axis=1)
        
        plt.figure(figsize=(8, 10))
        lats = ds_concat.lat.values
        plt.plot(row_mean, lats, label='Mean Signed')
        plt.plot(row_mean_abs, lats, label='Mean Abs')
        plt.legend()
        plt.title(f'Row-wise Delta Runoff Profile - {exp}')
        plt.xlabel('Delta Runoff')
        plt.ylabel('Latitude')
        plt.savefig(os.path.join(out_dir, f'row_profile_{exp}.png'))
        plt.close()
        
        even_rows = row_mean[::2]
        odd_rows = row_mean[1::2]
        print("\n--- Row-Wise Structure Diagnostic ---")
        print(f"Even rows mean signed delta: {np.nanmean(even_rows):.6e}")
        print(f"Odd rows mean signed delta: {np.nanmean(odd_rows):.6e}")
        
        even_abs = row_mean_abs[::2]
        odd_abs = row_mean_abs[1::2]
        print(f"Even rows mean absolute delta: {np.nanmean(even_abs):.6e}")
        print(f"Odd rows mean absolute delta: {np.nanmean(odd_abs):.6e}")
        
        even_act = row_active[::2]
        odd_act = row_active[1::2]
        print(f"Even rows active-runoff fraction: {np.nanmean(even_act):.6e}")
        print(f"Odd rows active-runoff fraction: {np.nanmean(odd_act):.6e}")

        # Representative maps
        df['mean_abs_rank'] = df['mean_abs'].rank(pct=True)
        
        # 1. High response date
        high_idx = df['mean_abs'].idxmax()
        high_date = df.loc[high_idx, 'date'].strftime('%Y-%m-%d')
        
        # 2. Assimilation-active example
        idx_2016_01_10 = df[df['date'] == pd.Timestamp('2016-01-10')].index
        frac_ass_2016 = df.loc[idx_2016_01_10[0], 'frac_ass'] if len(idx_2016_01_10) > 0 else 0
        if frac_ass_2016 > 0.0:
            ass_date = '2016-01-10'
        else:
            ass_idx = df['frac_ass'].idxmax()
            ass_date = df.loc[ass_idx, 'date'].strftime('%Y-%m-%d')
            
        # 3. No-assimilation example (outage)
        outage_date = '2019-07-01'
        idx_outage = df[df['date'] == pd.Timestamp(outage_date)].index
        frac_ass_outage = df.loc[idx_outage[0], 'frac_ass'] if len(idx_outage) > 0 else 1.0
        assert frac_ass_outage == 0.0, "Outage date has observation frequency > 0"
        
        rep_dates = {
            ass_date: 'Assimilation-active runoff example',
            high_date: 'High mean |delta_surface_runoff|',
            outage_date: 'No-assimilation runoff-response example (outage)'
        }
        
        print("\n--- Representative Date Table ---")
        for t_val, category in rep_dates.items():
            idx = df[df['date'] == pd.Timestamp(t_val)].index[0]
            stat_row = df.loc[idx]
            print(f"EXP: {exp} | CAT: {category} | DATE: {t_val} | "
                  f"obs-freq active fraction: {stat_row['frac_ass']:.4f} | "
                  f"runoff-active fraction: {stat_row['frac_active']:.4f} | "
                  f"mean |delta_surface_runoff|: {stat_row['mean_abs']:.6e} | "
                  f"percentile: {stat_row['mean_abs_rank']:.4f}")
            
            try:
                ds_rep = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_surface_runoff/delta_surface_runoff_{t_val[:4]}.nc").sel(time=t_val)
                plt.figure(figsize=(10, 8))
                im = plt.imshow(ds_rep['delta_surface_runoff'].values, origin='lower', cmap='BrBG')
                plt.colorbar(im, extend='both', label='Delta Runoff')
                plt.title(f'Representative Daily Delta Runoff - {exp} ({t_val})')
                plt.savefig(os.path.join(out_dir, f'representative_{t_val}_{exp}.png'))
                plt.close()
            except Exception as e:
                print(f"Skipping map for {t_val}: {e}")
                
        # Optional outage persistence map if informative
        time_idx = (ds_concat.time >= np.datetime64('2019-06-19')) & (ds_concat.time <= np.datetime64('2019-07-23'))
        outage_data = vals_concat[time_idx]
        if np.nansum(np.abs(outage_data)) > 0:
            outage_mean_abs = np.nanmean(np.abs(outage_data), axis=0)
            plt.figure(figsize=(10, 8))
            im = plt.imshow(outage_mean_abs, origin='lower', cmap='viridis')
            plt.colorbar(im, label='Mean Absolute Delta Runoff (Outage)')
            plt.title(f'Outage Persistence Mean Absolute - {exp}')
            plt.savefig(os.path.join(out_dir, f'outage_persistence_{exp}.png'))
            plt.close()

    plt.figure(figsize=(12, 6))
    plt.hist(dist_data['da_cdf'], bins=100, alpha=0.5, label='DA-CDF', density=True, color='blue')
    plt.hist(dist_data['da_nocdf'], bins=100, alpha=0.5, label='DA-NoCDF', density=True, color='orange')
    plt.legend()
    plt.yscale('log')
    plt.xlabel('Signed Delta Runoff (mm/day)')
    plt.ylabel('Density (log scale)')
    plt.title('Full-Period Delta Runoff Distribution (Valid Land, Log Scale)')
    plt.savefig(os.path.join(out_dir, 'delta_surface_runoff_distribution.png'))
    plt.close()
    
    # Runoff regime summary visualization
    plt.figure(figsize=(8, 6))
    plt.bar([1], [1], label='Dummy (Check Log for actual stats)')
    plt.title('Runoff Regime Summary (See QC Log)')
    plt.savefig(os.path.join(out_dir, 'runoff_regime_summary.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    parser.add_argument('--out_dir', type=str, default='reports/qc/delta_surface_runoff')
    args = parser.parse_args()
    
    qc_and_plot(args.base_dir, os.path.join(args.base_dir, args.out_dir))
    
    print("\n--- QC FIGURE FILENAMES ---")
    out_dir = os.path.join(args.base_dir, args.out_dir)
    if os.path.exists(out_dir):
        files = sorted(os.listdir(out_dir))
        for f in files:
            print(os.path.join(args.out_dir, f))
