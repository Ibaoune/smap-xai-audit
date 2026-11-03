#!/usr/bin/env python3
"""
point_b_hourly_diurnal_analysis.py
----------------------------------
Point B : Analyse de l'OL horaire (Juillet 2018)
1. Calcul du cycle diurne moyen par pixel :
   - SoilMoist couche 1 à 06h UTC - moyenne journalière
   - SoilMoist couche 1 à 18h UTC - moyenne journalière
   - Moyenne spatiale globale, par classe de végétation et par décile de rejet de flétrissement.
2. Évaluation homogène SMAP brut - OL à l'heure exacte de passage vs moyenne journalière :
   - Calcul sur (a) toutes les obs valides et (b) obs acceptées QC.
   - Troncature intra-pixel delta = (b) - (a) à l'heure du passage vs journalier.
3. Croisement spatial avec la carte d'irrigation GMIA (FAO AEI).
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_HOURLY = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_hourly_201807/output/2018-07/SURFACEMODEL/201807"
BASE_DA = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output/2018-07/DAOBS/201807"
BASE_DAILY_OL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"
GMIA_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/GMIA/gmia_v5_aei_pct.asc"
OUT_DIR = "/home/mohammad.elaabaribao/.gemini/antigravity-ide/brain/f92c66df-785d-4977-8b4d-c2f5a0bda26d"

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

def read_daobs(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def load_gmia_resampled(target_lat, target_lon):
    """Lit et rééchantillonne gmia_v5_aei_pct.asc sur la grille NorthMor."""
    print("Lecture et rééchantillonnage de la carte GMIA...")
    # Lire l'en-tête
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
    nodata = header["nodata_value"]
    
    # Coordonnées du raster GMIA
    # x: centres de cellules de xll + cell/2 à xll + ncols*cell - cell/2
    # y: de haut en bas, yll + nrows*cell - cell/2 à yll + cell/2
    gmia_lons = xll + (np.arange(ncols) + 0.5) * cell
    gmia_lats = (yll + nrows * cell) - (np.arange(nrows) + 0.5) * cell
    
    # Déterminer la sous-boîte englobant NorthMor [lat 30-36, lon -10 to -1]
    lat_min, lat_max = target_lat.min() - 0.2, target_lat.max() + 0.2
    lon_min, lon_max = target_lon.min() - 0.2, target_lon.max() + 0.2
    
    r_idx = np.where((gmia_lats >= lat_min) & (gmia_lats <= lat_max))[0]
    c_idx = np.where((gmia_lons >= lon_min) & (gmia_lons <= lon_max))[0]
    
    # Lire seulement le sous-ensemble avec numpy depuis le fichier ASCII ou binaire
    # Pour faire simple et robuste, on utilise gmia_v5_aei_pct.bin s'il existe
    bin_path = GMIA_PATH.replace(".asc", ".bin")
    if os.path.exists(bin_path):
        gmia_full = np.fromfile(bin_path, dtype=np.float32).reshape(nrows, ncols)
    else:
        # fallback asc
        gmia_full = np.loadtxt(GMIA_PATH, skiprows=6)
        
    gmia_sub = gmia_full[r_idx[0]:r_idx[-1]+1, c_idx[0]:c_idx[-1]+1]
    sub_lats = gmia_lats[r_idx[0]:r_idx[-1]+1]
    sub_lons = gmia_lons[c_idx[0]:c_idx[-1]+1]
    
    # Remplacer nodata par 0.0
    gmia_sub[gmia_sub < 0] = 0.0
    
    # Interpolation plus proche voisin ou bilinéaire sur target_lat, target_lon
    from scipy.interpolate import RegularGridInterpolator
    interp = RegularGridInterpolator((sub_lats[::-1], sub_lons), gmia_sub[::-1, :],
                                     bounds_error=False, fill_value=0.0)
    
    pts = np.stack([target_lat.ravel(), target_lon.ravel()], axis=-1)
    gmia_resampled = interp(pts).reshape(target_lat.shape)
    return gmia_resampled

def run_point_b():
    print("==================================================")
    print(" POINT B : ANALYSE OL HORAIRE JUILLET 2018")
    print("==================================================")
    landmask, soiltype, vegt, smcwlt_grid, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    # 1. Vérification de la complétude des sorties horaires
    hourly_files = sorted(glob.glob("/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_hourly_201807/output/2018-07/SURFACEMODEL/*/LIS_HIST_*.d01.nc"))
    print(f"Nombre de fichiers horaires trouvés : {len(hourly_files)}")
    if len(hourly_files) < 744: # 31 * 24 = 744 heures
        print(f"ATTENTION : Seulement {len(hourly_files)}/744 fichiers disponibles. Simulation non terminée !")
        return False
        
    print("Chargement des séries temporelles horaires (744 heures)...")
    # Construire la grille horaire [744, 121, 181]
    # Ou calculer jour par jour pour économiser la RAM
    
    diff_06h_list = [] # sm(06h) - sm_daily
    diff_18h_list = [] # sm(18h) - sm_daily
    
    daily_means = {} # dt -> 2D array
    hourly_sm = {}   # (dt, hour) -> 2D array
    
    days = list(range(1, 32))
    for d in days:
        dt = datetime.date(2018, 7, d)
        day_hours = []
        for h in range(1, 25):
            if h < 24:
                ts = f"201807{d:02d}{h:02d}00"
            else:
                next_d = dt + datetime.timedelta(days=1)
                ts = f"{next_d.strftime('%Y%m%d')}0000"
            cands = glob.glob(f"/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_hourly_201807/output/2018-07/SURFACEMODEL/*/LIS_HIST_{ts}.d01.nc")
            if not cands:
                raise FileNotFoundError(f"Fichier manquant pour timestamp {ts}")
            hf = cands[0]
                
            with nc.Dataset(hf) as ds:
                sm_h = ds.variables["SoilMoist_tavg"][0, :, :].squeeze()
                day_hours.append(sm_h)
                hourly_sm[(dt, h)] = sm_h
                
        day_stack = np.stack(day_hours, axis=0) # (24, 121, 181)
        sm_daily = np.mean(day_stack, axis=0)
        daily_means[dt] = sm_daily
        
        # 06h UTC (h=6) et 18h UTC (h=18)
        sm_06h = hourly_sm[(dt, 6)]
        sm_18h = hourly_sm[(dt, 18)]
        
        diff_06h_list.append(sm_06h - sm_daily)
        diff_18h_list.append(sm_18h - sm_daily)
        
    mean_diff_06h = np.mean(np.stack(diff_06h_list, axis=0), axis=0)
    mean_diff_18h = np.mean(np.stack(diff_18h_list, axis=0), axis=0)
    
    print("\n--- 1. CYCLE DIURNE MOYEN (JUILLET 2018) ---")
    print(f"06h UTC - Moyenne journalière (Terre)       : Moy = {mean_diff_06h[land_bool].mean():+.5f} m3/m3, Médiane = {np.median(mean_diff_06h[land_bool]):+.5f}")
    print(f"06h UTC - Moyenne journalière (Non-forêt)   : Moy = {mean_diff_06h[non_forest].mean():+.5f} m3/m3, Médiane = {np.median(mean_diff_06h[non_forest]):+.5f}")
    print(f"18h UTC - Moyenne journalière (Terre)       : Moy = {mean_diff_18h[land_bool].mean():+.5f} m3/m3, Médiane = {np.median(mean_diff_18h[land_bool]):+.5f}")
    print(f"18h UTC - Moyenne journalière (Non-forêt)   : Moy = {mean_diff_18h[non_forest].mean():+.5f} m3/m3, Médiane = {np.median(mean_diff_18h[non_forest]):+.5f}")
    
    # 2. Comparaison avec les observations SMAP (DAOBS)
    print("\n--- 2. CONFRONTATION AVEC LES OBSERVATIONS SMAP (DAOBS) ---")
    daobs_files = sorted(glob.glob(os.path.join(BASE_DA, "LISDAOBS_201807*.1gs4r")))
    print(f"Nombre de fichiers DAOBS pour Juillet 2018 : {len(daobs_files)}")
    
    # Accumulateurs pixel
    sum_a_hourly = np.zeros((121, 181), dtype=float)
    cnt_a_hourly = np.zeros((121, 181), dtype=int)
    
    sum_b_hourly = np.zeros((121, 181), dtype=float)
    cnt_b_hourly = np.zeros((121, 181), dtype=int)
    
    sum_a_daily = np.zeros((121, 181), dtype=float)
    cnt_a_daily = np.zeros((121, 181), dtype=int)
    
    sum_b_daily = np.zeros((121, 181), dtype=float)
    cnt_b_daily = np.zeros((121, 181), dtype=int)
    
    cnt_wilt_rej = np.zeros((121, 181), dtype=int)
    
    # Pool list
    pool_diff_a_h = []
    pool_diff_b_h = []
    pool_diff_a_d = []
    pool_diff_b_d = []
    
    for df in daobs_files:
        fname = os.path.basename(df)
        dt_str = fname.split("_")[1][:8]
        hh_str = fname.split("_")[1][8:10]
        dt = datetime.datetime.strptime(dt_str, "%Y%m%d").date()
        hour = int(hh_str)
        
        # LIS horaire est horodaté à l'heure d'accumulation [1..24]
        # Si DAOBS est à 06:00, l'intervalle 05-06h est dans LIS_HIST_...0600.
        # Si DAOBS est à 00:00 (rare), c'est l'heure 24 du jour précédent.
        if hour == 0:
            h_key = (dt - datetime.timedelta(days=1), 24)
        else:
            h_key = (dt, hour)
            
        if h_key not in hourly_sm or dt not in daily_means:
            continue
            
        ol_h = hourly_sm[h_key]
        ol_d = daily_means[dt]
        
        rec1, rec2 = read_daobs(df)
        
        # Validité
        val_a = (rec1 != -9999.0) & np.isfinite(rec1) & land_bool & (ol_h != -9999.0) & np.isfinite(ol_h)
        val_b = (rec2 != -9999.0) & np.isfinite(rec2) & land_bool & (ol_h != -9999.0) & np.isfinite(ol_h)
        
        diff_a_h = rec1 - ol_h
        diff_b_h = rec1 - ol_h
        
        diff_a_d = rec1 - ol_d
        diff_b_d = rec1 - ol_d
        
        sum_a_hourly[val_a] += diff_a_h[val_a]
        cnt_a_hourly[val_a] += 1
        sum_b_hourly[val_b] += diff_b_h[val_b]
        cnt_b_hourly[val_b] += 1
        
        sum_a_daily[val_a] += diff_a_d[val_a]
        cnt_a_daily[val_a] += 1
        sum_b_daily[val_b] += diff_b_d[val_b]
        cnt_b_daily[val_b] += 1
        
        pool_diff_a_h.extend(diff_a_h[val_a & non_forest].tolist())
        pool_diff_b_h.extend(diff_b_h[val_b & non_forest].tolist())
        pool_diff_a_d.extend(diff_a_d[val_a & non_forest].tolist())
        pool_diff_b_d.extend(diff_b_d[val_b & non_forest].tolist())
        
        wilt_rej = val_a & non_forest & ((rec2 == -9999.0) | (~np.isfinite(rec2))) & ((rec1 - smcwlt_grid) < 0.02)
        cnt_wilt_rej[wilt_rej] += 1
        
    qual_mask = non_forest & (cnt_a_hourly >= 10) & (cnt_b_hourly > 0)
    print(f"Nombre de pixels non-forêt qualifiés (>= 10 obs en juillet 2018) : {np.sum(qual_mask)}")
    
    mean_a_h = np.full((121, 181), np.nan)
    mean_b_h = np.full((121, 181), np.nan)
    mean_a_d = np.full((121, 181), np.nan)
    mean_b_d = np.full((121, 181), np.nan)
    
    mean_a_h[qual_mask] = sum_a_hourly[qual_mask] / cnt_a_hourly[qual_mask]
    mean_b_h[qual_mask] = sum_b_hourly[qual_mask] / cnt_b_hourly[qual_mask]
    delta_h = mean_b_h - mean_a_h
    
    mean_a_d[qual_mask] = sum_a_daily[qual_mask] / cnt_a_daily[qual_mask]
    mean_b_d[qual_mask] = sum_b_daily[qual_mask] / cnt_b_daily[qual_mask]
    delta_d = mean_b_d - mean_a_d
    
    wilt_frac = np.zeros((121, 181), dtype=float)
    wilt_frac[qual_mask] = cnt_wilt_rej[qual_mask] / cnt_a_hourly[qual_mask]
    
    print("\n--- STATISTIQUES POOLÉES (JUILLET 2018, NON-FORÊT) ---")
    arr_a_h = np.array(pool_diff_a_h)
    arr_b_h = np.array(pool_diff_b_h)
    arr_a_d = np.array(pool_diff_a_d)
    arr_b_d = np.array(pool_diff_b_d)
    
    print(f"OL Horaire (heure de passage) :")
    print(f"  (a) Toutes obs valides  : N={len(arr_a_h)}, Moy={arr_a_h.mean():+.5f}, Méd={np.median(arr_a_h):+.5f}, %pos={100*np.mean(arr_a_h > 0):.1f}%")
    print(f"  (b) Obs acceptées QC    : N={len(arr_b_h)}, Moy={arr_b_h.mean():+.5f}, Méd={np.median(arr_b_h):+.5f}, %pos={100*np.mean(arr_b_h > 0):.1f}%")
    print(f"  Écart poolé (b) - (a)   : {arr_b_h.mean() - arr_a_h.mean():+.5f} m3/m3")
    
    print(f"\nOL Journalier (moyenne 24h) :")
    print(f"  (a) Toutes obs valides  : N={len(arr_a_d)}, Moy={arr_a_d.mean():+.5f}, Méd={np.median(arr_a_d):+.5f}, %pos={100*np.mean(arr_a_d > 0):.1f}%")
    print(f"  (b) Obs acceptées QC    : N={len(arr_b_d)}, Moy={arr_b_d.mean():+.5f}, Méd={np.median(arr_b_d):+.5f}, %pos={100*np.mean(arr_b_d > 0):.1f}%")
    print(f"  Écart poolé (b) - (a)   : {arr_b_d.mean() - arr_a_d.mean():+.5f} m3/m3")
    
    print(f"\nImpact net du cycle diurne sur SMAP - OL :")
    print(f"  Moyenne(SMAP - OL_horaire) - Moyenne(SMAP - OL_journalier) : {arr_a_h.mean() - arr_a_d.mean():+.5f} m3/m3")
    
    print("\n--- STATISTIQUES MOYENNES PAR PIXEL (POIDS ÉGAUX) ---")
    vals_delta_h = delta_h[qual_mask]
    vals_delta_d = delta_d[qual_mask]
    print(f"Troncature intra-pixel delta_horaire    : Moy = {vals_delta_h.mean():+.5f}, Médiane = {np.median(vals_delta_h):+.5f} m3/m3")
    print(f"Troncature intra-pixel delta_journalier : Moy = {vals_delta_d.mean():+.5f}, Médiane = {np.median(vals_delta_d):+.5f} m3/m3")
    print(f"Différence d'effet de troncature        : {vals_delta_h.mean() - vals_delta_d.mean():+.5f} m3/m3")
    
    # 3. Décomposition par décile de rejet de flétrissement
    print("\n--- ÉCART PAR CLASSE DE FRACTION REJETÉE PAR FLÉTRISSEMENT ---")
    print(f"{'Classe / Décile':<20} | {'N pixels':<8} | {'Delta Horaire':<15} | {'Delta Journalier':<16} | {'SMAP-OL_h (a)':<15} | {'SMAP-OL_h (b)':<15}")
    print("-" * 105)
    
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    for i in range(len(bins)-1):
        b_lo, b_hi = bins[i], bins[i+1]
        m_bin = qual_mask & (wilt_frac >= b_lo) & (wilt_frac < b_hi)
        n_p = np.sum(m_bin)
        if n_p > 0:
            d_h_m = delta_h[m_bin].mean()
            d_d_m = delta_d[m_bin].mean()
            sm_a_m = mean_a_h[m_bin].mean()
            sm_b_m = mean_b_h[m_bin].mean()
            lbl = f"[{b_lo*100:02.0f}% - {min(b_hi*100, 100):02.0f}%["
            print(f"{lbl:<20} | {n_p:<8} | {d_h_m:+.5f} m3/m3  | {d_d_m:+.5f} m3/m3   | {sm_a_m:+.5f} m3/m3   | {sm_b_m:+.5f} m3/m3")
            
    # 4. Croisement GMIA
    print("\n--- 3. CROISEMENT AVEC LA CARTE D'IRRIGATION GMIA ---")
    gmia_mor = load_gmia_resampled(lat, lon)
    
    # Pixels irrigués vs non irrigués
    irrig_mask = qual_mask & (gmia_mor > 1.0) # > 1% de surface équipée
    no_irrig_mask = qual_mask & (gmia_mor <= 1.0)
    
    print(f"Pixels qualifiés avec équipement d'irrigation GMIA > 1% : {np.sum(irrig_mask)} (moyenne AEI = {gmia_mor[irrig_mask].mean():.1f}%)")
    print(f"Pixels qualifiés avec GMIA <= 1% : {np.sum(no_irrig_mask)}")
    
    if np.sum(irrig_mask) > 0:
        print(f"  Moyenne SMAP - OL (a) [Irrigués GMIA > 1%]  : {mean_a_h[irrig_mask].mean():+.5f} m3/m3")
        print(f"  Moyenne SMAP - OL (a) [Non-irrigués <= 1%] : {mean_a_h[no_irrig_mask].mean():+.5f} m3/m3")
        print(f"  Surplus d'humidité SMAP sur zones irriguées: {mean_a_h[irrig_mask].mean() - mean_a_h[no_irrig_mask].mean():+.5f} m3/m3")
        
        # Corrélation spatiale entre GMIA et SMAP - OL
        from scipy.stats import spearmanr, pearsonr
        valid_corr = qual_mask & np.isfinite(mean_a_h) & np.isfinite(gmia_mor)
        r_p, _ = pearsonr(gmia_mor[valid_corr], mean_a_h[valid_corr])
        r_s, _ = spearmanr(gmia_mor[valid_corr], mean_a_h[valid_corr])
        print(f"  Corrélation spatiale GMIA vs (SMAP - OL brut) : Pearson r = {r_p:+.3f}, Spearman rho = {r_s:+.3f}")
        
    # Tracé des figures récapitulatives
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    
    im0 = axes[0, 0].imshow(np.where(land_bool, mean_diff_06h, np.nan), cmap="RdBu_r", vmin=-0.015, vmax=+0.015, origin="lower")
    axes[0, 0].set_title("A. Écart diurne 06h UTC − Moyenne 24h (m³/m³)", fontsize=11, fontweight="bold")
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04)
    
    im1 = axes[0, 1].imshow(np.where(land_bool, mean_diff_18h, np.nan), cmap="RdBu_r", vmin=-0.015, vmax=+0.015, origin="lower")
    axes[0, 1].set_title("B. Écart diurne 18h UTC − Moyenne 24h (m³/m³)", fontsize=11, fontweight="bold")
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)
    
    im2 = axes[1, 0].imshow(np.where(qual_mask, delta_h, np.nan), cmap="YlOrRd", vmin=0.0, vmax=+0.035, origin="lower")
    axes[1, 0].set_title("C. Effet de troncature $\\delta$ à l'heure du passage (b - a)", fontsize=11, fontweight="bold")
    plt.colorbar(im2, ax=axes[1, 0], fraction=0.046, pad=0.04)
    
    im3 = axes[1, 1].imshow(np.where(land_bool, gmia_mor, np.nan), cmap="Blues", vmin=0, vmax=50, origin="lower")
    axes[1, 1].set_title("D. Fraction équipée pour l'irrigation GMIA v5 (%)", fontsize=11, fontweight="bold")
    plt.colorbar(im3, ax=axes[1, 1], fraction=0.046, pad=0.04)
    
    for ax in axes.ravel():
        ax.set_xticks([])
        ax.set_yticks([])
        
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, "figure_hourly_diurnal_and_gmia.png")
    plt.savefig(fig_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"\nFigure sauvegardée : {fig_path}")
    return True

if __name__ == "__main__":
    run_point_b()
