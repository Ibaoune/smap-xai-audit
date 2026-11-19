#!/usr/bin/env python3
"""
compute_member_truncation_stats.py

Calcule la fréquence d'écrêtage par membre (sur les 320 600 tuiles membres)
à partir des restarts mensuels pour ENS_OPL_2018 et DA_nocdf_noirr_2016_2020 :
- Part des membres à 0.02 (seuil minimal physique MIN_THRESHOLD)
- Part des membres à SMCMAX (saturation)
- Part des membres à SMCWLT (point de flétrissement)
Par couche (1, 2, 3, 4) et par mois (janvier-mai 2018).
"""

import os
import netCDF4 as nc
import numpy as np
import pandas as pd

BASE_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_e6_clean")
os.makedirs(OUT_DIR, exist_ok=True)

SOILPARM_PATH = os.path.join(BASE_DIR, "data/land_params/noahmp401_parms/SOILPARM.TBL")
maxsmc_table = {}
wltsmc_table = {}
with open(SOILPARM_PATH, 'r') as f:
    in_stas = False
    for line in f:
        if 'STAS' in line and not 'STAS-RUC' in line:
            in_stas = True
            continue
        if 'STAS-RUC' in line:
            break
        if in_stas and line.strip() and line.strip()[0].isdigit():
            parts = [p.strip() for p in line.split(',') if p.strip()]
            if len(parts) >= 10:
                cat = int(parts[0])
                maxsmc_table[cat] = float(parts[4])
                wltsmc_table[cat] = float(parts[9])

with nc.Dataset(os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")) as ds:
    landmask = ds.variables['LANDMASK'][:].squeeze().astype(bool)
    texture = ds.variables['TEXTURE'][:]

soiltype = np.argmax(texture, axis=0) + 1
soiltype_tiles = soiltype[landmask]
smcmax_tiles = np.array([maxsmc_table.get(st, 0.439) for st in soiltype_tiles], dtype=np.float32)
smcwlt_tiles = np.array([wltsmc_table.get(st, 0.066) for st in soiltype_tiles], dtype=np.float32)

n_tiles = 16030
n_ens = 20
total_member_tiles = n_tiles * n_ens  # 320 600

simulations = [
    ("ENS_OPL", os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/ENS_OPL_2018/output/SURFACEMODEL")),
    ("DA_nocdf", os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020"))
]

months = [
    ("2018-01", "201801", "201801312345"),
    ("2018-02", "201802", "201802282345"),
    ("2018-03", "201803", "201803312345"),
    ("2018-04", "201804", "201804302345"),
    ("2018-05", "201805", "201805312345"),
]

rows = []

for sim_name, sim_path in simulations:
    for m_label, ym, t_end in months:
        if sim_name == "ENS_OPL":
            fp = os.path.join(sim_path, ym, f"LIS_RST_NOAHMP401_{t_end}.d01.nc")
        else:
            fp = os.path.join(sim_path, f"output/{m_label}/SURFACEMODEL/{ym}/LIS_RST_NOAHMP401_{t_end}.d01.nc")
            
        with nc.Dataset(fp) as ds:
            smc = ds.variables['SMC'][:]
            smc_reshaped = smc.reshape(4, n_tiles, n_ens)
            
            for lyr in range(4):
                smc_lyr = smc_reshaped[lyr, :, :]
                
                c_002 = int(np.sum(smc_lyr <= 0.02001))
                pct_002 = 100.0 * c_002 / total_member_tiles
                
                smcmax_2d = smcmax_tiles[:, None]
                smcwlt_2d = smcwlt_tiles[:, None]
                
                c_sat = int(np.sum(smc_lyr >= (smcmax_2d - 1e-4)))
                pct_sat = 100.0 * c_sat / total_member_tiles
                
                c_wlt = int(np.sum(smc_lyr <= smcwlt_2d))
                pct_wlt = 100.0 * c_wlt / total_member_tiles
                
                min_val = float(np.min(smc_lyr))
                max_val = float(np.max(smc_lyr))
                
                rows.append({
                    'simulation': sim_name,
                    'month': m_label,
                    'layer': lyr + 1,
                    'total_member_tiles': total_member_tiles,
                    'count_below_002': c_002,
                    'pct_below_002': round(pct_002, 4),
                    'count_above_smcmax': c_sat,
                    'pct_above_smcmax': round(pct_sat, 4),
                    'count_below_smcwlt': c_wlt,
                    'pct_below_smcwlt': round(pct_wlt, 4),
                    'min_smc': round(min_val, 5),
                    'max_smc': round(max_val, 5)
                })

df_trunc = pd.DataFrame(rows)
out_csv = os.path.join(OUT_DIR, "e6_member_truncation_restarts.csv")
df_trunc.to_csv(out_csv, index=False)
print(f"[SUCCES] Statistiques d'ecretage par membre sauvegardees dans : {out_csv}")
print(df_trunc[df_trunc['layer'] == 1][['simulation', 'month', 'pct_below_002', 'pct_above_smcmax', 'pct_below_smcwlt', 'min_smc', 'max_smc']])
