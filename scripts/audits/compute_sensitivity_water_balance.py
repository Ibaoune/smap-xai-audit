#!/usr/bin/env python3
"""
Compute Internal Water Balance for Sensitivity Runs (March 2018):
- ENS_FORC_201803 (Forcing-only perturbations, std=0 on state)
- ENS_STATE_201803 (State-only perturbations, std=0 on forcing)
- ENS_OPL_2018 (Full perturbations: forcing + state)
- OL_DAIC_2018 (Deterministic 1-member, no pert)

Internal Water Balance formula:
  Residu = P - ET - Qs - Qsb - DeltaStock
where:
  Stock = sum(dz_l * SMC_l) + WA + CANWAT + SNEQV (ensemble mean over land pixels)
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

def read_storage_ens(fp):
    if not os.path.exists(fp):
        raise FileNotFoundError(f"Missing restart: {fp}")
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

def get_monthly_fluxes(flist):
    p_tot, et_tot, qs_tot, qsb_tot = 0.0, 0.0, 0.0, 0.0
    for f in flist:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing history file: {f}")
        with nc.Dataset(f) as ds:
            p_tot   += float(np.mean(ds.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
            et_tot  += float(np.mean(ds.variables['Evap_tavg'][:].squeeze()[landmask] * 86400.0))
            qs_tot  += float(np.mean(ds.variables['Qs_tavg'][:].squeeze()[landmask] * 86400.0))
            qsb_tot += float(np.mean(ds.variables['Qsb_tavg'][:].squeeze()[landmask] * 86400.0))
    return p_tot, et_tot, qs_tot, qsb_tot

def compute_run_balance(run_name, base_out_dir, rst_start_path, rst_end_path):
    print(f"--- Computing balance for: {run_name} ---")
    s_start = read_storage_ens(rst_start_path)
    s_end   = read_storage_ens(rst_end_path)
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

if __name__ == "__main__":
    rst_start = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL/201802/LIS_RST_NOAHMP401_201802282345.d01.nc")
    
    # 1. ENS_FORC_201803
    dir_forc = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_FORC_201803/output")
    rst_forc = os.path.join(dir_forc, "SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc")
    
    # 2. ENS_STATE_201803
    dir_stat = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_STATE_201803/output")
    rst_stat = os.path.join(dir_stat, "SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc")
    
    # 3. Reference ENS_OPL_2018
    dir_opl = os.path.join(BASE_DIR, "NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output")
    rst_opl = os.path.join(dir_opl, "SURFACEMODEL/201803/LIS_RST_NOAHMP401_201803312345.d01.nc")
    
    results = []
    
    # Always include reference ENS_OPL (computed previously: -7.85 mm)
    if os.path.exists(rst_opl):
        res_opl = compute_run_balance("ENS_OPL_2018 (Forc + State)", dir_opl, rst_start, rst_opl)
        results.append(res_opl)
        
    if os.path.exists(rst_forc):
        res_forc = compute_run_balance("ENS_FORC_201803 (Forc seule, std_state=0)", dir_forc, rst_start, rst_forc)
        results.append(res_forc)
    else:
        print("[WAIT] ENS_FORC_201803 restart not ready yet.")
        
    if os.path.exists(rst_stat):
        res_stat = compute_run_balance("ENS_STATE_201803 (Etat seule, std_forc=0)", dir_stat, rst_start, rst_stat)
        results.append(res_stat)
    else:
        print("[WAIT] ENS_STATE_201803 restart not ready yet.")
        
    if results:
        df = pd.DataFrame(results)
        print("\n=== RESULTATS DU BILAN D'EAU INTERNE (MARS 2018) ===")
        print(df.to_string(index=False))
        out_csv = os.path.join(OUT_DIR, "sensitivity_internal_water_balance_201803.csv")
        df.to_csv(out_csv, index=False)
        print(f"\nSauvegarde dans: {out_csv}")
