#!/usr/bin/env python3
"""
SMAP-XAI Audit: Cross-Target Transfer Audit (Text Report)
Author: M. El Aabaribaoune (@um6p)
"""

import os
import sys
import numpy as np
import xarray as xr
import pandas as pd
from scipy.stats import pearsonr, spearmanr

def main():
    base_dir = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
    out_dir = os.path.join(base_dir, "reports/qc/transfer_targets")
    os.makedirs(out_dir, exist_ok=True)
    
    exps = ["da_cdf", "da_nocdf"]
    targets = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
    years = [2016, 2017, 2018, 2019, 2020]
    
    print("="*50)
    print("1. AUDIT THE INPUT PATHS FIRST")
    print("="*50)
    
    ref_ds = xr.open_dataset(f"{base_dir}/data/processed/transfer/da_cdf/delta_rzsm/delta_rzsm_2016.nc")
    mask = ~np.isnan(ref_ds["delta_rzsm"].values[0])
    lats = ref_ds.lat.values
    lons = ref_ds.lon.values
    num_valid = np.sum(mask)
    
    data = {exp: {target: [] for target in targets} for exp in exps}
    freq_data = {exp: [] for exp in exps}
    time_all = []
    
    for exp in exps:
        for target in targets:
            files = [f"{base_dir}/data/processed/transfer/{exp}/{target}/{target}_{y}.nc" for y in years]
            ds_list = [xr.open_dataset(f) for f in files]
            total_time = sum(len(ds.time) for ds in ds_list)
            print(f"Target: {target} | Exp: {exp}")
            print(f"  File pattern: data/processed/transfer/{exp}/{target}/{target}_YYYY.nc")
            print(f"  Variable name: {target}")
            print(f"  Dimensions: {ds_list[0][target].dims}")
            print(f"  Dtype: {ds_list[0][target].dtype}")
            print(f"  Number of annual files: {len(files)}")
            print(f"  Total time count: {total_time}")
            
    for year in years:
        f_cdf = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/da_cdf/observation_frequency/observation_frequency_{year}.nc")
        f_nocdf = xr.open_dataset(f"{base_dir}/data/processed/daily_enkf/da_nocdf/observation_frequency/observation_frequency_{year}.nc")
        
        freq_data['da_cdf'].append(f_cdf['observation_frequency'].values[:, mask])
        freq_data['da_nocdf'].append(f_nocdf['observation_frequency'].values[:, mask])
        
        t_vals = f_cdf.time.values
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
        freq_data[exp] = np.concatenate(freq_data[exp], axis=0)
        for target in targets:
            data[exp][target] = np.concatenate(data[exp][target], axis=0)

    print("\n="*50)
    print("2. REGRESSION-CHECK EACH TARGET AGAINST ITS OWN QC")
    print("="*50)
    
    reg_checks = {
        'delta_rzsm': {'da_cdf': {'min': -0.248663}, 'da_nocdf': {'min': -0.275876}},
        'delta_et': {'da_cdf': {'zero': 1}, 'da_nocdf': {'zero': 4}},
        'delta_surface_runoff': {'da_cdf': {'zero': 1524407}, 'da_nocdf': {'zero': 1539398}},
        'delta_baseflow': {'da_cdf': {'zero': 36607}, 'da_nocdf': {'zero': 24283}}
    }
    
    for exp in exps:
        for target in targets:
            vals = data[exp][target].flatten()
            finite_count = np.sum(np.isfinite(vals))
            valid_vals = vals[np.isfinite(vals)]
            n_neg = np.sum(valid_vals < 0)
            n_zero = np.sum(valid_vals == 0)
            n_pos = np.sum(valid_vals > 0)
            min_v = np.min(valid_vals)
            max_v = np.max(valid_vals)
            mean_v = np.mean(valid_vals)
            med_v = np.median(valid_vals)
            std_v = np.std(valid_vals)
            
            print(f"Target: {target} | Exp: {exp}")
            print(f"  finite count: {finite_count}")
            print(f"  min: {min_v:.6e}, max: {max_v:.6e}, mean: {mean_v:.6e}, median: {med_v:.6e}, std: {std_v:.6e}")
            print(f"  exact negative: {n_neg}, exact zero: {n_zero}, exact positive: {n_pos}")
            
            if 'min' in reg_checks[target][exp]:
                expected = reg_checks[target][exp]['min']
                if not np.isclose(min_v, expected, atol=1e-5):
                    print(f"  [ERROR] Min mismatch! Expected {expected}, got {min_v}")
                    sys.exit(1)
            if 'zero' in reg_checks[target][exp]:
                expected = reg_checks[target][exp]['zero']
                if n_zero != expected:
                    print(f"  [ERROR] Zero count mismatch! Expected {expected}, got {n_zero}")
                    sys.exit(1)

    print("\n="*50)
    print("3. REGRESSION-CHECK ABSOLUTE MEDIANS")
    print("="*50)
    for exp in exps:
        for target in targets:
            vals = data[exp][target].flatten()
            valid_vals = vals[np.isfinite(vals)]
            abs_vals = np.abs(valid_vals)
            med_abs = np.median(abs_vals)
            print(f"Target: {target} | Exp: {exp}")
            print(f"  median |target|: {med_abs:.6e}")

    print("\n="*50)
    print("4. FIX ZERO / NEAR-ZERO DEFINITIONS AND SANITY")
    print("="*50)
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for target in targets:
            vals = data[exp][target].flatten()
            vals = vals[np.isfinite(vals)]
            n_tot = len(vals)
            abs_vals = np.abs(vals)
            
            n_eq_0 = np.sum(vals == 0)
            n_le_1e8 = np.sum(abs_vals <= 1e-8)
            n_le_1e6 = np.sum(abs_vals <= 1e-6)
            n_le_1e4 = np.sum(abs_vals <= 1e-4)
            n_le_1e3 = np.sum(abs_vals <= 1e-3)
            
            n_gt_1e8 = n_tot - n_le_1e8
            n_gt_1e6 = n_tot - n_le_1e6
            n_gt_1e4 = n_tot - n_le_1e4
            n_gt_1e3 = n_tot - n_le_1e3
            
            print(f"  Target: {target}")
            print(f"    exact-zero count: {n_eq_0} ({n_eq_0/n_tot:.4%})")
            print(f"    <=1e-8 count: {n_le_1e8} ({n_le_1e8/n_tot:.4%}) | >1e-8 count: {n_gt_1e8} ({n_gt_1e8/n_tot:.4%})")
            print(f"    <=1e-6 count: {n_le_1e6} ({n_le_1e6/n_tot:.4%}) | >1e-6 count: {n_gt_1e6} ({n_gt_1e6/n_tot:.4%})")
            print(f"    <=1e-4 count: {n_le_1e4} ({n_le_1e4/n_tot:.4%}) | >1e-4 count: {n_gt_1e4} ({n_gt_1e4/n_tot:.4%})")
            print(f"    <=1e-3 count: {n_le_1e3} ({n_le_1e3/n_tot:.4%}) | >1e-3 count: {n_gt_1e3} ({n_gt_1e3/n_tot:.4%})")
            
            # Assertions
            assert n_eq_0 <= n_le_1e8, f"Monotonicity failed for {target} {exp}: n_eq_0 > n_le_1e8"
            assert n_le_1e8 <= n_le_1e6, f"Monotonicity failed for {target} {exp}: n_le_1e8 > n_le_1e6"
            assert n_le_1e6 <= n_le_1e4, f"Monotonicity failed for {target} {exp}: n_le_1e6 > n_le_1e4"
            assert n_le_1e4 <= n_le_1e3, f"Monotonicity failed for {target} {exp}: n_le_1e4 > n_le_1e3"
            
            med_abs = np.median(abs_vals)
            
            sanity_pass = True
            for thresh, count_le in [(1e-8, n_le_1e8), (1e-6, n_le_1e6), (1e-4, n_le_1e4), (1e-3, n_le_1e3)]:
                frac_le = count_le / n_tot
                if med_abs > thresh:
                    if frac_le >= 0.5: sanity_pass = False
                elif med_abs < thresh:
                    if frac_le < 0.5: sanity_pass = False
            
            if sanity_pass:
                print("    Sanity: PASS")
            else:
                print("    Sanity: FAIL")
                sys.exit(1)

    print("\n="*50)
    print("5. PRESERVE THE CORRECTED ASSIMILATION OVERLAP")
    print("="*50)
    
    val_cdf = freq_data['da_cdf'].flatten()
    val_nocdf = freq_data['da_nocdf'].flatten()
    
    mask_cdf = (val_cdf == 1)
    mask_nocdf = (val_nocdf == 1)
    
    cat_A = (~mask_cdf) & (~mask_nocdf)
    cat_B = mask_cdf & mask_nocdf
    cat_C = mask_cdf & (~mask_nocdf)
    cat_D = (~mask_cdf) & mask_nocdf
    
    n_A = np.sum(cat_A)
    n_B = np.sum(cat_B)
    n_C = np.sum(cat_C)
    n_D = np.sum(cat_D)
    
    tot_support = len(val_cdf)
    print(f"Total canonical support: {tot_support}")
    print(f"  A. neither assimilates (~CDF & ~NoCDF): {n_A} ({n_A/tot_support:.2%})")
    print(f"  B. both assimilate (CDF & NoCDF): {n_B} ({n_B/tot_support:.2%})")
    print(f"  C. CDF-only (CDF & ~NoCDF): {n_C} ({n_C/tot_support:.2%})")
    print(f"  D. NoCDF-only (~CDF & NoCDF): {n_D} ({n_D/tot_support:.2%})")
    
    assert n_A == 21764715, "Mismatch neither"
    assert n_B == 2441779, "Mismatch both"
    assert n_C == 14454, "Mismatch CDF-only"
    assert n_D == 5065862, "Mismatch NoCDF-only"
    
    assert n_A + n_B + n_C + n_D == tot_support, "Closure A+B+C+D failed"
    assert tot_support == 29286810, "Total support failed"
    assert n_B + n_C == 2456233, "CDF total marginal failed"
    assert n_B + n_D == 7507641, "NoCDF total marginal failed"
    
    print("\n="*50)
    print("6. RECOMPUTE MATCHED-SUPPORT ANALYSES ONLY AFTER FIX")
    print("="*50)
    for target in targets:
        print(f"\nTarget: {target}")
        v_cdf = data['da_cdf'][target].flatten()
        v_nocdf = data['da_nocdf'][target].flatten()
        
        for name, mask_c in [('neither assimilates', cat_A), ('both assimilate', cat_B), ('CDF-only', cat_C), ('NoCDF-only', cat_D)]:
            if np.sum(mask_c) > 0:
                print(f"  Support: {name} (Count: {np.sum(mask_c)})")
                mc = np.mean(v_cdf[mask_c])
                mn = np.mean(v_nocdf[mask_c])
                medc = np.median(v_cdf[mask_c])
                medn = np.median(v_nocdf[mask_c])
                mac = np.mean(np.abs(v_cdf[mask_c]))
                man = np.mean(np.abs(v_nocdf[mask_c]))
                mdac = np.median(np.abs(v_cdf[mask_c]))
                mdan = np.median(np.abs(v_nocdf[mask_c]))
                p95c = np.percentile(np.abs(v_cdf[mask_c]), 95)
                p95n = np.percentile(np.abs(v_nocdf[mask_c]), 95)
                print(f"    CDF   -> mean: {mc:.6e}, median: {medc:.6e}, mean_abs: {mac:.6e}, median_abs: {mdac:.6e}, p95_abs: {p95c:.6e}")
                print(f"    NoCDF -> mean: {mn:.6e}, median: {medn:.6e}, mean_abs: {man:.6e}, median_abs: {mdan:.6e}, p95_abs: {p95n:.6e}")
                
    print("\n="*50)
    print("7. FULL CORRELATION OUTPUT")
    print("="*50)
    pairs = [('delta_rzsm', 'delta_et'), ('delta_rzsm', 'delta_surface_runoff'), 
             ('delta_rzsm', 'delta_baseflow'), ('delta_et', 'delta_surface_runoff'),
             ('delta_et', 'delta_baseflow'), ('delta_surface_runoff', 'delta_baseflow')]
    
    stride = 10
    corr_results = {exp: {} for exp in exps}
    for exp in exps:
        print(f"\nExperiment: {exp}")
        freq = freq_data[exp].flatten()
        for p1, p2 in pairs:
            v1 = data[exp][p1].flatten()
            v2 = data[exp][p2].flatten()
            for mask_name, m in [('ALL', np.ones(tot_support, dtype=bool)), ('OBS_FREQ=1', freq == 1), ('OBS_FREQ=0', freq == 0)]:
                s1 = v1[m][::stride]
                s2 = v2[m][::stride]
                p_sgn = pearsonr(s1, s2)[0]
                sp_sgn = spearmanr(s1, s2)[0]
                p_abs = pearsonr(np.abs(s1), np.abs(s2))[0]
                sp_abs = spearmanr(np.abs(s1), np.abs(s2))[0]
                print(f"  {p1} vs {p2} [{mask_name}]:")
                print(f"    Signed -> Pearson: {p_sgn:.4f}, Spearman: {sp_sgn:.4f}")
                print(f"    Absolute -> Pearson: {p_abs:.4f}, Spearman: {sp_abs:.4f}")
                
                if mask_name == 'ALL':
                    if p1 not in corr_results[exp]: corr_results[exp][p1] = {}
                    if p2 not in corr_results[exp]: corr_results[exp][p2] = {}
                    corr_results[exp][p1][p2] = {'p_sgn': p_sgn, 'sp_sgn': sp_sgn, 'p_abs': p_abs, 'sp_abs': sp_abs}
                    corr_results[exp][p2][p1] = {'p_sgn': p_sgn, 'sp_sgn': sp_sgn, 'p_abs': p_abs, 'sp_abs': sp_abs}
    np.save(os.path.join(out_dir, "corr_results.npy"), corr_results)

    print("\n="*50)
    print("8. RECOMPUTE MATCHED TEMPORAL PERSISTENCE")
    print("="*50)
    persistence_table = []
    for exp in exps:
        for target in targets:
            vals = data[exp][target] 
            ts_mean_sgn = np.nanmean(vals, axis=1)
            ts_mean_abs = np.nanmean(np.abs(vals), axis=1)
            
            def autocorr(x, lag):
                return np.corrcoef(x[:-lag], x[lag:])[0, 1]
                
            s_l1 = autocorr(ts_mean_sgn, 1)
            s_l3 = autocorr(ts_mean_sgn, 3)
            s_l7 = autocorr(ts_mean_sgn, 7)
            
            a_l1 = autocorr(ts_mean_abs, 1)
            a_l3 = autocorr(ts_mean_abs, 3)
            a_l7 = autocorr(ts_mean_abs, 7)
            
            persistence_table.append({
                'Experiment': exp,
                'Target': target,
                'signed_lag1': s_l1, 'signed_lag3': s_l3, 'signed_lag7': s_l7,
                'abs_lag1': a_l1, 'abs_lag3': a_l3, 'abs_lag7': a_l7
            })
            
    df_pers = pd.DataFrame(persistence_table)
    print(df_pers.to_string(index=False))
    df_pers.to_csv(os.path.join(out_dir, "temporal_persistence.csv"), index=False)
    
    print("\n="*50)
    print("9. COMPLETE ROW-STRUCTURE TABLE")
    print("="*50)
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for i, target in enumerate(targets):
            vals = data[exp][target] 
            
            even_mask = np.zeros(len(lats), dtype=bool)
            even_mask[::2] = True
            
            full_2d = np.full((len(time_all), len(lats), len(lons)), np.nan)
            for t in range(len(time_all)):
                temp = np.full((len(lats), len(lons)), np.nan)
                temp[mask] = vals[t]
                full_2d[t] = temp
                
            even_vals = full_2d[:, even_mask, :].flatten()
            odd_vals = full_2d[:, ~even_mask, :].flatten()
            even_vals = even_vals[np.isfinite(even_vals)]
            odd_vals = odd_vals[np.isfinite(odd_vals)]
            
            e_mean = np.mean(even_vals)
            o_mean = np.mean(odd_vals)
            e_abs = np.mean(np.abs(even_vals))
            o_abs = np.mean(np.abs(odd_vals))
            
            diff_sgn = o_mean - e_mean
            diff_abs = o_abs - e_abs
            overall_abs = np.mean(np.abs(full_2d[np.isfinite(full_2d)]))
            norm_contrast = diff_abs / overall_abs if overall_abs != 0 else 0
            
            print(f"  Target: {target}")
            print(f"    Even-row signed mean: {e_mean:.6e}")
            print(f"    Odd-row signed mean: {o_mean:.6e}")
            print(f"    Even-row absolute mean: {e_abs:.6e}")
            print(f"    Odd-row absolute mean: {o_abs:.6e}")
            print(f"    Signed odd-even diff: {diff_sgn:.6e}")
            print(f"    Absolute odd-even diff: {diff_abs:.6e}")
            print(f"    Normalized absolute contrast: {norm_contrast:.4f}")
            if target == "delta_rzsm":
                print("    No comparable rigid row-dependent structure is evident in this unified diagnostic.")

    print("\n="*50)
    print("10. COMPLETE EXTREME-DATE RESULTS")
    print("="*50)
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for target in targets:
            vals = data[exp][target]
            abs_vals = np.abs(vals)
            daily_sum = np.nansum(abs_vals, axis=1)
            total_sum = np.sum(daily_sum)
            top10_idx = np.argsort(daily_sum)[-10:][::-1]
            top10_sum = np.sum(daily_sum[top10_idx])
            top10_dates = time_all[top10_idx].strftime('%Y-%m-%d').tolist()
            
            print(f"  Target: {target}")
            print(f"    top-10 dates by sum(abs(target)): {top10_dates}")
            print(f"    contribution of those 10 dates to total absolute response: {top10_sum/total_sum:.4%}")

    print("\n="*50)
    print("11. COMPLETE EXTREME-PIXEL RESULTS")
    print("="*50)
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for target in targets:
            vals = data[exp][target]
            abs_vals = np.abs(vals)
            pixel_sum = np.nansum(abs_vals, axis=0)
            total_sum = np.sum(pixel_sum)
            pixel_sum_sorted = np.sort(pixel_sum)
            top1_sum = np.sum(pixel_sum_sorted[-int(0.01*len(pixel_sum_sorted)):])
            top5_sum = np.sum(pixel_sum_sorted[-int(0.05*len(pixel_sum_sorted)):])
            
            p50 = np.percentile(pixel_sum_sorted, 50)
            p75 = np.percentile(pixel_sum_sorted, 75)
            p90 = np.percentile(pixel_sum_sorted, 90)
            p95 = np.percentile(pixel_sum_sorted, 95)
            p99 = np.percentile(pixel_sum_sorted, 99)
            
            print(f"  Target: {target}")
            print(f"    top 1% land-pixel contribution: {top1_sum/total_sum:.4%}")
            print(f"    top 5% land-pixel contribution: {top5_sum/total_sum:.4%}")
            print(f"    per-pixel accumulated-response distribution:")
            print(f"      p50: {p50:.6e}")
            print(f"      p75: {p75:.6e}")
            print(f"      p90: {p90:.6e}")
            print(f"      p95: {p95:.6e}")
            print(f"      p99: {p99:.6e}")

    print("\n="*50)
    print("12. COMPLETE OUTAGE TABLE")
    print("="*50)
    outage_mask = pd.Series(time_all).between('2019-06-19', '2019-07-23').values
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for target in targets:
            out_vals = data[exp][target][outage_mask].flatten()
            finite_out = np.sum(np.isfinite(out_vals))
            valid_out = out_vals[np.isfinite(out_vals)]
            m_sgn = np.mean(valid_out)
            med_sgn = np.median(valid_out)
            abs_out = np.abs(valid_out)
            m_abs = np.mean(abs_out)
            med_abs = np.median(abs_out)
            p95_abs = np.percentile(abs_out, 95)
            
            print(f"  Target: {target}")
            print(f"    finite count: {finite_out}")
            print(f"    mean signed: {m_sgn:.6e}")
            print(f"    median signed: {med_sgn:.6e}")
            print(f"    mean absolute: {m_abs:.6e}")
            print(f"    median absolute: {med_abs:.6e}")
            print(f"    p95 absolute: {p95_abs:.6e}")

    print("\n="*50)
    print("13. COMPLETE SEASONAL TABLE")
    print("="*50)
    full_months = time_all.month
    for exp in exps:
        print(f"\nExperiment: {exp}")
        for target in targets:
            vals = data[exp][target]
            print(f"  Target: {target}")
            for s, m_list in [('DJF', [12, 1, 2]), ('MAM', [3, 4, 5]), ('JJA', [6, 7, 8]), ('SON', [9, 10, 11])]:
                s_mask = np.isin(full_months, m_list)
                s_vals = vals[s_mask].flatten()
                valid_s = s_vals[np.isfinite(s_vals)]
                m_sgn = np.mean(valid_s)
                med_sgn = np.median(valid_s)
                abs_s = np.abs(valid_s)
                m_abs = np.mean(abs_s)
                med_abs = np.median(abs_s)
                print(f"    Season: {s}")
                print(f"      mean signed: {m_sgn:.6e} | median signed: {med_sgn:.6e}")
                print(f"      mean absolute: {m_abs:.6e} | median absolute: {med_abs:.6e}")

if __name__ == "__main__":
    main()
