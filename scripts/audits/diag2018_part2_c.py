#!/usr/bin/env python3
"""
diag2018_part2_c.py
Partie 2.c : Censure (E5) — Bilan des observations acceptées DA_nocdf_nowilt vs DA_nocdf,
et impact par texture sur humidité, incréments, ET et Qsb.
Année complète 2018 (Janvier–Décembre) + lignes JJA et Annuel.
"""
import os
import glob
import datetime
import numpy as np
import pandas as pd
import netCDF4 as nc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_e6_clean")
ALT_OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_janmay")
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ALT_OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")
SOILPARM_PATH = os.path.join(BASE_DIR, "data/land_params/noahmp401_parms/SOILPARM.TBL")

# Static data
with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(bool)
    texture_3d = ds.variables["TEXTURE"][:]
    lc_3d = ds.variables["LANDCOVER"][:]
    soiltype = np.argmax(texture_3d, axis=0) + 1
    vegt = np.argmax(lc_3d, axis=0) + 1

is_forest = np.isin(vegt, [1, 2, 3, 4, 5])

smcwlt_table = {}
with open(SOILPARM_PATH, "r") as f:
    in_stas = False
    for line in f:
        if "STAS" in line and not "STAS-RUC" in line:
            in_stas = True
            continue
        if "STAS-RUC" in line:
            break
        if in_stas and line.strip() and line.strip()[0].isdigit():
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 10:
                smcwlt_table[int(parts[0])] = float(parts[9])

smcwlt_grid = np.zeros_like(soiltype, dtype=float)
for cid in smcwlt_table:
    smcwlt_grid[soiltype == cid] = smcwlt_table[cid]

TEXTURE_NAMES = {
    1: "Sand", 2: "Loamy Sand", 3: "Sandy Loam", 4: "Silt Loam", 5: "Silt",
    6: "Loam", 7: "Sandy Clay Loam", 8: "Silty Clay Loam", 9: "Clay Loam",
    10: "Sandy Clay", 11: "Silty Clay", 12: "Clay"
}
NOMINAL_CLAY = {
    1: 3.0, 2: 6.0, 3: 10.0, 4: 13.0, 5: 6.0, 6: 19.0,
    7: 27.0, 8: 34.0, 9: 34.0, 10: 42.0, 11: 47.0, 12: 58.0
}

def read_daobs_file(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

months_tuples = [
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

# -------------------------------------------------------------
# 1. Observation counts: DA_nocdf vs DA_nocdf_nowilt
# -------------------------------------------------------------
obs_summary = []
for m_label, ym, ndays, t_start, t_end in months_tuples:
    ym_dash = m_label
    patt_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output", ym_dash, "DAOBS", ym, "LISDAOBS_*.1gs4r")
    patt_nowilt = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/DAOBS", ym, "LISDAOBS_*.1gs4r")
    
    files_nocdf = sorted(glob.glob(patt_nocdf))
    files_nowilt = sorted(glob.glob(patt_nowilt))
    
    n_raw_tot = 0
    n_acc_nocdf = 0
    n_acc_nowilt = 0
    n_cand_wilt_nocdf = 0
    
    dict_nowilt = {os.path.basename(f): f for f in files_nowilt}
    for fn in files_nocdf:
        bn = os.path.basename(fn)
        if bn not in dict_nowilt:
            continue
        fw = dict_nowilt[bn]
        
        r1_c, r2_c = read_daobs_file(fn)
        r1_w, r2_w = read_daobs_file(fw)
        
        mask = landmask
        v_raw = (r1_c != -9999.0) & mask
        acc_c = (r2_c != -9999.0) & mask
        acc_w = (r2_w != -9999.0) & mask
        
        cand_wilt = (r1_c != -9999.0) & (r2_c == -9999.0) & (r1_c - smcwlt_grid < 0.02) & (~is_forest) & mask
        
        n_raw_tot += int(np.sum(v_raw))
        n_acc_nocdf += int(np.sum(acc_c))
        n_acc_nowilt += int(np.sum(acc_w))
        n_cand_wilt_nocdf += int(np.sum(cand_wilt))
        
    diff_acc = n_acc_nowilt - n_acc_nocdf
    gain_pct = (diff_acc / n_acc_nocdf * 100.0) if n_acc_nocdf > 0 else 0.0
    reconciliation_pct = (diff_acc / n_cand_wilt_nocdf * 100.0) if n_cand_wilt_nocdf > 0 else 0.0
    
    obs_summary.append({
        'month': ym,
        'raw_obs': n_raw_tot,
        'accepted_DA_nocdf': n_acc_nocdf,
        'accepted_DA_nowilt': n_acc_nowilt,
        'uncensored_gain': diff_acc,
        'uncensored_gain_pct': round(gain_pct, 2),
        'predicted_censored_obs': n_cand_wilt_nocdf,
        'reconciliation_match_pct': round(reconciliation_pct, 2)
    })

df_obs = pd.DataFrame(obs_summary)

# JJA line for obs count
jja_obs = df_obs[df_obs['month'].isin(['201806', '201807', '201808'])]
raw_jja = int(jja_obs['raw_obs'].sum())
acc_c_jja = int(jja_obs['accepted_DA_nocdf'].sum())
acc_w_jja = int(jja_obs['accepted_DA_nowilt'].sum())
diff_jja = acc_w_jja - acc_c_jja
gain_pct_jja = (diff_jja / acc_c_jja * 100.0) if acc_c_jja > 0 else 0.0
cand_jja = int(jja_obs['predicted_censored_obs'].sum())
rec_jja = (diff_jja / cand_jja * 100.0) if cand_jja > 0 else 0.0

jja_obs_row = {
    'month': 'JJA',
    'raw_obs': raw_jja,
    'accepted_DA_nocdf': acc_c_jja,
    'accepted_DA_nowilt': acc_w_jja,
    'uncensored_gain': diff_jja,
    'uncensored_gain_pct': round(gain_pct_jja, 2),
    'predicted_censored_obs': cand_jja,
    'reconciliation_match_pct': round(rec_jja, 2)
}

# Annuel line for obs count
raw_ann = int(df_obs['raw_obs'].sum())
acc_c_ann = int(df_obs['accepted_DA_nocdf'].sum())
acc_w_ann = int(df_obs['accepted_DA_nowilt'].sum())
diff_ann = acc_w_ann - acc_c_ann
gain_pct_ann = (diff_ann / acc_c_ann * 100.0) if acc_c_ann > 0 else 0.0
cand_ann = int(df_obs['predicted_censored_obs'].sum())
rec_ann = (diff_ann / cand_ann * 100.0) if cand_ann > 0 else 0.0

ann_obs_row = {
    'month': 'Annuel',
    'raw_obs': raw_ann,
    'accepted_DA_nocdf': acc_c_ann,
    'accepted_DA_nowilt': acc_w_ann,
    'uncensored_gain': diff_ann,
    'uncensored_gain_pct': round(gain_pct_ann, 2),
    'predicted_censored_obs': cand_ann,
    'reconciliation_match_pct': round(rec_ann, 2)
}

df_obs = pd.concat([df_obs, pd.DataFrame([jja_obs_row, ann_obs_row])], ignore_index=True)

out_csv_obs = os.path.join(OUT_DIR, "e5_censorship_obs_count_monthly.csv")
df_obs.to_csv(out_csv_obs, index=False)
df_obs.to_csv(os.path.join(ALT_OUT_DIR, "e5_censorship_obs_count_monthly.csv"), index=False)
print(f"[INFO] Saved {out_csv_obs}")
print(df_obs[['month', 'accepted_DA_nocdf', 'accepted_DA_nowilt', 'uncensored_gain', 'uncensored_gain_pct', 'reconciliation_match_pct']])

# -------------------------------------------------------------
# 2. Monthly and By-Texture Impacts: nowilt vs nocdf and nowilt vs ENS_OPL
# -------------------------------------------------------------
print("[INFO] Computing spatial monthly means and increments across all 12 months...")

rst_ens_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL")
rst_nowilt_dir = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/SURFACEMODEL")
rst_da_base = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020")

texture_rows = []

def get_mean_grids(flist, ndays):
    sm1_s = 0.0
    smcol_s = 0.0
    evap_s = 0.0
    qsb_s = 0.0
    c = 0
    for f in flist:
        with nc.Dataset(f) as ds:
            sm = ds.variables["SoilMoist_tavg"][:].squeeze()
            ev = ds.variables["Evap_tavg"][:].squeeze() * 86400.0
            qb = ds.variables["Qsb_tavg"][:].squeeze() * 86400.0
            
            sm1_s += sm[0]
            smcol = (0.1*sm[0] + 0.3*sm[1] + 0.6*sm[2] + 1.0*sm[3]) / 2.0
            smcol_s += smcol
            evap_s += ev
            qsb_s += qb
            c += 1
    return sm1_s / c, smcol_s / c, (evap_s / c) * ndays, (qsb_s / c) * ndays

def get_incr_grids(flist):
    inc1_s = 0.0
    inccol_s = 0.0
    c = 0
    for f in flist:
        with nc.Dataset(f) as ds:
            i1 = ds.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
            i2 = ds.variables["anlys_incr_Soil Moisture Layer 2_01"][:].squeeze()
            i3 = ds.variables["anlys_incr_Soil Moisture Layer 3_01"][:].squeeze()
            i4 = ds.variables["anlys_incr_Soil Moisture Layer 4_01"][:].squeeze()
            
            inc1_s += i1
            inccol = (0.1*i1 + 0.3*i2 + 0.6*i3 + 1.0*i4) / 2.0
            inccol_s += inccol
            c += 1
    return (inc1_s / c, inccol_s / c) if c > 0 else (np.zeros((121, 181)), np.zeros((121, 181)))

for m_label, ym, ndays, t_start, t_end in months_tuples:
    print(f"[INFO] Texture analysis for {m_label}...")
    start_dt = datetime.datetime.strptime(t_start[:8], "%Y%m%d")
    days_dt = [start_dt + datetime.timedelta(days=i) for i in range(ndays)]
    
    files_ens, files_nowilt, files_nocdf = [], [], []
    for d in days_dt:
        d_next = d + datetime.timedelta(days=1)
        ym_next = d_next.strftime("%Y%m")
        d_next_str = d_next.strftime("%Y%m%d")
        
        f_ens = os.path.join(rst_ens_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_ens):
            f_ens = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        files_ens.append(f_ens)
        
        f_nowilt = os.path.join(rst_nowilt_dir, ym_next, f"LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_nowilt):
            f_nowilt = os.path.join(BASE_DIR, f"experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/_partial_201806_hang/SURFACEMODEL_{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        files_nowilt.append(f_nowilt)
        
        f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym_next}/LIS_HIST_{d_next_str}0000.d01.nc")
        if not os.path.exists(f_da):
            f_da = os.path.join(rst_da_base, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_HIST_{d_next_str}0000.d01.nc")
        files_nocdf.append(f_da)
        
    sm1_w, smcol_w, et_w, qsb_w = get_mean_grids(files_nowilt, ndays)
    sm1_c, smcol_c, et_c, qsb_c = get_mean_grids(files_nocdf, ndays)
    sm1_e, smcol_e, et_e, qsb_e = get_mean_grids(files_ens, ndays)
    
    # 2. Increments from EnKF
    p_incr_nowilt = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/EnKF", ym, "*_incr.*.nc")
    p_incr_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output", m_label, "EnKF", ym, "*_incr.*.nc")
    
    f_incr_w = sorted(glob.glob(p_incr_nowilt))
    f_incr_c = sorted(glob.glob(p_incr_nocdf))
    
    incr1_w, incrcol_w = get_incr_grids(f_incr_w)
    incr1_c, incrcol_c = get_incr_grids(f_incr_c)
    
    for tid in range(1, 13):
        tmask = (soiltype == tid) & landmask
        n_pix = int(np.sum(tmask))
        if n_pix < 10:
            continue
            
        wlt_mean = float(np.mean(smcwlt_grid[tmask]))
        clay_pct = NOMINAL_CLAY.get(tid, np.nan)
        
        # nowilt - nocdf
        d_sm1_w_c = float(np.mean((sm1_w - sm1_c)[tmask]))
        d_smcol_w_c = float(np.mean((smcol_w - smcol_c)[tmask]))
        d_et_w_c = float(np.mean((et_w - et_c)[tmask]))
        d_qsb_w_c = float(np.mean((qsb_w - qsb_c)[tmask]))
        
        # nowilt - ens
        d_sm1_w_e = float(np.mean((sm1_w - sm1_e)[tmask]))
        d_smcol_w_e = float(np.mean((smcol_w - smcol_e)[tmask]))
        d_et_w_e = float(np.mean((et_w - et_e)[tmask]))
        d_qsb_w_e = float(np.mean((qsb_w - qsb_e)[tmask]))
        
        # Increments
        inc1_w_mean = float(np.mean(incr1_w[tmask]))
        inc1_c_mean = float(np.mean(incr1_c[tmask]))
        inccol_w_mean = float(np.mean(incrcol_w[tmask]))
        inccol_c_mean = float(np.mean(incrcol_c[tmask]))
        
        texture_rows.append({
            'month': ym,
            'soil_id': tid,
            'texture_name': TEXTURE_NAMES[tid],
            'clay_pct': clay_pct,
            'smcwlt': round(wlt_mean, 3),
            'n_pixels': n_pix,
            
            # nowilt - nocdf
            'delta_SM1_nowilt_minus_nocdf': round(d_sm1_w_c, 5),
            'delta_SMcol_nowilt_minus_nocdf': round(d_smcol_w_c, 5),
            'delta_ET_nowilt_minus_nocdf_mm': round(d_et_w_c, 2),
            'delta_Qsb_nowilt_minus_nocdf_mm': round(d_qsb_w_c, 2),
            
            # nowilt - ENS_OPL
            'delta_SM1_nowilt_minus_ENS': round(d_sm1_w_e, 5),
            'delta_SMcol_nowilt_minus_ENS': round(d_smcol_w_e, 5),
            'delta_ET_nowilt_minus_ENS_mm': round(d_et_w_e, 2),
            'delta_Qsb_nowilt_minus_ENS_mm': round(d_qsb_w_e, 2),
            
            # Increments
            'incr1_nowilt': round(inc1_w_mean, 6),
            'incr1_nocdf': round(inc1_c_mean, 6),
            'delta_incr1_nowilt_minus_nocdf': round(inc1_w_mean - inc1_c_mean, 6),
            'incrcol_nowilt': round(inccol_w_mean, 6),
            'incrcol_nocdf': round(inccol_c_mean, 6),
        })

df_tex = pd.DataFrame(texture_rows)

# JJA and Annuel rows per texture
jja_tex_rows = []
ann_tex_rows = []

for tid in sorted(df_tex['soil_id'].unique()):
    sub_all = df_tex[df_tex['soil_id'] == tid]
    sub_jja = df_tex[(df_tex['soil_id'] == tid) & (df_tex['month'].isin(['201806', '201807', '201808']))]
    
    tname = sub_all['texture_name'].iloc[0]
    cpct = sub_all['clay_pct'].iloc[0]
    wlt = sub_all['smcwlt'].iloc[0]
    npix = sub_all['n_pixels'].iloc[0]
    
    # JJA
    jja_tex_rows.append({
        'month': 'JJA',
        'soil_id': tid,
        'texture_name': tname,
        'clay_pct': cpct,
        'smcwlt': wlt,
        'n_pixels': npix,
        'delta_SM1_nowilt_minus_nocdf': round(sub_jja['delta_SM1_nowilt_minus_nocdf'].mean(), 5),
        'delta_SMcol_nowilt_minus_nocdf': round(sub_jja['delta_SMcol_nowilt_minus_nocdf'].mean(), 5),
        'delta_ET_nowilt_minus_nocdf_mm': round(sub_jja['delta_ET_nowilt_minus_nocdf_mm'].sum(), 2),
        'delta_Qsb_nowilt_minus_nocdf_mm': round(sub_jja['delta_Qsb_nowilt_minus_nocdf_mm'].sum(), 2),
        'delta_SM1_nowilt_minus_ENS': round(sub_jja['delta_SM1_nowilt_minus_ENS'].mean(), 5),
        'delta_SMcol_nowilt_minus_ENS': round(sub_jja['delta_SMcol_nowilt_minus_ENS'].mean(), 5),
        'delta_ET_nowilt_minus_ENS_mm': round(sub_jja['delta_ET_nowilt_minus_ENS_mm'].sum(), 2),
        'delta_Qsb_nowilt_minus_ENS_mm': round(sub_jja['delta_Qsb_nowilt_minus_ENS_mm'].sum(), 2),
        'incr1_nowilt': round(sub_jja['incr1_nowilt'].mean(), 6),
        'incr1_nocdf': round(sub_jja['incr1_nocdf'].mean(), 6),
        'delta_incr1_nowilt_minus_nocdf': round(sub_jja['incr1_nowilt'].mean() - sub_jja['incr1_nocdf'].mean(), 6),
        'incrcol_nowilt': round(sub_jja['incrcol_nowilt'].mean(), 6),
        'incrcol_nocdf': round(sub_jja['incrcol_nocdf'].mean(), 6),
    })
    
    # Annuel
    ann_tex_rows.append({
        'month': 'Annuel',
        'soil_id': tid,
        'texture_name': tname,
        'clay_pct': cpct,
        'smcwlt': wlt,
        'n_pixels': npix,
        'delta_SM1_nowilt_minus_nocdf': round(sub_all['delta_SM1_nowilt_minus_nocdf'].mean(), 5),
        'delta_SMcol_nowilt_minus_nocdf': round(sub_all['delta_SMcol_nowilt_minus_nocdf'].mean(), 5),
        'delta_ET_nowilt_minus_nocdf_mm': round(sub_all['delta_ET_nowilt_minus_nocdf_mm'].sum(), 2),
        'delta_Qsb_nowilt_minus_nocdf_mm': round(sub_all['delta_Qsb_nowilt_minus_nocdf_mm'].sum(), 2),
        'delta_SM1_nowilt_minus_ENS': round(sub_all['delta_SM1_nowilt_minus_ENS'].mean(), 5),
        'delta_SMcol_nowilt_minus_ENS': round(sub_all['delta_SMcol_nowilt_minus_ENS'].mean(), 5),
        'delta_ET_nowilt_minus_ENS_mm': round(sub_all['delta_ET_nowilt_minus_ENS_mm'].sum(), 2),
        'delta_Qsb_nowilt_minus_ENS_mm': round(sub_all['delta_Qsb_nowilt_minus_ENS_mm'].sum(), 2),
        'incr1_nowilt': round(sub_all['incr1_nowilt'].mean(), 6),
        'incr1_nocdf': round(sub_all['incr1_nocdf'].mean(), 6),
        'delta_incr1_nowilt_minus_nocdf': round(sub_all['incr1_nowilt'].mean() - sub_all['incr1_nocdf'].mean(), 6),
        'incrcol_nowilt': round(sub_all['incrcol_nowilt'].mean(), 6),
        'incrcol_nocdf': round(sub_all['incrcol_nocdf'].mean(), 6),
    })

df_tex = pd.concat([df_tex, pd.DataFrame(jja_tex_rows), pd.DataFrame(ann_tex_rows)], ignore_index=True)

out_csv_tex = os.path.join(OUT_DIR, "e5_nowilt_impact_by_texture.csv")
df_tex.to_csv(out_csv_tex, index=False)
df_tex.to_csv(os.path.join(ALT_OUT_DIR, "e5_nowilt_impact_by_texture.csv"), index=False)
print(f"[INFO] Saved {out_csv_tex}")
