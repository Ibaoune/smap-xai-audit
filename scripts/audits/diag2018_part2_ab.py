#!/usr/bin/env python3
"""
diag2018_part2_ab.py
Partie 2.a et 2.b : Effet d'ensemble (E6) et Troncature des bornes dans ENS_OPL (Janvier-Mai 2018).
"""
import os
import glob
import re
import datetime
import numpy as np
import pandas as pd
import netCDF4 as nc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Paths
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
    soiltype = np.argmax(texture_3d, axis=0) + 1

# Soil parameters: MAXSMC (saturation) and WLTSMC (wilting point)
smcmax_table = {}
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
                cid = int(parts[0])
                smcmax_table[cid] = float(parts[4])
                smcwlt_table[cid] = float(parts[9])

smcmax_grid = np.zeros_like(soiltype, dtype=float)
smcwlt_grid = np.zeros_like(soiltype, dtype=float)
for cid in smcmax_table:
    smcmax_grid[soiltype == cid] = smcmax_table[cid]
    smcwlt_grid[soiltype == cid] = smcwlt_table[cid]

print(f"[INFO] Static loaded. Land pixels: {np.sum(landmask)}")

# Simulation paths
runs = {
    'OPL': os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"),
    'ENS_OPL': os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output"),
    'DA_nocdf': os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"),
    'DA_cdf': os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output"),
}

months = [f"2018{m:02d}" for m in range(1, 6)]
days_in_month = {
    '201801': 31, '201802': 28, '201803': 31, '201804': 30, '201805': 31
}

# Monthly metrics storage
# Run -> Month -> dict of mean values
monthly_data = {r: {} for r in runs}

# Bounded check storage for ENS_OPL
# Month -> Layer -> {'below_002': count, 'below_wilt': count, 'above_sat': count, 'total': count}
truncation_stats = {m: {l: {'below_002': 0, 'below_wilt': 0, 'above_sat': 0, 'total': 0} for l in range(4)} for m in months}

def get_file_list(run_name, ym):
    base = runs[run_name]
    if run_name in ['OPL', 'DA_nocdf', 'DA_cdf']:
        ym_dash = f"{ym[:4]}-{ym[4:6]}"
        patt = os.path.join(base, ym_dash, "SURFACEMODEL", ym, "LIS_HIST_*.nc")
    else:
        patt = os.path.join(base, "SURFACEMODEL", ym, "LIS_HIST_*.nc")
    files = sorted(glob.glob(patt))
    # Exclude restart nc if any matched
    files = [f for f in files if "LIS_HIST" in os.path.basename(f)]
    return files

for ym in months:
    print(f"[INFO] Processing month {ym}...")
    ndays = days_in_month[ym]
    
    for r_name in runs:
        flist = get_file_list(r_name, ym)
        if len(flist) < ndays:
            print(f"[WARN] {r_name} in {ym} has {len(flist)} files (expected {ndays})")
            
        evap_sum = 0.0
        qs_sum = 0.0
        qsb_sum = 0.0
        precip_sum = 0.0
        sm_sum = np.zeros(4)
        count = 0
        
        for f in flist:
            with nc.Dataset(f) as ds:
                # ET, Qs, Qsb in kg/m2/s -> mm/day = val * 86400
                evap = ds.variables["Evap_tavg"][:].squeeze()
                qs = ds.variables["Qs_tavg"][:].squeeze()
                qsb = ds.variables["Qsb_tavg"][:].squeeze()
                precip = ds.variables["TotalPrecip_tavg"][:].squeeze() if "TotalPrecip_tavg" in ds.variables else ds.variables["Rainf_f_tavg"][:].squeeze()
                sm = ds.variables["SoilMoist_tavg"][:].squeeze() # (4, 121, 181)
                
                evap_sum += np.nanmean(evap[landmask]) * 86400.0
                qs_sum += np.nanmean(qs[landmask]) * 86400.0
                qsb_sum += np.nanmean(qsb[landmask]) * 86400.0
                precip_sum += np.nanmean(precip[landmask]) * 86400.0
                
                for l in range(4):
                    sm_sum[l] += np.nanmean(sm[l][landmask])
                    
                # Truncation check for ENS_OPL
                if r_name == 'ENS_OPL':
                    for l in range(4):
                        sm_l = sm[l][landmask]
                        wlt_l = smcwlt_grid[landmask]
                        sat_l = smcmax_grid[landmask]
                        
                        b_002 = np.sum(sm_l <= 0.02001)
                        b_wlt = np.sum(sm_l <= (wlt_l + 1e-4))
                        a_sat = np.sum(sm_l >= (sat_l - 1e-4))
                        tot = len(sm_l)
                        
                        truncation_stats[ym][l]['below_002'] += int(b_002)
                        truncation_stats[ym][l]['below_wilt'] += int(b_wlt)
                        truncation_stats[ym][l]['above_sat'] += int(a_sat)
                        truncation_stats[ym][l]['total'] += tot
                        
                count += 1
                
        # Scale to monthly totals / means
        # Total mm = (daily mean mm/day) * ndays
        # In case count != ndays, mean * ndays
        evap_monthly = (evap_sum / count) * ndays
        qs_monthly = (qs_sum / count) * ndays
        qsb_monthly = (qsb_sum / count) * ndays
        precip_monthly = (precip_sum / count) * ndays
        sm_monthly = sm_sum / count
        
        # Column soil moisture: weights 0.1, 0.3, 0.6, 1.0 / 2.0
        sm_col = (0.1 * sm_monthly[0] + 0.3 * sm_monthly[1] + 0.6 * sm_monthly[2] + 1.0 * sm_monthly[3]) / 2.0
        
        monthly_data[r_name][ym] = {
            'ET_mm': evap_monthly,
            'Qs_mm': qs_monthly,
            'Qsb_mm': qsb_monthly,
            'Precip_mm': precip_monthly,
            'SM1': sm_monthly[0],
            'SM2': sm_monthly[1],
            'SM3': sm_monthly[2],
            'SM4': sm_monthly[3],
            'SM_col': sm_col
        }

# Build summary dataframe for Part 2.a
rows_a = []
for ym in months:
    opl = monthly_data['OPL'][ym]
    ens = monthly_data['ENS_OPL'][ym]
    da_nocdf = monthly_data['DA_nocdf'][ym]
    da_cdf = monthly_data['DA_cdf'][ym]
    
    # Diffs with OPL
    d_ens_et = ens['ET_mm'] - opl['ET_mm']
    d_danocdf_et = da_nocdf['ET_mm'] - opl['ET_mm']
    d_dacdf_et = da_cdf['ET_mm'] - opl['ET_mm']
    
    d_ens_qs = ens['Qs_mm'] - opl['Qs_mm']
    d_danocdf_qs = da_nocdf['Qs_mm'] - opl['Qs_mm']
    d_dacdf_qs = da_cdf['Qs_mm'] - opl['Qs_mm']
    
    d_ens_qsb = ens['Qsb_mm'] - opl['Qsb_mm']
    d_danocdf_qsb = da_nocdf['Qsb_mm'] - opl['Qsb_mm']
    d_dacdf_qsb = da_cdf['Qsb_mm'] - opl['Qsb_mm']
    
    d_ens_p = ens['Precip_mm'] - opl['Precip_mm']
    
    # SM diffs
    d_ens_sm1 = ens['SM1'] - opl['SM1']
    d_danocdf_sm1 = da_nocdf['SM1'] - opl['SM1']
    d_dacdf_sm1 = da_cdf['SM1'] - opl['SM1']
    
    d_ens_smcol = ens['SM_col'] - opl['SM_col']
    d_danocdf_smcol = da_nocdf['SM_col'] - opl['SM_col']
    d_dacdf_smcol = da_cdf['SM_col'] - opl['SM_col']
    
    # Fraction explained by ensemble alone:
    # d_ens / d_da
    ratio_et_nocdf = (d_ens_et / d_danocdf_et * 100.0) if abs(d_danocdf_et) > 1e-4 else np.nan
    ratio_et_cdf = (d_ens_et / d_dacdf_et * 100.0) if abs(d_dacdf_et) > 1e-4 else np.nan
    
    ratio_sm1_nocdf = (d_ens_sm1 / d_danocdf_sm1 * 100.0) if abs(d_danocdf_sm1) > 1e-5 else np.nan
    ratio_sm1_cdf = (d_ens_sm1 / d_dacdf_sm1 * 100.0) if abs(d_dacdf_sm1) > 1e-5 else np.nan
    
    ratio_smcol_nocdf = (d_ens_smcol / d_danocdf_smcol * 100.0) if abs(d_danocdf_smcol) > 1e-5 else np.nan
    ratio_smcol_cdf = (d_ens_smcol / d_dacdf_smcol * 100.0) if abs(d_dacdf_smcol) > 1e-5 else np.nan

    rows_a.append({
        'month': ym,
        'Precip_OPL_mm': round(opl['Precip_mm'], 2),
        'Precip_ENS_mm': round(ens['Precip_mm'], 2),
        'delta_Precip_ENS_OPL_mm': round(d_ens_p, 2),
        
        'delta_ET_ENS_OPL_mm': round(d_ens_et, 2),
        'delta_ET_DAnocdf_mm': round(d_danocdf_et, 2),
        'delta_ET_DAcdf_mm': round(d_dacdf_et, 2),
        'fraction_ET_explained_nocdf_pct': round(ratio_et_nocdf, 1),
        'fraction_ET_explained_cdf_pct': round(ratio_et_cdf, 1),
        
        'delta_Qs_ENS_OPL_mm': round(d_ens_qs, 3),
        'delta_Qs_DAnocdf_mm': round(d_danocdf_qs, 3),
        'delta_Qs_DAcdf_mm': round(d_dacdf_qs, 3),
        
        'delta_Qsb_ENS_OPL_mm': round(d_ens_qsb, 3),
        'delta_Qsb_DAnocdf_mm': round(d_danocdf_qsb, 3),
        'delta_Qsb_DAcdf_mm': round(d_dacdf_qsb, 3),
        
        'delta_SM1_ENS_OPL': round(d_ens_sm1, 5),
        'delta_SM1_DAnocdf': round(d_danocdf_sm1, 5),
        'delta_SM1_DAcdf': round(d_dacdf_sm1, 5),
        'fraction_SM1_explained_nocdf_pct': round(ratio_sm1_nocdf, 1),
        'fraction_SM1_explained_cdf_pct': round(ratio_sm1_cdf, 1),
        
        'delta_SM2_ENS_OPL': round(ens['SM2'] - opl['SM2'], 5),
        'delta_SM3_ENS_OPL': round(ens['SM3'] - opl['SM3'], 5),
        'delta_SM4_ENS_OPL': round(ens['SM4'] - opl['SM4'], 5),
        
        'delta_SMcol_ENS_OPL': round(d_ens_smcol, 5),
        'delta_SMcol_DAnocdf': round(d_danocdf_smcol, 5),
        'delta_SMcol_DAcdf': round(d_dacdf_smcol, 5),
        'fraction_SMcol_explained_nocdf_pct': round(ratio_smcol_nocdf, 1),
        'fraction_SMcol_explained_cdf_pct': round(ratio_smcol_cdf, 1),
    })

df_a = pd.DataFrame(rows_a)
csv_a = os.path.join(OUT_DIR, "e6_ensemble_effect_monthly.csv")
df_a.to_csv(csv_a, index=False)
print(f"[INFO] Saved {csv_a}")

# Build summary dataframe for Part 2.b (Truncations)
rows_b = []
for ym in months:
    for l in range(4):
        s = truncation_stats[ym][l]
        tot = s['total']
        p_002 = (s['below_002'] / tot * 100.0) if tot > 0 else 0.0
        p_wlt = (s['below_wilt'] / tot * 100.0) if tot > 0 else 0.0
        p_sat = (s['above_sat'] / tot * 100.0) if tot > 0 else 0.0
        rows_b.append({
            'month': ym,
            'layer': l + 1,
            'thickness_m': [0.1, 0.3, 0.6, 1.0][l],
            'total_pixel_days': tot,
            'count_below_002': s['below_002'],
            'freq_below_002_pct': round(p_002, 4),
            'count_below_wilt': s['below_wilt'],
            'freq_below_wilt_pct': round(p_wlt, 2),
            'count_above_sat': s['above_sat'],
            'freq_above_sat_pct': round(p_sat, 4)
        })

df_b = pd.DataFrame(rows_b)
csv_b = os.path.join(OUT_DIR, "e6_boundary_truncation_ens_opl.csv")
df_b.to_csv(csv_b, index=False)
print(f"[INFO] Saved {csv_b}")

# -------------------------------------------------------------
# Figures
# -------------------------------------------------------------
# Figure 1: ET & SM response comparison: ENS_OPL vs DA_nocdf vs DA_cdf
plt.figure(figsize=(12, 8))

# Subplot 1: delta ET
plt.subplot(2, 2, 1)
x = np.arange(len(months))
width = 0.25
plt.bar(x - width, df_a['delta_ET_ENS_OPL_mm'], width, label='ENS_OPL − OPL', color='#4575b4')
plt.bar(x, df_a['delta_ET_DAnocdf_mm'], width, label='DA_nocdf − OPL', color='#d73027')
plt.bar(x + width, df_a['delta_ET_DAcdf_mm'], width, label='DA_cdf − OPL', color='#fdae61')
plt.xticks(x, [m[4:] for m in months])
plt.xlabel('Mois 2018')
plt.ylabel('Δ ET (mm/mois)')
plt.title('Impact sur l\'Évapotranspiration (ET)')
plt.legend(frameon=True, fontsize=9)
plt.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: delta SoilMoist Layer 1
plt.subplot(2, 2, 2)
plt.bar(x - width, df_a['delta_SM1_ENS_OPL'] * 100, width, label='ENS_OPL − OPL', color='#4575b4')
plt.bar(x, df_a['delta_SM1_DAnocdf'] * 100, width, label='DA_nocdf − OPL', color='#d73027')
plt.bar(x + width, df_a['delta_SM1_DAcdf'] * 100, width, label='DA_cdf − OPL', color='#fdae61')
plt.xticks(x, [m[4:] for m in months])
plt.xlabel('Mois 2018')
plt.ylabel('Δ θ1 (vol. %)')
plt.title('Impact sur l\'Humidité Couche 1 (0–10 cm)')
plt.legend(frameon=True, fontsize=9)
plt.grid(True, linestyle='--', alpha=0.5)

# Subplot 3: Fraction explained by ensemble alone
plt.subplot(2, 2, 3)
plt.plot(x, df_a['fraction_ET_explained_nocdf_pct'], 'o-', label='ET (% de DA_nocdf)', color='#d73027', lw=2)
plt.plot(x, df_a['fraction_SM1_explained_nocdf_pct'], 's-', label='θ1 (% de DA_nocdf)', color='#313695', lw=2)
plt.plot(x, df_a['fraction_ET_explained_cdf_pct'], 'o--', label='ET (% de DA_cdf)', color='#fdae61', lw=1.5)
plt.axhline(0, color='gray', linestyle=':', alpha=0.7)
plt.xticks(x, [m[4:] for m in months])
plt.xlabel('Mois 2018')
plt.ylabel('Fraction expliquée par l\'ensemble (%)')
plt.title('Fraction de la réponse DA expliquée par ENS seul')
plt.legend(frameon=True, fontsize=9)
plt.grid(True, linestyle='--', alpha=0.5)

# Subplot 4: Bounded state frequency in ENS_OPL
plt.subplot(2, 2, 4)
for l in range(4):
    sub = df_b[df_b['layer'] == l + 1]
    plt.plot(x, sub['freq_below_wilt_pct'], 'o-', label=f'Couche {l+1} (≤ SMCWLT)', lw=1.8)
plt.xticks(x, [m[4:] for m in months])
plt.xlabel('Mois 2018')
plt.ylabel('Fréquence (%)')
plt.title('Fréquence de sol ≤ SMCWLT dans ENS_OPL')
plt.legend(frameon=True, fontsize=9)
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
fig_out = os.path.join(FIG_DIR, "fig_e6_ensemble_vs_da_response.png")
plt.savefig(fig_out, dpi=200)
plt.close()
print(f"[INFO] Saved {fig_out}")

# Figure 2: Soil moisture profile diffs across all 4 layers
plt.figure(figsize=(10, 5))
layers = [1, 2, 3, 4]
for ym in months:
    d_sm_layers = [
        monthly_data['ENS_OPL'][ym]['SM1'] - monthly_data['OPL'][ym]['SM1'],
        monthly_data['ENS_OPL'][ym]['SM2'] - monthly_data['OPL'][ym]['SM2'],
        monthly_data['ENS_OPL'][ym]['SM3'] - monthly_data['OPL'][ym]['SM3'],
        monthly_data['ENS_OPL'][ym]['SM4'] - monthly_data['OPL'][ym]['SM4'],
    ]
    plt.plot([d * 100 for d in d_sm_layers], [1, 2, 3, 4], 'o-', label=ym, lw=2)
plt.gca().invert_yaxis()
plt.yticks([1, 2, 3, 4], ['Couche 1 (0-10cm)', 'Couche 2 (10-40cm)', 'Couche 3 (40-100cm)', 'Couche 4 (100-200cm)'])
plt.axvline(0, color='black', linestyle='--')
plt.xlabel('Δ θ (ENS_OPL − OPL) [vol. %]')
plt.title('Profil vertical de l\'effet d\'ensemble (ENS_OPL − OPL) par mois en 2018')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fig_out2 = os.path.join(FIG_DIR, "fig_e6_vertical_profile_sm_diffs.png")
plt.savefig(fig_out2, dpi=200)
plt.close()
print(f"[INFO] Saved {fig_out2}")
print("[SUCCÈS] Partie 2.a et 2.b complétées.")
