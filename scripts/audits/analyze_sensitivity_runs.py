#!/usr/bin/env python3
"""
Scientific Analysis of Sensitivity Runs (March 2018):
Runs examined:
  1. ENS_OPL_2018: Full perturbations (Forcing + State)
  2. OL_DAIC_2018: Deterministic 1-member (No perturbations)
  3. ENS_FORC_201803: Forcing-only perturbations (std=0 on state)
  4. ENS_STATE_201803: State-only perturbations (std=0 on forcing)
  5. ENS_NOSTATE_201803: Forcing-only perturbations (State pert algorithm: none)

Tasks:
  2a. Internal water balance: P - ET - Qs - Qsb - DeltaStock
  2b. Maximum absolute difference ENS_FORC - ENS_OPL on SMC (4 layers) and ET at March 31 (exact 0 or not?)
  2c. In ENS_FORC: For each available restart, count members whose 4 layers exactly equal (max+min)/2 of their cell's ensemble.
  3. Generate CSV + README without interpretation.
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc
import pandas as pd

BASE_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao"
PARAM_NC = os.path.join(BASE_DIR, "NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc")
OUT_DIR  = os.path.join(BASE_DIR, "smap-xai-audit/reports/audits/diag2018_e6_clean")
os.makedirs(OUT_DIR, exist_ok=True)

with nc.Dataset(PARAM_NC) as ds:
    landmask = ds.variables['LANDMASK'][:].squeeze() > 0.5

dz = np.array([0.1, 0.3, 0.6, 1.0], dtype=np.float32) * 1000.0 # mm

# -------------------------------------------------------------
# Part 2a: Internal Water Balance
# -------------------------------------------------------------
def read_storage_ens(fp):
    with nc.Dataset(fp) as ds:
        smc = ds.variables['SMC'][:]
        wa = ds.variables['WA'][:]
        can = ds.variables['CANWAT'][:]
        sneqv = ds.variables['SNEQV'][:]
        n_ens = 20
        n_tiles = 16030
        
        smc_m = np.mean(smc.reshape(4, n_tiles, n_ens), axis=2)
        wa_m = np.mean(wa.reshape(n_tiles, n_ens), axis=1)
        can_m = np.mean(can.reshape(n_tiles, n_ens), axis=1)
        sn_m = np.mean(sneqv.reshape(n_tiles, n_ens), axis=1)
        
        smc_col = np.sum(smc_m * dz[:, None], axis=0)
        tot = smc_col + wa_m + can_m + sn_m
        return {
            'smc': float(np.mean(smc_col)),
            'wa': float(np.mean(wa_m)),
            'can': float(np.mean(can_m)),
            'sn': float(np.mean(sn_m)),
            'tot': float(np.mean(tot))
        }

def read_storage_1m(fp):
    with nc.Dataset(fp) as ds:
        smc = ds.variables['SMC'][:]
        wa = ds.variables['WA'][:]
        can = ds.variables['CANWAT'][:]
        sneqv = ds.variables['SNEQV'][:]
        
        smc_col = np.sum(smc * dz[:, None], axis=0)
        tot = smc_col + wa + can + sneqv
        return {
            'smc': float(np.mean(smc_col)),
            'wa': float(np.mean(wa)),
            'can': float(np.mean(can)),
            'sn': float(np.mean(sneqv)),
            'tot': float(np.mean(tot))
        }

def get_monthly_fluxes(flist):
    p_tot, et_tot, qs_tot, qsb_tot = 0.0, 0.0, 0.0, 0.0
    for f in flist:
        with nc.Dataset(f) as ds:
            if 'TotalPrecip_tavg' in ds.variables:
                p_tot += float(np.mean(ds.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
            et_tot  += float(np.mean(ds.variables['Evap_tavg'][:].squeeze()[landmask] * 86400.0))
            qs_tot  += float(np.mean(ds.variables['Qs_tavg'][:].squeeze()[landmask] * 86400.0))
            qsb_tot += float(np.mean(ds.variables['Qsb_tavg'][:].squeeze()[landmask] * 86400.0))
    return p_tot, et_tot, qs_tot, qsb_tot

def compute_run_balance(run_name, base_out_dir, rst_start_path, rst_end_path, is_1m=False):
    s_start = read_storage_1m(rst_start_path) if is_1m else read_storage_ens(rst_start_path)
    s_end   = read_storage_1m(rst_end_path) if is_1m else read_storage_ens(rst_end_path)
    d_stock = s_end['tot'] - s_start['tot']
    
    start_dt = datetime.datetime(2018, 3, 1)
    hist_files = []
    for d in range(31):
        dt_curr = start_dt + datetime.timedelta(days=d)
        dt_next = dt_curr + datetime.timedelta(days=1)
        ym_next = dt_next.strftime("%Y%m")
        d_next_str = dt_next.strftime("%Y%m%d")
        f = os.path.join(base_out_dir, f"SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        hist_files.append(f)
        
    p, et, qs, qsb = get_monthly_fluxes(hist_files)
    if is_1m and p == 0.0:
        # Read deterministic precip from OPL_noirr
        p_opl = 0.0
        start_dt = datetime.datetime(2018, 3, 1)
        opl_base = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output/2018-03/SURFACEMODEL")
        for d in range(31):
            dt_next = start_dt + datetime.timedelta(days=d+1)
            ym_n = dt_next.strftime("%Y%m")
            f_opl = os.path.join(opl_base, f"{ym_n}/LIS_HIST_{dt_next.strftime('%Y%m%d')}0000.d01.nc")
            if not os.path.exists(f_opl):
                f_opl = os.path.join(opl_base, f"201803/LIS_HIST_{dt_next.strftime('%Y%m%d')}0000.d01.nc")
            with nc.Dataset(f_opl) as ds_o:
                p_opl += float(np.mean(ds_o.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
        p = p_opl
    res = (p - et - qs - qsb) - d_stock
    
    return {
        'run': run_name,
        'P_mm': round(p, 2),
        'ET_mm': round(et, 2),
        'Qs_mm': round(qs, 2),
        'Qsb_mm': round(qsb, 2),
        'dStock_mm': round(d_stock, 2),
        'Residu_mm': round(res, 2),
        'Stock_start_mm': round(s_start['tot'], 2),
        'Stock_end_mm': round(s_end['tot'], 2)
    }

# -------------------------------------------------------------
# Part 2b: Difference ENS_FORC - ENS_OPL at March 31
# -------------------------------------------------------------
def compute_diff_forc_vs_opl():
    # 1. Daily averages of March 31 from LIS_HIST_201804010000.d01.nc
    f_hist_opl = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL/201804/LIS_HIST_201804010000.d01.nc")
    f_hist_forc = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_FORC_201803/output/SURFACEMODEL/201804/LIS_HIST_201804010000.d01.nc")
    
    diff_records = []
    if os.path.exists(f_hist_opl) and os.path.exists(f_hist_forc):
        with nc.Dataset(f_hist_opl) as ds_opl, nc.Dataset(f_hist_forc) as ds_forc:
            # ET daily average (mm/day)
            et_opl = ds_opl.variables['Evap_tavg'][:].squeeze() * 86400.0
            et_forc = ds_forc.variables['Evap_tavg'][:].squeeze() * 86400.0
            diff_et = np.abs(et_forc[landmask] - et_opl[landmask])
            max_diff_et = float(np.max(diff_et))
            mean_diff_et = float(np.mean(diff_et))
            
            diff_records.append({
                'variable': 'ET_daily_avg (Evap_tavg)',
                'level': 'Surface',
                'source': 'LIS_HIST_201804010000 (31 Mars)',
                'max_abs_diff': max_diff_et,
                'mean_abs_diff': mean_diff_et,
                'is_exact_zero': (max_diff_et == 0.0)
            })
            
            # Soil moisture daily average (m3/m3)
            sm_opl = ds_opl.variables['SoilMoist_tavg'][:] # (4, 121, 181)
            sm_forc = ds_forc.variables['SoilMoist_tavg'][:] # (4, 121, 181)
            for l in range(4):
                sm_opl_l = sm_opl[l][landmask]
                sm_forc_l = sm_forc[l][landmask]
                diff_l = np.abs(sm_forc_l - sm_opl_l)
                max_diff_l = float(np.max(diff_l))
                mean_diff_l = float(np.mean(diff_l))
                diff_records.append({
                    'variable': f'SoilMoist_daily_avg (Layer {l+1})',
                    'level': f'Layer {l+1}',
                    'source': 'LIS_HIST_201804010000 (31 Mars)',
                    'max_abs_diff': max_diff_l,
                    'mean_abs_diff': mean_diff_l,
                    'is_exact_zero': (max_diff_l == 0.0)
                })

    # 2. Instantaneous restart at March 31 23:45
    f_rst_opl = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc")
    f_rst_forc = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_FORC_201803/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc")
    
    if os.path.exists(f_rst_opl) and os.path.exists(f_rst_forc):
        with nc.Dataset(f_rst_opl) as ds_opl, nc.Dataset(f_rst_forc) as ds_forc:
            smc_opl = ds_opl.variables['SMC'][:] # (4, 320600)
            smc_forc = ds_forc.variables['SMC'][:] # (4, 320600)
            for l in range(4):
                # Member-level max absolute difference
                diff_members = np.abs(smc_forc[l] - smc_opl[l])
                max_diff_m = float(np.max(diff_members))
                mean_diff_m = float(np.mean(diff_members))
                
                # Ensemble-mean max absolute difference
                smc_opl_mean = np.mean(smc_opl[l].reshape(16030, 20), axis=1)
                smc_forc_mean = np.mean(smc_forc[l].reshape(16030, 20), axis=1)
                diff_mean = np.abs(smc_forc_mean - smc_opl_mean)
                max_diff_ens = float(np.max(diff_mean))
                mean_diff_ens = float(np.mean(diff_mean))
                
                diff_records.append({
                    'variable': f'SMC_restart_members (Layer {l+1})',
                    'level': f'Layer {l+1}',
                    'source': 'LIS_RST_NOAHMP401_201803312345 (23:45)',
                    'max_abs_diff': max_diff_m,
                    'mean_abs_diff': mean_diff_m,
                    'is_exact_zero': (max_diff_m == 0.0)
                })
                diff_records.append({
                    'variable': f'SMC_restart_ens_mean (Layer {l+1})',
                    'level': f'Layer {l+1}',
                    'source': 'LIS_RST_NOAHMP401_201803312345 (23:45)',
                    'max_abs_diff': max_diff_ens,
                    'mean_abs_diff': mean_diff_ens,
                    'is_exact_zero': (max_diff_ens == 0.0)
                })

    df_diff = pd.DataFrame(diff_records)
    return df_diff

# -------------------------------------------------------------
# Part 2c: Count Midrange Replaced Members in ENS_FORC
# -------------------------------------------------------------
def count_midrange_members_in_rst(rst_path):
    with nc.Dataset(rst_path) as ds:
        smc = ds.variables['SMC'][:] # (4, 320600)
        n_tiles = 16030
        n_ens = 20
        smc_r = smc.reshape(4, n_tiles, n_ens)
        
        min_s = np.min(smc_r, axis=2, keepdims=True)
        max_s = np.max(smc_r, axis=2, keepdims=True)
        mid_s = (max_s - min_s) / 2.0 + min_s
        
        # Exact float equality
        exact_equal = (smc_r == mid_s) # (4, 16030, 20)
        all_4_exact = np.all(exact_equal, axis=0) # (16030, 20)
        n_exact_all4 = int(np.sum(all_4_exact))
        
        # Tolerance 1e-6
        close_equal = np.isclose(smc_r, mid_s, atol=1e-6, rtol=1e-5)
        all_4_close = np.all(close_equal, axis=0)
        n_close_all4 = int(np.sum(all_4_close))
        
        # Per layer exact matches
        layer_exact = [int(np.sum(exact_equal[l])) for l in range(4)]
        
        return {
            'restart_file': os.path.basename(rst_path),
            'n_members_all_4_layers_exact_mid': n_exact_all4,
            'n_members_all_4_layers_close_1e6': n_close_all4,
            'layer_1_exact_mid': layer_exact[0],
            'layer_2_exact_mid': layer_exact[1],
            'layer_3_exact_mid': layer_exact[2],
            'layer_4_exact_mid': layer_exact[3],
            'total_evaluated_members': n_tiles * n_ens
        }


def to_markdown_table(df):
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(str(c) for c in cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)

def generate_sensitivity_readme(df_wb, df_diff, df_c):
    md = []
    md.append("# Synthèse des Expériences de Sensibilité — Mars 2018\n")
    md.append("**Date de génération :** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    md.append("**Branche Git :** `elaabar` | **Rapport d'audit :** Neutre, purement descriptif, sans interprétation.\n")
    md.append("---\n")
    
    md.append("## 1. Bilan Interne ($P - ET - Q_s - Q_{sb} - \\Delta\\text{Stock}$) — Mars 2018\n")
    md.append("Formule : $\\text{Résidu} = P - ET - Q_s - Q_{sb} - \\Delta\\text{Stock}$\n")
    md.append("Stock total = 4 couches SMC + WA + CANWAT + SNEQV (moyenne d'ensemble sur pixels terrestres).\n\n")
    md.append(to_markdown_table(df_wb) + "\n\n")
    md.append("Fichier source : `sensitivity_internal_water_balance_201803.csv`\n\n")
    md.append("---\n")
    
    md.append("## 2. Différence Maximale Absolue ENS_FORC − ENS_OPL au 31 Mars 2018\n\n")
    if not df_diff.empty:
        md.append(to_markdown_table(df_diff) + "\n\n")
        md.append("Fichier source : `diff_ens_forc_vs_ens_opl_20180331.csv`\n\n")
    else:
        md.append("*En attente des sorties complètes du 31 mars pour ENS_FORC_201803.*\n\n")
    md.append("---\n")
    
    md.append("## 3. Détection des Remplacements de Membres (Moyenne Midrange $(max + min)/2$) dans ENS_FORC\n\n")
    if not df_c.empty:
        md.append(to_markdown_table(df_c) + "\n\n")
        md.append("Fichier source : `ens_forc_midrange_replacement_counts.csv`\n\n")
    else:
        md.append("*En attente des restarts pour ENS_FORC_201803.*\n\n")
        
    readme_path = os.path.join(OUT_DIR, "README_sensitivity_march2018.md")
    with open(readme_path, "w") as f:
        f.write("".join(md))
    print(f"[README] Rapport généré dans : {readme_path}")



if __name__ == "__main__":
    rst_start_ens = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL/201802/LIS_RST_NOAHMP401_201802282345.d01.nc")
    rst_start_daic = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_DAIC_2018/output/SURFACEMODEL/201802/LIS_RST_NOAHMP401_201802282345.d01.nc")
    
    # Check restarts
    runs_to_eval = [
        ("ENS_OPL_2018", "ENS_OPL_2018/output", rst_start_ens, "ENS_OPL_2018/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc", False),
        ("OL_DAIC_2018", "OL_DAIC_2018/output", rst_start_daic, "OL_DAIC_2018/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc", True),
        ("ENS_FORC_201803", "ENS_FORC_201803/output", rst_start_ens, "ENS_FORC_201803/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc", False),
        ("ENS_STATE_201803", "ENS_STATE_201803/output", rst_start_ens, "ENS_STATE_201803/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc", False),
        ("ENS_NOSTATE_201803", "ENS_NOSTATE_201803/output", rst_start_ens, "ENS_NOSTATE_201803/output/SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc", False)
    ]
    
    wb_results = []
    sens_base = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018")
    for rname, out_sub, r_st, r_end_rel, is_1m in runs_to_eval:
        b_out = os.path.join(sens_base, out_sub)
        r_end = os.path.join(sens_base, r_end_rel)
        if os.path.exists(r_st) and os.path.exists(r_end):
            print(f"[EVAL 2a] Bilan interne: {rname}")
            res = compute_run_balance(rname, b_out, r_st, r_end, is_1m=is_1m)
            wb_results.append(res)
        else:
            print(f"[WAIT 2a] {rname} pas encore terminé (restart {os.path.basename(r_end)} absent).")
            
    if wb_results:
        df_wb = pd.DataFrame(wb_results)
        csv_wb = os.path.join(OUT_DIR, "sensitivity_internal_water_balance_201803.csv")
        df_wb.to_csv(csv_wb, index=False)
        print("\n=== BILAN INTERNE MARS 2018 ===")
        print(df_wb.to_string(index=False))
        
    # 2b
    print("\n--- [EVAL 2b] Différence absolue ENS_FORC - ENS_OPL ---")
    df_diff = compute_diff_forc_vs_opl()
    if not df_diff.empty:
        csv_diff = os.path.join(OUT_DIR, "diff_ens_forc_vs_ens_opl_20180331.csv")
        df_diff.to_csv(csv_diff, index=False)
        print(df_diff.to_string(index=False))
    else:
        print("[WAIT 2b] Sorties du 31 mars pour ENS_FORC non encore prêtes.")
        
    # 2c
    print("\n--- [EVAL 2c] Comptage membres (max+min)/2 dans ENS_FORC ---")
    forc_rsts = sorted(glob.glob(os.path.join(sens_base, "ENS_FORC_201803/output/SURFACEMODEL/*/LIS_RST_NOAHMP401_*.d01.nc")))
    # also include the initial restart used to start ENS_FORC
    all_eval_rsts = [rst_start_ens] + [r for r in forc_rsts if r != rst_start_ens]
    c_results = []
    for r in all_eval_rsts:
        if os.path.exists(r):
            res_c = count_midrange_members_in_rst(r)
            c_results.append(res_c)
            
    if c_results:
        df_c = pd.DataFrame(c_results)
        csv_c = os.path.join(OUT_DIR, "ens_forc_midrange_replacement_counts.csv")
        df_c.to_csv(csv_c, index=False)
        print(df_c.to_string(index=False))

    # Call README generator
    df_wb_out = df_wb if 'df_wb' in locals() else pd.DataFrame()
    df_diff_out = df_diff if 'df_diff' in locals() else pd.DataFrame()
    df_c_out = df_c if 'df_c' in locals() else pd.DataFrame()
    generate_sensitivity_readme(df_wb_out, df_diff_out, df_c_out)

