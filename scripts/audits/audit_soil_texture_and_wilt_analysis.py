#!/usr/bin/env python3
"""
audit_soil_texture_and_wilt_analysis.py
---------------------------------------
Analyse approfondie de la texture du sol, du seuil de flétrissement et de la DA SMAP :
1. Cartes côte à côte (2x3) : texture dominante, smcwlt, fraction rejetée flétrissement (JA 2016-2020),
   SMAP brut moyen, OL moyen (couche 1), GMIA à 36 km, avec repères urbains.
2. Tableau par texture dominante (JA 2016-2020).
3. Diagnostic des pixels rejetés à plus de 95 % (distribution SMAP/OL vs smcwlt+0.02, croisement GMIA).
4. Test sans seuil (JA 2018) : révision incluant les pixels sans analyse (incrément nul),
   assèchement cumulé en mm, différence d'état par texture, et carte C avec échelle ±0.05 m³/m³.
5. Diagnostic du rejet par texture pour Mars-Avril (2016-2020) vs Juillet-Août.
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import uniform_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch

# Chemins
BASE_DA = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
BASE_OL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"
DIR_NOWILT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_TEST_nowilt/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"
GMIA_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/GMIA/gmia_v5_aei_pct.asc"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_FIG_DIR = os.path.join(REPO_ROOT, "figures", "assimilation")

# Repères urbains
CITIES = {
    "Rabat": (34.0209, -6.8416),
    "Kénitra": (34.2610, -6.5802),
    "Fès": (34.0331, -5.0003),
    "Meknès": (33.8938, -5.5473),
    "Casablanca": (33.5731, -7.5898),
    "El Jadida": (33.2316, -8.5007),
    "Béni Mellal": (32.3373, -6.3498)
}

# Noms textures USDA standard
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
    12: "Clay"
}

def load_static():
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
        texture = ds.variables["TEXTURE"][:]
        landcover = ds.variables["LANDCOVER"][:]
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]
    soiltype = np.argmax(texture, axis=0) + 1
    vegt = np.argmax(landcover, axis=0) + 1
    
    wltsmc = {}
    with open(SOILPARM, "r") as f:
        in_s = False
        for line in f:
            if "STAS" in line and not "STAS-RUC" in line: in_s = True; continue
            if "STAS-RUC" in line: break
            if in_s and line.strip() and line.strip()[0].isdigit():
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 10: wltsmc[int(parts[0])] = float(parts[9])
    wlt_grid = np.zeros_like(soiltype, dtype=float)
    for c, w in wltsmc.items(): wlt_grid[soiltype == c] = w
    return landmask, soiltype, vegt, wlt_grid, wltsmc, lat, lon

def read_daobs(fpath):
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

def load_gmia_36km(target_lat, target_lon, landmask):
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
    
    land_float = (landmask == 1).astype(float)
    gmia_masked = gmia_5km * land_float
    k = 7
    num = uniform_filter(gmia_masked, size=k, mode='constant', cval=0.0) * (k*k)
    denom = uniform_filter(land_float, size=k, mode='constant', cval=0.0) * (k*k)
    
    gmia_36km = np.zeros_like(gmia_5km)
    valid_denom = denom > 0
    gmia_36km[valid_denom] = num[valid_denom] / denom[valid_denom]
    gmia_36km[~valid_denom] = 0.0
    gmia_36km[landmask != 1] = np.nan
    return gmia_36km

def compute_period_stats(years, months, landmask, wlt_grid):
    land_bool = (landmask == 1)
    
    smap_sum = np.zeros((121, 181), dtype=float)
    smap_cnt = np.zeros((121, 181), dtype=int)
    
    ol_sum = np.zeros((121, 181), dtype=float)
    ol_cnt = np.zeros((121, 181), dtype=int)
    
    wilt_rej_cnt = np.zeros((121, 181), dtype=int)
    raw_obs_cnt = np.zeros((121, 181), dtype=int)
    acc_obs_cnt = np.zeros((121, 181), dtype=int)
    
    for y in years:
        for m in months:
            ym = f"{y}-{m:02d}"
            ym_c = f"{y}{m:02d}"
            da_files = sorted(glob.glob(f"{BASE_DA}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r"))
            ol_cache = {}
            
            for f in da_files:
                bname = os.path.basename(f)
                dstr = bname.split("_")[1][:8]
                dt = datetime.datetime.strptime(dstr, "%Y%m%d")
                
                if dt not in ol_cache:
                    ol_f = find_ol_file(dt)
                    if ol_f and os.path.exists(ol_f):
                        with nc.Dataset(ol_f) as ds:
                            ol_sm = ds.variables["SoilMoist_tavg"][0, :, :].squeeze()
                            ol_cache[dt] = np.where(np.isfinite(ol_sm), ol_sm, np.nan)
                    else:
                        ol_cache[dt] = None
                        
                ol_data = ol_cache[dt]
                r1, r2 = read_daobs(f)
                
                val_raw = (r1 != -9999.0) & np.isfinite(r1) & land_bool
                val_acc = (r2 != -9999.0) & np.isfinite(r2) & land_bool
                
                raw_obs_cnt[val_raw] += 1
                acc_obs_cnt[val_acc] += 1
                
                smap_sum[val_raw] += r1[val_raw]
                smap_cnt[val_raw] += 1
                
                wilt_rej = val_raw & ((r2 == -9999.0) | (~np.isfinite(r2))) & ((r1 - wlt_grid) < 0.02)
                wilt_rej_cnt[wilt_rej] += 1
                
                if ol_data is not None:
                    val_ol = val_raw & np.isfinite(ol_data)
                    ol_sum[val_ol] += ol_data[val_ol]
                    ol_cnt[val_ol] += 1
                    
    smap_mean = np.full((121, 181), np.nan)
    v_s = smap_cnt > 0
    smap_mean[v_s] = smap_sum[v_s] / smap_cnt[v_s]
    
    ol_mean = np.full((121, 181), np.nan)
    v_o = ol_cnt > 0
    ol_mean[v_o] = ol_sum[v_o] / ol_cnt[v_o]
    
    wilt_frac = np.full((121, 181), np.nan)
    v_r = raw_obs_cnt >= 10
    wilt_frac[v_r] = wilt_rej_cnt[v_r] / raw_obs_cnt[v_r]
    
    return smap_mean, ol_mean, wilt_frac, raw_obs_cnt, acc_obs_cnt, wilt_rej_cnt

def add_city_markers(ax, lat, lon):
    for name, (clat, clon) in CITIES.items():
        ax.plot(clon, clat, marker='o', markersize=4, color='red', markeredgecolor='black', markeredgewidth=0.7, zorder=5)
        offset_x, offset_y = 0.08, 0.08
        if name in ["Kénitra", "Casablanca", "El Jadida"]:
            offset_x = -0.75
        elif name == "Fès":
            offset_y = 0.12
        elif name == "Meknès":
            offset_y = -0.18
        ax.text(clon + offset_x, clat + offset_y, name, fontsize=7.5, fontweight='bold', color='black',
                bbox=dict(boxstyle="round,pad=0.15", facecolor='white', alpha=0.75, edgecolor='none'), zorder=6)

def main():
    print("==================================================================")
    print(" AUDIT COMPLET : TEXTURE DU SOL, SEUIL DE FLÉTRISSEMENT & DA SMAP")
    print("==================================================================")
    
    os.makedirs(OUT_FIG_DIR, exist_ok=True)
    
    landmask, soiltype, vegt, wlt_grid, wltsmc, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    # -------------------------------------------------------------
    # 1. CALCULS POUR JUILLET-AOÛT (2016-2020)
    # -------------------------------------------------------------
    print("\n[1/5] Traitement Juillet-Août (2016-2020)...")
    years_5y = [2016, 2017, 2018, 2019, 2020]
    months_ja = [7, 8]
    smap_ja, ol_ja, wilt_frac_ja, raw_cnt_ja, acc_cnt_ja, wilt_cnt_ja = compute_period_stats(
        years_5y, months_ja, landmask, wlt_grid)
        
    print("[1/5] Chargement GMIA à 36 km...")
    gmia_36km = load_gmia_36km(lat, lon, landmask)
    
    # -------------------------------------------------------------
    # POINT 1 : TRACÉ DES 6 CARTES CÔTE À CÔTE
    # -------------------------------------------------------------
    print("\n[Point 1] Génération de la figure multi-panneaux (6 cartes)...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11), dpi=200)
    
    # (a) Texture dominante
    ax = axes[0, 0]
    present_cats = [1, 3, 4, 6, 7, 9, 12]
    cmap_tex = plt.get_cmap("tab10", len(present_cats))
    tex_grid_plot = np.full_like(soiltype, np.nan, dtype=float)
    for idx, c in enumerate(present_cats):
        tex_grid_plot[(soiltype == c) & land_bool] = idx
        
    im_tex = ax.pcolormesh(lon, lat, tex_grid_plot, cmap=cmap_tex, vmin=-0.5, vmax=len(present_cats)-0.5, shading='auto')
    ax.set_title("(a) Texture dominante du sol (Noah-MP)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    
    legend_elements = [
        Patch(facecolor=cmap_tex(idx), edgecolor='k', label=f"{c}: {TEXTURE_NAMES.get(c, 'Inconnu')}")
        for idx, c in enumerate(present_cats)
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=7.5, framealpha=0.9)
    
    # (b) Seuil de flétrissement smcwlt
    ax = axes[0, 1]
    wlt_plot = np.where(land_bool, wlt_grid, np.nan)
    im_wlt = ax.pcolormesh(lon, lat, wlt_plot, cmap='YlOrBr', vmin=0.01, vmax=0.14, shading='auto')
    ax.set_title("(b) Seuil de flétrissement smcwlt (m³/m³)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig.colorbar(im_wlt, ax=ax, orientation='horizontal', pad=0.08, shrink=0.7)
    cb.set_label("smcwlt (m³/m³)", fontsize=9)
    
    # (c) Fraction rejetée par flétrissement (JA 2016-2020)
    ax = axes[0, 2]
    wilt_plot_frac = np.where(land_bool & (raw_cnt_ja >= 10), wilt_frac_ja * 100, np.nan)
    im_rej = ax.pcolormesh(lon, lat, wilt_plot_frac, cmap='Reds', vmin=0, vmax=100, shading='auto')
    ax.set_title("(c) Fraction rejetée par flétrissement JA 2016-2020 (%)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig.colorbar(im_rej, ax=ax, orientation='horizontal', pad=0.08, shrink=0.7)
    cb.set_label("Fraction rejetée (%)", fontsize=9)
    
    # (d) SMAP brut moyen
    ax = axes[1, 0]
    smap_plot = np.where(land_bool & (raw_cnt_ja >= 10), smap_ja, np.nan)
    im_smap = ax.pcolormesh(lon, lat, smap_plot, cmap='Blues', vmin=0.02, vmax=0.18, shading='auto')
    ax.set_title("(d) SMAP brut moyen (Juillet-Août 2016-2020)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig.colorbar(im_smap, ax=ax, orientation='horizontal', pad=0.08, shrink=0.7)
    cb.set_label("SMAP brut (m³/m³)", fontsize=9)
    
    # (e) OL moyen (couche 1)
    ax = axes[1, 1]
    ol_plot = np.where(land_bool & (raw_cnt_ja >= 10), ol_ja, np.nan)
    im_ol = ax.pcolormesh(lon, lat, ol_plot, cmap='Blues', vmin=0.02, vmax=0.18, shading='auto')
    ax.set_title("(e) OL moyen couche 1 (Juillet-Août 2016-2020)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig.colorbar(im_ol, ax=ax, orientation='horizontal', pad=0.08, shrink=0.7)
    cb.set_label("OL couche 1 (m³/m³)", fontsize=9)
    
    # (f) Carte GMIA à 36 km
    ax = axes[1, 2]
    gmia_plot = np.where(land_bool, gmia_36km, np.nan)
    im_gmia = ax.pcolormesh(lon, lat, gmia_plot, cmap='YlGn', vmin=0, vmax=60, shading='auto')
    ax.set_title("(f) Fraction irriguée GMIA agrégée à ~36 km (%)", fontsize=11, fontweight='bold')
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig.colorbar(im_gmia, ax=ax, orientation='horizontal', pad=0.08, shrink=0.7)
    cb.set_label("Fraction irriguée (%)", fontsize=9)
    
    plt.tight_layout()
    fig1_path = os.path.join(OUT_FIG_DIR, "figure_soil_texture_rejection_maps.png")
    plt.savefig(fig1_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  -> Figure sauvegardée : {fig1_path}")
    
    # -------------------------------------------------------------
    # POINT 2 : TABLEAU PAR TEXTURE DOMINANTE (JA 2016-2020)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" POINT 2 : TABLEAU PAR TEXTURE DOMINANTE (JA 2016-2020)")
    print("-------------------------------------------------------------")
    diff_ja = smap_ja - ol_ja
    qual_px = land_bool & non_forest & (raw_cnt_ja >= 10)
    
    print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'smcwlt':<7} | {'seuil':<7} | {'Rejet Moy':<9} | {'Rejet Méd':<9} | {'SMAP Moy':<9} | {'OL Moy':<9} | {'SMAP-OL Moy':<11} | {'SMAP-OL Méd':<11}")
    print("-" * 115)
    
    for c in present_cats:
        m_c = qual_px & (soiltype == c)
        n_px = np.sum(m_c)
        if n_px == 0:
            continue
        wlt_val = wltsmc[c]
        thr_val = wlt_val + 0.02
        rej_m = np.nanmean(wilt_frac_ja[m_c]) * 100
        rej_med = np.nanmedian(wilt_frac_ja[m_c]) * 100
        smap_m = np.nanmean(smap_ja[m_c])
        ol_m = np.nanmean(ol_ja[m_c])
        diff_m = np.nanmean(diff_ja[m_c])
        diff_med = np.nanmedian(diff_ja[m_c])
        
        name = TEXTURE_NAMES.get(c, "Inconnu")
        print(f"{c:<4} | {name:<16} | {n_px:<6} | {wlt_val:<7.3f} | {thr_val:<7.3f} | {rej_m:<8.1f}% | {rej_med:<8.1f}% | {smap_m:<9.4f} | {ol_m:<9.4f} | {diff_m:<+11.4f} | {diff_med:<+11.4f}")
        
    print("-" * 115)
    print(f"{'ALL':<4} | {'Ensemble':<16} | {np.sum(qual_px):<6} | {'-':<7} | {'-':<7} | {np.nanmean(wilt_frac_ja[qual_px])*100:<8.1f}% | {np.nanmedian(wilt_frac_ja[qual_px])*100:<8.1f}% | {np.nanmean(smap_ja[qual_px]):<9.4f} | {np.nanmean(ol_ja[qual_px]):<9.4f} | {np.nanmean(diff_ja[qual_px]):<+11.4f} | {np.nanmedian(diff_ja[qual_px]):<+11.4f}")
    
    # -------------------------------------------------------------
    # POINT 3 : PIXELS REJETÉS À PLUS DE 95 %
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" POINT 3 : DIAGNOSTIC DES PIXELS REJETÉS À PLUS DE 95 %")
    print("-------------------------------------------------------------")
    rej_95_mask = qual_px & (wilt_frac_ja >= 0.95)
    n_rej_95 = np.sum(rej_95_mask)
    tot_qual = np.sum(qual_px)
    print(f"Nombre de pixels rejetés à >= 95% : {n_rej_95} sur {tot_qual} ({100*n_rej_95/tot_qual:.1f}%)")
    
    print("\nRépartition par classe de texture des pixels rejetés à >= 95% :")
    for c in present_cats:
        n_c_tot = np.sum(qual_px & (soiltype == c))
        n_c_95 = np.sum(rej_95_mask & (soiltype == c))
        pct_in_cat = 100 * n_c_95 / n_c_tot if n_c_tot > 0 else 0
        pct_of_all95 = 100 * n_c_95 / n_rej_95 if n_rej_95 > 0 else 0
        print(f"  {TEXTURE_NAMES.get(c):<16} (Cat {c:2d}) : {n_c_95:5d} / {n_c_tot:5d} pixels de la texture ({pct_in_cat:5.1f}%) | {pct_of_all95:5.1f}% des pixels rejetés")
        
    smap_95 = smap_ja[rej_95_mask]
    ol_95 = ol_ja[rej_95_mask]
    thr_95 = wlt_grid[rej_95_mask] + 0.02
    
    print("\nStatistiques sur les pixels rejetés à >= 95% (Juillet-Août 2016-2020) :")
    print(f"  SMAP brut  : Moy = {np.mean(smap_95):.4f}, Std = {np.std(smap_95):.4f}, Min = {np.min(smap_95):.4f}, Q25 = {np.percentile(smap_95, 25):.4f}, Méd = {np.median(smap_95):.4f}, Q75 = {np.percentile(smap_95, 75):.4f}, Max = {np.max(smap_95):.4f}")
    print(f"  OL couche1 : Moy = {np.mean(ol_95):.4f}, Std = {np.std(ol_95):.4f}, Min = {np.min(ol_95):.4f}, Q25 = {np.percentile(ol_95, 25):.4f}, Méd = {np.median(ol_95):.4f}, Q75 = {np.percentile(ol_95, 75):.4f}, Max = {np.max(ol_95):.4f}")
    print(f"  Seuil LIS  : Moy = {np.mean(thr_95):.4f}, Min = {np.min(thr_95):.4f}, Méd = {np.median(thr_95):.4f}, Max = {np.max(thr_95):.4f}")
    
    deficit_smap = smap_95 - thr_95
    deficit_ol = ol_95 - thr_95
    print(f"  Écart moyen SMAP - seuil : {np.mean(deficit_smap):+.4f} m³/m³ (SMAP est en moyenne à {abs(np.mean(deficit_smap)):.4f} en-dessous du seuil de flétrissement)")
    print(f"  Écart moyen OL - seuil   : {np.mean(deficit_ol):+.4f} m³/m³")
    
    # Part dans les classes GMIA
    n_gmia_gt10_tot = np.sum(qual_px & (gmia_36km > 10.0))
    n_gmia_gt10_in95 = np.sum(rej_95_mask & (gmia_36km > 10.0))
    n_gmia_gt30_tot = np.sum(qual_px & (gmia_36km > 30.0))
    n_gmia_gt30_in95 = np.sum(rej_95_mask & (gmia_36km > 30.0))
    
    print("\nCroisement avec la carte GMIA à 36 km :")
    print(f"  Pixels GMIA > 10% dans le domaine qualifié : {n_gmia_gt10_tot} pixels")
    print(f"  Dont rejetés à >= 95%                      : {n_gmia_gt10_in95} pixels ({100*n_gmia_gt10_in95/n_gmia_gt10_tot:.1f}% des zones irriguées > 10%)")
    print(f"  Pixels GMIA > 30% dans le domaine qualifié : {n_gmia_gt30_tot} pixels")
    print(f"  Dont rejetés à >= 95%                      : {n_gmia_gt30_in95} pixels ({100*n_gmia_gt30_in95/n_gmia_gt30_tot:.1f}% des zones irriguées > 30%)")
    print(f"  Part des pixels rejetés (>=95%) ayant GMIA > 10% : {100*n_gmia_gt10_in95/n_rej_95:.1f}%")
    print(f"  Part des pixels rejetés (>=95%) ayant GMIA > 30% : {100*n_gmia_gt30_in95/n_rej_95:.1f}%")
    
    # -------------------------------------------------------------
    # POINT 4 : TEST SANS SEUIL (JA 2018) AVEC INCLUSION DES INC=0
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" POINT 4 : TEST SANS SEUIL (JA 2018) INCLUANT PIXELS SANS ANALYSE")
    print("-------------------------------------------------------------")
    
    months_18 = ["2018-07", "2018-08"]
    incr_ctrl_sum = np.zeros((121, 181), dtype=float)
    incr_nowilt_sum = np.zeros((121, 181), dtype=float)
    incr_ctrl_cnt = np.zeros((121, 181), dtype=int)
    incr_nowilt_cnt = np.zeros((121, 181), dtype=int)
    n_cycles = 0
    
    for ym in months_18:
        ym_c = ym.replace("-", "")
        f_inc_ctrl = sorted(glob.glob(f"{BASE_DA}/{ym}/EnKF/{ym_c}/LIS_DA_EnKF_*_incr.a01.d01.nc"))
        f_inc_nowilt = sorted(glob.glob(f"{DIR_NOWILT}/{ym}/EnKF/{ym_c}/LIS_DA_EnKF_*_incr.a01.d01.nc"))
        
        for fc, fn in zip(f_inc_ctrl, f_inc_nowilt):
            n_cycles += 1
            with nc.Dataset(fc) as dsc, nc.Dataset(fn) as dsn:
                ic = dsc.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
                inw = dsn.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
                
                ic_clean = np.where(land_bool & np.isfinite(ic), ic, 0.0)
                inw_clean = np.where(land_bool & np.isfinite(inw), inw, 0.0)
                
                incr_ctrl_sum += ic_clean
                incr_nowilt_sum += inw_clean
                
                incr_ctrl_cnt += (land_bool & np.isfinite(ic) & (ic != 0.0)).astype(int)
                incr_nowilt_cnt += (land_bool & np.isfinite(inw) & (inw != 0.0)).astype(int)
                
    raw_cnt_18 = np.zeros((121, 181), dtype=int)
    wilt_cnt_18 = np.zeros((121, 181), dtype=int)
    for ym in months_18:
        ym_c = ym.replace("-", "")
        f_ctrl = sorted(glob.glob(f"{BASE_DA}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r"))
        for fc in f_ctrl:
            r1, r2 = read_daobs(fc)
            val_raw = (r1 != -9999.0) & np.isfinite(r1) & land_bool
            raw_cnt_18[val_raw] += 1
            wilt_rej = val_raw & ((r2 == -9999.0) | (~np.isfinite(r2))) & ((r1 - wlt_grid) < 0.02)
            wilt_cnt_18[wilt_rej] += 1
            
    wilt_frac_18 = np.zeros((121, 181), dtype=float)
    v18 = raw_cnt_18 >= 10
    wilt_frac_18[v18] = wilt_cnt_18[v18] / raw_cnt_18[v18]
    
    mean_incr_ctrl_all = incr_ctrl_sum / n_cycles
    mean_incr_nowilt_all = incr_nowilt_sum / n_cycles
    
    m_nf = land_bool & non_forest
    n_nf = np.sum(m_nf)
    n_zero_ctrl = np.sum(m_nf & (incr_ctrl_cnt == 0))
    
    print(f"Nombre de cycles d'assimilation EnKF : {n_cycles}")
    print(f"Pixels non-forêt : {n_nf}")
    print(f"Pixels non-forêt SANS AUCUNE ANALYSE au témoin (incr = 0 strict) : {n_zero_ctrl} ({100*n_zero_ctrl/n_nf:.1f}%)")
    
    print("\n--- Incréments moyens (Juillet-Août 2018) sur TOUS les pixels non-forêt (N=12,675) ---")
    print(f"1. En incluant les incréments nuls (moyenne par cycle d'assimilation) :")
    print(f"   Contrôle : {np.mean(mean_incr_ctrl_all[m_nf]):+.6f} m³/m³ / cycle")
    print(f"   Nowilt   : {np.mean(mean_incr_nowilt_all[m_nf]):+.6f} m³/m³ / cycle")
    print(f"   Différence (Nowilt - Ctrl) : {np.mean(mean_incr_nowilt_all[m_nf] - mean_incr_ctrl_all[m_nf]):+.6f} m³/m³ / cycle")
    
    print(f"\n2. Somme cumulée moyenne des incréments sur les 2 mois :")
    cum_ctrl_mm = np.mean(incr_ctrl_sum[m_nf]) * 100.0
    cum_nowilt_mm = np.mean(incr_nowilt_sum[m_nf]) * 100.0
    print(f"   Contrôle : {cum_ctrl_mm:+.2f} mm d'eau ajoutés/retirés par DA")
    print(f"   Nowilt   : {cum_nowilt_mm:+.2f} mm d'eau ajoutés/retirés par DA")
    print(f"   Assèchement cumulé net apporté par la suppression du seuil : {cum_nowilt_mm - cum_ctrl_mm:+.2f} mm")
    
    print("\nIncréments cumulés et par cycle par décile de rejet (TOUS pixels non-forêt inclus) :")
    print(f"{'Décile rejet':<12} | {'N px':<6} | {'Incr Ctrl (cycle)':<18} | {'Incr Nowilt (cycle)':<19} | {'Diff (Nowilt-Ctrl)':<18} | {'Cumul Ctrl (mm)':<15} | {'Cumul Nowilt (mm)':<17}")
    print("-" * 115)
    for d in range(10):
        d_min, d_max = d * 0.1, (d + 1) * 0.1
        if d == 9:
            m_dec = m_nf & (wilt_frac_18 >= d_min) & (wilt_frac_18 <= d_max)
        else:
            m_dec = m_nf & (wilt_frac_18 >= d_min) & (wilt_frac_18 < d_max)
        n_d = np.sum(m_dec)
        if n_d == 0: continue
        c_cyc = np.mean(mean_incr_ctrl_all[m_dec])
        n_cyc = np.mean(mean_incr_nowilt_all[m_dec])
        diff_cyc = n_cyc - c_cyc
        c_mm = np.mean(incr_ctrl_sum[m_dec]) * 100.0
        n_mm = np.mean(incr_nowilt_sum[m_dec]) * 100.0
        print(f"[{d*10:02d}% - {(d+1)*10:02d}%[ | {n_d:<6} | {c_cyc:<+18.6f} | {n_cyc:<+19.6f} | {diff_cyc:<+18.6f} | {c_mm:<+15.2f} | {n_mm:<+17.2f}")
        
    print("\n--- Différence d'état d'humidité du sol simulée (SURFACEMODEL, JA 2018) ---")
    sm_ctrl_layers = np.zeros((4, 121, 181), dtype=float)
    sm_nowilt_layers = np.zeros((4, 121, 181), dtype=float)
    cnt_sm = 0
    
    for ym in months_18:
        ym_c = ym.replace("-", "")
        f_sm_c = sorted(glob.glob(f"{BASE_DA}/{ym}/SURFACEMODEL/{ym_c}/LIS_HIST_*.nc"))
        f_sm_n = sorted(glob.glob(f"{DIR_NOWILT}/{ym}/SURFACEMODEL/{ym_c}/LIS_HIST_*.nc"))
        for fc, fn in zip(f_sm_c, f_sm_n):
            cnt_sm += 1
            with nc.Dataset(fc) as dsc, nc.Dataset(fn) as dsn:
                sm_ctrl_layers += dsc.variables["SoilMoist_tavg"][:].squeeze()
                sm_nowilt_layers += dsn.variables["SoilMoist_tavg"][:].squeeze()
                
    sm_ctrl_layers /= cnt_sm
    sm_nowilt_layers /= cnt_sm
    diff_sm_l1 = sm_nowilt_layers[0] - sm_ctrl_layers[0]
    
    layer_dz = np.array([100.0, 300.0, 600.0, 1000.0]) # mm
    diff_storage_mm = np.zeros((121, 181), dtype=float)
    for l_idx in range(4):
        diff_storage_mm += (sm_nowilt_layers[l_idx] - sm_ctrl_layers[l_idx]) * layer_dz[l_idx]
        
    print(f"Différence moyenne couche 1 (0-10 cm)  : {np.mean(diff_sm_l1[m_nf]):+.6f} m³/m³")
    print(f"Assèchement moyen couche 1 en mm d'eau : {np.mean(diff_sm_l1[m_nf] * 100.0):+.3f} mm")
    print(f"Assèchement total profil (0-2 m) en mm : {np.mean(diff_storage_mm[m_nf]):+.3f} mm")
    
    print("\nDifférence d'état d'humidité du sol par classe de texture (JA 2018) :")
    print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'Ctrl L1 (m3/m3)':<15} | {'Nowilt L1 (m3/m3)':<17} | {'Diff L1 (m3/m3)':<15} | {'Diff L1 (mm)':<12} | {'Diff Total (mm)':<15} | {'% asséché':<10}")
    print("-" * 125)
    for c in present_cats:
        m_c = m_nf & (soiltype == c)
        n_c = np.sum(m_c)
        if n_c == 0: continue
        c_l1 = np.mean(sm_ctrl_layers[0][m_c])
        n_l1 = np.mean(sm_nowilt_layers[0][m_c])
        d_l1 = np.mean(diff_sm_l1[m_c])
        d_l1_mm = d_l1 * 100.0
        d_tot_mm = np.mean(diff_storage_mm[m_c])
        pct_dry = 100 * np.sum(m_c & (diff_sm_l1 < 0)) / n_c
        name = TEXTURE_NAMES.get(c, "Inconnu")
        print(f"{c:<4} | {name:<16} | {n_c:<6} | {c_l1:<15.4f} | {n_l1:<17.4f} | {d_l1:<+15.5f} | {d_l1_mm:<+12.3f} | {d_tot_mm:<+15.3f} | {pct_dry:<9.1f}%")
        
    print("-" * 125)
    d_l1_all = np.mean(diff_sm_l1[m_nf])
    pct_dry_all = 100 * np.sum(m_nf & (diff_sm_l1 < 0)) / n_nf
    print(f"{'ALL':<4} | {'Ensemble':<16} | {n_nf:<6} | {np.mean(sm_ctrl_layers[0][m_nf]):<15.4f} | {np.mean(sm_nowilt_layers[0][m_nf]):<17.4f} | {d_l1_all:<+15.5f} | {d_l1_all*100:<+12.3f} | {np.mean(diff_storage_mm[m_nf]):<+15.3f} | {pct_dry_all:<9.1f}%")
    
    print("\n[Point 4] Génération de la figure révisée Point D avec échelle ±0.05 m³/m³...")
    fig_d, axes_d = plt.subplots(1, 3, figsize=(18, 5.5), dpi=200)
    
    ax = axes_d[0]
    im_a = ax.pcolormesh(lon, lat, np.where(m_nf, wilt_frac_18 * 100, np.nan),
                         cmap="Reds", vmin=0, vmax=100, shading="auto")
    ax.set_title("(A) Fraction rejetée flétrissement (Contrôle, JA 2018)", fontsize=10, fontweight="bold")
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig_d.colorbar(im_a, ax=ax, orientation="horizontal", pad=0.1, shrink=0.7)
    cb.set_label("Fraction rejetée (%)", fontsize=9)
    
    ax = axes_d[1]
    diff_incr_cum = (incr_nowilt_sum - incr_ctrl_sum) * 100.0
    vlim_cum = np.nanpercentile(np.abs(diff_incr_cum[m_nf]), 98)
    im_b = ax.pcolormesh(lon, lat, np.where(m_nf, diff_incr_cum, np.nan),
                         cmap="BrBG", vmin=-max(vlim_cum, 5), vmax=max(vlim_cum, 5), shading="auto")
    ax.set_title("(B) Différence incrément DA cumulé (Nowilt − Ctrl, mm)", fontsize=10, fontweight="bold")
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig_d.colorbar(im_b, ax=ax, orientation="horizontal", pad=0.1, shrink=0.7)
    cb.set_label("Écart cumulé DA (mm d'eau)", fontsize=9)
    
    ax = axes_d[2]
    im_c = ax.pcolormesh(lon, lat, np.where(m_nf, diff_sm_l1, np.nan),
                         cmap="RdBu", vmin=-0.05, vmax=0.05, shading="auto")
    ax.set_title("(C) Différence humidité couche 1 (Nowilt − Ctrl, m³/m³)\nÉchelle fixée à [−0.05 ; +0.05] m³/m³", fontsize=10, fontweight="bold")
    add_city_markers(ax, lat, lon)
    ax.set_xlim(lon.min(), lon.max())
    ax.set_ylim(lat.min(), lat.max())
    cb = fig_d.colorbar(im_c, ax=ax, orientation="horizontal", pad=0.1, shrink=0.7)
    cb.set_label("Nowilt − Contrôle (m³/m³)", fontsize=9)
    
    plt.tight_layout()
    fig_d_path = os.path.join(OUT_FIG_DIR, "figure_point_d_nowilt_vs_control_pm005.png")
    plt.savefig(fig_d_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  -> Figure sauvegardée : {fig_d_path}")
    
    # -------------------------------------------------------------
    # POINT 5 : DIAGNOSTIC DU REJET PAR TEXTURE POUR MARS-AVRIL
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" POINT 5 : DIAGNOSTIC DU REJET PAR TEXTURE POUR MARS-AVRIL (2016-2020)")
    print("-------------------------------------------------------------")
    months_ma = [3, 4]
    smap_ma, ol_ma, wilt_frac_ma, raw_cnt_ma, acc_cnt_ma, wilt_cnt_ma = compute_period_stats(
        years_5y, months_ma, landmask, wlt_grid)
        
    diff_ma = smap_ma - ol_ma
    qual_px_ma = land_bool & non_forest & (raw_cnt_ma >= 10)
    
    tot_raw_ma = np.sum(raw_cnt_ma[land_bool])
    tot_acc_ma = np.sum(acc_cnt_ma[land_bool])
    tot_wilt_ma = np.sum(wilt_cnt_ma[land_bool])
    
    print(f"\nBilan global d'observations DAOBS en Mars-Avril (2016-2020) :")
    print(f"  Obs brutes valides : {tot_raw_ma:,}")
    print(f"  Obs acceptées      : {tot_acc_ma:,} ({100*tot_acc_ma/tot_raw_ma:.1f}%)")
    print(f"  Obs rejetées wilt  : {tot_wilt_ma:,} ({100*tot_wilt_ma/tot_raw_ma:.1f}%)")
    
    print("\nTableau comparatif par texture dominante : Mars-Avril vs Juillet-Août (2016-2020) :")
    print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'smcwlt':<7} | {'seuil':<7} | {'Rejet MA (%)':<13} | {'Rejet JA (%)':<13} | {'SMAP MA':<9} | {'OL MA':<9} | {'SMAP-OL MA':<11}")
    print("-" * 115)
    for c in present_cats:
        m_c_ma = qual_px_ma & (soiltype == c)
        m_c_ja = qual_px & (soiltype == c)
        n_px = np.sum(m_c_ma)
        if n_px == 0: continue
        wlt_val = wltsmc[c]
        thr_val = wlt_val + 0.02
        rej_ma_m = np.nanmean(wilt_frac_ma[m_c_ma]) * 100
        rej_ja_m = np.nanmean(wilt_frac_ja[m_c_ja]) * 100 if np.sum(m_c_ja) > 0 else np.nan
        smap_ma_m = np.nanmean(smap_ma[m_c_ma])
        ol_ma_m = np.nanmean(ol_ma[m_c_ma])
        diff_ma_m = np.nanmean(diff_ma[m_c_ma])
        name = TEXTURE_NAMES.get(c, "Inconnu")
        print(f"{c:<4} | {name:<16} | {n_px:<6} | {wlt_val:<7.3f} | {thr_val:<7.3f} | {rej_ma_m:<12.1f}% | {rej_ja_m:<12.1f}% | {smap_ma_m:<9.4f} | {ol_ma_m:<9.4f} | {diff_ma_m:<+11.4f}")
        
    print("-" * 115)
    all_rej_ma = np.nanmean(wilt_frac_ma[qual_px_ma]) * 100
    all_rej_ja = np.nanmean(wilt_frac_ja[qual_px]) * 100
    print(f"{'ALL':<4} | {'Ensemble':<16} | {np.sum(qual_px_ma):<6} | {'-':<7} | {'-':<7} | {all_rej_ma:<12.1f}% | {all_rej_ja:<12.1f}% | {np.nanmean(smap_ma[qual_px_ma]):<9.4f} | {np.nanmean(ol_ma[qual_px_ma]):<9.4f} | {np.nanmean(diff_ma[qual_px_ma]):<+11.4f}")

if __name__ == "__main__":
    main()
