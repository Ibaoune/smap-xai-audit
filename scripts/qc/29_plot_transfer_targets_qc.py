#!/usr/bin/env python3
"""
SMAP-XAI Audit: Cross-Target Transfer Plotting Script
Author: M. El Aabaribaoune (@um6p)
"""
__author__ = "M. El Aabaribaoune (@um6p)"

import os
import argparse
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default='/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
    parser.add_argument('--out_dir', type=str, default='reports/qc/transfer_targets')
    args = parser.parse_args()
    
    base_dir = args.base_dir
    out_dir = os.path.join(base_dir, args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    
    exps = ["da_cdf", "da_nocdf"]
    targets = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
    years = [2016, 2017, 2018, 2019, 2020]
    
    # Load canonical mask
    ref_ds = xr.open_dataset(f"{base_dir}/data/processed/transfer/da_cdf/delta_rzsm/delta_rzsm_2016.nc")
    mask = ~np.isnan(ref_ds["delta_rzsm"].values[0])
    lats = ref_ds.lat.values
    lons = ref_ds.lon.values
    
    data = {exp: {target: [] for target in targets} for exp in exps}
    time_all = []
    
    for year in years:
        t_vals = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/da_cdf/observation_frequency/observation_frequency_{year}.nc").time.values
        if year == 2016:
            time_all = list(t_vals)
        else:
            time_all.extend(t_vals)
            
        for exp in exps:
            for target in targets:
                ds = xr.open_dataset(f"{base_dir}/data/processed/transfer/{exp}/{target}/{target}_{year}.nc")
                data[exp][target].append(ds[target].values[:, mask])
                
    time_all = pd.to_datetime(time_all)
    for exp in exps:
        for target in targets:
            data[exp][target] = np.concatenate(data[exp][target], axis=0)
            
    print("Generating Correlation Matrices...")
    stride = 10
    pairs = [('delta_rzsm', 'delta_et'), ('delta_rzsm', 'delta_surface_runoff'), 
             ('delta_rzsm', 'delta_baseflow'), ('delta_et', 'delta_surface_runoff'),
             ('delta_et', 'delta_baseflow'), ('delta_surface_runoff', 'delta_baseflow')]
    
    for exp in exps:
        corr_res = {'p_sgn': np.ones((4,4)), 'sp_sgn': np.ones((4,4)), 'p_abs': np.ones((4,4)), 'sp_abs': np.ones((4,4))}
        for i, t1 in enumerate(targets):
            for j, t2 in enumerate(targets):
                if i < j:
                    s1 = data[exp][t1].flatten()[::stride]
                    s2 = data[exp][t2].flatten()[::stride]
                    
                    corr_res['p_sgn'][i,j] = corr_res['p_sgn'][j,i] = pearsonr(s1, s2)[0]
                    corr_res['sp_sgn'][i,j] = corr_res['sp_sgn'][j,i] = spearmanr(s1, s2)[0]
                    corr_res['p_abs'][i,j] = corr_res['p_abs'][j,i] = pearsonr(np.abs(s1), np.abs(s2))[0]
                    corr_res['sp_abs'][i,j] = corr_res['sp_abs'][j,i] = spearmanr(np.abs(s1), np.abs(s2))[0]
                    
        for name, mat in corr_res.items():
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(mat, cmap='coolwarm', vmin=-1, vmax=1)
            ax.set_xticks(np.arange(len(targets)))
            ax.set_yticks(np.arange(len(targets)))
            ax.set_xticklabels(targets)
            ax.set_yticklabels(targets)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            for i_idx in range(len(targets)):
                for j_idx in range(len(targets)):
                    ax.text(j_idx, i_idx, f"{mat[i_idx, j_idx]:.2f}", ha="center", va="center", color="w" if abs(mat[i_idx, j_idx]) > 0.5 else "k")
            plt.colorbar(im)
            
            title = "Signed Pearson" if name == 'p_sgn' else "Signed Spearman" if name == 'sp_sgn' else "Absolute Pearson" if name == 'p_abs' else "Absolute Spearman"
            plt.title(f"{title} - {exp}")
            plt.tight_layout()
            out_name = title.lower().replace(' ', '_')
            plt.savefig(os.path.join(out_dir, f"{out_name}_{exp}.png"))
            plt.close()

    print("Generating Temporal Persistence Summary...")
    persistence_table = []
    for exp in exps:
        for target in targets:
            vals = data[exp][target]
            ts_mean_abs = np.nanmean(np.abs(vals), axis=1)
            
            def autocorr(x, lag):
                return np.corrcoef(x[:-lag], x[lag:])[0, 1]
                
            persistence_table.append({
                'Experiment': exp,
                'Target': target,
                'abs_lag1': autocorr(ts_mean_abs, 1),
                'abs_lag3': autocorr(ts_mean_abs, 3),
                'abs_lag7': autocorr(ts_mean_abs, 7)
            })
    df_pers = pd.DataFrame(persistence_table)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=df_pers.round(4).values, colLabels=df_pers.columns, loc='center')
    plt.title('Temporal Persistence Summary (Absolute Mean)')
    plt.savefig(os.path.join(out_dir, 'temporal_persistence_summary.png'), bbox_inches='tight')
    plt.close()

    print("Generating Row-wise Structure...")
    for exp in exps:
        fig_sgn, axes_sgn = plt.subplots(2, 2, figsize=(10, 10))
        for i, target in enumerate(targets):
            vals = data[exp][target]
            full_2d = np.full((len(time_all), len(lats), len(lons)), np.nan)
            for t in range(len(time_all)):
                temp = np.full((len(lats), len(lons)), np.nan)
                temp[mask] = vals[t]
                full_2d[t] = temp
                
            row_mean_sgn = np.nanmean(full_2d, axis=(0, 2))
            
            ax_s = axes_sgn.flatten()[i]
            ax_s.plot(row_mean_sgn, lats)
            ax_s.set_title(target)
            
        fig_sgn.suptitle(f"Row-wise Mean Signed Profile - {exp}")
        fig_sgn.tight_layout()
        fig_sgn.savefig(os.path.join(out_dir, f"row_structure_summary_{exp}.png"))
        plt.close(fig_sgn)

    print("Generating Seasonal Summary...")
    full_months = time_all.month
    for exp in exps:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        for i, target in enumerate(targets):
            vals = data[exp][target]
            season_means = []
            for m_list in [[12, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]:
                s_mask = np.isin(full_months, m_list)
                season_means.append(np.mean(np.abs(vals[s_mask])))
            
            norm_means = np.array(season_means) / np.max(season_means)
            axes[i].bar(['DJF', 'MAM', 'JJA', 'SON'], norm_means)
            axes[i].set_title(f"{target} (Visualization-Only Normalization)")
        plt.suptitle(f"Seasonal Mean Absolute - {exp}")
        plt.savefig(os.path.join(out_dir, f"seasonal_normalized_summary_{exp}.png"))
        plt.close()

    print("Generating Outage Summary...")
    time_mask_outage = pd.Series(time_all).between('2019-06-19', '2019-07-23').values
    for exp in exps:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        for i, target in enumerate(targets):
            out_vals = np.abs(data[exp][target][time_mask_outage])
            mean_map = np.nanmean(out_vals, axis=0)
            full_map = np.full((len(lats), len(lons)), np.nan)
            full_map[mask] = mean_map
            im = axes[i].imshow(full_map, origin='lower', cmap='viridis')
            fig.colorbar(im, ax=axes[i])
            axes[i].set_title(target)
            axes[i].axis('off')
        plt.suptitle(f"Outage Mean Absolute - {exp}")
        plt.savefig(os.path.join(out_dir, f"outage_summary_{exp}.png"))
        plt.close()
        
    print("Generating Distribution Scale Summary...")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for i, exp in enumerate(exps):
        for target in targets:
            vals = np.abs(data[exp][target])
            p95 = np.percentile(vals, 95)
            axes[i].bar(target, p95)
        axes[i].set_title(f"p95 Absolute Scale - {exp}")
        axes[i].set_ylabel("Absolute Scale (Native Units)")
    plt.suptitle("Distribution Scale Comparison (Native Units, Not Normalized)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "distribution_scale_summary.png"))
    plt.close()

    print("Generating Extreme Concentration Summaries...")
    fig_d, axes_d = plt.subplots(1, 2, figsize=(12, 5))
    fig_p, axes_p = plt.subplots(1, 2, figsize=(12, 5))
    
    for i, exp in enumerate(exps):
        d_vals = []
        p_vals = []
        for target in targets:
            abs_vals = np.abs(data[exp][target])
            
            # Dates
            daily_sum = np.nansum(abs_vals, axis=1)
            total_sum = np.sum(daily_sum)
            top10_sum = np.sum(np.sort(daily_sum)[-10:])
            d_vals.append(top10_sum / total_sum)
            
            # Pixels
            pixel_sum = np.nansum(abs_vals, axis=0)
            top1_sum = np.sum(np.sort(pixel_sum)[-int(0.01*len(pixel_sum)):])
            p_vals.append(top1_sum / total_sum)
            
        axes_d[i].bar(targets, d_vals)
        axes_d[i].set_title(f"Top 10 Dates % Contribution - {exp}")
        axes_d[i].set_ylim(0, 1)
        
        axes_p[i].bar(targets, p_vals)
        axes_p[i].set_title(f"Top 1% Pixels % Contribution - {exp}")
        axes_p[i].set_ylim(0, 1)
        
    fig_d.tight_layout()
    fig_d.savefig(os.path.join(out_dir, "extreme_date_concentration.png"))
    plt.close(fig_d)
    
    fig_p.tight_layout()
    fig_p.savefig(os.path.join(out_dir, "extreme_pixel_concentration.png"))
    plt.close(fig_p)

    print("Done generating plots.")

if __name__ == "__main__":
    main()
