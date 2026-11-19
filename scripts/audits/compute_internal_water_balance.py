#!/usr/bin/env python3
"""
compute_internal_water_balance.py

Calcule le bilan d'eau interne de chaque simulation seule, par mois (janvier-décembre 2018) :
Bilan = P - ET - Qs - Qsb - Delta_Stock
Pour :
1. ENS_OPL_2018 (moyenne d'ensemble)
2. DA_nocdf_noirr_2016_2020 (moyenne d'ensemble, avec assimilation EnKF)
3. DA_nocdf_nowilt_2018 (moyenne d'ensemble, assimilation EnKF sans filtre flétrissement)
4. OL_DAIC_2018 (run 1 membre, avec P_OPL_noirr déterministe)
+ Incréments EnKF archivés pour DA_nocdf et DA_nocdf_nowilt
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

dz = np.array([0.1, 0.3, 0.6, 1.0], dtype=np.float32) * 1000.0 # mm

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

def get_monthly_fluxes_full(flist):
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

def get_monthly_enkf_increments_da(ym):
    d_part = f"{ym[:4]}-{ym[4:]}"
    pat = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output/{d_part}/EnKF/{ym}/LIS_DA_EnKF_*_incr.a01.d01.nc")
    flist = sorted(glob.glob(pat))
    if not flist:
        return 0.0
    total_incr = np.zeros(np.sum(landmask), dtype=float)
    for f in flist:
        with nc.Dataset(f) as ds:
            i1 = ds.variables['anlys_incr_Soil Moisture Layer 1_01'][:].squeeze()[landmask]
            i2 = ds.variables['anlys_incr_Soil Moisture Layer 2_01'][:].squeeze()[landmask]
            i3 = ds.variables['anlys_incr_Soil Moisture Layer 3_01'][:].squeeze()[landmask]
            i4 = ds.variables['anlys_incr_Soil Moisture Layer 4_01'][:].squeeze()[landmask]
            total_incr += (dz[0]*i1 + dz[1]*i2 + dz[2]*i3 + dz[3]*i4)
    return float(np.mean(total_incr))

def get_monthly_enkf_increments_nowilt(ym):
    pat = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/EnKF/{ym}/LIS_DA_EnKF_*_incr.a01.d01.nc")
    flist = sorted(glob.glob(pat))
    if not flist:
        return 0.0
    total_incr = np.zeros(np.sum(landmask), dtype=float)
    for f in flist:
        with nc.Dataset(f) as ds:
            i1 = ds.variables['anlys_incr_Soil Moisture Layer 1_01'][:].squeeze()[landmask]
            i2 = ds.variables['anlys_incr_Soil Moisture Layer 2_01'][:].squeeze()[landmask]
            i3 = ds.variables['anlys_incr_Soil Moisture Layer 3_01'][:].squeeze()[landmask]
            i4 = ds.variables['anlys_incr_Soil Moisture Layer 4_01'][:].squeeze()[landmask]
            total_incr += (dz[0]*i1 + dz[1]*i2 + dz[2]*i3 + dz[3]*i4)
    return float(np.mean(total_incr))

rst_ens_dir    = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL")
rst_nowilt_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/SURFACEMODEL")
rst_da_base    = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020")
daic_dir       = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_DAIC_2018")

prev_rst_ens    = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
prev_rst_da     = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
prev_rst_nowilt = os.path.join(rst_da_base, "restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
prev_rst_daic   = os.path.join(daic_dir, "restart/LIS_RST_NOAHMP401_201801010000.d01.nc")

rows = []

for m_label, ym, n_days, t_start, t_end in months:
    print(f"[INFO] Traitement du bilan interne pour {m_label}...")
    curr_rst_ens    = os.path.join(rst_ens_dir, ym, f"LIS_RST_NOAHMP401_{t_end}.d01.nc")
    curr_rst_da     = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_RST_NOAHMP401_{t_end}.d01.nc")
    curr_rst_nowilt = os.path.join(rst_nowilt_dir, ym, f"LIS_RST_NOAHMP401_{t_end}.d01.nc")
    curr_rst_daic   = os.path.join(daic_dir, f"output/SURFACEMODEL/{ym}/LIS_RST_NOAHMP401_{t_end}.d01.nc")
    
    start_dt = datetime.datetime.strptime(t_start[:8], "%Y%m%d")
    days_dt = [start_dt + datetime.timedelta(days=i) for i in range(n_days)]
    hist_ens = []
    hist_da  = []
    hist_nowilt = []
    hist_daic = []
    has_daic = os.path.exists(curr_rst_daic)
    
    for d in days_dt:
        d_next = d + datetime.timedelta(days=1)
        ym_next = d_next.strftime("%Y%m")
        d_next_str = d_next.strftime("%Y%m%d")
        
        # ENS_OPL
        f_ens = os.path.join(rst_ens_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_ens):
            f_ens_hang = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
            if os.path.exists(f_ens_hang):
                f_ens = f_ens_hang
        hist_ens.append(f_ens)
        
        # DA_nocdf
        f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_da):
            f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_HIST_{d_next_str}0000.d01.nc")
        hist_da.append(f_da)
        
        # DA_nocdf_nowilt
        f_nowilt = os.path.join(rst_nowilt_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_nowilt):
            f_nowilt_hang = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
            if os.path.exists(f_nowilt_hang):
                f_nowilt = f_nowilt_hang
        hist_nowilt.append(f_nowilt)
        
        # OL_DAIC
        if has_daic:
            f_daic = os.path.join(daic_dir, f"output/SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
            if not os.path.exists(f_daic):
                has_daic = False
            hist_daic.append(f_daic)
            
    # 1. ENS_OPL
    s_start_ens = read_storage_ens(prev_rst_ens)
    s_end_ens   = read_storage_ens(curr_rst_ens)
    d_stock_ens = s_end_ens['tot'] - s_start_ens['tot']
    p_ens, et_ens, qs_ens, qsb_ens = get_monthly_fluxes_full(hist_ens)
    res_ens = (p_ens - et_ens - qs_ens - qsb_ens) - d_stock_ens
    
    # 2. DA_nocdf
    s_start_da = read_storage_ens(prev_rst_da)
    s_end_da   = read_storage_ens(curr_rst_da)
    d_stock_da = s_end_da['tot'] - s_start_da['tot']
    p_da, et_da, qs_da, qsb_da = get_monthly_fluxes_full(hist_da)
    res_da = (p_da - et_da - qs_da - qsb_da) - d_stock_da
    incr_enkf_da = get_monthly_enkf_increments_da(ym)
    
    # 3. DA_nocdf_nowilt
    s_start_nowilt = read_storage_ens(prev_rst_nowilt)
    s_end_nowilt   = read_storage_ens(curr_rst_nowilt)
    d_stock_nowilt = s_end_nowilt['tot'] - s_start_nowilt['tot']
    p_nowilt, et_nowilt, qs_nowilt, qsb_nowilt = get_monthly_fluxes_full(hist_nowilt)
    res_nowilt = (p_nowilt - et_nowilt - qs_nowilt - qsb_nowilt) - d_stock_nowilt
    incr_enkf_nowilt = get_monthly_enkf_increments_nowilt(ym)
    
    # 4. OL_DAIC
    p_opl = get_monthly_precip_opl_noirr(m_label, ym, n_days, t_start)
    if has_daic:
        s_start_daic = read_storage_1m(prev_rst_daic)
        s_end_daic   = read_storage_1m(curr_rst_daic)
        d_stock_daic = s_end_daic['tot'] - s_start_daic['tot']
        et_daic, qs_daic, qsb_daic = get_monthly_fluxes_daic(hist_daic)
        res_daic = (p_opl - et_daic - qs_daic - qsb_daic) - d_stock_daic
        prev_rst_daic = curr_rst_daic
    else:
        d_stock_daic = np.nan
        et_daic, qs_daic, qsb_daic, res_daic = np.nan, np.nan, np.nan, np.nan
        
    rows.append({
        'month': m_label,
        'P_ENS': round(p_ens, 2),
        'ET_ENS': round(et_ens, 2),
        'Qs_ENS': round(qs_ens, 2),
        'Qsb_ENS': round(qsb_ens, 2),
        'dStock_ENS': round(d_stock_ens, 2),
        'Residu_ENS': round(res_ens, 2),
        'P_DA': round(p_da, 2),
        'ET_DA': round(et_da, 2),
        'Qs_DA': round(qs_da, 2),
        'Qsb_DA': round(qsb_da, 2),
        'dStock_DA': round(d_stock_da, 2),
        'Residu_DA': round(res_da, 2),
        'Incr_EnKF': round(incr_enkf_da, 2),
        'P_DA_nowilt': round(p_nowilt, 2),
        'ET_DA_nowilt': round(et_nowilt, 2),
        'Qs_DA_nowilt': round(qs_nowilt, 2),
        'Qsb_DA_nowilt': round(qsb_nowilt, 2),
        'dStock_DA_nowilt': round(d_stock_nowilt, 2),
        'Residu_DA_nowilt': round(res_nowilt, 2),
        'Incr_EnKF_nowilt': round(incr_enkf_nowilt, 2),
        'P_OL_DAIC': round(p_opl, 2),
        'ET_OL_DAIC': round(et_daic, 2) if not np.isnan(et_daic) else np.nan,
        'Qs_OL_DAIC': round(qs_daic, 2) if not np.isnan(qs_daic) else np.nan,
        'Qsb_OL_DAIC': round(qsb_daic, 2) if not np.isnan(qsb_daic) else np.nan,
        'dStock_OL_DAIC': round(d_stock_daic, 2) if not np.isnan(d_stock_daic) else np.nan,
        'Residu_OL_DAIC': round(res_daic, 2) if not np.isnan(res_daic) else np.nan
    })
    
    prev_rst_ens    = curr_rst_ens
    prev_rst_da     = curr_rst_da
    prev_rst_nowilt = curr_rst_nowilt

df_res = pd.DataFrame(rows)

# JJA line (months 2018-06, 2018-07, 2018-08)
jja_rows = df_res[df_res['month'].isin(['2018-06', '2018-07', '2018-08'])]
jja_entry = {'month': 'JJA'}
for col in df_res.columns:
    if col != 'month':
        jja_entry[col] = round(jja_rows[col].sum(), 2)

# Annuel line (all 12 months)
ann_entry = {'month': 'Annuel'}
for col in df_res.columns:
    if col != 'month':
        ann_entry[col] = round(df_res[col].sum(), 2)

df_res = pd.concat([df_res, pd.DataFrame([jja_entry, ann_entry])], ignore_index=True)

out_csv = os.path.join(OUT_DIR, "internal_water_balance_monthly.csv")
df_res.to_csv(out_csv, index=False)
print(f"[SUCCES] Bilan interne sauvegarde dans : {out_csv}")
print(df_res[['month', 'Residu_ENS', 'Residu_DA', 'Incr_EnKF', 'Residu_DA_nowilt', 'Incr_EnKF_nowilt', 'Residu_OL_DAIC']])
