#!/usr/bin/env python3
"""
QC and Plot Delta Baseflow

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Performs comprehensive QC and plotting for delta_baseflow.
Includes exact-zero decomposition, row-wise numerical pattern analysis,
temporal persistence, and correlations with other transfer targets.
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
        all_delta_runoff = []
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
        ds_ref = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/baseflow/baseflow_2016.nc")
        land_mask = ~np.isnan(ds_ref['baseflow'].values[0])
        num_valid = np.sum(land_mask)
        
        for year in years:
            print(f"Loading {year}...")
            
            # Load delta_baseflow
            ds_delta = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_baseflow/delta_baseflow_{year}.nc")
            delta_val = ds_delta['delta_baseflow'].values
            
            # Direct Reconstruction QC
            ds_opl = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/baseflow/baseflow_{year}.nc")
            ds_da = xr.open_dataset(f"{base_dir}/data/interim/noahmp/{exp}/baseflow/baseflow_{year}.nc")
            val_opl = ds_opl['baseflow'].values
            val_da = ds_da['baseflow'].values
            
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
            
            # Load delta_surface_runoff
            ds_drunoff = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_surface_runoff/delta_surface_runoff_{year}.nc")
            drunoff = ds_drunoff['delta_surface_runoff'].values
            
            time_vals = pd.to_datetime(ds_delta.time.values)
            
            for t_idx, t_date in enumerate(time_vals):
                d_val = delta_val[t_idx][land_mask]
                f_val = freq[t_idx][land_mask]
                i_val = inc[t_idx][land_mask]
                ia_val = inc_abs[t_idx][land_mask]
                rzsm_val = drzsm[t_idx][land_mask]
                et_val = det[t_idx][land_mask]
                runoff_val = drunoff[t_idx][land_mask]
                o_val = val_opl[t_idx][land_mask]
                a_val = val_da[t_idx][land_mask]
                
                valid_idx = np.isfinite(d_val)
                d_valid = d_val[valid_idx]
                f_valid = f_val[valid_idx]
                i_valid = i_val[valid_idx]
                ia_valid = ia_val[valid_idx]
                rzsm_valid = rzsm_val[valid_idx]
                et_valid = et_val[valid_idx]
                runoff_valid = runoff_val[valid_idx]
                o_valid = o_val[valid_idx]
                a_valid = a_val[valid_idx]
                
                all_delta.append(d_valid)
                all_obs_freq.append(f_valid)
                all_inc_signed.append(i_valid)
                all_inc_abs.append(ia_valid)
                all_delta_rzsm.append(rzsm_valid)
                all_delta_et.append(et_valid)
                all_delta_runoff.append(runoff_valid)
                all_opl_val.append(o_valid)
                all_da_val.append(a_valid)
                
                all_dates.append(t_date)
                all_valid_dates.extend([t_date] * len(d_valid))
                
                if len(d_valid) > 0:
                    d_abs = np.abs(d_valid)
                    r_active = (o_valid != 0) | (a_valid != 0)
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
            spatial_sum_active += np.nansum((val_opl != 0) | (val_da != 0), axis=0)
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
        full_runoff = np.concatenate(all_delta_runoff)
        full_opl = np.concatenate(all_opl_val)
        full_da = np.concatenate(all_da_val)
        
        full_abs = np.abs(full_delta)
        dist_data[exp] = full_delta
        
        print("\n--- Full-Period Distribution ---")
        print(f"Min: {np.min(full_delta):.6e}")
        print(f"Max: {np.max(full_delta):.6e}")
        print(f"Mean: {np.mean(full_delta):.6e}")
        print(f"Median: {np.median(full_delta):.6e}")
        print(f"Std: {np.std(full_delta):.6e}")
        print(f"p01: {np.percentile(full_delta, 1):.6e}")
        print(f"p05: {np.percentile(full_delta, 5):.6e}")
        print(f"p25: {np.percentile(full_delta, 25):.6e}")
        print(f"p75: {np.percentile(full_delta, 75):.6e}")
        print(f"p95: {np.percentile(full_delta, 95):.6e}")
        print(f"p99: {np.percentile(full_delta, 99):.6e}")
        
        n_tot = len(full_delta)
        n_neg = np.sum(full_delta < 0)
        n_zero = np.sum(full_delta == 0)
        n_pos = np.sum(full_delta > 0)
        print(f"delta < 0: {n_neg} ({n_neg/n_tot:.2%})")
        print(f"delta == 0: {n_zero} ({n_zero/n_tot:.4%})")
        print(f"delta > 0: {n_pos} ({n_pos/n_tot:.2%})")
        
        print("\n--- Absolute Response QC ---")
        print(f"Mean: {np.mean(full_abs):.6e}")
        print(f"Median: {np.median(full_abs):.6e}")
        print(f"p75: {np.percentile(full_abs, 75):.6e}")
        print(f"p90: {np.percentile(full_abs, 90):.6e}")
        print(f"p95: {np.percentile(full_abs, 95):.6e}")
        print(f"p99: {np.percentile(full_abs, 99):.6e}")
        print(f"Max: {np.max(full_abs):.6e}")
        
        # Zero Delta Decomposition
        print("\n--- Zero Delta Decomposition ---")
        mask_z = full_delta == 0
        cnt_z = np.sum(mask_z)
        if cnt_z > 0:
            cond_A = (full_opl == 0) & (full_da == 0)
            cond_z_A = cond_A & mask_z
            cond_B = (full_opl != 0) & (full_da != 0)
            cond_z_B = cond_B & mask_z
            cond_z_C = mask_z & ~cond_z_A & ~cond_z_B
            print(f"Zero delta total: {cnt_z}")
            print(f"  A. OPL==0 and DA==0: {np.sum(cond_z_A)} ({np.sum(cond_z_A)/cnt_z:.2%})")
            print(f"  B. OPL!=0 and DA!=0 (equal): {np.sum(cond_z_B)} ({np.sum(cond_z_B)/cnt_z:.2%})")
            print(f"  C. Other exact equality configurations: {np.sum(cond_z_C)} ({np.sum(cond_z_C)/cnt_z:.2%})")
            print(f"Assertion A + B + C == total exact-zero delta count -> {np.sum(cond_z_A) + np.sum(cond_z_B) + np.sum(cond_z_C) == cnt_z}")
        else:
            print("Exact-zero count is negligible or zero.")
            
        # Non-Zero Baseflow Support
        print("\n--- Baseflow Non-Zero Support ---")
        mask_nonzero = (full_opl != 0) | (full_da != 0)
        cnt_active = np.sum(mask_nonzero)
        cnt_inactive = np.sum(~mask_nonzero)
        if cnt_inactive / n_tot > 0.01:
            print(f"Baseflow exact-zero is common. Non-zero support count: {cnt_active} ({cnt_active/n_tot:.2%})")
            print(f"Inactive both-zero count: {cnt_inactive} ({cnt_inactive/n_tot:.2%})")
            use_active = True
        else:
            print(f"Source baseflow is essentially non-zero everywhere. (Non-zero fraction: {cnt_active/n_tot:.4%})")
            print("Will not force an artificial active/inactive analysis.")
            use_active = False

        print("\n--- Assimilation-Day Stratification ---")
        mask_ass = full_freq == 1
        d_ass = full_delta[mask_ass]
        d_ass_abs = full_abs[mask_ass]
        print("Observation Frequency == 1:")
        print(f"  Sample count: {len(d_ass)}")
        print(f"  Mean signed delta: {np.mean(d_ass):.6e}")
        print(f"  Median signed delta: {np.median(d_ass):.6e}")
        print(f"  Mean |delta|: {np.mean(d_ass_abs):.6e}")
        print(f"  Median |delta|: {np.median(d_ass_abs):.6e}")
        print(f"  p95 |delta|: {np.percentile(d_ass_abs, 95):.6e}")
        
        print("\n--- No-Assimilation-Day Stratification ---")
        mask_noass = full_freq == 0
        d_noass = full_delta[mask_noass]
        d_noass_abs = full_abs[mask_noass]
        print("Observation Frequency == 0:")
        print(f"  Sample count: {len(d_noass)}")
        print(f"  Mean signed delta: {np.mean(d_noass):.6e}")
        print(f"  Median signed delta: {np.median(d_noass):.6e}")
        print(f"  Mean |delta|: {np.mean(d_noass_abs):.6e}")
        print(f"  Median |delta|: {np.median(d_noass_abs):.6e}")
        print(f"  p95 |delta|: {np.percentile(d_noass_abs, 95):.6e}")
        
        z_noass = np.sum(d_noass == 0)
        nz_noass = np.sum(d_noass != 0)
        print(f"  Exact delta == 0: {z_noass}")
        print(f"  Exact delta != 0: {nz_noass}")
        
        for th in [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3]:
            c1 = np.sum(d_noass_abs > th)
            print(f"  |delta| > {th}: {c1} / {len(d_noass)} ({c1/len(d_noass):.4%})")

        print("\n--- Persistence During No-Assimilation Support ---")
        # daily_signed_increment == 0 AND |delta| > th
        # We need to map back to original indices. Or just use boolean masks.
        mask_noass_zero_inc = (full_freq == 0) & (full_inc == 0)
        total_noass = np.sum(full_freq == 0)
        if total_noass > 0:
            for th in [1e-8, 1e-6, 1e-4]:
                c = np.sum(mask_noass_zero_inc & (full_abs > th))
                print(f"  daily_signed_increment == 0 AND |delta_baseflow| > {th}: {c} / {total_noass} ({c/total_noass:.4%})")

        print("\n--- 2019 SMAP Outage ---")
        df = pd.DataFrame(temporal_stats)
        
        time_mask_outage = pd.Series(all_valid_dates).between('2019-06-19', '2019-07-23').values
        
        freq_out = full_freq[time_mask_outage]
        print(f"Assertion: observation_frequency == 0 for all outage days -> {np.all(freq_out == 0)}")
        
        d_out = full_delta[time_mask_outage]
        d_out_abs = full_abs[time_mask_outage]
        
        print(f"  Finite count: {len(d_out)}")
        print(f"  Mean signed delta: {np.mean(d_out):.6e}")
        print(f"  Median signed delta: {np.median(d_out):.6e}")
        print(f"  Mean |delta|: {np.mean(d_out_abs):.6e}")
        print(f"  Median |delta|: {np.median(d_out_abs):.6e}")
        print(f"  p95 |delta|: {np.percentile(d_out_abs, 95):.6e}")
            
        print("Fractions:")
        for th in [1e-8, 1e-6, 1e-4, 1e-3]:
            c1 = np.sum(d_out_abs > th)
            print(f"  |delta| > {th}: {c1} / {len(d_out)} ({c1/len(d_out):.4%})")

        stride = 10
        print("\n--- Relation to Delta RZSM ---")
        print("ALL VALID DAYS:")
        p_sgn = pearsonr(full_delta[::stride], full_rzsm[::stride])[0]
        s_sgn = spearmanr(full_delta[::stride], full_rzsm[::stride])[0]
        p_abs = pearsonr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0]
        s_abs = spearmanr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        if use_active:
            print("NON-ZERO SUPPORT DAYS:")
            d_act = full_delta[mask_nonzero]
            r_act = full_rzsm[mask_nonzero]
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
        
        print("OBS_FREQ == 1:")
        e_1 = full_et[mask_ass]
        p_sgn = pearsonr(d_1[::stride], e_1[::stride])[0]
        s_sgn = spearmanr(d_1[::stride], e_1[::stride])[0]
        p_abs = pearsonr(np.abs(d_1[::stride]), np.abs(e_1[::stride]))[0]
        s_abs = spearmanr(np.abs(d_1[::stride]), np.abs(e_1[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("OBS_FREQ == 0:")
        e_0 = full_et[mask_noass]
        p_sgn = pearsonr(d_0[::stride], e_0[::stride])[0]
        s_sgn = spearmanr(d_0[::stride], e_0[::stride])[0]
        p_abs = pearsonr(np.abs(d_0[::stride]), np.abs(e_0[::stride]))[0]
        s_abs = spearmanr(np.abs(d_0[::stride]), np.abs(e_0[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")

        print("\n--- Relation to Delta Surface Runoff ---")
        print("ALL VALID DAYS:")
        p_sgn = pearsonr(full_delta[::stride], full_runoff[::stride])[0]
        s_sgn = spearmanr(full_delta[::stride], full_runoff[::stride])[0]
        p_abs = pearsonr(full_abs[::stride], np.abs(full_runoff[::stride]))[0]
        s_abs = spearmanr(full_abs[::stride], np.abs(full_runoff[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("OBS_FREQ == 1:")
        ro_1 = full_runoff[mask_ass]
        p_sgn = pearsonr(d_1[::stride], ro_1[::stride])[0]
        s_sgn = spearmanr(d_1[::stride], ro_1[::stride])[0]
        p_abs = pearsonr(np.abs(d_1[::stride]), np.abs(ro_1[::stride]))[0]
        s_abs = spearmanr(np.abs(d_1[::stride]), np.abs(ro_1[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("OBS_FREQ == 0:")
        ro_0 = full_runoff[mask_noass]
        p_sgn = pearsonr(d_0[::stride], ro_0[::stride])[0]
        s_sgn = spearmanr(d_0[::stride], ro_0[::stride])[0]
        p_abs = pearsonr(np.abs(d_0[::stride]), np.abs(ro_0[::stride]))[0]
        s_abs = spearmanr(np.abs(d_0[::stride]), np.abs(ro_0[::stride]))[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")

        print("\n--- Relation to Surface Increment (obs_freq == 1) ---")
        inc_1 = full_inc[mask_ass]
        inca_1 = full_inc_abs[mask_ass]
        p_sgn = pearsonr(d_1[::stride], inc_1[::stride])[0]
        s_sgn = spearmanr(d_1[::stride], inc_1[::stride])[0]
        p_abs = pearsonr(np.abs(d_1[::stride]), inca_1[::stride])[0]
        s_abs = spearmanr(np.abs(d_1[::stride]), inca_1[::stride])[0]
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        print("\n--- Temporal Persistence Diagnostic ---")
        ts_mean = df['mean'].values
        ts_mean_abs = df['mean_abs'].values
        
        def autocorr(x, lag):
            return np.corrcoef(x[:-lag], x[lag:])[0, 1]
            
        print("Daily Spatial Mean Autocorrelation:")
        for lag in [1, 3, 7]:
            print(f"  Lag {lag} days: {autocorr(ts_mean, lag):.4f}")
        print("Daily Spatial Mean |delta| Autocorrelation:")
        for lag in [1, 3, 7]:
            print(f"  Lag {lag} days: {autocorr(ts_mean_abs, lag):.4f}")

        print("\n--- Seasonal QC ---")
        print("No zero/non-zero support split is needed as source baseflow is essentially 100% positive.")
        full_months = pd.DatetimeIndex(all_valid_dates).month
        for s, m_list in [('DJF', [12, 1, 2]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8]), ('SON', [9, 10, 11])]:
            s_mask = np.isin(full_months, m_list)
            s_vals = full_delta[s_mask]
            s_nz_mask = mask_nonzero[s_mask]
            print(f"{s}:")
            print(f"  Sample count: {len(s_vals)}")
            print(f"  Mean signed delta: {np.mean(s_vals):.6e}")
            print(f"  Median signed delta: {np.median(s_vals):.6e}")
            print(f"  Mean |delta|: {np.mean(np.abs(s_vals)):.6e}")
            print(f"  Median |delta|: {np.median(np.abs(s_vals)):.6e}")

        # Temporal plotting
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['mean'], label='Mean')
        plt.plot(df['date'], df['mean_abs'], label='Mean Abs')
        plt.legend()
        plt.title(f'Delta Baseflow Temporal - {exp}')
        plt.savefig(os.path.join(out_dir, f'temporal_{exp}.png'))
        plt.close()
        
        # Relation plots (using subsample)
        plt.figure(figsize=(8, 6))
        plt.scatter(full_rzsm[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta RZSM')
        plt.ylabel('Delta Baseflow')
        plt.title(f'Delta RZSM vs Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_rzsm_vs_delta_baseflow_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(full_et[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta ET')
        plt.ylabel('Delta Baseflow')
        plt.title(f'Delta ET vs Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_et_vs_delta_baseflow_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(full_runoff[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta Surface Runoff')
        plt.ylabel('Delta Baseflow')
        plt.title(f'Delta Surface Runoff vs Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_surface_runoff_vs_delta_baseflow_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(inc_1[::stride], d_1[::stride], alpha=0.1, s=1)
        plt.xlabel('Increment')
        plt.ylabel('Delta Baseflow')
        plt.title(f'Increment vs Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'increment_vs_delta_baseflow_{exp}.png'))
        plt.close()

        # Spatial diagnostics
        ds_all = []
        for year in years:
            ds_all.append(xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_baseflow/delta_baseflow_{year}.nc"))
            
        ds_concat = xr.concat(ds_all, dim='time')
        vals_concat = ds_concat['delta_baseflow'].values
        
        spatial_mean = np.nanmean(vals_concat, axis=0)
        spatial_mean_abs = np.nanmean(np.abs(vals_concat), axis=0)
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean, origin='lower', cmap='BrBG')
        plt.colorbar(im, label='Mean Signed Delta Baseflow')
        plt.title(f'Mean Signed Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_signed_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta Baseflow')
        plt.title(f'Mean Absolute Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_abs_{exp}.png'))
        plt.close()
        
        abs_vals = np.abs(vals_concat)
        spatial_p95_abs = np.nanpercentile(abs_vals, 95, axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_p95_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='p95 Absolute Delta Baseflow')
        plt.title(f'p95 Absolute Delta Baseflow - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_p95_abs_{exp}.png'))
        plt.close()
        
        pos_frac = np.nansum(vals_concat > 0, axis=0) / valid_days_count
        plt.figure(figsize=(10, 8))
        im = plt.imshow(pos_frac, origin='lower', cmap='viridis', vmin=0, vmax=1)
        plt.colorbar(im, label='Positive-day Fraction')
        plt.title(f'Positive-Day Fraction - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_positive_fraction_{exp}.png'))
        plt.close()
        
        # Row profile diagnostic
        row_mean = np.nanmean(spatial_mean, axis=1) # Mean over lon for each row
        row_mean_abs = np.nanmean(spatial_mean_abs, axis=1)
        
        plt.figure(figsize=(8, 10))
        lats = ds_concat.lat.values
        plt.plot(row_mean, lats, label='Mean Signed')
        plt.plot(row_mean_abs, lats, label='Mean Abs')
        plt.legend()
        plt.title(f'Row-wise Delta Baseflow Profile - {exp}')
        plt.xlabel('Delta Baseflow')
        plt.ylabel('Latitude')
        plt.savefig(os.path.join(out_dir, f'row_profile_{exp}.png'))
        plt.close()
        
        even_rows = row_mean[::2]
        odd_rows = row_mean[1::2]
        print("\n--- Row-Wise Structure Diagnostic ---")
        print("Method: first compute each latitude-row mean over valid longitude/time, then average row means equally.")
        print(f"Even rows mean signed delta: {np.nanmean(even_rows):.6e}")
        print(f"Odd rows mean signed delta: {np.nanmean(odd_rows):.6e}")
        
        even_abs = row_mean_abs[::2]
        odd_abs = row_mean_abs[1::2]
        print(f"Even rows mean absolute delta: {np.nanmean(even_abs):.6e}")
        print(f"Odd rows mean absolute delta: {np.nanmean(odd_abs):.6e}")
        
        print(f"Odd-even absolute difference: {np.nanmean(odd_abs) - np.nanmean(even_abs):.6e}")
        print(f"Odd-even relative difference: {(np.nanmean(odd_abs) - np.nanmean(even_abs)) / np.nanmean(even_abs):.4%}")
        
        # Representative maps
        df['mean_abs_rank'] = df['mean_abs'].rank(pct=True)
        
        # 1. High response date
        high_idx = df['mean_abs'].idxmax()
        high_date = df.loc[high_idx, 'date'].strftime('%Y-%m-%d')
        
        # 2. Assimilation-active example
        ass_idx = df['frac_ass'].idxmax()
        ass_date = df.loc[ass_idx, 'date'].strftime('%Y-%m-%d')
            
        # 3. No-assimilation example (outage)
        outage_date = '2019-07-01'
        idx_outage = df[df['date'] == pd.Timestamp(outage_date)].index
        frac_ass_outage = df.loc[idx_outage[0], 'frac_ass'] if len(idx_outage) > 0 else 1.0
        assert frac_ass_outage == 0.0, "Outage date has observation frequency > 0"
        
        rep_dates = {
            ass_date: 'Assimilation-active baseflow example',
            high_date: 'High mean |delta_baseflow|',
            outage_date: 'No-assimilation baseflow-response example (outage)'
        }
        
        print("\n--- Representative Date Table ---")
        for t_val, category in rep_dates.items():
            idx = df[df['date'] == pd.Timestamp(t_val)].index[0]
            stat_row = df.loc[idx]
            print(f"EXP: {exp} | CAT: {category} | DATE: {t_val} | "
                  f"mean |delta_baseflow|: {stat_row['mean_abs']:.6e} | "
                  f"percentile rank: {stat_row['mean_abs_rank']:.4f} | "
                  f"count of valid land with obs_freq == 1: {int(stat_row['frac_ass'] * num_valid)} | "
                  f"fraction of valid land with obs_freq == 1: {stat_row['frac_ass']:.4f}")
            
            try:
                ds_rep = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_baseflow/delta_baseflow_{t_val[:4]}.nc").sel(time=t_val)
                plt.figure(figsize=(10, 8))
                im = plt.imshow(ds_rep['delta_baseflow'].values, origin='lower', cmap='BrBG')
                plt.colorbar(im, extend='both', label='Delta Baseflow')
                plt.title(f'Representative Daily Delta Baseflow - {exp} ({t_val})')
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
            plt.colorbar(im, label='Mean Absolute Delta Baseflow (Outage)')
            plt.title(f'Outage Persistence Mean Absolute - {exp}')
            plt.savefig(os.path.join(out_dir, f'outage_persistence_{exp}.png'))
            plt.close()

    plt.figure(figsize=(12, 6))
    plt.hist(dist_data['da_cdf'], bins=100, alpha=0.5, label='DA-CDF', density=True, color='blue')
    plt.hist(dist_data['da_nocdf'], bins=100, alpha=0.5, label='DA-NoCDF', density=True, color='orange')
    plt.legend()
    plt.yscale('log')
    plt.xlabel('Signed Delta Baseflow (mm/day)')
    plt.ylabel('Density (log scale)')
    plt.title('Full-Period Delta Baseflow Distribution (Valid Land, Log Scale)')
    plt.savefig(os.path.join(out_dir, 'delta_baseflow_distribution.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    parser.add_argument('--out_dir', type=str, default='reports/qc/delta_baseflow')
    args = parser.parse_args()
    
    qc_and_plot(args.base_dir, os.path.join(args.base_dir, args.out_dir))
    
    print("\n--- QC FIGURE FILENAMES ---")
    out_dir = os.path.join(args.base_dir, args.out_dir)
    if os.path.exists(out_dir):
        files = sorted(os.listdir(out_dir))
        for f in files:
            print(os.path.join(args.out_dir, f))
