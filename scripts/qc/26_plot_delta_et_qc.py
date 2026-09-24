#!/usr/bin/env python3
"""
QC and Plot Delta ET

Author
------
M. El Aabaribaoune (@um6p)

Description
-----------
Performs comprehensive QC and plotting for delta_et.
Includes row-wise numerical pattern analysis and comparisons with delta_rzsm.
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
        all_delta_rzsm = []
        
        all_reconstruct_diffs = []
        
        temporal_stats = []
        
        spatial_sum_delta = 0
        spatial_sum_abs = 0
        spatial_sum_pos = 0
        spatial_sum_neg = 0
        valid_days_count = 0
        
        all_dates = []
        
        # Load canonical land mask from 2016
        ds_ref = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_2016.nc")
        land_mask = ~np.isnan(ds_ref['et'].values[0])
        num_valid = np.sum(land_mask)
        
        for year in years:
            print(f"Loading {year}...")
            
            # Load delta_et
            ds_delta = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_et/delta_et_{year}.nc")
            delta_et = ds_delta['delta_et'].values
            
            # Direct Reconstruction QC
            ds_opl = xr.open_dataset(f"{base_dir}/data/interim/noahmp/opl/et/et_{year}.nc")
            ds_da = xr.open_dataset(f"{base_dir}/data/interim/noahmp/{exp}/et/et_{year}.nc")
            et_opl = ds_opl['et'].values
            et_da = ds_da['et'].values
            
            reconstructed = (et_da - et_opl).astype(np.float32)
            mask_opl = np.isnan(et_opl)
            reconstructed[mask_opl] = np.nan
            
            diff = np.abs(reconstructed - delta_et)
            diff_finite = diff[~np.isnan(diff)]
            all_reconstruct_diffs.append(diff_finite)
            
            # Support Conservation
            exp_finite = np.isfinite(et_da) & np.isfinite(et_opl)
            act_finite = np.isfinite(delta_et)
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
            
            time_vals = pd.to_datetime(ds_delta.time.values)
            
            for t_idx, t_date in enumerate(time_vals):
                d_val = delta_et[t_idx][land_mask]
                f_val = freq[t_idx][land_mask]
                i_val = inc[t_idx][land_mask]
                ia_val = inc_abs[t_idx][land_mask]
                rzsm_val = drzsm[t_idx][land_mask]
                
                # Align on finite delta_et
                valid_idx = np.isfinite(d_val)
                d_valid = d_val[valid_idx]
                f_valid = f_val[valid_idx]
                i_valid = i_val[valid_idx]
                ia_valid = ia_val[valid_idx]
                rzsm_valid = rzsm_val[valid_idx]
                
                all_delta.append(d_valid)
                all_obs_freq.append(f_valid)
                all_inc_signed.append(i_valid)
                all_inc_abs.append(ia_valid)
                all_delta_rzsm.append(rzsm_valid)
                
                all_dates.append(t_date)
                
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
            
            spatial_sum_delta += np.nansum(delta_et, axis=0)
            spatial_sum_abs += np.nansum(np.abs(delta_et), axis=0)
            spatial_sum_pos += np.nansum(delta_et > 0, axis=0)
            spatial_sum_neg += np.nansum(delta_et < 0, axis=0)
            valid_days_count += np.sum(~np.isnan(delta_et), axis=0)
            
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
        print(f"Finite delta_et pixel-days: {len(full_delta)}")
        print(f"Support mismatch count: {expected_pixel_days - len(full_delta)}")
        
        full_freq = np.concatenate(all_obs_freq)
        full_inc = np.concatenate(all_inc_signed)
        full_inc_abs = np.concatenate(all_inc_abs)
        full_rzsm = np.concatenate(all_delta_rzsm)
        
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
        print(f"delta_et < 0: {n_neg} ({n_neg/n_tot:.2%})")
        print(f"delta_et == 0: {n_zero} ({n_zero/n_tot:.4%})")
        print(f"delta_et > 0: {n_pos} ({n_pos/n_tot:.2%})")
        
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
            print(f"  Mean signed delta_et: {np.mean(d_sub):.6f}")
            print(f"  Median signed delta_et: {np.median(d_sub):.6f}")
            print(f"  Mean |delta_et|: {np.mean(d_abs_sub):.6f}")
            print(f"  Median |delta_et|: {np.median(d_abs_sub):.6f}")
            print(f"  p95 |delta_et|: {np.percentile(d_abs_sub, 95):.6f}")
            
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
            "|delta| > 1e-3": np.sum(d_abs_noass > 1e-3),
            "|delta| > 1e-2": np.sum(d_abs_noass > 1e-2)
        }
        for k, c in counts.items():
            print(f"Count {k}: {c} ({c/n_noass:.4%})")
            
        print("\n--- Relation to Delta RZSM ---")
        # Subsample for correlation if it's too large to compute pearsonr quickly (though scipy can handle 29M usually)
        # We will subsample every 10th element to ensure memory/speed
        stride = 10
        print(f"Correlation using subsampling stride={stride}")
        
        p_sgn, s_sgn = pearsonr(full_delta[::stride], full_rzsm[::stride])[0], spearmanr(full_delta[::stride], full_rzsm[::stride])[0]
        p_abs, s_abs = pearsonr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0], spearmanr(full_abs[::stride], np.abs(full_rzsm[::stride]))[0]
        
        print("ALL DAYS:")
        print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        for name, m in [("Assimilation == 1", mask_ass), ("Assimilation == 0", mask_noass)]:
            p_sgn, s_sgn = pearsonr(full_delta[m][::stride], full_rzsm[m][::stride])[0], spearmanr(full_delta[m][::stride], full_rzsm[m][::stride])[0]
            p_abs, s_abs = pearsonr(full_abs[m][::stride], np.abs(full_rzsm[m][::stride]))[0], spearmanr(full_abs[m][::stride], np.abs(full_rzsm[m][::stride]))[0]
            print(f"{name}:")
            print(f"  Signed Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
            print(f"  Absolute Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
            
        print("\n--- Relation to Daily SSM Increment (Assimilation == 1) ---")
        d_ass = full_delta[mask_ass]
        d_abs_ass = full_abs[mask_ass]
        inc_ass = full_inc[mask_ass]
        inc_abs_ass = full_inc_abs[mask_ass]
        
        p_sgn, _ = pearsonr(inc_ass[::stride], d_ass[::stride])
        s_sgn, _ = spearmanr(inc_ass[::stride], d_ass[::stride])
        p_abs, _ = pearsonr(inc_abs_ass[::stride], d_abs_ass[::stride])
        s_abs, _ = spearmanr(inc_abs_ass[::stride], d_abs_ass[::stride])
        
        print("Signed Increment vs Delta ET:")
        print(f"  Pearson: {p_sgn:.4f}, Spearman: {s_sgn:.4f}")
        print("Absolute Increment vs |Delta ET|:")
        print(f"  Pearson: {p_abs:.4f}, Spearman: {s_abs:.4f}")
        
        # 2019 SMAP Outage
        print("\n--- 2019 SMAP Outage ---")
        df = pd.DataFrame(temporal_stats)
        
        ds_outage = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_et/delta_et_2019.nc").sel(time=slice('2019-06-19', '2019-07-23'))
        outage_vals = ds_outage['delta_et'].values
        outage_valid = outage_vals[~np.isnan(outage_vals)]
        outage_abs = np.abs(outage_valid)
        
        print(f"Finite count: {len(outage_valid)}")
        print(f"Mean delta_et: {np.mean(outage_valid):.6f}")
        print(f"Median delta_et: {np.median(outage_valid):.6f}")
        print(f"Mean |delta_et|: {np.mean(outage_abs):.6f}")
        print(f"Median |delta_et|: {np.median(outage_abs):.6f}")
        print(f"p95 |delta_et|: {np.percentile(outage_abs, 95):.6f}")
        print(f"Fraction |delta_et| > 1e-6: {np.sum(outage_abs > 1e-6)/len(outage_valid):.2%}")
        print(f"Fraction |delta_et| > 1e-4: {np.sum(outage_abs > 1e-4)/len(outage_valid):.2%}")
        print(f"Fraction |delta_et| > 1e-3: {np.sum(outage_abs > 1e-3)/len(outage_valid):.2%}")
        
        # Temporal plotting
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['mean'], label='Mean')
        plt.plot(df['date'], df['mean_abs'], label='Mean Abs')
        plt.legend()
        plt.title(f'Delta ET Temporal - {exp}')
        plt.savefig(os.path.join(out_dir, f'temporal_{exp}.png'))
        plt.close()
        
        # Relation plots (using subsample)
        plt.figure(figsize=(8, 6))
        plt.scatter(full_rzsm[::stride], full_delta[::stride], alpha=0.1, s=1)
        plt.xlabel('Delta RZSM')
        plt.ylabel('Delta ET')
        plt.title(f'Delta RZSM vs Delta ET - {exp}')
        plt.savefig(os.path.join(out_dir, f'delta_rzsm_vs_delta_et_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(8, 6))
        plt.scatter(inc_ass[::stride], d_ass[::stride], alpha=0.1, s=1)
        plt.xlabel('Increment')
        plt.ylabel('Delta ET')
        plt.title(f'Increment vs Delta ET - {exp}')
        plt.savefig(os.path.join(out_dir, f'increment_vs_delta_et_{exp}.png'))
        plt.close()
        
        print("\n--- Seasonal QC ---")
        full_months = np.concatenate([np.full(len(d_valid), t_date.month) for t_date, d_valid in zip(all_dates, all_delta)])
        for s, m_list in [('DJF', [12, 1, 2]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8]), ('SON', [9, 10, 11])]:
            s_mask = np.isin(full_months, m_list)
            s_vals = full_delta[s_mask]
            print(f"{s}: Mean={np.mean(s_vals):.6f}, Median={np.median(s_vals):.6f}, Mean|ABS|={np.mean(np.abs(s_vals)):.6f}, Median|ABS|={np.median(np.abs(s_vals)):.6f}")

        # Spatial diagnostics
        ds_all = []
        for year in years:
            ds_all.append(xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_et/delta_et_{year}.nc"))
        ds_concat = xr.concat(ds_all, dim='time')
        vals_concat = ds_concat['delta_et'].values
        
        spatial_mean = np.nanmean(vals_concat, axis=0)
        spatial_mean_abs = np.nanmean(np.abs(vals_concat), axis=0)
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean, origin='lower', cmap='BrBG')
        plt.colorbar(im, label='Mean Signed Delta ET')
        plt.title(f'Mean Signed Delta ET - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_signed_{exp}.png'))
        plt.close()
        
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_mean_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta ET')
        plt.title(f'Mean Absolute Delta ET - {exp}')
        plt.savefig(os.path.join(out_dir, f'spatial_mean_abs_{exp}.png'))
        plt.close()
        
        abs_vals = np.abs(vals_concat)
        spatial_p95_abs = np.nanpercentile(abs_vals, 95, axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(spatial_p95_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='p95 Absolute Delta ET')
        plt.title(f'p95 Absolute Delta ET - {exp}')
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
        plt.title(f'Row-wise Delta ET Profile - {exp}')
        plt.xlabel('Delta ET')
        plt.ylabel('Latitude')
        plt.savefig(os.path.join(out_dir, f'row_profile_{exp}.png'))
        plt.close()
        
        # Print even/odd row mean statistics
        # Note: rows here refer to latitude index (0 to 120)
        even_rows = row_mean[::2]
        odd_rows = row_mean[1::2]
        print("\n--- Row-Wise Structure Diagnostic ---")
        print(f"Even rows mean signed delta_et: {np.nanmean(even_rows):.6e}")
        print(f"Odd rows mean signed delta_et: {np.nanmean(odd_rows):.6e}")
        
        even_abs = row_mean_abs[::2]
        odd_abs = row_mean_abs[1::2]
        print(f"Even rows mean absolute delta_et: {np.nanmean(even_abs):.6e}")
        print(f"Odd rows mean absolute delta_et: {np.nanmean(odd_abs):.6e}")

        # Outage persistence map
        outage_mean_abs = np.nanmean(np.abs(ds_outage['delta_et'].values), axis=0)
        plt.figure(figsize=(10, 8))
        im = plt.imshow(outage_mean_abs, origin='lower', cmap='viridis')
        plt.colorbar(im, label='Mean Absolute Delta ET (Outage)')
        plt.title(f'Outage Persistence Mean Absolute - {exp}')
        plt.savefig(os.path.join(out_dir, f'outage_persistence_{exp}.png'))
        plt.close()
        
        # Representative maps
        rep_dates = {
            '2016-01-10': 'Assimilation-active example',
            '2016-05-15': 'High-|delta_et| response example',
            '2019-07-01': 'No-assimilation / persistence example (outage)'
        }
        for t_val, category in rep_dates.items():
            print(f"Representative map for {exp} on {t_val} (Category: {category})")
            try:
                ds_rep = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/delta_et/delta_et_{t_val[:4]}.nc").sel(time=t_val)
                plt.figure(figsize=(10, 8))
                im = plt.imshow(ds_rep['delta_et'].values, origin='lower', cmap='BrBG')
                plt.colorbar(im, extend='both', label='Delta ET')
                plt.title(f'Representative Daily Delta ET - {exp} ({t_val})')
                plt.savefig(os.path.join(out_dir, f'representative_{t_val}_{exp}.png'))
                plt.close()
            except Exception as e:
                print(f"Skipping map for {t_val}: {e}")

    plt.figure(figsize=(12, 6))
    plt.hist(dist_data['da_cdf'], bins=100, alpha=0.5, label='DA-CDF', density=True, color='blue', range=(-2, 2))
    plt.hist(dist_data['da_nocdf'], bins=100, alpha=0.5, label='DA-NoCDF', density=True, color='orange', range=(-2, 2))
    plt.legend()
    plt.xlabel('Signed Delta ET (mm/day)')
    plt.ylabel('Density')
    plt.title('Full-Period Delta ET Distribution (Valid Land)')
    plt.savefig(os.path.join(out_dir, 'delta_et_distribution.png'))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    parser.add_argument('--out_dir', type=str, default='reports/qc/delta_et')
    args = parser.parse_args()
    
    qc_and_plot(args.base_dir, os.path.join(args.base_dir, args.out_dir))
    
    print("\n--- QC FIGURE FILENAMES ---")
    out_dir = os.path.join(args.base_dir, args.out_dir)
    if os.path.exists(out_dir):
        files = sorted(os.listdir(out_dir))
        for f in files:
            print(os.path.join(args.out_dir, f))
