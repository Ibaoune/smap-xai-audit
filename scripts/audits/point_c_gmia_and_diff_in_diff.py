#!/usr/bin/env python3
"""
point_c_gmia_and_diff_in_diff.py
--------------------------------
Point C : Analyse de la relation entre l'écart SMAP - OL et l'irrigation GMIA
1. Agrégation de la fraction irriguée GMIA à ~36 km (empreinte SMAP).
   Comparaison par classes (0-1%, 1-10%, 10-30%, >30%) pour :
   - (a) Toutes obs brutes valides
   - (b) Obs acceptées par le QC
2. Différence de différences :
   Accroissement estival D = mean(SMAP - OL)_JA - mean(SMAP - OL)_MA
   Comparaison de cet accroissement entre classes d'irrigation à occupation du sol égale :
   - Cultures seulement (classe 12, et 12+14)
   - Cultures + Prairies (classes 12+10, et 12+14+10)
   Calculé pour 2018 et pour la période 5 ans (2016-2020).
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc
from scipy.ndimage import uniform_filter
from scipy.interpolate import RegularGridInterpolator

BASE_DA = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
BASE_OL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"
GMIA_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/GMIA/gmia_v5_aei_pct.asc"

def load_static():
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
        texture = ds.variables["TEXTURE"][:] # (16, 121, 181)
        landcover = ds.variables["LANDCOVER"][:] # (20, 121, 181)
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]
        
    soiltype = np.argmax(texture, axis=0) + 1
    vegt = np.argmax(landcover, axis=0) + 1
    
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
        
    return landmask, soiltype, vegt, smcwlt_grid, lat, lon

def load_gmia_36km(target_lat, target_lon, landmask):
    """Lit GMIA, rééchantillonne à 5 km, puis agrège à ~36 km (fenêtre 7x7)."""
    with open(GMIA_PATH, "r") as f:
        header = {}
        for _ in range(6):
            parts = f.readline().split()
            header[parts[0].lower()] = float(parts[1])
            
    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    xll = header["xllcorner"]
    yll = header["yllcorner"]
    cell = header["cellsize"]
    
    gmia_lons = xll + (np.arange(ncols) + 0.5) * cell
    gmia_lats = (yll + nrows * cell) - (np.arange(nrows) + 0.5) * cell
    
    lat_min, lat_max = target_lat.min() - 0.2, target_lat.max() + 0.2
    lon_min, lon_max = target_lon.min() - 0.2, target_lon.max() + 0.2
    
    r_idx = np.where((gmia_lats >= lat_min) & (gmia_lats <= lat_max))[0]
    c_idx = np.where((gmia_lons >= lon_min) & (gmia_lons <= lon_max))[0]
    
    bin_path = GMIA_PATH.replace(".asc", ".bin")
    if os.path.exists(bin_path):
        gmia_full = np.fromfile(bin_path, dtype=np.float32).reshape(nrows, ncols)
    else:
        gmia_full = np.loadtxt(GMIA_PATH, skiprows=6)
        
    gmia_sub = gmia_full[r_idx[0]:r_idx[-1]+1, c_idx[0]:c_idx[-1]+1]
    sub_lats = gmia_lats[r_idx[0]:r_idx[-1]+1]
    sub_lons = gmia_lons[c_idx[0]:c_idx[-1]+1]
    gmia_sub[gmia_sub < 0] = 0.0
    
    interp = RegularGridInterpolator((sub_lats[::-1], sub_lons), gmia_sub[::-1, :],
                                     bounds_error=False, fill_value=0.0)
    pts = np.stack([target_lat.ravel(), target_lon.ravel()], axis=-1)
    gmia_5km = interp(pts).reshape(target_lat.shape)
    
    # Agrégation à ~36 km : fenêtre 7x7 (35 km à 5 km/pixel)
    # Prise en compte du masque de terre pour normaliser
    land_float = (landmask == 1).astype(float)
    gmia_masked = gmia_5km * land_float
    
    # Convolution uniforme 7x7
    k = 7
    num = uniform_filter(gmia_masked, size=k, mode='constant', cval=0.0) * (k*k)
    denom = uniform_filter(land_float, size=k, mode='constant', cval=0.0) * (k*k)
    
    gmia_36km = np.zeros_like(gmia_5km)
    valid_denom = denom > 0
    gmia_36km[valid_denom] = num[valid_denom] / denom[valid_denom]
    gmia_36km[landmask == 0] = 0.0
    
    return gmia_5km, gmia_36km

def read_daobs_file(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def find_ol_file(date_dt):
    next_dt = date_dt + datetime.timedelta(days=1)
    dstr = next_dt.strftime("%Y%m%d")
    target = f"LIS_HIST_{dstr}0000.d01.nc"
    ym_cur = date_dt.strftime("%Y-%m")
    ym_cur_c = date_dt.strftime("%Y%m")
    ym_next = next_dt.strftime("%Y-%m")
    ym_next_c = next_dt.strftime("%Y%m")
    
    cands = [
        os.path.join(BASE_OL, ym_cur, "SURFACEMODEL", ym_cur_c, target),
        os.path.join(BASE_OL, ym_cur, "SURFACEMODEL", ym_next_c, target),
        os.path.join(BASE_OL, ym_next, "SURFACEMODEL", ym_next_c, target),
        os.path.join("/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/combined_OPL_noirr/SURFACEMODEL", ym_cur_c, target),
        os.path.join("/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/combined_OPL_noirr/SURFACEMODEL", ym_next_c, target),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return None

def compute_season_bias(years, months, landmask):
    """Calcule pour chaque pixel la moyenne de (SMAP - OL) sur la période spécifiée."""
    land_bool = (landmask == 1)
    sum_a = np.zeros((121, 181), dtype=float)
    cnt_a = np.zeros((121, 181), dtype=int)
    sum_b = np.zeros((121, 181), dtype=float)
    cnt_b = np.zeros((121, 181), dtype=int)
    
    ol_cache = {}
    for y in years:
        for m in months:
            ym_str = f"{y}-{m:02d}"
            ym_compact = f"{y}{m:02d}"
            daobs_dir = os.path.join(BASE_DA, ym_str, "DAOBS", ym_compact)
            files = sorted(glob.glob(os.path.join(daobs_dir, "LISDAOBS_*.1gs4r")))
            for df in files:
                fname = os.path.basename(df)
                dt_str = fname.split("_")[1][:8]
                dt = datetime.datetime.strptime(dt_str, "%Y%m%d").date()
                if dt not in ol_cache:
                    ol_f = find_ol_file(dt)
                    if ol_f is not None:
                        with nc.Dataset(ol_f) as ds:
                            ol_cache[dt] = ds.variables["SoilMoist_tavg"][0, :, :].squeeze()
                    else:
                        ol_cache[dt] = None
                ol_sm = ol_cache[dt]
                if ol_sm is None:
                    continue
                rec1, rec2 = read_daobs_file(df)
                val_a = (rec1 != -9999.0) & np.isfinite(rec1) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                val_b = (rec2 != -9999.0) & np.isfinite(rec2) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                
                diff = rec1 - ol_sm
                sum_a[val_a] += diff[val_a]
                cnt_a[val_a] += 1
                sum_b[val_b] += diff[val_b]
                cnt_b[val_b] += 1
                
    mean_a = np.full((121, 181), np.nan)
    mean_b = np.full((121, 181), np.nan)
    
    valid_a = cnt_a >= 10
    mean_a[valid_a] = sum_a[valid_a] / cnt_a[valid_a]
    valid_b = cnt_b >= 10
    mean_b[valid_b] = sum_b[valid_b] / cnt_b[valid_b]
    
    return mean_a, mean_b, cnt_a, cnt_b

def run_point_c():
    print("=================================================================")
    print(" POINT C : ANALYSE IRRIGATION GMIA & DIFFÉRENCE DE DIFFÉRENCES")
    print("=================================================================")
    landmask, soiltype, vegt, smcwlt_grid, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    gmia_5km, gmia_36km = load_gmia_36km(lat, lon, landmask)
    
    print("\n[INFO] Distribution GMIA agrégée à ~36 km sur pixels terre :")
    print(f"  Min = {gmia_36km[land_bool].min():.2f}%, Max = {gmia_36km[land_bool].max():.2f}%, Moyenne = {gmia_36km[land_bool].mean():.2f}%")
    
    classes_36km = [
        ("0–1 %", (gmia_36km >= 0.0) & (gmia_36km <= 1.0)),
        ("1–10 %", (gmia_36km > 1.0) & (gmia_36km <= 10.0)),
        ("10–30 %", (gmia_36km > 10.0) & (gmia_36km <= 30.0)),
        ("> 30 %", (gmia_36km > 30.0)),
    ]
    
    # -------------------------------------------------------------
    # C.1 : Comparaison par classes GMIA 36 km (Juillet-Août 2016-2020)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 1. COMPARAISON PAR CLASSES GMIA AGRÉGÉES À 36 KM (JA 2016-2020)")
    print("-------------------------------------------------------------")
    print("Calcul des écarts SMAP - OL pour Juillet-Août (2016-2020)...")
    mean_a_ja, mean_b_ja, cnt_a_ja, cnt_b_ja = compute_season_bias([2016, 2017, 2018, 2019, 2020], [7, 8], landmask)
    
    print("\n--- A. SUR PIXELS NON-FORÊT (vegt > 4) ---")
    print(f"{'Classe GMIA 36km':<12} | {'N pixels':<8} | {'(a) Toutes obs: Moy':<20} | {'(a) Méd':<10} | {'(b) QC acc: Moy':<18} | {'(b) Méd':<10} | {'Delta (b)-(a)':<12}")
    print("-" * 105)
    for c_name, c_mask in classes_36km:
        m = c_mask & non_forest & np.isfinite(mean_a_ja) & np.isfinite(mean_b_ja)
        n_p = np.sum(m)
        if n_p > 0:
            va = mean_a_ja[m]
            vb = mean_b_ja[m]
            del_val = vb.mean() - va.mean()
            print(f"{c_name:<12} | {n_p:<8} | {va.mean():+.5f} m3/m3        | {np.median(va):+.5f}  | {vb.mean():+.5f} m3/m3      | {np.median(vb):+.5f}  | {del_val:+.5f}")
            
    print("\n--- B. SUR TOUS LES PIXELS TERRE VALIDES ---")
    print(f"{'Classe GMIA 36km':<12} | {'N pixels':<8} | {'(a) Toutes obs: Moy':<20} | {'(a) Méd':<10} | {'(b) QC acc: Moy':<18} | {'(b) Méd':<10} | {'Delta (b)-(a)':<12}")
    print("-" * 105)
    for c_name, c_mask in classes_36km:
        m = c_mask & land_bool & np.isfinite(mean_a_ja) & np.isfinite(mean_b_ja)
        n_p = np.sum(m)
        if n_p > 0:
            va = mean_a_ja[m]
            vb = mean_b_ja[m]
            del_val = vb.mean() - va.mean()
            print(f"{c_name:<12} | {n_p:<8} | {va.mean():+.5f} m3/m3        | {np.median(va):+.5f}  | {vb.mean():+.5f} m3/m3      | {np.median(vb):+.5f}  | {del_val:+.5f}")

    # -------------------------------------------------------------
    # C.2 : Différence de Différences (Juillet-Août vs Mars-Avril)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 2. DIFFÉRENCE DE DIFFÉRENCES : (SMAP - OL)_JA - (SMAP - OL)_MA")
    print("-------------------------------------------------------------")
    print("Calcul des écarts SMAP - OL pour Mars-Avril (2016-2020)...")
    mean_a_ma, mean_b_ma, cnt_a_ma, cnt_b_ma = compute_season_bias([2016, 2017, 2018, 2019, 2020], [3, 4], landmask)
    
    # Accroissement estival D = mean_a_ja - mean_a_ma (toutes obs valides)
    diff_in_diff = mean_a_ja - mean_a_ma
    valid_did = land_bool & np.isfinite(diff_in_diff) & (cnt_a_ja >= 10) & (cnt_a_ma >= 10)
    
    # Définition des masques d'occupation du sol (MODIS-IGBP) :
    # 12 = Croplands
    # 14 = Cropland / natural vegetation mosaic
    # 10 = Grasslands
    is_crop_pure = (vegt == 12)
    is_crop_all = (vegt == 12) | (vegt == 14)
    is_crop_grass = (vegt == 12) | (vegt == 10)
    is_crop_grass_all = (vegt == 12) | (vegt == 14) | (vegt == 10)
    
    def report_did(subset_name, subset_mask):
        print(f"\n>>> Occupation du sol : {subset_name}")
        print(f"{'Classe GMIA 36km':<12} | {'N pixels':<8} | {'Diff-in-Diff D (JA-MA) Moy':<26} | {'Médiane':<10} | {'SMAP-OL JA':<14} | {'SMAP-OL MA':<14}")
        print("-" * 95)
        for c_name, c_mask in classes_36km:
            m = valid_did & subset_mask & c_mask
            n_p = np.sum(m)
            if n_p > 0:
                vals_d = diff_in_diff[m]
                vals_ja = mean_a_ja[m]
                vals_ma = mean_a_ma[m]
                print(f"{c_name:<12} | {n_p:<8} | {vals_d.mean():+.5f} m3/m3            | {np.median(vals_d):+.5f}  | {vals_ja.mean():+.5f} m3/m3 | {vals_ma.mean():+.5f} m3/m3")
            else:
                print(f"{c_name:<12} | 0        | N/A                        | N/A        | N/A            | N/A")

    report_did("CULTURES SEULEMENT (Classe 12 Croplands)", is_crop_pure)
    report_did("CULTURES + MOSAÏQUE (Classes 12 + 14)", is_crop_all)
    report_did("CULTURES + PRAIRIES (Classes 12 + 10)", is_crop_grass)
    report_did("CULTURES + MOSAÏQUE + PRAIRIES (Classes 12 + 14 + 10)", is_crop_grass_all)
    report_did("TOUTES OCCUPATIONS NON-FORÊT (vegt > 4)", non_forest)

    # Même calcul restreint à l'année 2018 seule
    print("\n-------------------------------------------------------------")
    print(" 2b. DIFFÉRENCE DE DIFFÉRENCES SPÉCIFIQUE À 2018")
    print("-------------------------------------------------------------")
    mean_a_ja_18, _, cnt_ja_18, _ = compute_season_bias([2018], [7, 8], landmask)
    mean_a_ma_18, _, cnt_ma_18, _ = compute_season_bias([2018], [3, 4], landmask)
    did_18 = mean_a_ja_18 - mean_a_ma_18
    valid_did_18 = land_bool & np.isfinite(did_18) & (cnt_ja_18 >= 10) & (cnt_ma_18 >= 10)
    
    def report_did_18(subset_name, subset_mask):
        print(f"\n>>> [2018] Occupation du sol : {subset_name}")
        print(f"{'Classe GMIA 36km':<12} | {'N pixels':<8} | {'Diff-in-Diff D (JA-MA) Moy':<26} | {'Médiane':<10} | {'SMAP-OL JA':<14} | {'SMAP-OL MA':<14}")
        print("-" * 95)
        for c_name, c_mask in classes_36km:
            m = valid_did_18 & subset_mask & c_mask
            n_p = np.sum(m)
            if n_p > 0:
                vals_d = did_18[m]
                vals_ja = mean_a_ja_18[m]
                vals_ma = mean_a_ma_18[m]
                print(f"{c_name:<12} | {n_p:<8} | {vals_d.mean():+.5f} m3/m3            | {np.median(vals_d):+.5f}  | {vals_ja.mean():+.5f} m3/m3 | {vals_ma.mean():+.5f} m3/m3")
            else:
                print(f"{c_name:<12} | 0        | N/A                        | N/A        | N/A            | N/A")

    report_did_18("CULTURES SEULEMENT (Classe 12)", is_crop_pure)
    report_did_18("CULTURES + PRAIRIES (Classes 12 + 10)", is_crop_grass)

if __name__ == "__main__":
    run_point_c()
