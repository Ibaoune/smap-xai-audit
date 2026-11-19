#!/usr/bin/env python3
"""
diag2018_part2_c.py
Partie 2.c : Censure (E5) — Bilan des observations acceptées DA_nocdf_nowilt vs DA_nocdf,
et impact par texture sur humidité, incréments, ET et Qsb.
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

BASE_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_janmay")
FIG_DIR = os.path.join(OUT_DIR, "figures")
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

months = [f"2018{m:02d}" for m in range(1, 6)]
days_in_month = {'201801': 31, '201802': 28, '201803': 31, '201804': 30, '201805': 31}

# -------------------------------------------------------------
# 1. Observation counts: DA_nocdf vs DA_nocdf_nowilt
# -------------------------------------------------------------
obs_summary = []
for ym in months:
    ym_dash = f"{ym[:4]}-{ym[4:6]}"
    patt_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output", ym_dash, "DAOBS", ym, "LISDAOBS_*.1gs4r")
    patt_nowilt = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/DAOBS", ym, "LISDAOBS_*.1gs4r")
    
    files_nocdf = sorted(glob.glob(patt_nocdf))
    files_nowilt = sorted(glob.glob(patt_nowilt))
    
    n_raw_tot = 0
    n_acc_nocdf = 0
    n_acc_nowilt = 0
    n_cand_wilt_nocdf = 0
    
    # Process paired files
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
out_csv_obs = os.path.join(OUT_DIR, "e5_censorship_obs_count_monthly.csv")
df_obs.to_csv(out_csv_obs, index=False)
print(f"[INFO] Saved {out_csv_obs}")
print(df_obs[['month', 'accepted_DA_nocdf', 'accepted_DA_nowilt', 'uncensored_gain', 'uncensored_gain_pct', 'reconciliation_match_pct']])

# -------------------------------------------------------------
# 2. Monthly and By-Texture Impacts: nowilt vs nocdf and nowilt vs ENS_OPL
# -------------------------------------------------------------
# We compute monthly mean grids for:
# - nowilt (SURFACEMODEL + EnKF)
# - nocdf (SURFACEMODEL + EnKF)
# - ens_opl (SURFACEMODEL)
print("[INFO] Computing spatial monthly means and increments...")

texture_rows = []

for ym in months:
    ym_dash = f"{ym[:4]}-{ym[4:6]}"
    ndays = days_in_month[ym]
    
    # 1. Surface outputs
    p_nowilt = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/SURFACEMODEL", ym, "LIS_HIST_*.nc")
    p_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output", ym_dash, "SURFACEMODEL", ym, "LIS_HIST_*.nc")
    p_ens = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL", ym, "LIS_HIST_*.nc")
    
    files_nowilt = sorted(glob.glob(p_nowilt))
    files_nocdf = sorted(glob.glob(p_nocdf))
    files_ens = sorted(glob.glob(p_ens))
    
    def get_mean_grids(flist):
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
        
    sm1_w, smcol_w, et_w, qsb_w = get_mean_grids(files_nowilt)
    sm1_c, smcol_c, et_c, qsb_c = get_mean_grids(files_nocdf)
    sm1_e, smcol_e, et_e, qsb_e = get_mean_grids(files_ens)
    
    # 2. Increments from EnKF
    p_incr_nowilt = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/DA_nocdf_nowilt_2018/output/EnKF", ym, "*_incr.*.nc")
    p_incr_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output", ym_dash, "EnKF", ym, "*_incr.*.nc")
    
    f_incr_w = sorted(glob.glob(p_incr_nowilt))
    f_incr_c = sorted(glob.glob(p_incr_nocdf))
    
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
        
    incr1_w, incrcol_w = get_incr_grids(f_incr_w)
    incr1_c, incrcol_c = get_incr_grids(f_incr_c)
    
    # Texture breakdown
    for tid in range(1, 13):
        tmask = (soiltype == tid) & landmask
        n_pix = int(np.sum(tmask))
        if n_pix < 10:
            continue
            
        wlt_mean = float(np.mean(smcwlt_grid[tmask]))
        clay_pct = NOMINAL_CLAY.get(tid, np.nan)
        
        # Means
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
            
            # nowilt - nocdf (pure uncensoring impact)
            'delta_SM1_nowilt_minus_nocdf': round(d_sm1_w_c, 5),
            'delta_SMcol_nowilt_minus_nocdf': round(d_smcol_w_c, 5),
            'delta_ET_nowilt_minus_nocdf_mm': round(d_et_w_c, 2),
            'delta_Qsb_nowilt_minus_nocdf_mm': round(d_qsb_w_c, 2),
            
            # nowilt - ENS_OPL (pure DA impact)
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
out_csv_tex = os.path.join(OUT_DIR, "e5_nowilt_impact_by_texture.csv")
df_tex.to_csv(out_csv_tex, index=False)
print(f"[INFO] Saved {out_csv_tex}")

# -------------------------------------------------------------
# Figures for Part 2.c
# -------------------------------------------------------------
# Figure 1: Monthly Accepted Observations and Uncensoring Gain
plt.figure(figsize=(10, 5))
x = np.arange(len(months))
width = 0.35

plt.bar(x - width/2, df_obs['accepted_DA_nocdf'].to_numpy(), width, label='DA_nocdf (standard QC avec filtre flétrissement)', color='#3182bd')
plt.bar(x + width/2, df_obs['accepted_DA_nowilt'].to_numpy(), width, label='DA_nocdf_nowilt (QC sans filtre flétrissement)', color='#de2d26')

for i in range(len(months)):
    gain = df_obs['uncensored_gain'].to_numpy()[i]
    gain_pct = df_obs['uncensored_gain_pct'].to_numpy()[i]
    plt.text(x[i] + width/2, df_obs['accepted_DA_nowilt'].to_numpy()[i] + 500, f'+{gain:,}\n(+{gain_pct:.1f}%)', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#a50f15')

plt.xticks(x, [f"{m[4:]}/2018" for m in months])
plt.xlabel('Mois 2018')
plt.ylabel('Nombre d\'observations SMAP acceptées')
plt.title('Bilan de Censure SMAP : observations acceptées avant et après suppression du filtre de flétrissement')
plt.legend(frameon=True, loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fig1_path = os.path.join(FIG_DIR, "fig_e5_accepted_obs_monthly.png")
plt.savefig(fig1_path, dpi=200)
plt.close()

# Figure 2: Impact by Texture in MAM (Spring dry-down season)
# Average over MAM (months 201803, 201804, 201805)
mam_df = df_tex[df_tex['month'].isin(['201803', '201804', '201805'])].groupby(['soil_id', 'texture_name', 'clay_pct']).mean().reset_index()
mam_df = mam_df.sort_values('clay_pct')

plt.figure(figsize=(12, 5))

# Subplot 1: delta SM1 vs clay
plt.subplot(1, 2, 1)
plt.plot(mam_df['clay_pct'].to_numpy(), mam_df['delta_SM1_nowilt_minus_nocdf'].to_numpy() * 100, 'o-', color='#b2182b', lw=2, label='DA_nowilt − DA_nocdf (effet censure)')
plt.plot(mam_df['clay_pct'].to_numpy(), mam_df['delta_SM1_nowilt_minus_ENS'].to_numpy() * 100, 's--', color='#2166ac', lw=1.8, label='DA_nowilt − ENS_OPL (DA pur)')
plt.axhline(0, color='gray', linestyle=':')
plt.xlabel('Teneur nominale en argile (%)')
plt.ylabel('Δ θ1 (vol. %)')
plt.title('MAM 2018 : Impact sur l\'humidité de surface (0–10 cm)')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: delta ET vs clay
plt.subplot(1, 2, 2)
plt.plot(mam_df['clay_pct'].to_numpy(), mam_df['delta_ET_nowilt_minus_nocdf_mm'].to_numpy(), 'o-', color='#b2182b', lw=2, label='DA_nowilt − DA_nocdf')
plt.plot(mam_df['clay_pct'].to_numpy(), mam_df['delta_ET_nowilt_minus_ENS_mm'].to_numpy(), 's--', color='#2166ac', lw=1.8, label='DA_nowilt − ENS_OPL')
plt.axhline(0, color='gray', linestyle=':')
plt.xlabel('Teneur nominale en argile (%)')
plt.ylabel('Δ ET (mm/mois)')
plt.title('MAM 2018 : Impact sur l\'évapotranspiration mensuelle')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
fig2_path = os.path.join(FIG_DIR, "fig_e5_nowilt_vs_da_and_ens.png")
plt.savefig(fig2_path, dpi=200)
plt.close()

print(f"[SUCCÈS] Partie 2.c terminée. Figures et CSV sauvegardés dans {OUT_DIR}.")
