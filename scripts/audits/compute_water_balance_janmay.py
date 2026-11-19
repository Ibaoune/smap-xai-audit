#!/usr/bin/env python3
"""
compute_water_balance_janmay.py
Calcule le bilan d'eau mensuel complet (Janvier à Mai 2018) :
Stock total = 4 couches (SMC) + aquifère (WA) + canopée (CANWAT) + neige (SNEQV).
Bilan différentiel DA_nocdf - ENS_OPL :
Résidu = ΔP − ΔET − ΔQs − ΔQsb − Δ(Δstock)
Comparaison directe face aux incréments EnKF archivés.
"""
import os
import glob
import datetime
import netCDF4 as nc
import numpy as np
import pandas as pd

BASE_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_e6_clean")
os.makedirs(OUT_DIR, exist_ok=True)

LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")
with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(bool)

dz = np.array([0.1, 0.3, 0.6, 1.0], dtype=np.float32) * 1000.0 # mm

months = [
    ("2018-01", "201801", 31, "201801010000", "201801312345"),
    ("2018-02", "201802", 28, "201802010000", "201802282345"),
    ("2018-03", "201803", 31, "201803010000", "201803312345"),
    ("2018-04", "201804", 30, "201804010000", "201804302345"),
    ("2018-05", "201805", 31, "201805010000", "201805312345"),
]

def read_storage(fp):
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
        with nc.Dataset(f) as ds:
            p_tot += float(np.mean(ds.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
            et_tot += float(np.mean(ds.variables['Evap_tavg'][:].squeeze()[landmask] * 86400.0))
            qs_tot += float(np.mean(ds.variables['Qs_tavg'][:].squeeze()[landmask] * 86400.0))
            qsb_tot += float(np.mean(ds.variables['Qsb_tavg'][:].squeeze()[landmask] * 86400.0))
    return p_tot, et_tot, qs_tot, qsb_tot

def get_monthly_enkf_increments(ym):
    d_part = f"{ym[:4]}-{ym[4:]}"
    pat = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output/{d_part}/EnKF/{ym}/LIS_DA_EnKF_*_incr.a01.d01.nc")
    flist = sorted(glob.glob(pat))
    if not flist:
        return 0.0, 0
    total_incr = np.zeros(np.sum(landmask), dtype=float)
    for f in flist:
        with nc.Dataset(f) as ds:
            i1 = ds.variables['anlys_incr_Soil Moisture Layer 1_01'][:].squeeze()[landmask]
            i2 = ds.variables['anlys_incr_Soil Moisture Layer 2_01'][:].squeeze()[landmask]
            i3 = ds.variables['anlys_incr_Soil Moisture Layer 3_01'][:].squeeze()[landmask]
            i4 = ds.variables['anlys_incr_Soil Moisture Layer 4_01'][:].squeeze()[landmask]
            total_incr += (dz[0]*i1 + dz[1]*i2 + dz[2]*i3 + dz[3]*i4)
    return float(np.mean(total_incr)), len(flist)

rows = []

rst_ens_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL")
rst_da_base = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020")

prev_rst_ens = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
prev_rst_da  = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")

for m_label, ym, n_days, t_start, t_end in months:
    print(f"[INFO] Traitement du bilan hydrique pour le mois {m_label}...")
    
    curr_rst_ens = os.path.join(rst_ens_dir, ym, f"LIS_RST_NOAHMP401_{t_end}.d01.nc")
    curr_rst_da  = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_RST_NOAHMP401_{t_end}.d01.nc")
    
    s_start_ens = read_storage(prev_rst_ens)
    s_end_ens   = read_storage(curr_rst_ens)
    s_start_da  = read_storage(prev_rst_da)
    s_end_da    = read_storage(curr_rst_da)
    
    delta_stock_ens = s_end_ens['tot'] - s_start_ens['tot']
    delta_stock_da  = s_end_da['tot'] - s_start_da['tot']
    diff_delta_stock = delta_stock_da - delta_stock_ens
    
    diff_d_smc = (s_end_da['smc'] - s_start_da['smc']) - (s_end_ens['smc'] - s_start_ens['smc'])
    diff_d_wa  = (s_end_da['wa'] - s_start_da['wa']) - (s_end_ens['wa'] - s_start_ens['wa'])
    diff_d_can = (s_end_da['can'] - s_start_da['can']) - (s_end_ens['can'] - s_start_ens['can'])
    diff_d_sn  = (s_end_da['sn'] - s_start_da['sn']) - (s_end_ens['sn'] - s_start_ens['sn'])
    
    start_dt = datetime.datetime.strptime(t_start[:8], "%Y%m%d")
    days_dt = [start_dt + datetime.timedelta(days=i) for i in range(n_days)]
    hist_ens = []
    hist_da  = []
    for d in days_dt:
        d_next = d + datetime.timedelta(days=1)
        ym_next = d_next.strftime("%Y%m")
        d_next_str = d_next.strftime("%Y%m%d")
        
        f_ens = os.path.join(rst_ens_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_ens):
            # Check partial hang directory
            f_ens_hang = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
            if os.path.exists(f_ens_hang):
                f_ens = f_ens_hang
                
        f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_da):
            f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_HIST_{d_next_str}0000.d01.nc")
            
        hist_ens.append(f_ens)
        hist_da.append(f_da)
        
    p_ens, et_ens, qs_ens, qsb_ens = get_monthly_fluxes(hist_ens)
    p_da, et_da, qs_da, qsb_da = get_monthly_fluxes(hist_da)
    
    dp   = p_da - p_ens
    det  = et_da - et_ens
    dqs  = qs_da - qs_ens
    dqsb = qsb_da - qsb_ens
    
    flux_balance = dp - det - dqs - dqsb
    residue = flux_balance - diff_delta_stock
    
    enkf_incr, n_incr_files = get_monthly_enkf_increments(ym)
    
    rows.append({
        'month': m_label,
        'P_ENS_mm': round(p_ens, 2),
        'P_DA_mm': round(p_da, 2),
        'delta_P_mm': round(dp, 2),
        'ET_ENS_mm': round(et_ens, 2),
        'ET_DA_mm': round(et_da, 2),
        'delta_ET_mm': round(det, 2),
        'Qs_ENS_mm': round(qs_ens, 2),
        'Qs_DA_mm': round(qs_da, 2),
        'delta_Qs_mm': round(dqs, 2),
        'Qsb_ENS_mm': round(qsb_ens, 2),
        'Qsb_DA_mm': round(qsb_da, 2),
        'delta_Qsb_mm': round(dqsb, 2),
        'delta_Stock_ENS_mm': round(delta_stock_ens, 2),
        'delta_Stock_DA_mm': round(delta_stock_da, 2),
        'delta_delta_Stock_mm': round(diff_delta_stock, 2),
        'diff_d_SMC_mm': round(diff_d_smc, 2),
        'diff_d_WA_mm': round(diff_d_wa, 2),
        'diff_d_CAN_mm': round(diff_d_can, 2),
        'diff_d_SN_mm': round(diff_d_sn, 2),
        'flux_balance_diff_mm': round(flux_balance, 2),
        'residue_mm': round(residue, 2),
        'EnKF_increment_mm': round(enkf_incr, 2),
        'n_EnKF_events': n_incr_files,
        'unaccounted_discrepancy_mm': round(residue - (-enkf_incr), 2)
    })
    
    prev_rst_ens = curr_rst_ens
    prev_rst_da  = curr_rst_da

df_wb = pd.DataFrame(rows)
out_csv = os.path.join(OUT_DIR, "water_balance_da_minus_ens_monthly.csv")
df_wb.to_csv(out_csv, index=False)
print(f"[SUCCÈS] Bilan d'eau sauvegardé dans : {out_csv}")
print(df_wb[['month', 'delta_P_mm', 'delta_ET_mm', 'delta_Qs_mm', 'delta_Qsb_mm', 'delta_delta_Stock_mm', 'residue_mm', 'EnKF_increment_mm', 'unaccounted_discrepancy_mm']])
