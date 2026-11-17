#!/usr/bin/env python3
"""
drydown_point1_uncensored.py
----------------------------
ÉTAPE A : Analyse des séchages (dry-downs) avec série SMAP non censurée,
bilan de censure NoCDF vs CDF, régression tau vs argile, et comparaison ET vs GLEAM.

Auteur : Antigravity / Mohammad El Aabaribaoune
Date : 2026-11-17
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
from scipy.interpolate import RegularGridInterpolator

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# Configuration des chemins
# -------------------------------------------------------------
BASE_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"

LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")
SOILPARM_PATH = os.path.join(BASE_DIR, "data/land_params/noahmp401_parms/SOILPARM.TBL")

BASE_DA_NOCDF = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output")
BASE_DA_CDF = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output")

OLD_CACHE_FILE = os.path.join(AUDIT_DIR, "reports/audits/drydown_point1/daily_cache_2016_2020.npz")
OLD_CSV_FILE = os.path.join(AUDIT_DIR, "reports/audits/drydown_point1/drydown_results_by_season_texture.csv")

OUTPUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/drydown_point1_uncensored")
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, "daily_cache_uncensored_2016_2020.npz")
CENSORSHIP_CACHE = os.path.join(OUTPUT_DIR, "censorship_budget_2016_2020.npz")

GLEAM_DIR = os.path.join(BASE_DIR, "data/validation/evapotranspiration/GLEAM/raw")
OPL_ET_DIR = os.path.join(AUDIT_DIR, "data/interim/noahmp/opl/et")

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

NOMINAL_CLAY_FRACTION = {
    1: 0.03,
    2: 0.06,
    3: 0.10,
    4: 0.13,
    5: 0.06,
    6: 0.19,
    7: 0.27,
    8: 0.34,
    9: 0.34,
    10: 0.42,
    11: 0.47,
    12: 0.58,
}

G_LAND_BOOL = None
G_PRECIP = None
G_OL = None
G_SMAP_UNCENSORED = None
G_SOILTYPE = None
G_SMCWLT = None
G_BLOCK = None
G_LAT = None
G_LON = None
G_DATES = None
G_N_DAYS = None
G_SEASON_INDICES = None

def load_static():
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
        texture = ds.variables["TEXTURE"][:]
        lc = ds.variables["LANDCOVER"][:]
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]
        
    soiltype = np.argmax(texture, axis=0) + 1
    vegt = np.argmax(lc, axis=0) + 1
    
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
                    wltsmc_table[int(parts[0])] = float(parts[9])
                    
    smcwlt_grid = np.zeros_like(soiltype, dtype=float)
    for cat, wlt in wltsmc_table.items():
        smcwlt_grid[soiltype == cat] = wlt
        
    block_id_grid = np.full(landmask.shape, -1, dtype=int)
    n_col_blocks = int(np.ceil(181 / 7))
    for r in range(121):
        for c in range(181):
            if landmask[r, c] == 1:
                block_id_grid[r, c] = (r // 7) * n_col_blocks + (c // 7)
                
    return landmask, soiltype, smcwlt_grid, vegt, block_id_grid, lat, lon

def read_daobs_file(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def build_or_load_daily_cache(landmask, smcwlt_grid, vegt):
    if os.path.exists(CACHE_FILE):
        print(f"[INFO] Chargement du cache depuis {CACHE_FILE}...")
        data = np.load(CACHE_FILE)
        return (
            data["precip_daily"],
            data["ol_daily"],
            data["smap_censored_daily"],
            data["smap_uncensored_daily"],
            [datetime.date.fromisoformat(d) for d in data["dates_str"]]
        )
        
    print("[INFO] Construction du cache journalier uncensored 2016–2020...")
    t0 = time.time()
    
    if os.path.exists(OLD_CACHE_FILE):
        print(f"[INFO] Réutilisation précip & OL depuis {OLD_CACHE_FILE}...")
        old_data = np.load(OLD_CACHE_FILE)
        precip_arr = old_data["precip_daily"]
        ol_arr = old_data["ol_daily"]
        dates_list = [datetime.date.fromisoformat(d) for d in old_data["dates_str"]]
    else:
        raise RuntimeError("L'ancien cache d'OL/Précip n'existe pas !")

    print("[INFO] Indexation des fichiers DAOBS NoCDF...")
    daobs_by_date = {}
    for ym in [f"{y}-{m:02d}" for y in range(2016, 2021) for m in range(1, 13)]:
        ym_compact = ym.replace("-", "")
        patt = os.path.join(BASE_DA_NOCDF, ym, "DAOBS", ym_compact, "LISDAOBS_*.1gs4r")
        for fp in glob.glob(patt):
            bn = os.path.basename(fp)
            dstr = bn.split("_")[1][:8]
            if dstr not in daobs_by_date:
                daobs_by_date[dstr] = []
            daobs_by_date[dstr].append(fp)
            
    print(f"[INFO] {len(daobs_by_date)} dates avec observations DAOBS trouvées.")
    
    smap_cens_list = []
    smap_uncens_list = []
    total_checks = 0
    total_diffs = 0
    is_forest = (vegt <= 4)
    
    for dt in dates_list:
        dstr = dt.strftime("%Y%m%d")
        if dstr in daobs_by_date:
            sum_cens = np.zeros((121, 181), dtype=float)
            cnt_cens = np.zeros((121, 181), dtype=int)
            sum_uncens = np.zeros((121, 181), dtype=float)
            cnt_uncens = np.zeros((121, 181), dtype=int)
            
            for df in daobs_by_date[dstr]:
                rec1, rec2 = read_daobs_file(df)
                cand_wilt = (rec1 != -9999.0) & (rec2 == -9999.0) & (rec1 - smcwlt_grid < 0.02) & (~is_forest)
                uncens_pass = np.where(rec2 != -9999.0, rec2, np.where(cand_wilt, rec1, np.nan))
                
                test_cens = np.where(uncens_pass - smcwlt_grid >= 0.02, uncens_pass, np.nan)
                expected_cens = np.where(rec2 != -9999.0, rec2, np.nan)
                
                mask_diff = np.abs(np.nan_to_num(test_cens, nan=-9999.0) - np.nan_to_num(expected_cens, nan=-9999.0)) > 1e-5
                if np.any(mask_diff):
                    total_diffs += np.sum(mask_diff)
                total_checks += (rec1 != -9999.0).sum()
                
                v_c = np.isfinite(expected_cens)
                sum_cens[v_c] += expected_cens[v_c]
                cnt_cens[v_c] += 1
                
                v_u = np.isfinite(uncens_pass)
                sum_uncens[v_u] += uncens_pass[v_u]
                cnt_uncens[v_u] += 1
                
            day_cens = np.full((121, 181), np.nan, dtype=np.float32)
            day_uncens = np.full((121, 181), np.nan, dtype=np.float32)
            
            vc_d = cnt_cens > 0
            vu_d = cnt_uncens > 0
            day_cens[vc_d] = sum_cens[vc_d] / cnt_cens[vc_d]
            day_uncens[vu_d] = sum_uncens[vu_d] / cnt_uncens[vu_d]
        else:
            day_cens = np.full((121, 181), np.nan, dtype=np.float32)
            day_uncens = np.full((121, 181), np.nan, dtype=np.float32)
            
        smap_cens_list.append(day_cens)
        smap_uncens_list.append(day_uncens)
        
    print(f"[VERIFICATION ÉTAPE A.2] Total obs brutes testées : {total_checks}")
    print(f"[VERIFICATION ÉTAPE A.2] Différences avec rec2 après réapplication du seuil : {total_diffs}")
    if total_diffs == 0:
        print("[VERIFICATION ÉTAPE A.2] SUCCÈS PARFAIT : 100.00% d'accord exact avec rec2 !")
        
    smap_cens_arr = np.stack(smap_cens_list, axis=0)
    smap_uncens_arr = np.stack(smap_uncens_list, axis=0)
    dates_str = [d.isoformat() for d in dates_list]
    
    print(f"[INFO] Sauvegarde dans {CACHE_FILE}...")
    np.savez_compressed(
        CACHE_FILE,
        precip_daily=precip_arr,
        ol_daily=ol_arr,
        smap_censored_daily=smap_cens_arr,
        smap_uncensored_daily=smap_uncens_arr,
        dates_str=dates_str
    )
    print(f"[INFO] Cache construit en {time.time() - t0:.1f} s.")
    return precip_arr, ol_arr, smap_cens_arr, smap_uncens_arr, dates_list

def compute_censorship_budget(landmask, smcwlt_grid, vegt, soiltype):
    if os.path.exists(CENSORSHIP_CACHE):
        print(f"[INFO] Chargement du bilan de censure depuis {CENSORSHIP_CACHE}...")
        data = np.load(CENSORSHIP_CACHE)
        return (
            data["nocdf_wilt_rej_monthly"],
            data["nocdf_valid_monthly"],
            data["cdf_wilt_rej_monthly"],
            data["cdf_valid_monthly"]
        )
        
    print("[INFO] Calcul du bilan de censure NoCDF et CDF (2016–2020)...")
    t0 = time.time()
    
    nocdf_wilt_rej = np.zeros((12, 121, 181), dtype=np.int32)
    nocdf_valid = np.zeros((12, 121, 181), dtype=np.int32)
    cdf_wilt_rej = np.zeros((12, 121, 181), dtype=np.int32)
    cdf_valid = np.zeros((12, 121, 181), dtype=np.int32)
    is_forest = (vegt <= 4)
    
    print("  ... Traitement NoCDF...")
    for ym in [f"{y}-{m:02d}" for y in range(2016, 2021) for m in range(1, 13)]:
        m_idx = int(ym.split("-")[1]) - 1
        ym_compact = ym.replace("-", "")
        patt = os.path.join(BASE_DA_NOCDF, ym, "DAOBS", ym_compact, "LISDAOBS_*.1gs4r")
        for fp in glob.glob(patt):
            rec1, rec2 = read_daobs_file(fp)
            cand_wilt = (rec1 != -9999.0) & (rec2 == -9999.0) & (rec1 - smcwlt_grid < 0.02) & (~is_forest)
            accepted = (rec2 != -9999.0)
            nocdf_valid[m_idx] += (accepted | cand_wilt).astype(np.int32)
            nocdf_wilt_rej[m_idx] += cand_wilt.astype(np.int32)
            
    print("  ... Traitement CDF...")
    for ym in [f"{y}-{m:02d}" for y in range(2016, 2021) for m in range(1, 13)]:
        m_idx = int(ym.split("-")[1]) - 1
        ym_compact = ym.replace("-", "")
        patt = os.path.join(BASE_DA_CDF, ym, "DAOBS", ym_compact, "LISDAOBS_*.1gs4r")
        for fp in glob.glob(patt):
            rec1, rec2 = read_daobs_file(fp)
            cand_wilt = (rec1 != -9999.0) & (rec2 == -9999.0) & (rec1 - smcwlt_grid < 0.02) & (~is_forest)
            accepted = (rec2 != -9999.0)
            cdf_valid[m_idx] += (accepted | cand_wilt).astype(np.int32)
            cdf_wilt_rej[m_idx] += cand_wilt.astype(np.int32)
            
    np.savez_compressed(
        CENSORSHIP_CACHE,
        nocdf_wilt_rej_monthly=nocdf_wilt_rej,
        nocdf_valid_monthly=nocdf_valid,
        cdf_wilt_rej_monthly=cdf_wilt_rej,
        cdf_valid_monthly=cdf_valid
    )
    print(f"[INFO] Bilan de censure calculé et sauvegardé en {time.time() - t0:.1f} s.")
    return nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid

def plot_censorship_maps(nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid, landmask, lat, lon):
    mam_idx = [2, 3, 4]
    jja_idx = [5, 6, 7]
    
    with np.errstate(divide='ignore', invalid='ignore'):
        nocdf_mam = np.sum(nocdf_wilt_rej[mam_idx], axis=0) / np.maximum(1, np.sum(nocdf_valid[mam_idx], axis=0))
        nocdf_jja = np.sum(nocdf_wilt_rej[jja_idx], axis=0) / np.maximum(1, np.sum(nocdf_valid[jja_idx], axis=0))
        cdf_mam = np.sum(cdf_wilt_rej[mam_idx], axis=0) / np.maximum(1, np.sum(cdf_valid[mam_idx], axis=0))
        cdf_jja = np.sum(cdf_wilt_rej[jja_idx], axis=0) / np.maximum(1, np.sum(cdf_valid[jja_idx], axis=0))
        
    for arr in [nocdf_mam, nocdf_jja, cdf_mam, cdf_jja]:
        arr[landmask == 0] = np.nan
        
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
    
    panels = [
        (axes[0, 0], nocdf_mam, "(a) NoCDF — Printemps (MAM)"),
        (axes[0, 1], nocdf_jja, "(b) NoCDF — Été (JJA)"),
        (axes[1, 0], cdf_mam, "(c) CDF — Printemps (MAM)"),
        (axes[1, 1], cdf_jja, "(d) CDF — Été (JJA)")
    ]
    
    cmap = plt.cm.YlOrRd
    cmap.set_bad("lightgray")
    
    for ax, data, title in panels:
        im = ax.pcolormesh(lon, lat, data * 100.0, cmap=cmap, vmin=0, vmax=100, shading="auto")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, linestyle="--", alpha=0.5)
        
    fig.subplots_adjust(right=0.88, hspace=0.15, wspace=0.1)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label("Fraction d'observations rejetées par flétrissement (%)", fontsize=11, fontweight="bold")
    
    plt.suptitle("Bilan de la censure du filtre de flétrissement (smobs − smcwlt < 0.02)\nsur les observations SMAP (2016–2020)", fontsize=14, fontweight="bold")
    
    out_png = os.path.join(OUTPUT_DIR, "censorship_budget_maps_mam_jja.png")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Carte sauvegardée dans {out_png}")

def generate_censorship_table(nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid, soiltype, landmask, smcwlt_grid):
    mam_idx = [2, 3, 4]
    jja_idx = [5, 6, 7]
    
    with np.errstate(divide='ignore', invalid='ignore'):
        nocdf_mam = np.sum(nocdf_wilt_rej[mam_idx], axis=0) / np.maximum(1, np.sum(nocdf_valid[mam_idx], axis=0))
        nocdf_jja = np.sum(nocdf_wilt_rej[jja_idx], axis=0) / np.maximum(1, np.sum(nocdf_valid[jja_idx], axis=0))
        nocdf_ann = np.sum(nocdf_wilt_rej, axis=0) / np.maximum(1, np.sum(nocdf_valid, axis=0))
        
        cdf_mam = np.sum(cdf_wilt_rej[mam_idx], axis=0) / np.maximum(1, np.sum(cdf_valid[mam_idx], axis=0))
        cdf_jja = np.sum(cdf_wilt_rej[jja_idx], axis=0) / np.maximum(1, np.sum(cdf_valid[jja_idx], axis=0))
        cdf_ann = np.sum(cdf_wilt_rej, axis=0) / np.maximum(1, np.sum(cdf_valid, axis=0))

    rows = []
    for cat in sorted(TEXTURE_NAMES.keys()):
        mask = (soiltype == cat) & (landmask == 1)
        n_pix = mask.sum()
        if n_pix == 0:
            continue
            
        clay_pct = NOMINAL_CLAY_FRACTION[cat] * 100.0
        wlt_val = np.nanmean(smcwlt_grid[mask])
        
        rows.append({
            "soil_id": cat,
            "texture": TEXTURE_NAMES[cat],
            "n_pixels": n_pix,
            "clay_fraction_pct": round(clay_pct, 1),
            "smcwlt": round(float(wlt_val), 3),
            "nocdf_mam_pct": round(float(np.nanmean(nocdf_mam[mask])) * 100.0, 1),
            "nocdf_jja_pct": round(float(np.nanmean(nocdf_jja[mask])) * 100.0, 1),
            "nocdf_ann_pct": round(float(np.nanmean(nocdf_ann[mask])) * 100.0, 1),
            "cdf_mam_pct": round(float(np.nanmean(cdf_mam[mask])) * 100.0, 1),
            "cdf_jja_pct": round(float(np.nanmean(cdf_jja[mask])) * 100.0, 1),
            "cdf_ann_pct": round(float(np.nanmean(cdf_ann[mask])) * 100.0, 1),
        })
        
    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUTPUT_DIR, "censorship_budget_by_texture.csv")
    df.to_csv(out_csv, index=False)
    print(f"[INFO] Tableau de censure sauvegardé dans {out_csv}")
    return df

def exp_decay(t, theta_res, delta_theta, tau):
    return theta_res + delta_theta * np.exp(-t / tau)

def fit_single_drydown(t_obs, sm_obs, min_obs=3):
    if len(t_obs) < min_obs:
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
    m = dt.month
    if m in [3, 4, 5]:
        return "MAM"
    elif m in [6, 7, 8]:
        return "JJA"
    elif m in [9, 10, 11]:
        return "SON"
    else:
        return "DJF"

def init_worker(landmask, precip, ol, smap_uncensored, soiltype, smcwlt, block_id, lat, lon, dates, season_indices):
    global G_LAND_BOOL, G_PRECIP, G_OL, G_SMAP_UNCENSORED, G_SOILTYPE, G_SMCWLT, G_BLOCK, G_LAT, G_LON, G_DATES, G_N_DAYS, G_SEASON_INDICES
    G_LAND_BOOL = landmask.astype(bool)
    G_PRECIP = precip
    G_OL = ol
    G_SMAP_UNCENSORED = smap_uncensored
    G_SOILTYPE = soiltype
    G_SMCWLT = smcwlt
    G_BLOCK = block_id
    G_LAT = lat
    G_LON = lon
    G_DATES = dates
    G_N_DAYS = len(dates)
    G_SEASON_INDICES = season_indices

def process_pixel_batch(pixel_list):
    results_base = []
    results_sens = []
    p5_results = []
    
    for r, c in pixel_list:
        if not G_LAND_BOOL[r, c]:
            continue
            
        p_series = G_PRECIP[:, r, c]
        ol_series = G_OL[:, r, c]
        smap_series = G_SMAP_UNCENSORED[:, r, c]
        
        stype = int(G_SOILTYPE[r, c])
        wlt = float(G_SMCWLT[r, c])
        b_id = int(G_BLOCK[r, c])
        lat_v = float(G_LAT[r, c])
        lon_v = float(G_LON[r, c])
        
        for s_name, s_idx in G_SEASON_INDICES.items():
            ol_s = ol_series[s_idx]
            smap_s = smap_series[s_idx]
            ol_valid = ol_s[np.isfinite(ol_s)]
            smap_valid = smap_s[np.isfinite(smap_s)]
            
            p5_ol = float(np.percentile(ol_valid, 5)) if len(ol_valid) >= 20 else np.nan
            p5_smap = float(np.percentile(smap_valid, 5)) if len(smap_valid) >= 15 else np.nan
            
            p5_results.append({
                "row": r, "col": c, "lat": lat_v, "lon": lon_v, "soil_id": stype, "block_id": b_id,
                "smcwlt": wlt, "season": s_name, "p5_ol": p5_ol, "p5_smap": p5_smap,
                "n_smap_season": len(smap_valid), "n_ol_season": len(ol_valid)
            })

        i = 0
        while i < G_N_DAYS - 7:
            if p_series[i] >= 5.0 and np.isfinite(p_series[i]):
                dry_len = 0
                k = i + 1
                while k < G_N_DAYS and (p_series[k] < 1.0) and np.isfinite(p_series[k]):
                    dry_len += 1
                    k += 1
                    
                if dry_len >= 7:
                    t_idx = np.arange(1, dry_len + 1)
                    smap_window = smap_series[i + 1 : i + 1 + dry_len]
                    ol_window = ol_series[i + 1 : i + 1 + dry_len]
                    
                    v_smap = np.isfinite(smap_window)
                    n_smap = np.sum(v_smap)
                    
                    if n_smap >= 3:
                        t_smap = t_idx[v_smap]
                        sm_smap = smap_window[v_smap]
                        sm_ol_paired = ol_window[v_smap]
                        
                        fit_smap = fit_single_drydown(t_smap, sm_smap, min_obs=3)
                        fit_ol = fit_single_drydown(t_smap, sm_ol_paired, min_obs=3)
                        
                        start_date = G_DATES[i + 1]
                        season = get_season(start_date)
                        
                        if fit_smap is not None and fit_ol is not None:
                            res_dict = {
                                "row": r, "col": c, "lat": lat_v, "lon": lon_v,
                                "soil_id": stype, "block_id": b_id, "smcwlt": wlt,
                                "start_date": start_date.isoformat(), "dry_len": dry_len,
                                "season": season, "n_obs_smap": int(n_smap),
                                "tau_smap": fit_smap["tau"], "theta_res_smap": fit_smap["theta_res"],
                                "delta_theta_smap": fit_smap["delta_theta"], "r2_smap": fit_smap["r2"],
                                "tau_ol": fit_ol["tau"], "theta_res_ol": fit_ol["theta_res"],
                                "delta_theta_ol": fit_ol["delta_theta"], "r2_ol": fit_ol["r2"],
                            }
                            results_base.append(res_dict)
                            if n_smap >= 4:
                                results_sens.append(res_dict)
                                
                    i += dry_len + 1
                else:
                    i += 1
            else:
                i += 1
                
    return results_base, results_sens, p5_results

def block_bootstrap_ci(df_data, metric_col, block_col="block_id", n_boot=1000, ci=95, seed=42):
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
    low = np.percentile(valid_stats, alpha)
    high = np.percentile(valid_stats, 100.0 - alpha)
    return float(low), float(high)

def block_bootstrap_slope(df_data, x_col, y_col, block_col="block_id", n_boot=1000, ci=95, seed=42):
    blocks = df_data[block_col].unique()
    n_blocks = len(blocks)
    if n_blocks < 2 or len(df_data) < 5:
        return np.nan, np.nan, np.nan
        
    p_obs = np.polyfit(df_data[x_col].values, df_data[y_col].values, 1)[0]
    
    rng = np.random.default_rng(seed)
    grouped = {b: (grp[x_col].values, grp[y_col].values) for b, grp in df_data.groupby(block_col)}
    
    boot_slopes = np.empty(n_boot)
    for i in range(n_boot):
        sampled_blocks = rng.choice(blocks, size=n_blocks, replace=True)
        x_vals = np.concatenate([grouped[b][0] for b in sampled_blocks if len(grouped[b][0]) > 0])
        y_vals = np.concatenate([grouped[b][1] for b in sampled_blocks if len(grouped[b][1]) > 0])
        if len(x_vals) >= 5 and np.std(x_vals) > 1e-4:
            boot_slopes[i] = np.polyfit(x_vals, y_vals, 1)[0]
        else:
            boot_slopes[i] = np.nan
            
    valid = boot_slopes[np.isfinite(boot_slopes)]
    alpha = (100.0 - ci) / 2.0
    low = np.percentile(valid, alpha) if len(valid) > 0 else np.nan
    high = np.percentile(valid, 100.0 - alpha) if len(valid) > 0 else np.nan
    return float(p_obs), float(low), float(high)

def load_and_regrid_gleam_mam(dates_list, lat_target, lon_target):
    print("[INFO] Chargement et interpolation de GLEAM v4.3a pour le printemps (MAM)...")
    t0 = time.time()
    
    mam_dates = [d for d in dates_list if d.month in [3, 4, 5]]
    gleam_by_date = {}
    years = sorted(set(d.year for d in mam_dates))
    
    for y in years:
        gfile = os.path.join(GLEAM_DIR, f"E_{y}_GLEAM_v4.3a.nc")
        if not os.path.exists(gfile):
            print(f"[WARNING] GLEAM file introuvable : {gfile}")
            continue
            
        with nc.Dataset(gfile) as ds:
            glat = ds.variables["lat"][:]
            glon = ds.variables["lon"][:]
            
            lat_min, lat_max = lat_target.min() - 0.2, lat_target.max() + 0.2
            lon_min, lon_max = lon_target.min() - 0.2, lon_target.max() + 0.2
            
            i_lat = np.where((glat >= lat_min) & (glat <= lat_max))[0]
            i_lon = np.where((glon >= lon_min) & (glon <= lon_max))[0]
            
            sub_lat = glat[i_lat]
            sub_lon = glon[i_lon]
            
            if sub_lat[0] > sub_lat[-1]:
                sub_lat = sub_lat[::-1]
                lat_reverse = True
            else:
                lat_reverse = False
                
            year_dates = [d for d in mam_dates if d.year == y]
            day_of_year = [d.timetuple().tm_yday - 1 for d in year_dates]
            
            if lat_reverse:
                cube = ds.variables["E"][day_of_year, i_lat[::-1], i_lon]
            else:
                cube = ds.variables["E"][day_of_year, i_lat, i_lon]
                
            pts_target = np.stack([lat_target.flatten(), lon_target.flatten()], axis=-1)
            
            for idx_d, dt in enumerate(year_dates):
                interp = RegularGridInterpolator((sub_lat, sub_lon), cube[idx_d], bounds_error=False, fill_value=np.nan)
                regridded = interp(pts_target).reshape(121, 181)
                gleam_by_date[dt.isoformat()] = regridded
                
    print(f"[INFO] GLEAM MAM interpolé pour {len(gleam_by_date)} dates en {time.time() - t0:.1f} s.")
    return gleam_by_date

def load_opl_et(dates_list):
    print("[INFO] Chargement de l'ET journalière OL...")
    opl_et_by_date = {}
    years = sorted(set(d.year for d in dates_list))
    for y in years:
        f = os.path.join(OPL_ET_DIR, f"et_{y}.nc")
        if not os.path.exists(f):
            print(f"[WARNING] OPL ET introuvable : {f}")
            continue
        with nc.Dataset(f) as ds:
            et_cube = ds.variables["et"][:]
            y_dates = [d for d in dates_list if d.year == y]
            for idx_d, dt in enumerate(y_dates):
                opl_et_by_date[dt.isoformat()] = et_cube[idx_d]
    return opl_et_by_date

def analyze_et_during_drydowns(df_episodes_mam, gleam_by_date, opl_et_by_date, soiltype, landmask):
    print("[INFO] Analyse comparative de l'ET sur les 5 premiers jours après la pluie en MAM...")
    et_records = []
    
    for _, row in df_episodes_mam.iterrows():
        r = int(row["row"])
        c = int(row["col"])
        stype = int(row["soil_id"])
        b_id = int(row["block_id"])
        start_dt = datetime.date.fromisoformat(row["start_date"])
        
        ol_5d = []
        gleam_5d = []
        
        for d_offset in range(5):
            cur_dt = start_dt + datetime.timedelta(days=d_offset)
            dt_str = cur_dt.isoformat()
            if dt_str in opl_et_by_date and dt_str in gleam_by_date:
                e_ol = opl_et_by_date[dt_str][r, c]
                e_gl = gleam_by_date[dt_str][r, c]
                if np.isfinite(e_ol) and np.isfinite(e_gl):
                    ol_5d.append(e_ol)
                    gleam_5d.append(e_gl)
                    
        if len(ol_5d) >= 4:
            mean_ol = float(np.mean(ol_5d))
            mean_gl = float(np.mean(gleam_5d))
            et_records.append({
                "row": r, "col": c, "soil_id": stype, "block_id": b_id,
                "start_date": row["start_date"],
                "et_ol_5d": mean_ol,
                "et_gleam_5d": mean_gl,
                "delta_et": mean_ol - mean_gl
            })
            
    df_et = pd.DataFrame(et_records)
    out_csv_all = os.path.join(OUTPUT_DIR, "et_mam_drydown_5days_all_events.csv")
    df_et.to_csv(out_csv_all, index=False)
    
    summary_rows = []
    for cat in sorted(TEXTURE_NAMES.keys()):
        sub = df_et[df_et["soil_id"] == cat]
        if len(sub) < 5:
            continue
        ol_mean = float(sub["et_ol_5d"].mean())
        ol_med = float(sub["et_ol_5d"].median())
        gl_mean = float(sub["et_gleam_5d"].mean())
        gl_med = float(sub["et_gleam_5d"].median())
        delta_mean = float(sub["delta_et"].mean())
        delta_med = float(sub["delta_et"].median())
        bias_pct = (delta_mean / gl_mean) * 100.0 if gl_mean > 0 else np.nan
        
        summary_rows.append({
            "soil_id": cat,
            "texture": TEXTURE_NAMES[cat],
            "clay_fraction_pct": NOMINAL_CLAY_FRACTION[cat] * 100.0,
            "n_events": len(sub),
            "et_ol_mean_mm_d": round(ol_mean, 2),
            "et_ol_med_mm_d": round(ol_med, 2),
            "et_gleam_mean_mm_d": round(gl_mean, 2),
            "et_gleam_med_mm_d": round(gl_med, 2),
            "delta_et_mean_mm_d": round(delta_mean, 2),
            "delta_et_med_mm_d": round(delta_med, 2),
            "bias_rel_pct": round(bias_pct, 1)
        })
        
    df_et_summary = pd.DataFrame(summary_rows)
    out_csv_summary = os.path.join(OUTPUT_DIR, "et_mam_drydown_5days_by_texture.csv")
    df_et_summary.to_csv(out_csv_summary, index=False)
    print(f"[INFO] Synthèse ET sauvegardée dans {out_csv_summary}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df_et_summary))
    w = 0.35
    ax.bar(x - w/2, df_et_summary["et_ol_mean_mm_d"], width=w, label="Noah-MP OL", color="#e74c3c", alpha=0.85)
    ax.bar(x + w/2, df_et_summary["et_gleam_mean_mm_d"], width=w, label="GLEAM v4.3a", color="#2ecc71", alpha=0.85)
    
    for i in range(len(df_et_summary)):
        b = df_et_summary.iloc[i]["bias_rel_pct"]
        ax.text(x[i], max(df_et_summary.iloc[i]["et_ol_mean_mm_d"], df_et_summary.iloc[i]["et_gleam_mean_mm_d"]) + 0.1,
                f"{b:+.1f}%", ha="center", fontsize=9, fontweight="bold",
                color="red" if b > 0 else "blue")
                
    ax.set_xticks(x)
    ax.set_xticklabels(df_et_summary["texture"], rotation=35, ha="right", fontsize=10)
    ax.set_ylabel("Évapotranspiration moyenne J1–J5 (mm/j)", fontsize=11, fontweight="bold")
    ax.set_title("Évapotranspiration moyenne sur les 5 premiers jours après la pluie (MAM)\nNoah-MP (OL) vs GLEAM v4.3a par classe de texture", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    plt.tight_layout()
    out_png = os.path.join(OUTPUT_DIR, "et_mam_drydown_ol_vs_gleam.png")
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"[INFO] Figure ET sauvegardée dans {out_png}")
    return df_et_summary

def main():
    print("=" * 70)
    print("ÉTAPE A : ANALYSE DES SÉCHAGES AVEC SMAP NON CENSURÉ")
    print("=" * 70)
    t_start = time.time()
    
    print("\n--- 1. CHARGEMENT DES DONNÉES STATIQUES ---")
    landmask, soiltype, smcwlt_grid, vegt, block_id_grid, lat, lon = load_static()
    n_land_pixels = landmask.sum()
    print(f"Pixels terrestres : {n_land_pixels}")
    
    print("\n--- 2. CONSTRUCTION DE LA SÉRIE SMAP SANS CENSURE DE FLÉTRISSEMENT ---")
    precip_arr, ol_arr, smap_cens_arr, smap_uncens_arr, dates_list = build_or_load_daily_cache(
        landmask, smcwlt_grid, vegt
    )
    
    print("\n--- 3. BILAN DE CENSURE PAR LE SEUIL DE FLÉTRISSEMENT ---")
    nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid = compute_censorship_budget(
        landmask, smcwlt_grid, vegt, soiltype
    )
    plot_censorship_maps(nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid, landmask, lat, lon)
    df_censorship = generate_censorship_table(
        nocdf_wilt_rej, nocdf_valid, cdf_wilt_rej, cdf_valid, soiltype, landmask, smcwlt_grid
    )
    
    print("\n--- 4. AJUSTEMENT EXPONENTIEL DES SÉCHAGES (PARALLÉLISATION) ---")
    season_indices = {
        "MAM": [idx for idx, d in enumerate(dates_list) if d.month in [3, 4, 5]],
        "JJA": [idx for idx, d in enumerate(dates_list) if d.month in [6, 7, 8]],
        "SON": [idx for idx, d in enumerate(dates_list) if d.month in [9, 10, 11]],
        "DJF": [idx for idx, d in enumerate(dates_list) if d.month in [12, 1, 2]],
    }
    
    land_coords = [(r, c) for r in range(121) for c in range(181) if landmask[r, c] == 1]
    n_workers = min(16, mp.cpu_count())
    batch_size = int(np.ceil(len(land_coords) / n_workers))
    batches = [land_coords[i : i + batch_size] for i in range(0, len(land_coords), batch_size)]
    
    print(f"Lancement de {len(batches)} batches sur {n_workers} cœurs...")
    with mp.Pool(
        processes=n_workers,
        initializer=init_worker,
        initargs=(landmask, precip_arr, ol_arr, smap_uncens_arr, soiltype, smcwlt_grid, block_id_grid, lat, lon, dates_list, season_indices)
    ) as pool:
        batch_results = pool.map(process_pixel_batch, batches)
        
    all_res_base = []
    all_res_sens = []
    all_p5 = []
    for b, s, p in batch_results:
        all_res_base.extend(b)
        all_res_sens.extend(s)
        all_p5.extend(p)
        
    df_base = pd.DataFrame(all_res_base)
    df_sens = pd.DataFrame(all_res_sens)
    df_p5 = pd.DataFrame(all_p5)
    
    print(f"Épisodes ajustés (Baseline N>=3) : {len(df_base)}")
    print(f"Épisodes ajustés (Sensibilité N>=4) : {len(df_sens)}")
    
    df_base.to_csv(os.path.join(OUTPUT_DIR, "drydown_events_uncensored_n3.csv"), index=False)
    df_sens.to_csv(os.path.join(OUTPUT_DIR, "drydown_events_uncensored_n4.csv"), index=False)
    df_p5.to_csv(os.path.join(OUTPUT_DIR, "soil_moisture_p5_uncensored.csv"), index=False)
    
    print("\n--- 5. RÉGRESSION TAU VS FRACTION D'ARGILE (AVEC IC BOOTSTRAP 7x7) ---")
    df_base["clay_fraction"] = df_base["soil_id"].map(NOMINAL_CLAY_FRACTION)
    df_sens["clay_fraction"] = df_sens["soil_id"].map(NOMINAL_CLAY_FRACTION)
    
    slope_rows = []
    for s_name in ["MAM", "JJA", "ALL"]:
        sub = df_base if s_name == "ALL" else df_base[df_base["season"] == s_name]
        if len(sub) > 10:
            p_smap, lo_smap, hi_smap = block_bootstrap_slope(sub, "clay_fraction", "tau_smap")
            p_ol, lo_ol, hi_ol = block_bootstrap_slope(sub, "clay_fraction", "tau_ol")
            slope_rows.append({
                "subset": "Baseline (N>=3)",
                "season": s_name,
                "n_events": len(sub),
                "slope_smap": round(p_smap, 2),
                "slope_smap_ci95_low": round(lo_smap, 2),
                "slope_smap_ci95_high": round(hi_smap, 2),
                "slope_ol": round(p_ol, 2),
                "slope_ol_ci95_low": round(lo_ol, 2),
                "slope_ol_ci95_high": round(hi_ol, 2),
            })
            
    for s_name in ["MAM", "JJA"]:
        sub = df_sens[df_sens["season"] == s_name]
        if len(sub) > 10:
            p_smap, lo_smap, hi_smap = block_bootstrap_slope(sub, "clay_fraction", "tau_smap")
            p_ol, lo_ol, hi_ol = block_bootstrap_slope(sub, "clay_fraction", "tau_ol")
            slope_rows.append({
                "subset": "Sensitivity (N>=4)",
                "season": s_name,
                "n_events": len(sub),
                "slope_smap": round(p_smap, 2),
                "slope_smap_ci95_low": round(lo_smap, 2),
                "slope_smap_ci95_high": round(hi_smap, 2),
                "slope_ol": round(p_ol, 2),
                "slope_ol_ci95_low": round(lo_ol, 2),
                "slope_ol_ci95_high": round(hi_ol, 2),
            })
            
    df_slopes = pd.DataFrame(slope_rows)
    out_slopes_csv = os.path.join(OUTPUT_DIR, "tau_vs_clay_slopes_bootstrap.csv")
    df_slopes.to_csv(out_slopes_csv, index=False)
    print(f"[INFO] Pentes tau vs argile sauvegardées dans {out_slopes_csv}")
    
    sub_mam = df_base[df_base["season"] == "MAM"]
    if len(sub_mam) > 10:
        fig, ax = plt.subplots(figsize=(8, 6))
        grp_tex = sub_mam.groupby("soil_id").agg({
            "clay_fraction": "first",
            "tau_smap": "median",
            "tau_ol": "median",
            "row": "count"
        }).reset_index()
        
        ax.scatter(grp_tex["clay_fraction"] * 100.0, grp_tex["tau_smap"], color="#2980b9", s=grp_tex["row"]*2, label="SMAP uncensored (médianes)", zorder=3)
        ax.scatter(grp_tex["clay_fraction"] * 100.0, grp_tex["tau_ol"], color="#e67e22", s=grp_tex["row"]*2, marker="s", label="Noah-MP OL (médianes)", zorder=3)
        
        p_smap_row = df_slopes[(df_slopes["subset"]=="Baseline (N>=3)") & (df_slopes["season"]=="MAM")]
        p_smap_val = p_smap_row["slope_smap"].values[0] if len(p_smap_row)>0 else 0
        p_ol_row = df_slopes[(df_slopes["subset"]=="Baseline (N>=3)") & (df_slopes["season"]=="MAM")]
        p_ol_val = p_ol_row["slope_ol"].values[0] if len(p_ol_row)>0 else 0
        
        x_grid = np.linspace(0.02, 0.60, 50)
        fit_s = np.polyfit(sub_mam["clay_fraction"], sub_mam["tau_smap"], 1)
        fit_o = np.polyfit(sub_mam["clay_fraction"], sub_mam["tau_ol"], 1)
        
        ax.plot(x_grid * 100.0, np.polyval(fit_s, x_grid), color="#2980b9", linestyle="-", linewidth=2,
                label=f"SMAP pente : {p_smap_val:+.1f} j/%argile")
        ax.plot(x_grid * 100.0, np.polyval(fit_o, x_grid), color="#e67e22", linestyle="--", linewidth=2,
                label=f"OL pente : {p_ol_val:+.1f} j/%argile")
                
        ax.set_xlabel("Fraction nominale d'argile (%)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Constante de temps de séchage tau (jours)", fontsize=11, fontweight="bold")
        ax.set_title("Sensibilité de la vitesse de séchage à la teneur en argile au printemps (MAM)\nSMAP uncensored vs Noah-MP OL", fontsize=12, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "tau_vs_clay_regression_mam.png"), dpi=300)
        plt.close()

    print("\n--- 6. TABLEAU COMPARATIF CONSOLIDÉ : CENSURÉ VS NON-CENSURÉ ---")
    if os.path.exists(OLD_CSV_FILE):
        df_old = pd.read_csv(OLD_CSV_FILE)
    else:
        df_old = pd.DataFrame()
        
    consolidated_rows = []
    for s_name in ["MAM", "JJA"]:
        sub_uncens = df_base[df_base["season"] == s_name]
        sub_p5 = df_p5[df_p5["season"] == s_name]
        
        for cat in sorted(TEXTURE_NAMES.keys()):
            ev_unc = sub_uncens[sub_uncens["soil_id"] == cat]
            p5_sub = sub_p5[sub_p5["soil_id"] == cat]
            
            if len(ev_unc) < 3 and len(p5_sub) < 3:
                continue
                
            wlt_val = np.nanmean(smcwlt_grid[soiltype == cat])
            
            tau_smap_med = float(ev_unc["tau_smap"].median()) if len(ev_unc) > 0 else np.nan
            tau_smap_lo, tau_smap_hi = block_bootstrap_ci(ev_unc, "tau_smap") if len(ev_unc) > 0 else (np.nan, np.nan)
            
            tau_ol_med = float(ev_unc["tau_ol"].median()) if len(ev_unc) > 0 else np.nan
            tau_ol_lo, tau_ol_hi = block_bootstrap_ci(ev_unc, "tau_ol") if len(ev_unc) > 0 else (np.nan, np.nan)
            
            th_smap_med = float(ev_unc["theta_res_smap"].median()) if len(ev_unc) > 0 else np.nan
            th_smap_lo, th_smap_hi = block_bootstrap_ci(ev_unc, "theta_res_smap") if len(ev_unc) > 0 else (np.nan, np.nan)
            
            th_ol_med = float(ev_unc["theta_res_ol"].median()) if len(ev_unc) > 0 else np.nan
            th_ol_lo, th_ol_hi = block_bootstrap_ci(ev_unc, "theta_res_ol") if len(ev_unc) > 0 else (np.nan, np.nan)
            
            p5_smap_med = float(p5_sub["p5_smap"].median()) if len(p5_sub) > 0 else np.nan
            p5_ol_med = float(p5_sub["p5_ol"].median()) if len(p5_sub) > 0 else np.nan
            
            if len(df_old) > 0:
                old_row = df_old[(df_old["season"] == s_name) & (df_old["soil_id"] == cat)]
                if len(old_row) > 0:
                    tau_cens_str = str(old_row["tau_smap_median_ci"].values[0])
                    p5_cens_str = str(old_row["p5_smap_median_ci"].values[0])
                    th_cens_str = str(old_row["theta_res_smap_median_ci"].values[0])
                    n_cens = int(old_row["n_events"].values[0])
                else:
                    tau_cens_str, p5_cens_str, th_cens_str, n_cens = "N/A", "N/A", "N/A", 0
            else:
                tau_cens_str, p5_cens_str, th_cens_str, n_cens = "N/A", "N/A", "N/A", 0
                
            consolidated_rows.append({
                "season": s_name,
                "soil_id": cat,
                "texture": TEXTURE_NAMES[cat],
                "clay_pct": NOMINAL_CLAY_FRACTION[cat] * 100.0,
                "smcwlt": round(float(wlt_val), 3),
                "n_censored_events": n_cens,
                "n_uncensored_events": len(ev_unc),
                "tau_smap_censored": tau_cens_str,
                "tau_smap_uncensored": f"{tau_smap_med:.1f} [{tau_smap_lo:.1f}, {tau_smap_hi:.1f}]" if np.isfinite(tau_smap_med) else "N/A",
                "tau_ol": f"{tau_ol_med:.1f} [{tau_ol_lo:.1f}, {tau_ol_hi:.1f}]" if np.isfinite(tau_ol_med) else "N/A",
                "p5_smap_censored": p5_cens_str,
                "p5_smap_uncensored": f"{p5_smap_med:.3f}" if np.isfinite(p5_smap_med) else "N/A",
                "p5_ol": f"{p5_ol_med:.3f}" if np.isfinite(p5_ol_med) else "N/A",
                "theta_res_smap_censored": th_cens_str,
                "theta_res_smap_uncensored": f"{th_smap_med:.3f} [{th_smap_lo:.3f}, {th_smap_hi:.3f}]" if np.isfinite(th_smap_med) else "N/A",
                "theta_res_ol": f"{th_ol_med:.3f} [{th_ol_lo:.3f}, {th_ol_hi:.3f}]" if np.isfinite(th_ol_med) else "N/A",
            })
            
    df_consolidated = pd.DataFrame(consolidated_rows)
    out_cons_csv = os.path.join(OUTPUT_DIR, "consolidated_drydown_censored_vs_uncensored.csv")
    df_consolidated.to_csv(out_cons_csv, index=False)
    print(f"[INFO] Tableau consolidé sauvegardé dans {out_cons_csv}")
    
    print("\n--- 7. COMPARAISON ET (OL VS GLEAM v4.3a) EN MAM ---")
    gleam_by_date = load_and_regrid_gleam_mam(dates_list, lat, lon)
    opl_et_by_date = load_opl_et(dates_list)
    df_mam_episodes = df_base[df_base["season"] == "MAM"]
    df_et_summary = analyze_et_during_drydowns(df_mam_episodes, gleam_by_date, opl_et_by_date, soiltype, landmask)

    print(f"\n[SUCCÈS] ÉTAPE A terminée avec succès en {time.time() - t_start:.1f} s !")

if __name__ == "__main__":
    main()
