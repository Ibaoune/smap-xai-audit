#!/usr/bin/env python3
"""
QC and Plot Delta RZSM

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Performs comprehensive QC and plotting for delta_rzsm.
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
    
    # We will aggregate things for full-period stats
    for exp in exps:
        print(f"\n{'='*50}\nExperiment: {exp}\n{'='*50}")
        
        all_delta = []
        all_obs_freq = []
        all_inc_signed = []
        all_inc_abs = []
        
        all_reconstruct_diffs = []
        
        temporal_stats = []
        
        spatial_sum_delta = 0
        spatial_sum_abs = 0
        spatial_sum_pos = 0
        spatial_sum_neg = 0
        valid_days_count = 0
        
        all_dates = []
        
        # Load canonical land mask from 2016
        ds_ref = xr.open_dataset(f"{base_dir}/data/processed/daily_model/opl/rzsm/rzsm_2016.nc")
        land_mask = ~np.isnan(ds_ref['rzsm'].values[0])
        num_valid = np.sum(land_mask)
        
        for year in years:
            print(f"Loading {year}...")
            
            # Load delta_rzsm
            ds_delta = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_{year}.nc")
            delta_rzsm = ds_delta['delta_rzsm'].values
            
            # Direct Reconstruction QC
            ds_opl = xr.open_dataset(f"{base_dir}/data/processed/daily_model/opl/rzsm/rzsm_{year}.nc")
            ds_da = xr.open_dataset(f"{base_dir}/data/processed/daily_model/{exp}/rzsm/rzsm_{year}.nc")
            rzsm_opl = ds_opl['rzsm'].values
            rzsm_da = ds_da['rzsm'].values
            
            reconstructed = (rzsm_da - rzsm_opl).astype(np.float32)
            mask_opl = np.isnan(rzsm_opl)
            reconstructed[mask_opl] = np.nan
            
            diff = np.abs(reconstructed - delta_rzsm)
            diff_finite = diff[~np.isnan(diff)]
            all_reconstruct_diffs.append(diff_finite)
            
            # Support Conservation
            exp_finite = np.isfinite(rzsm_da) & np.isfinite(rzsm_opl)
            act_finite = np.isfinite(delta_rzsm)
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
            
            # Align time just in case (should be identical)
            time_vals = pd.to_datetime(ds_delta.time.values)
            
            for t_idx, t_date in enumerate(time_vals):
                d_val = delta_rzsm[t_idx][land_mask]
                f_val = freq[t_idx][land_mask]
                i_val = inc[t_idx][land_mask]
                ia_val = inc_abs[t_idx][land_mask]
                
                # Append to full list (only where finite)
                valid_idx = np.isfinite(d_val)
                d_valid = d_val[valid_idx]
                f_valid = f_val[valid_idx]
                i_valid = i_val[valid_idx]
                ia_valid = ia_val[valid_idx]
                
                all_delta.append(d_valid)
                all_obs_freq.append(f_valid)
                all_inc_signed.append(i_valid)
                all_inc_abs.append(ia_valid)
                
                all_dates.append(t_date)
                
                # Temporal diagnostics
                if len(d_valid) > 0:
                    d_abs = np.abs(d_valid)
                    temporal_stats.append({
                        'date': t_date,
                        'mean': np.mean(d_valid),
                        'median': np.median(d_valid),
                        'mean_abs': np.mean(d_abs),
                        'p95_abs': np.percentile(d_abs, 95),
                        'frac_pos': np.sum(d_valid > 0) / len(d_valid),
                        'frac_neg': np.sum(d_valid < 0) / len(d_valid)
                    })
            
            # Spatial running sum
            spatial_sum_delta += np.nansum(delta_rzsm, axis=0)
            spatial_sum_abs += np.nansum(np.abs(delta_rzsm), axis=0)
            spatial_sum_pos += np.nansum(delta_rzsm > 0, axis=0)
            spatial_sum_neg += np.nansum(delta_rzsm < 0, axis=0)
            valid_days_count += np.sum(~np.isnan(delta_rzsm), axis=0)
            
        print("\n--- All-Day Support Check ---")
        total_canonical_days = 1827
        expected_pixel_days = num_valid * total_canonical_days
        actual_finite = len(all_delta)
        # Using the length of concatenated arrays since we collected only finite delta_rzsm
        # But wait, full_delta length is the number of finite values.
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
        print(f"Finite delta_rzsm pixel-days: {len(full_delta)}")
        print(f"Support mismatch count: {expected_pixel_days - len(full_delta)}")
        
        full_freq = np.concatenate(all_obs_freq)
        full_inc = np.concatenate(all_inc_signed)
        full_inc_abs = np.concatenate(all_inc_abs)
        
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
        print(f"delta_rzsm < 0: {n_neg} ({n_neg/n_tot:.2%})")
        print(f"delta_rzsm == 0: {n_zero} ({n_zero/n_tot:.4%})")
        print(f"delta_rzsm > 0: {n_pos} ({n_pos/n_tot:.2%})")
        
        print("\n--- Absolute Response QC ---")
        print(f"Mean: {np.mean(full_abs):.6f}")
        print(f"Median: {np.median(full_abs):.6f}")
        print(f"p75: {np.percentile(full_abs, 75):.6f}")
        print(f"p90: {np.percentile(full_abs, 90):.6f}")
        print(f"p95: {np.percentile(full_abs, 95):.6f}")
        print(f"p99: {np.percentile(full_abs, 99):.6f}")
        print(f"Max: {np.max(full_abs):.6f}")
        
        print("\n--- Conditional on Assimilation Support ---")
        mask_ass = full_freq == 1
        mask_noass = full_freq == 0
        
        for name, m in [("Assimilation == 1", mask_ass), ("Assimilation == 0", mask_noass)]:
            d_sub = full_delta[m]
            d_abs_sub = full_abs[m]
            print(f"{name}:")
            print(f"  Sample count: {len(d_sub)}")
            print(f"  Mean delta_rzsm: {np.mean(d_sub):.6f}")
            print(f"  Median delta_rzsm: {np.median(d_sub):.6f}")
            print(f"  Mean |delta_rzsm|: {np.mean(d_abs_sub):.6f}")
            print(f"  Median |delta_rzsm|: {np.median(d_abs_sub):.6f}")
            print(f"  p95 |delta_rzsm|: {np.percentile(d_abs_sub, 95):.6f}")
            
        print("\n--- Persistence on No-Assimilation Days ---")
        d_noass = full_delta[mask_noass]
        d_abs_noass = full_abs[mask_noass]
        n_noass = len(d_noass)
        
        counts = {
            "== 0": np.sum(d_noass == 0),
            "!= 0": np.sum(d_noass != 0),
            "|delta| > 1e-6": np.sum(d_abs_noass > 1e-6),
            "|delta| > 1e-5": np.sum(d_abs_noass > 1e-5),
            "|delta| > 1e-4": np.sum(d_abs_noass > 1e-4),
            "|delta| > 1e-3": np.sum(d_abs_noass > 1e-3)
        }
        for k, c in counts.items():
            print(f"Count {k}: {c} ({c/n_noass:.4%})")
        
        print("\n--- Relation on No-Assimilation Days ---")
        inc_noass = full_inc[mask_noass]
        match_condition = (inc_noass == 0) & (d_abs_noass > 1e-6)
        match_count = np.sum(match_condition)
        denom_count = len(d_noass)
        print(f"Count of inc==0 AND |delta| > 1e-6: {match_count}")
        print(f"Denominator (no-assimilation pixel-days): {denom_count}")
        print(f"Percentage: {match_count/denom_count:.2%}")
        
        print("\n--- Relation to Daily SSM Increment (Assimilation == 1) ---")
        d_ass = full_delta[mask_ass]
        d_abs_ass = full_abs[mask_ass]
        inc_ass = full_inc[mask_ass]
        inc_abs_ass = full_inc_abs[mask_ass]
        
        p_sgn, _ = pearsonr(inc_ass, d_ass)
        s_sgn, _ = spearmanr(inc_ass, d_ass)
        p_abs, _ = pearsonr(inc_abs_ass, d_abs_ass)
        s_abs, _ = spearmanr(inc_abs_ass, d_abs_ass)
        
        print("Signed Increment vs Delta RZSM:")
        print(f"  Pearson: {p_sgn:.4f}")
        print(f"  Spearman: {s_sgn:.4f}")
        print("Absolute Increment vs |Delta RZSM|:")
        print(f"  Pearson: {p_abs:.4f}")
        print(f"  Spearman: {s_abs:.4f}")
        
        # 2019 SMAP Outage
        print("\n--- 2019 SMAP Outage ---")
        # Find dates between 2019-06-19 and 2019-07-23
        df = pd.DataFrame(temporal_stats)
        outage_mask = (df['date'] >= '2019-06-19') & (df['date'] <= '2019-07-23')
        
        # Reconstruct exactly for the outage
        ds_outage = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_2019.nc").sel(time=slice('2019-06-19', '2019-07-23'))
        outage_vals = ds_outage['delta_rzsm'].values
        outage_valid = outage_vals[~np.isnan(outage_vals)]
        outage_abs = np.abs(outage_valid)
        
        print(f"Finite count: {len(outage_valid)}")
        print(f"Mean delta: {np.mean(outage_valid):.6f}")
        print(f"Median delta: {np.median(outage_valid):.6f}")
        print(f"Mean |delta|: {np.mean(outage_abs):.6f}")
        print(f"Median |delta|: {np.median(outage_abs):.6f}")
        print(f"Fraction > 1e-6: {np.sum(outage_abs > 1e-6)/len(outage_valid):.2%}")
        print(f"Fraction > 1e-4: {np.sum(outage_abs > 1e-4)/len(outage_valid):.2%}")
        
        # Temporal plotting
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['mean'], label='Mean')
        plt.plot(df['date'], df['mean_abs'], label='Mean Abs')
        plt.legend()
        plt.title(f'Delta RZSM Temporal - {exp}')
        plt.savefig(os.path.join(out_dir, f'temporal_{exp}.png'))
        plt.close()
        
        # Hexbins
        plt.figure(figsize=(8, 6))
        plt.hexbin(inc_ass, d_ass, gridsize=50, cmap='viridis', mincnt=1)
        plt.colorbar(label='Count')
        plt.xlabel('Daily Signed Increment')
        plt.ylabel('Delta RZSM')
        plt.title(f'Increment vs Delta RZSM - {exp}')
        plt.savefig(os.path.join(out_dir, f'hexbin_signed_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.hexbin(inc_abs_ass, d_abs_ass, gridsize=50, cmap='viridis', mincnt=1)
        plt.colorbar(label='Count')
        plt.xlabel('Daily Absolute Increment')
        plt.ylabel('|Delta RZSM|')
        plt.title(f'|Increment| vs |Delta RZSM| - {exp}')
        plt.savefig(os.path.join(out_dir, f'hexbin_abs_{exp}.png'))
        plt.close()
        
        print("\n--- Seasonal QC ---")
        months = np.array([t.month for t in time_vals for _ in range(num_valid)])
        
        # This approach might be slow, so let's just use the fact that we have the full array 
        # and we can iterate over the time_vals.
        
        # We need an array of months that aligns with full_delta
        full_months = np.concatenate([np.full(len(d_valid), t_date.month) for t_date, d_valid in zip(all_dates, all_delta)])
        
        for s, m_list in [('DJF', [12, 1, 2]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8]), ('SON', [9, 10, 11])]:
            s_mask = np.isin(full_months, m_list)
            s_vals = full_delta[s_mask]
            print(f"{s}: Mean={np.mean(s_vals):.6f}, Median={np.median(s_vals):.6f}, Mean|ABS|={np.mean(np.abs(s_vals)):.6f}")

        # Spatial diagnostics for Row-wise assessment
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_sum_delta / valid_days_count, origin='lower', cmap='BrBG')
        plt.colorbar(im, label='Mean Signed Delta RZSM')
        plt.title(f'Mean Signed Delta RZSM - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_signed_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_sum_abs / valid_days_count, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta RZSM')
        plt.title(f'Mean Absolute Delta RZSM - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_abs_{exp}.png'))
        plt.close()

        # p95 absolute map
        # Load all years for exact p95 spatial and exact fractions
        ds_all = []
        for year in years:
            ds_all.append(xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_{year}.nc"))
        ds_concat = xr.concat(ds_all, dim='time')
        vals_concat = ds_concat['delta_rzsm'].values
        
        abs_vals = np.abs(vals_concat)
        spatial_p95_abs = np.nanpercentile(abs_vals, 95, axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_p95_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='p95 Absolute Delta RZSM')
        plt.title(f'p95 Absolute Delta RZSM - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_p95_abs_{exp}.png'))
        plt.close()
        
        # Exact fractions check
        spatial_median = np.nanmedian(vals_concat, axis=0)
        pos_frac = np.nansum(vals_concat > 0, axis=0) / valid_days_count
        neg_frac = np.nansum(vals_concat < 0, axis=0) / valid_days_count
        zero_frac = np.nansum(vals_concat == 0, axis=0) / valid_days_count
        
        sum_frac = pos_frac + neg_frac + zero_frac
        valid_mask = valid_days_count > 0
        all_one = np.allclose(sum_frac[valid_mask], 1.0)
        print(f"Spatial positive_fraction + negative_fraction + exact_zero_fraction == 1: {all_one}")
        
        # Positive-day fraction map
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_sum_pos / valid_days_count, origin='lower', cmap='viridis', vmin=0, vmax=1)
        plt.colorbar(im, label='Positive-day Fraction')
        plt.title(f'Positive-Day Fraction - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_positive_fraction_{exp}.png'))
        plt.close()
        
        # 2019 outage persistence map
        ds_outage = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_2019.nc").sel(time=slice('2019-06-19', '2019-07-23'))
        outage_mean_abs = np.nanmean(np.abs(ds_outage['delta_rzsm'].values), axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(outage_mean_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta RZSM (Outage)')
        plt.title(f'Outage Persistence Mean Absolute - {exp}')
        plt.savefig(os.path.join(out_dir, f'outage_persistence_{exp}.png'))
        plt.close()
        
        # Representative daily maps
        # 2016-01-10: Assimilation-active example
        # 2016-05-15: High-|delta_rzsm| response example
        # 2019-07-01: No-assimilation / persistence example (outage)
        rep_dates = {
            '2016-01-10': 'Assimilation-active example',
            '2016-05-15': 'High-|delta_rzsm| response example',
            '2019-07-01': 'No-assimilation / persistence example (outage)'
        }
        for t_val, category in rep_dates.items():
            print(f"Representative map for {exp} on {t_val} (Category: {category})")
            try:
                ds_rep = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_rzsm/delta_rzsm_{t_val[:4]}.nc").sel(time=t_val)
                plt.figure(figsize=(10, 8))
                im = plt.imshow(ds_rep['delta_rzsm'].values, origin='lower', cmap='BrBG', vmin=-0.05, vmax=0.05)
                plt.colorbar(im, extend='both', label='Delta RZSM')
                plt.title(f'Representative Daily Delta RZSM - {exp} ({t_val})')
                plt.savefig(os.path.join(out_dir, f'representative_{t_val}_{exp}.png'))
                plt.close()
            except Exception as e:
                print(f"Skipping map for {t_val}: {e}")

    # After looping both exps, plot distribution
    plt.figure(figsize=(12, 6))
    plt.hist(dist_data['da_cdf'], bins=100, alpha=0.5, label='DA-CDF', density=True, color='blue', range=(-0.25, 0.25))
    plt.hist(dist_data['da_nocdf'], bins=100, alpha=0.5, label='DA-NoCDF', density=True, color='orange', range=(-0.25, 0.25))
    plt.legend()
    plt.xlabel('Signed Delta RZSM (m3 m-3)')
    plt.ylabel('Density')
    plt.title('Full-Period Delta RZSM Distribution (Valid Land)')
    plt.savefig(os.path.join(out_dir, 'delta_rzsm_distribution.png'))
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    parser.add_argument('--out_dir', type=str, default='reports/qc/delta_rzsm')
    args = parser.parse_args()
    
    qc_and_plot(args.base_dir, os.path.join(args.base_dir, args.out_dir))
    
    print("\n--- QC FIGURE FILENAMES ---")
    out_dir = os.path.join(args.base_dir, args.out_dir)
    if os.path.exists(out_dir):
        files = sorted(os.listdir(out_dir))
        for f in files:
            print(os.path.join(args.out_dir, f))
