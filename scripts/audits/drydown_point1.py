#!/usr/bin/env python3
"""
drydown_point1.py
------------------
Étape 1 : Analyse des dynamiques de séchage (dry-downs) SMAP vs Open-Loop (OL)
pour le domaine NorthMor (121x181, ~5 km), 2016–2020.

Hypothèse à tester :
Au printemps (MAM), Noah-MP (OL) sèche-t-il trop lentement (tau_OL > tau_SMAP)
ou bute-t-il sur un plancher (theta_res_OL ou P5_OL >= SMCWLT) alors que SMAP descend
plus bas, particulièrement sur les sols argileux ?

Méthodologie :
1. Détection des épisodes de séchage par pixel :
   - Pluie >= 5 mm/j (forçage du modèle) suivie d'au moins 7 jours avec pluie < 1 mm/j.
   - Au moins 3 observations SMAP acceptées par le QC (rec2 de LISDAOBS).
2. Ajustement exponentiel :
   theta(t) = theta_res + Delta_theta * exp(-t / tau)
   sur SMAP et sur l'OL échantillonné aux mêmes dates.
   Filtre physique : 0 < tau <= 60 j, Delta_theta > 0, R2 >= 0.5.
3. Planchers empiriques (5e percentile) par pixel et par saison.
4. Comparaison à SMCWLT (point de flétrissement SOILPARM.TBL).
5. Agrégation à l'échelle ~36 km (blocs 7x7) et bootstrap par blocs (IC 95%).
6. Sorties complètes dans reports/audits/drydown_point1/.
"""

import os
import sys
import glob
import datetime
import time
import multiprocessing as mp
import numpy as np
import pandas as pd
import netCDF4 as nc
from scipy.optimize import curve_fit

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# Configuration des chemins
# -------------------------------------------------------------
COMB_OL = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/combined_OPL_noirr/SURFACEMODEL"
BASE_OL = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"
BASE_DA = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
LIS_INPUT = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM_PATH = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports/audits/drydown_point1"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, "daily_cache_2016_2020.npz")

# Table de correspondance USDA texture
TEXTURE_NAMES = {
    1: "Sand",
    2: "Loamy Sand",
    3: "Sandy Loam",
    4: "Silt Loam",
    5: "Silt",
    6: "Loam",
    7: "Sandy Clay Loam",
    8: "Silty Clay Loam",
    9: "Clay Loam",
    10: "Sandy Clay",
    11: "Silty Clay",
    12: "Clay",
}

# Variables globales pour le partage mémoire en multiprocessing
G_LAND_BOOL = None
G_PRECIP = None
G_OL = None
G_SMAP = None
G_SOILTYPE = None
G_SMCWLT = None
G_BLOCK = None
G_LAT = None
G_LON = None
G_DATES = None
G_N_DAYS = None
G_SEASON_INDICES = None

def load_static():
    """Charge le masque terre, textures, SMCWLT et coordonnées."""
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
        texture = ds.variables["TEXTURE"][:] # (16, 121, 181)
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]
        
    soiltype = np.argmax(texture, axis=0) + 1
    
    wltsmc_table = {}
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
                    cat = int(parts[0])
                    wlt = float(parts[9])
                    wltsmc_table[cat] = wlt
                    
    smcwlt_grid = np.zeros_like(soiltype, dtype=float)
    for cat, wlt in wltsmc_table.items():
        smcwlt_grid[soiltype == cat] = wlt
        
    # Définition des blocs 7x7 (~36 km)
    block_id_grid = np.full(landmask.shape, -1, dtype=int)
    n_col_blocks = int(np.ceil(181 / 7))
    for r in range(121):
        for c in range(181):
            if landmask[r, c] == 1:
                block_id_grid[r, c] = (r // 7) * n_col_blocks + (c // 7)
                
    return landmask, soiltype, smcwlt_grid, block_id_grid, lat, lon

def find_ol_file(date_dt):
    """Localise le fichier journalier LIS_HIST de l'OL."""
    next_dt = date_dt + datetime.timedelta(days=1)
    dstr = next_dt.strftime("%Y%m%d")
    ym_cur = date_dt.strftime("%Y-%m")
    ym_cur_c = date_dt.strftime("%Y%m")
    ym_next = next_dt.strftime("%Y-%m")
    ym_next_c = next_dt.strftime("%Y%m")
    
    cands = [
        os.path.join(COMB_OL, ym_cur_c, f"LIS_HIST_{dstr}0000.d01.nc"),
        os.path.join(COMB_OL, ym_next_c, f"LIS_HIST_{dstr}0000.d01.nc"),
        os.path.join(BASE_OL, ym_cur, "SURFACEMODEL", ym_cur_c, f"LIS_HIST_{dstr}0000.d01.nc"),
        os.path.join(BASE_OL, ym_cur, "SURFACEMODEL", ym_next_c, f"LIS_HIST_{dstr}0000.d01.nc"),
        os.path.join(BASE_OL, ym_next, "SURFACEMODEL", ym_next_c, f"LIS_HIST_{dstr}0000.d01.nc"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return None

def read_daobs_rec2(fpath):
    """Lit l'enregistrement rec2 (QC accepté) d'un fichier LISDAOBS."""
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        _ = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec2.reshape(121, 181)

def load_or_build_cache():
    """Charge ou construit le cache journalier compact 2016-2020."""
    if os.path.exists(CACHE_FILE):
        print(f"[INFO] Chargement du cache journalier depuis {CACHE_FILE}...")
        data = np.load(CACHE_FILE)
        return (
            data["precip_daily"],
            data["ol_daily"],
            data["smap_daily"],
            [datetime.date.fromisoformat(d) for d in data["dates_str"]]
        )
        
    print(f"[INFO] Construction du cache journalier 2016–2020 (1827 jours)...")
    t0 = time.time()
    cur_dt = datetime.date(2016, 1, 1)
    end_dt = datetime.date(2020, 12, 31)
    
    dates_list = []
    precip_list = []
    ol_list = []
    smap_list = []
    
    print("[INFO] Indexation des fichiers DAOBS...")
    daobs_by_date = {}
    for ym in [f"{y}-{m:02d}" for y in range(2016, 2021) for m in range(1, 13)]:
        ym_compact = ym.replace("-", "")
        daobs_dir = os.path.join(BASE_DA, ym, "DAOBS", ym_compact)
        if os.path.isdir(daobs_dir):
            for f in glob.glob(os.path.join(daobs_dir, "LISDAOBS_*.1gs4r")):
                fname = os.path.basename(f)
                dstr = fname.split("_")[1][:8]
                if dstr not in daobs_by_date:
                    daobs_by_date[dstr] = []
                daobs_by_date[dstr].append(f)
                
    print(f"[INFO] Indexé {len(daobs_by_date)} jours avec observations SMAP.")
    
    day_count = 0
    while cur_dt <= end_dt:
        dstr = cur_dt.strftime("%Y%m%d")
        dates_list.append(cur_dt)
        
        ol_f = find_ol_file(cur_dt)
        if ol_f is not None:
            with nc.Dataset(ol_f) as ds:
                p = ds.variables["TotalPrecip_tavg"][:].squeeze() * 86400.0 # mm/j
                sm_ol = ds.variables["SoilMoist_tavg"][0, :, :].squeeze() # m3/m3
        else:
            p = np.full((121, 181), np.nan, dtype=np.float32)
            sm_ol = np.full((121, 181), np.nan, dtype=np.float32)
            
        precip_list.append(p.astype(np.float32))
        ol_list.append(sm_ol.astype(np.float32))
        
        if dstr in daobs_by_date:
            sum_smap = np.zeros((121, 181), dtype=float)
            cnt_smap = np.zeros((121, 181), dtype=int)
            for df in daobs_by_date[dstr]:
                rec2 = read_daobs_rec2(df)
                v = (rec2 != -9999.0) & np.isfinite(rec2)
                sum_smap[v] += rec2[v]
                cnt_smap[v] += 1
            smap_day = np.full((121, 181), np.nan, dtype=np.float32)
            v_day = cnt_smap > 0
            smap_day[v_day] = sum_smap[v_day] / cnt_smap[v_day]
        else:
            smap_day = np.full((121, 181), np.nan, dtype=np.float32)
            
        smap_list.append(smap_day)
        
        day_count += 1
        if day_count % 300 == 0:
            print(f"  ... {day_count}/1827 jours traités ({time.time() - t0:.1f} s)")
        cur_dt += datetime.timedelta(days=1)
        
    precip_arr = np.stack(precip_list, axis=0)
    ol_arr = np.stack(ol_list, axis=0)
    smap_arr = np.stack(smap_list, axis=0)
    dates_str = [d.isoformat() for d in dates_list]
    
    print(f"[INFO] Sauvegarde du cache dans {CACHE_FILE}...")
    np.savez_compressed(
        CACHE_FILE,
        precip_daily=precip_arr,
        ol_daily=ol_arr,
        smap_daily=smap_arr,
        dates_str=dates_str
    )
    print(f"[INFO] Cache construit et sauvegardé en {time.time() - t0:.1f} s.")
    return precip_arr, ol_arr, smap_arr, dates_list

def exp_decay(t, theta_res, delta_theta, tau):
    """Modèle de séchage exponentiel."""
    return theta_res + delta_theta * np.exp(-t / tau)

def fit_single_drydown(t_obs, sm_obs):
    """Ajuste le séchage exponentiel et vérifie la physicalité."""
    if len(t_obs) < 3:
        return None
    ss_tot = np.sum((sm_obs - np.mean(sm_obs))**2)
    if ss_tot < 1e-7:
        return None
        
    lb = [0.001, 0.001, 0.5]
    ub = [0.55, 0.50, 60.0]
    p0 = [min(sm_obs), max(sm_obs) - min(sm_obs), 5.0]
    p0[0] = max(lb[0], min(ub[0], p0[0]))
    p0[1] = max(lb[1], min(ub[1], p0[1]))
    
    try:
        popt, _ = curve_fit(exp_decay, t_obs, sm_obs, p0=p0, bounds=(lb, ub), maxfev=600)
        theta_res, delta_theta, tau = popt
        pred = exp_decay(t_obs, *popt)
        ss_res = np.sum((sm_obs - pred)**2)
        r2 = 1.0 - (ss_res / ss_tot)
        
        # Filtre physique strict : tau in ]0, 60], Delta_theta > 0, R2 >= 0.5
        if r2 >= 0.5 and delta_theta > 0.002 and (0.5 <= tau <= 60.0):
            return {
                "theta_res": float(theta_res),
                "delta_theta": float(delta_theta),
                "tau": float(tau),
                "r2": float(r2)
            }
        else:
            return None
    except Exception:
        return None

def get_season(dt):
    """Renvoie la saison météorologique."""
    m = dt.month
    if m in [3, 4, 5]:
        return "MAM"
    elif m in [6, 7, 8]:
        return "JJA"
    elif m in [9, 10, 11]:
        return "SON"
    else:
        return "DJF"

def block_bootstrap_ci(df_data, metric_col, block_col="block_id", n_boot=1000, ci=95, seed=42):
    """Calcule l'IC à 95% par rééchantillonnage de blocs (7x7 pixels ~36 km)."""
    blocks = df_data[block_col].unique()
    n_blocks = len(blocks)
    if n_blocks == 0 or len(df_data) == 0:
        return np.nan, np.nan
    if n_blocks == 1:
        val = np.median(df_data[metric_col])
        return val, val
        
    rng = np.random.default_rng(seed)
    grouped = {b: grp[metric_col].values for b, grp in df_data.groupby(block_col)}
    
    boot_stats = np.empty(n_boot)
    for i in range(n_boot):
        sampled_blocks = rng.choice(blocks, size=n_blocks, replace=True)
        sampled_vals = np.concatenate([grouped[b] for b in sampled_blocks if len(grouped[b]) > 0])
        if len(sampled_vals) > 0:
            boot_stats[i] = np.median(sampled_vals)
        else:
            boot_stats[i] = np.nan
            
    alpha = (100.0 - ci) / 2.0
    valid_stats = boot_stats[np.isfinite(boot_stats)]
    if len(valid_stats) == 0:
        return np.nan, np.nan
    low = float(np.percentile(valid_stats, alpha))
    high = float(np.percentile(valid_stats, 100.0 - alpha))
    return low, high

def process_single_row_episodes(r):
    """Traite tous les épisodes de séchage pour une ligne r."""
    row_records = []
    for c in range(181):
        if not G_LAND_BOOL[r, c]:
            continue
            
        p_series = G_PRECIP[:, r, c]
        ol_series = G_OL[:, r, c]
        smap_series = G_SMAP[:, r, c]
        st = G_SOILTYPE[r, c]
        wlt = G_SMCWLT[r, c]
        blk = G_BLOCK[r, c]
        lat_val = G_LAT[r, c]
        lon_val = G_LON[r, c]
        
        d = 1
        while d < G_N_DAYS - 7:
            if p_series[d-1] >= 5.0 and p_series[d] < 1.0:
                L = 0
                while (d + L) < G_N_DAYS and p_series[d + L] < 1.0:
                    L += 1
                    
                if L >= 7:
                    dry_indices = np.arange(d, d + L)
                    smap_sub = smap_series[dry_indices]
                    valid_mask = np.isfinite(smap_sub)
                    n_smap_obs = int(valid_mask.sum())
                    
                    if n_smap_obs >= 3:
                        t_obs = (dry_indices[valid_mask] - (d - 1)).astype(float)
                        smap_vals = smap_sub[valid_mask]
                        ol_vals = ol_series[dry_indices[valid_mask]]
                        
                        fit_smap = fit_single_drydown(t_obs, smap_vals)
                        if fit_smap is not None:
                            fit_ol = fit_single_drydown(t_obs, ol_vals)
                            if fit_ol is not None:
                                dt_start = G_DATES[d]
                                dt_rain = G_DATES[d - 1]
                                season = get_season(dt_start)
                                
                                row_records.append({
                                    "r": r,
                                    "c": c,
                                    "block_id": blk,
                                    "lat": lat_val,
                                    "lon": lon_val,
                                    "soiltype": st,
                                    "texture_nom": TEXTURE_NAMES.get(st, f"Type_{st}"),
                                    "smcwlt": wlt,
                                    "date_rain": dt_rain.isoformat(),
                                    "date_start": dt_start.isoformat(),
                                    "dry_days_L": L,
                                    "n_smap_obs": n_smap_obs,
                                    "season": season,
                                    "year": dt_start.year,
                                    "tau_smap": fit_smap["tau"],
                                    "theta_res_smap": fit_smap["theta_res"],
                                    "delta_theta_smap": fit_smap["delta_theta"],
                                    "r2_smap": fit_smap["r2"],
                                    "tau_ol": fit_ol["tau"],
                                    "theta_res_ol": fit_ol["theta_res"],
                                    "delta_theta_ol": fit_ol["delta_theta"],
                                    "r2_ol": fit_ol["r2"],
                                    "delta_tau": fit_ol["tau"] - fit_smap["tau"],
                                    "delta_theta_res": fit_ol["theta_res"] - fit_smap["theta_res"],
                                })
                    d += L
                else:
                    d += 1
            else:
                d += 1
    return row_records

def process_single_row_floors(r):
    """Calcule les planchers empiriques (P5) par saison pour la ligne r."""
    row_records = []
    for c in range(181):
        if not G_LAND_BOOL[r, c]:
            continue
        st = G_SOILTYPE[r, c]
        wlt = G_SMCWLT[r, c]
        blk = G_BLOCK[r, c]
        
        for s_name, s_idx in G_SEASON_INDICES.items():
            smap_s = G_SMAP[s_idx, r, c]
            ol_s = G_OL[s_idx, r, c]
            
            v_smap = smap_s[np.isfinite(smap_s)]
            v_ol = ol_s[np.isfinite(ol_s)]
            
            p5_smap = float(np.percentile(v_smap, 5)) if len(v_smap) >= 10 else np.nan
            p5_ol = float(np.percentile(v_ol, 5)) if len(v_ol) >= 10 else np.nan
            
            row_records.append({
                "r": r,
                "c": c,
                "block_id": blk,
                "soiltype": st,
                "texture_nom": TEXTURE_NAMES.get(st, f"Type_{st}"),
                "smcwlt": wlt,
                "saison": s_name,
                "p5_smap": p5_smap,
                "p5_ol": p5_ol,
                "delta_p5": p5_ol - p5_smap if (np.isfinite(p5_smap) and np.isfinite(p5_ol)) else np.nan,
                "ol_minus_smcwlt": p5_ol - wlt if np.isfinite(p5_ol) else np.nan,
                "ol_floor_gt_smap": int(p5_ol > p5_smap) if (np.isfinite(p5_smap) and np.isfinite(p5_ol)) else np.nan
            })
    return row_records

def main():
    print("=================================================================")
    print(" ÉTAPE 1 : ANALYSE DES SÉCHAGES (DRY-DOWNS) SMAP VS OPEN-LOOP")
    print("=================================================================")
    
    global G_LAND_BOOL, G_PRECIP, G_OL, G_SMAP, G_SOILTYPE, G_SMCWLT, G_BLOCK, G_LAT, G_LON, G_DATES, G_N_DAYS, G_SEASON_INDICES
    
    landmask, soiltype, smcwlt_grid, block_id_grid, lat, lon = load_static()
    land_bool = (landmask == 1)
    n_land_pixels = int(land_bool.sum())
    print(f"[INFO] Pixels terre valides : {n_land_pixels} / {121*181}")
    
    precip_arr, ol_arr, smap_arr, dates_list = load_or_build_cache()
    n_days = len(dates_list)
    
    # Saisons
    seasons_list = ["MAM", "SON", "DJF", "JJA"]
    season_indices = {s: [] for s in seasons_list}
    for idx, dt in enumerate(dates_list):
        s = get_season(dt)
        season_indices[s].append(idx)
    season_indices["SECHE"] = season_indices["MAM"] + season_indices["JJA"]
    
    # Affectation des globales
    G_LAND_BOOL = land_bool
    G_PRECIP = precip_arr
    G_OL = ol_arr
    G_SMAP = smap_arr
    G_SOILTYPE = soiltype
    G_SMCWLT = smcwlt_grid
    G_BLOCK = block_id_grid
    G_LAT = lat
    G_LON = lon
    G_DATES = dates_list
    G_N_DAYS = n_days
    G_SEASON_INDICES = season_indices
    
    n_workers = int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 8))
    print(f"[INFO] Utilisation de {n_workers} cœurs de calcul parallèles...")

    # -------------------------------------------------------------
    # 1. Détection et ajustement des épisodes par pixel (Parallèle)
    # -------------------------------------------------------------
    print("\n[INFO] Détection des épisodes de séchage (pluie >= 5mm/j suivie de >= 7j avec < 1mm/j)...")
    t0_scan = time.time()
    
    with mp.Pool(processes=n_workers) as pool:
        row_ep_results = pool.map(process_single_row_episodes, range(121))
        
    episodes_records = []
    for r_res in row_ep_results:
        episodes_records.extend(r_res)
        
    df_ep = pd.DataFrame(episodes_records)
    print(f"[INFO] Détection et ajustements terminés en {time.time() - t0_scan:.1f} s.")
    print(f"[INFO] Nombre total d'épisodes valides ajustés : {len(df_ep)}")
    df_ep.to_csv(os.path.join(OUTPUT_DIR, "drydown_episodes_all.csv"), index=False, float_format="%.5f")
    print(f"[INFO] Épisodes détaillés sauvegardés dans drydown_episodes_all.csv")

    # -------------------------------------------------------------
    # 2. Planchers empiriques (5e percentile) par pixel (Parallèle)
    # -------------------------------------------------------------
    print("\n[INFO] Calcul des planchers empiriques (5e percentile) par pixel...")
    t0_floors = time.time()
    with mp.Pool(processes=n_workers) as pool:
        row_fl_results = pool.map(process_single_row_floors, range(121))
        
    pixel_floor_records = []
    for r_res in row_fl_results:
        pixel_floor_records.extend(r_res)
        
    df_floors = pd.DataFrame(pixel_floor_records)
    df_floors.to_csv(os.path.join(OUTPUT_DIR, "drydown_pixel_floors_p5.csv"), index=False, float_format="%.5f")
    print(f"[INFO] Planchers P5 calculés en {time.time() - t0_floors:.1f} s et sauvegardés dans drydown_pixel_floors_p5.csv")

    # Grilles pour les cartes MAM
    grid_mam_delta_tau = np.full((121, 181), np.nan)
    grid_mam_delta_theta_res = np.full((121, 181), np.nan)
    grid_mam_delta_p5 = np.full((121, 181), np.nan)
    grid_mam_ol_margin_wlt = np.full((121, 181), np.nan)
    
    if len(df_ep) > 0:
        df_mam = df_ep[df_ep["season"] == "MAM"]
        for (r, c), grp in df_mam.groupby(["r", "c"]):
            grid_mam_delta_tau[r, c] = grp["delta_tau"].median()
            grid_mam_delta_theta_res[r, c] = grp["delta_theta_res"].median()
            
    df_fl_mam = df_floors[df_floors["saison"] == "MAM"]
    for _, row in df_fl_mam.iterrows():
        r = int(row["r"])
        c = int(row["c"])
        grid_mam_delta_p5[r, c] = row["delta_p5"]
        grid_mam_ol_margin_wlt[r, c] = row["ol_minus_smcwlt"]

    # -------------------------------------------------------------
    # 3. Synthèse par Saison x Texture avec Bootstrap par Blocs 7x7
    # -------------------------------------------------------------
    print("\n[INFO] Agrégation par Saison x Texture et Bootstrap par Blocs (IC 95%)...")
    summary_records = []
    
    target_textures = [6, 9, 12, 7, 3, 1] # Loam, Clay Loam, Clay, Sandy Clay Loam, Sandy Loam, Sand
    target_seasons = ["MAM", "SON", "DJF", "SECHE"]
    
    for s_name in target_seasons:
        sub_ep_season = df_ep[df_ep["season"] == s_name] if s_name != "SECHE" else df_ep[df_ep["season"].isin(["MAM", "JJA"])]
        sub_fl_season = df_floors[df_floors["saison"] == s_name]
        
        for st in target_textures:
            tex_name = TEXTURE_NAMES.get(st, f"Type_{st}")
            wlt_val = smcwlt_grid[soiltype == st][0]
            
            sub_ep = sub_ep_season[sub_ep_season["soiltype"] == st]
            sub_fl = sub_fl_season[sub_fl_season["soiltype"] == st]
            sub_fl_valid = sub_fl.dropna(subset=["delta_p5"])
            
            n_ep = len(sub_ep)
            n_pix_ep = sub_ep[["r", "c"]].drop_duplicates().shape[0] if n_ep > 0 else 0
            n_blk_ep = sub_ep["block_id"].nunique() if n_ep > 0 else 0
            n_pix_fl = len(sub_fl_valid)
            
            if n_ep >= 5:
                med_tau_smap = sub_ep["tau_smap"].median()
                med_tau_ol = sub_ep["tau_ol"].median()
                med_delta_tau = sub_ep["delta_tau"].median()
                
                med_res_smap = sub_ep["theta_res_smap"].median()
                med_res_ol = sub_ep["theta_res_ol"].median()
                med_delta_res = sub_ep["delta_theta_res"].median()
                
                ci_tau_smap = block_bootstrap_ci(sub_ep, "tau_smap")
                ci_tau_ol = block_bootstrap_ci(sub_ep, "tau_ol")
                ci_delta_tau = block_bootstrap_ci(sub_ep, "delta_tau")
                
                ci_res_smap = block_bootstrap_ci(sub_ep, "theta_res_smap")
                ci_res_ol = block_bootstrap_ci(sub_ep, "theta_res_ol")
                ci_delta_res = block_bootstrap_ci(sub_ep, "delta_theta_res")
            else:
                med_tau_smap = sub_ep["tau_smap"].median() if n_ep > 0 else np.nan
                med_tau_ol = sub_ep["tau_ol"].median() if n_ep > 0 else np.nan
                med_delta_tau = sub_ep["delta_tau"].median() if n_ep > 0 else np.nan
                med_res_smap = sub_ep["theta_res_smap"].median() if n_ep > 0 else np.nan
                med_res_ol = sub_ep["theta_res_ol"].median() if n_ep > 0 else np.nan
                med_delta_res = sub_ep["delta_theta_res"].median() if n_ep > 0 else np.nan
                ci_tau_smap = (np.nan, np.nan)
                ci_tau_ol = (np.nan, np.nan)
                ci_delta_tau = (np.nan, np.nan)
                ci_res_smap = (np.nan, np.nan)
                ci_res_ol = (np.nan, np.nan)
                ci_delta_res = (np.nan, np.nan)
                
            if len(sub_fl_valid) >= 5:
                med_delta_p5 = sub_fl_valid["delta_p5"].median()
                ci_delta_p5 = block_bootstrap_ci(sub_fl_valid, "delta_p5")
                frac_ol_gt_smap = (sub_fl_valid["ol_floor_gt_smap"] == 1).mean()
                med_margin_wlt = sub_fl_valid["ol_minus_smcwlt"].median()
            else:
                med_delta_p5 = np.nan
                ci_delta_p5 = (np.nan, np.nan)
                frac_ol_gt_smap = np.nan
                med_margin_wlt = np.nan
                
            summary_records.append({
                "saison": s_name,
                "texture_id": st,
                "texture_nom": tex_name,
                "smcwlt": wlt_val,
                "n_episodes": n_ep,
                "n_pixels_episodes": n_pix_ep,
                "n_blocs_36km": n_blk_ep,
                "tau_smap_med": med_tau_smap,
                "tau_smap_ci95_bas": ci_tau_smap[0],
                "tau_smap_ci95_haut": ci_tau_smap[1],
                "tau_ol_med": med_tau_ol,
                "tau_ol_ci95_bas": ci_tau_ol[0],
                "tau_ol_ci95_haut": ci_tau_ol[1],
                "delta_tau_med": med_delta_tau,
                "delta_tau_ci95_bas": ci_delta_tau[0],
                "delta_tau_ci95_haut": ci_delta_tau[1],
                "theta_res_smap_med": med_res_smap,
                "theta_res_smap_ci95_bas": ci_res_smap[0],
                "theta_res_smap_ci95_haut": ci_res_smap[1],
                "theta_res_ol_med": med_res_ol,
                "theta_res_ol_ci95_bas": ci_res_ol[0],
                "theta_res_ol_ci95_haut": ci_res_ol[1],
                "delta_theta_res_med": med_delta_res,
                "delta_theta_res_ci95_bas": ci_delta_res[0],
                "delta_theta_res_ci95_haut": ci_delta_res[1],
                "n_pixels_p5": n_pix_fl,
                "delta_p5_med": med_delta_p5,
                "delta_p5_ci95_bas": ci_delta_p5[0],
                "delta_p5_ci95_haut": ci_delta_p5[1],
                "ol_p5_minus_smcwlt_med": med_margin_wlt,
                "frac_pixels_ol_floor_gt_smap": frac_ol_gt_smap,
            })
            
    df_summary = pd.DataFrame(summary_records)
    df_summary.to_csv(os.path.join(OUTPUT_DIR, "drydown_season_texture_summary.csv"), index=False, float_format="%.5f")
    print(f"[INFO] Table récapitulative sauvegardée dans drydown_season_texture_summary.csv")

    # -------------------------------------------------------------
    # 4. Cartes spatiales MAM (Delta tau, Delta theta_res, Delta P5, Marge WLT)
    # -------------------------------------------------------------
    print("\n[INFO] Génération des cartes spatiales MAM...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    fig.patch.set_facecolor("#FFFFFF")
    
    cmap_div = plt.cm.RdBu_r
    
    # (a) Delta tau MAM (OL - SMAP)
    ax1 = axes[0, 0]
    im1 = ax1.pcolormesh(lon, lat, grid_mam_delta_tau, cmap=cmap_div, vmin=-15, vmax=15, shading="auto")
    ax1.set_title(r"(a) $\Delta\tau$ (OL − SMAP) en MAM [jours]", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Latitude [°N]", fontsize=10)
    plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04, label="Jours (>0: OL sèche plus lentement)")
    
    # (b) Delta theta_res MAM (OL - SMAP)
    ax2 = axes[0, 1]
    im2 = ax2.pcolormesh(lon, lat, grid_mam_delta_theta_res, cmap=cmap_div, vmin=-0.10, vmax=0.10, shading="auto")
    ax2.set_title(r"(b) $\Delta\theta_{res}$ (OL − SMAP) en MAM [$\mathrm{m^3/m^3}$]", fontsize=11, fontweight="bold")
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04, label=r"$\mathrm{m^3/m^3}$ (>0: plancher OL plus élevé)")
    
    # (c) Delta P5 MAM (Plancher empirique OL - SMAP)
    ax3 = axes[1, 0]
    im3 = ax3.pcolormesh(lon, lat, grid_mam_delta_p5, cmap=cmap_div, vmin=-0.08, vmax=0.08, shading="auto")
    ax3.set_title(r"(c) Écart des planchers empiriques (P5 OL − P5 SMAP) en MAM", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Longitude [°E]", fontsize=10)
    ax3.set_ylabel("Latitude [°N]", fontsize=10)
    plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04, label=r"$\mathrm{m^3/m^3}$")
    
    # (d) Marge au-dessus de SMCWLT en MAM (P5 OL - SMCWLT)
    ax4 = axes[1, 1]
    im4 = ax4.pcolormesh(lon, lat, grid_mam_ol_margin_wlt, cmap="viridis", vmin=-0.02, vmax=0.12, shading="auto")
    ax4.set_title(r"(d) Distance de l'OL au point de flétrissement (P5 OL − SMCWLT) en MAM", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Longitude [°E]", fontsize=10)
    plt.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04, label=r"$\mathrm{m^3/m^3}$ (>0: OL reste au-dessus de SMCWLT)")
    
    for ax in axes.flat:
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.6)
        
    fig.suptitle("Dynamiques de séchage au printemps (MAM) : Comparaison SMAP vs Open-Loop (OL)", fontsize=13, fontweight="heavy", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    maps_png = os.path.join(OUTPUT_DIR, "maps_mam_drydown_dynamics.png")
    maps_pdf = os.path.join(OUTPUT_DIR, "maps_mam_drydown_dynamics.pdf")
    plt.savefig(maps_png, dpi=300, bbox_inches="tight")
    plt.savefig(maps_pdf, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Cartes spatiales sauvegardées dans {maps_png} et {maps_pdf}.")

    # -------------------------------------------------------------
    # 5. Figure de synthèse : Distributions par texture SMAP vs OL
    # -------------------------------------------------------------
    print("\n[INFO] Génération de la figure de synthèse des distributions...")
    df_mam_ep = df_ep[df_ep["season"] == "MAM"]
    plot_textures = [6, 9, 12, 7] # Loam, Clay Loam, Clay, Sandy Clay Loam
    plot_labels = [TEXTURE_NAMES[st] for st in plot_textures]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#FFFFFF")
    
    # Panel 1 : Temps caractéristique tau (SMAP vs OL)
    ax1 = axes[0]
    ax1.set_facecolor("#FAFAFA")
    
    pos = np.arange(len(plot_textures))
    width = 0.35
    
    for i, st in enumerate(plot_textures):
        sub = df_mam_ep[df_mam_ep["soiltype"] == st]
        if len(sub) > 0:
            tau_s = sub["tau_smap"].values
            tau_o = sub["tau_ol"].values
            
            b1 = ax1.boxplot(tau_s, positions=[pos[i] - width/2], widths=width*0.8,
                             patch_artist=True, boxprops=dict(facecolor="#2b5c8f", color="black", alpha=0.8),
                             medianprops=dict(color="yellow", linewidth=2), showfliers=False)
            b2 = ax1.boxplot(tau_o, positions=[pos[i] + width/2], widths=width*0.8,
                             patch_artist=True, boxprops=dict(facecolor="#e7298a", color="black", alpha=0.8),
                             medianprops=dict(color="yellow", linewidth=2), showfliers=False)
            
            n_val = len(sub)
            ax1.annotate(f"N={n_val}", (pos[i], 32), ha="center", fontsize=9, fontweight="bold", color="#333333")
            
    ax1.set_xticks(pos)
    ax1.set_xticklabels(plot_labels, fontsize=10, fontweight="bold")
    ax1.set_ylabel(r"Temps caractéristique de séchage $\tau$ [jours]", fontsize=11, fontweight="bold")
    ax1.set_title(r"(a) Dynamique de séchage en MAM ($\tau$ : plus grand = séchage plus lent)", fontsize=11, fontweight="bold", pad=10)
    ax1.set_ylim(0, 35)
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    import matplotlib.patches as mpatches
    p_smap = mpatches.Patch(facecolor="#2b5c8f", edgecolor="black", label="SMAP (L3_SM_P_E, QC)")
    p_ol = mpatches.Patch(facecolor="#e7298a", edgecolor="black", label="Open-Loop (Noah-MP)")
    ax1.legend(handles=[p_smap, p_ol], loc="upper right", frameon=True, facecolor="white")

    # Panel 2 : Humidité résiduelle theta_res et plancher P5 vs SMCWLT
    ax2 = axes[1]
    ax2.set_facecolor("#FAFAFA")
    
    for i, st in enumerate(plot_textures):
        sub = df_mam_ep[df_mam_ep["soiltype"] == st]
        wlt = smcwlt_grid[soiltype == st][0]
        
        if len(sub) > 0:
            res_s = sub["theta_res_smap"].values
            res_o = sub["theta_res_ol"].values
            
            ax2.boxplot(res_s, positions=[pos[i] - width/2], widths=width*0.8,
                        patch_artist=True, boxprops=dict(facecolor="#2b5c8f", color="black", alpha=0.8),
                        medianprops=dict(color="yellow", linewidth=2), showfliers=False)
            ax2.boxplot(res_o, positions=[pos[i] + width/2], widths=width*0.8,
                        patch_artist=True, boxprops=dict(facecolor="#e7298a", color="black", alpha=0.8),
                        medianprops=dict(color="yellow", linewidth=2), showfliers=False)
            
        ax2.hlines(wlt, pos[i] - width*0.9, pos[i] + width*0.9, colors="#d95f02", linestyles="--", linewidth=2.0)
        ax2.annotate(f"WLT={wlt:.3f}", (pos[i] + width*0.95, wlt), va="center", fontsize=8, color="#d95f02", fontweight="bold")
        
    ax2.set_xticks(pos)
    ax2.set_xticklabels(plot_labels, fontsize=10, fontweight="bold")
    ax2.set_ylabel(r"Humidité résiduelle $\theta_{res}$ [$\mathrm{m^3/m^3}$]", fontsize=11, fontweight="bold")
    ax2.set_title(r"(b) Plancher asymptotique $\theta_{res}$ vs Point de flétrissement (WLT)", fontsize=11, fontweight="bold", pad=10)
    ax2.set_ylim(0.0, 0.28)
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    p_wlt = plt.Line2D([0], [0], color="#d95f02", linestyle="--", linewidth=2, label="Point de flétrissement (SMCWLT)")
    ax2.legend(handles=[p_smap, p_ol, p_wlt], loc="upper left", frameon=True, facecolor="white")

    fig.suptitle("Synthèse Étape 1 : Vitesse de séchage et planchers empiriques selon la texture du sol (MAM)", fontsize=13, fontweight="heavy", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    dist_png = os.path.join(OUTPUT_DIR, "drydown_synthesis_distributions.png")
    dist_pdf = os.path.join(OUTPUT_DIR, "drydown_synthesis_distributions.pdf")
    plt.savefig(dist_png, dpi=300, bbox_inches="tight")
    plt.savefig(dist_pdf, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Figure de synthèse sauvegardée dans {dist_png} et {dist_pdf}.")

    print("\n=================================================================")
    print(" SCRIPT ÉTAPE 1 EXÉCUTÉ AVEC SUCCÈS !")
    print("=================================================================")

if __name__ == "__main__":
    main()
