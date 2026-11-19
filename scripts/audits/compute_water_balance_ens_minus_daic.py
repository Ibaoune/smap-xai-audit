#!/usr/bin/env python3
"""
compute_water_balance_ens_minus_daic.py

Calcule le bilan d'eau mensuel complet pour ENS_OPL - OL_DAIC (effet d'ensemble pur)
pour les 12 mois (janvier-décembre 2018).
Stock total = 4 couches SMC + aquifere (WA) + canopee (CANWAT) + neige (SNEQV)
Residu = Delta_P - Delta_ET - Delta_Qs - Delta_Qsb - Delta(Delta_Stock)
Avec P_OL_DAIC extrait directement de OPL_noirr (meme forcage IMERG deterministe).
+ Ligne JJA et ligne de totaux annuels
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

dz = np.array([0.1, 0.3, 0.6, 1.0], dtype=np.float32) * 1000.0  # mm

months = [
    ("2018-01", "201801", 31, "201801010000", "201801312345"),
    ("2018-02", "201802", 28, "201802010000", "201802282345"),
    ("2018-03", "201803", 31, "201803010000", "201803312345"),
    ("2018-04", "201804", 30, "201804010000", "201804302345"),
    ("2018-05", "201805", 31, "201805010000", "201805312345"),
    ("2018-06", "201806", 30, "201806010000", "201806302345"),
    ("2018-07", "201807", 31, "201807010000", "201807312345"),
    ("2018-08", "201808", 31, "201808010000", "201808312345"),
    ("2018-09", "201809", 30, "201809010000", "201809302345"),
    ("2018-10", "201810", 31, "201810010000", "201810312345"),
    ("2018-11", "201811", 30, "201811010000", "201811302345"),
    ("2018-12", "201812", 31, "201812010000", "201812312345"),
]

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

def get_monthly_fluxes_ens(flist):
    p_tot, et_tot, qs_tot, qsb_tot = 0.0, 0.0, 0.0, 0.0
    for f in flist:
        with nc.Dataset(f) as ds:
            p_tot += float(np.mean(ds.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
            et_tot += float(np.mean(ds.variables['Evap_tavg'][:].squeeze()[landmask] * 86400.0))
            qs_tot += float(np.mean(ds.variables['Qs_tavg'][:].squeeze()[landmask] * 86400.0))
            qsb_tot += float(np.mean(ds.variables['Qsb_tavg'][:].squeeze()[landmask] * 86400.0))
    return p_tot, et_tot, qs_tot, qsb_tot

def get_monthly_fluxes_daic(flist):
    et_tot, qs_tot, qsb_tot = 0.0, 0.0, 0.0
    for f in flist:
        with nc.Dataset(f) as ds:
            et_tot += float(np.mean(ds.variables['Evap_tavg'][:].squeeze()[landmask] * 86400.0))
            qs_tot += float(np.mean(ds.variables['Qs_tavg'][:].squeeze()[landmask] * 86400.0))
            qsb_tot += float(np.mean(ds.variables['Qsb_tavg'][:].squeeze()[landmask] * 86400.0))
    return et_tot, qs_tot, qsb_tot

def get_monthly_precip_opl_noirr(m_label, ym, n_days, t_start):
    opl_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020")
    dt = datetime.datetime.strptime(t_start[:8], "%Y%m%d")
    p_tot = 0.0
    for i in range(n_days):
        d_next = dt + datetime.timedelta(days=i+1)
        ym_next = d_next.strftime("%Y%m")
        fn = f"LIS_HIST_{d_next.strftime('%Y%m%d')}0000.d01.nc"
        p1 = os.path.join(opl_dir, f"output/{m_label}/SURFACEMODEL/{ym_next}/{fn}")
        p2 = os.path.join(opl_dir, f"output/{m_label}/SURFACEMODEL/{ym}/{fn}")
        fpath = p1 if os.path.exists(p1) else p2
        with nc.Dataset(fpath) as ds:
            p_tot += float(np.mean(ds.variables['TotalPrecip_tavg'][:].squeeze()[landmask] * 86400.0))
    return p_tot

rst_ens_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL")
rst_da_base = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020")
daic_dir    = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_DAIC_2018")

prev_rst_ens  = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
prev_rst_daic = os.path.join(daic_dir, "restart/LIS_RST_NOAHMP401_201801010000.d01.nc")

rows = []

for m_label, ym, n_days, t_start, t_end in months:
    curr_rst_ens  = os.path.join(rst_ens_dir, ym, f"LIS_RST_NOAHMP401_{t_end}.d01.nc")
    curr_rst_daic = os.path.join(daic_dir, f"output/SURFACEMODEL/{ym}/LIS_RST_NOAHMP401_{t_end}.d01.nc")
    
    if not os.path.exists(curr_rst_daic):
        print(f"[INFO] Le restart de fin de mois pour {m_label} n'est pas encore disponible dans OL_DAIC. Arret.")
        break
        
    start_dt = datetime.datetime.strptime(t_start[:8], "%Y%m%d")
    days_dt = [start_dt + datetime.timedelta(days=i) for i in range(n_days)]
    hist_ens = []
    hist_daic = []
    all_daic_hist_exist = True
    
    for d in days_dt:
        d_next = d + datetime.timedelta(days=1)
        ym_next = d_next.strftime("%Y%m")
        d_next_str = d_next.strftime("%Y%m%d")
        
        f_ens = os.path.join(rst_ens_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_ens):
            f_ens_hang = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
            if os.path.exists(f_ens_hang):
                f_ens = f_ens_hang
        hist_ens.append(f_ens)
        
        f_daic = os.path.join(daic_dir, f"output/SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_daic):
            all_daic_hist_exist = False
        hist_daic.append(f_daic)
        
    if not all_daic_hist_exist:
        print(f"[INFO] Certains fichiers journaliers de {m_label} manquent encore pour OL_DAIC. Arret.")
        break
        
    print(f"[INFO] Calcul du bilan d'eau pour {m_label} (ENS_OPL vs OL_DAIC)...")
    
    s_start_ens  = read_storage_ens(prev_rst_ens)
    s_end_ens    = read_storage_ens(curr_rst_ens)
    s_start_daic = read_storage_1m(prev_rst_daic)
    s_end_daic   = read_storage_1m(curr_rst_daic)
    
    delta_stock_ens  = s_end_ens['tot'] - s_start_ens['tot']
    delta_stock_daic = s_end_daic['tot'] - s_start_daic['tot']
    diff_delta_stock = delta_stock_ens - delta_stock_daic
    
    diff_d_smc = (s_end_ens['smc'] - s_start_ens['smc']) - (s_end_daic['smc'] - s_start_daic['smc'])
    diff_d_wa  = (s_end_ens['wa'] - s_start_ens['wa']) - (s_end_daic['wa'] - s_start_daic['wa'])
    diff_d_can = (s_end_ens['can'] - s_start_ens['can']) - (s_end_daic['can'] - s_start_daic['can'])
    diff_d_sn  = (s_end_ens['sn'] - s_start_ens['sn']) - (s_end_daic['sn'] - s_start_daic['sn'])
    
    p_ens, et_ens, qs_ens, qsb_ens = get_monthly_fluxes_ens(hist_ens)
    et_daic, qs_daic, qsb_daic     = get_monthly_fluxes_daic(hist_daic)
    p_daic = get_monthly_precip_opl_noirr(m_label, ym, n_days, t_start)
    
    dp   = p_ens - p_daic
    det  = et_ens - et_daic
    dqs  = qs_ens - qs_daic
    dqsb = qsb_ens - qsb_daic
    
    flux_balance = dp - det - dqs - dqsb
    residue = flux_balance - diff_delta_stock
    
    rows.append({
        'month': m_label,
        'P_ENS_mm': round(p_ens, 2),
        'P_OL_DAIC_mm': round(p_daic, 2),
        'delta_P_mm': round(dp, 2),
        'ET_ENS_mm': round(et_ens, 2),
        'ET_OL_DAIC_mm': round(et_daic, 2),
        'delta_ET_mm': round(det, 2),
        'Qs_ENS_mm': round(qs_ens, 2),
        'Qs_OL_DAIC_mm': round(qs_daic, 2),
        'delta_Qs_mm': round(dqs, 2),
        'Qsb_ENS_mm': round(qsb_ens, 2),
        'Qsb_OL_DAIC_mm': round(qsb_daic, 2),
        'delta_Qsb_mm': round(dqsb, 2),
        'delta_Stock_ENS_mm': round(delta_stock_ens, 2),
        'delta_Stock_OL_DAIC_mm': round(delta_stock_daic, 2),
        'delta_delta_Stock_mm': round(diff_delta_stock, 2),
        'diff_d_SMC_mm': round(diff_d_smc, 2),
        'diff_d_WA_mm': round(diff_d_wa, 2),
        'diff_d_CAN_mm': round(diff_d_can, 2),
        'diff_d_SN_mm': round(diff_d_sn, 2),
        'flux_balance_diff_mm': round(flux_balance, 2),
        'residue_mm': round(residue, 2)
    })
    
    prev_rst_ens  = curr_rst_ens
    prev_rst_daic = curr_rst_daic

if rows:
    df_ens_daic = pd.DataFrame(rows)
    
    # JJA line
    jja_rows = df_ens_daic[df_ens_daic['month'].isin(['2018-06', '2018-07', '2018-08'])]
    jja_entry = {'month': 'JJA'}
    for col in df_ens_daic.columns:
        if col != 'month':
            jja_entry[col] = round(jja_rows[col].sum(), 2)
            
    # Annuel line
    ann_entry = {'month': 'Annuel'}
    for col in df_ens_daic.columns:
        if col != 'month':
            ann_entry[col] = round(df_ens_daic[col].sum(), 2)
            
    df_ens_daic = pd.concat([df_ens_daic, pd.DataFrame([jja_entry, ann_entry])], ignore_index=True)
    
    out_csv = os.path.join(OUT_DIR, "water_balance_ens_minus_daic_monthly.csv")
    df_ens_daic.to_csv(out_csv, index=False)
    print(f"[SUCCES] Bilan d'eau ENS_OPL - OL_DAIC sauvegarde dans : {out_csv}")
    print(df_ens_daic[['month', 'P_ENS_mm', 'P_OL_DAIC_mm', 'delta_P_mm', 'delta_ET_mm', 'delta_Qs_mm', 'delta_Qsb_mm', 'delta_delta_Stock_mm', 'residue_mm']])
