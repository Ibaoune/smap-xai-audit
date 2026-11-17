#!/usr/bin/env python3
"""
point_c_truncation_analysis.py
------------------------------
Point C : Analyse de la troncature par pixel (DA-NoCDF, juillet-août 2016-2020, contre l'OL)
- Pixels hors forêt (vegt > 4) avec au moins 20 obs valides.
- Pour chaque pixel : moyenne(SMAP brut - OL) sur toutes les obs (a) et sur les obs acceptées (b).
- Différence delta = (b) - (a).
- Moyenne et médiane de delta sur les pixels (poids égaux), globalement et par classe de fraction rejetée.
- Carte spatiale de delta et comparaison avec l'effet poolé (+0.020 à +0.025).
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DA = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
BASE_OL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM_PATH = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"

def load_static_params():
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
        lines = f.readlines()
        in_stas = False
        for line in lines:
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

def read_daobs_file(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def run_pixel_analysis():
    print("Chargement des paramètres statiques...")
    landmask, soiltype, vegt, smcwlt_grid, lat, lon = load_static_params()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    # Store accumulators per pixel
    # sum and count of (SMAP brut - OL) for all valid
    sum_a = np.zeros((121, 181), dtype=float)
    cnt_a = np.zeros((121, 181), dtype=int)
    
    # sum and count of (SMAP brut - OL) for QC accepted
    sum_b = np.zeros((121, 181), dtype=float)
    cnt_b = np.zeros((121, 181), dtype=int)
    
    # Count of wilting rejections
    cnt_wilt_rej = np.zeros((121, 181), dtype=int)
    
    years = [2016, 2017, 2018, 2019, 2020]
    months = [7, 8]
    
    print("Traitement des fichiers DAOBS et OL (Juillet-Août 2016-2020)...")
    for y in years:
        for m in months:
            ym_str = f"{y}-{m:02d}"
            ym_compact = f"{y}{m:02d}"
            daobs_dir = os.path.join(BASE_DA, ym_str, "DAOBS", ym_compact)
            daobs_files = sorted(glob.glob(os.path.join(daobs_dir, "LISDAOBS_*.1gs4r")))
            
            ol_cache = {}
            for df in daobs_files:
                fname = os.path.basename(df)
                dt_str = fname.split("_")[1][:8]
                dt = datetime.datetime.strptime(dt_str, "%Y%m%d").date()
                
                if dt not in ol_cache:
                    ol_file = find_ol_file(dt)
                    if ol_file is not None:
                        with nc.Dataset(ol_file) as ds:
                            ol_cache[dt] = ds.variables["SoilMoist_tavg"][0, :, :].squeeze()
                    else:
                        ol_cache[dt] = None
                        
                ol_sm = ol_cache[dt]
                if ol_sm is None:
                    continue
                    
                rec1, rec2 = read_daobs_file(df)
                
                # Raw valid on land
                val_a = (rec1 != -9999.0) & np.isfinite(rec1) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                # QC accepted on land
                val_b = (rec2 != -9999.0) & np.isfinite(rec2) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                
                diff_a = rec1 - ol_sm
                diff_b = rec1 - ol_sm
                
                sum_a[val_a] += diff_a[val_a]
                cnt_a[val_a] += 1
                
                sum_b[val_b] += diff_b[val_b]
                cnt_b[val_b] += 1
                
                # Wilting rejection
                wilt_rej = val_a & non_forest & ((rec2 == -9999.0) | (~np.isfinite(rec2))) & ((rec1 - smcwlt_grid) < 0.02)
                cnt_wilt_rej[wilt_rej] += 1

    # Qualified pixels: non-forest, at least 20 raw obs, and at least 1 accepted obs
    qual_mask = non_forest & (cnt_a >= 20) & (cnt_b > 0)
    # Also pixels with 0 accepted obs (100% rejected)
    all_non_forest_qual = non_forest & (cnt_a >= 20)
    
    mean_a = np.full((121, 181), np.nan)
    mean_b = np.full((121, 181), np.nan)
    delta = np.full((121, 181), np.nan)
    
    mean_a[all_non_forest_qual] = sum_a[all_non_forest_qual] / cnt_a[all_non_forest_qual]
    mean_b[qual_mask] = sum_b[qual_mask] / cnt_b[qual_mask]
    delta[qual_mask] = mean_b[qual_mask] - mean_a[qual_mask]
    
    frac_wilt = np.full((121, 181), np.nan)
    frac_wilt[all_non_forest_qual] = cnt_wilt_rej[all_non_forest_qual] / cnt_a[all_non_forest_qual]
    
    del_vals = delta[qual_mask]
    fw_vals = frac_wilt[qual_mask]
    ma_vals = mean_a[qual_mask]
    mb_vals = mean_b[qual_mask]
    
    print("\n" + "="*80)
    print("RESULTATS DU POINT C : TRONCATURE INTRA-PIXEL (JUILLET-AOUT 2016-2020)")
    print("="*80)
    print(f"Pixels terrestres totaux                    : {np.sum(land_bool):,}")
    print(f"Pixels non-forestiers (vegt > 4)            : {np.sum(non_forest):,}")
    print(f"Pixels qualifiés (vegt > 4, N_a >= 20)      : {np.sum(all_non_forest_qual):,}")
    print(f"Pixels avec au moins 1 obs acceptée (N_b>0) : {np.sum(qual_mask):,}")
    print(f"Pixels avec 100% d'obs rejetées (N_b = 0)   : {np.sum(all_non_forest_qual & (cnt_b == 0)):,}")
    
    mean_delta_pixels = float(np.mean(del_vals))
    median_delta_pixels = float(np.median(del_vals))
    std_delta_pixels = float(np.std(del_vals))
    p5_delta = float(np.percentile(del_vals, 5))
    p95_delta = float(np.percentile(del_vals, 95))
    
    print(f"\n--- Statistiques sur les pixels qualifiés (poids égaux, N={len(del_vals):,}) ---")
    print(f"Moyenne de (SMAP brut - OL) avant QC (a)   : {np.mean(ma_vals):+.4f} m3/m3 (médiane = {np.median(ma_vals):+.4f})")
    print(f"Moyenne de (SMAP brut - OL) après QC (b)   : {np.mean(mb_vals):+.4f} m3/m3 (médiane = {np.median(mb_vals):+.4f})")
    print(f"Différence intra-pixel delta = (b) - (a)   :")
    print(f"  * MOYENNE intra-pixel (poids égaux)      : {mean_delta_pixels:+.4f} m3/m3")
    print(f"  * MEDIANE intra-pixel (poids égaux)      : {median_delta_pixels:+.4f} m3/m3")
    print(f"  * Écart-type intra-pixel                 : {std_delta_pixels:.4f} m3/m3")
    print(f"  * Intervalle [5e - 95e percentile]       : [{p5_delta:+.4f} , {p95_delta:+.4f}]")
    print(f"  * % pixels avec delta > 0                : {np.sum(del_vals > 0) / len(del_vals) * 100:.1f} %")
    
    # Breakdown by classes of fraction rejected
    bins = np.linspace(0.0, 1.0, 11)
    bin_labels = [f"[{bins[i]:.1f} - {bins[i+1]:.1f}]" for i in range(10)]
    
    print("\n--- Répartition par classe de fraction rejetée (flétrissement) ---")
    print("| Classe Rejet | Nb Pixels | % Pixels Qual | Moyenne (a) | Moyenne (b) | Diff. Moyenne delta | Diff. Médiane delta |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    class_table = []
    for i in range(10):
        low, high = bins[i], bins[i+1]
        in_b = (fw_vals >= low) & (fw_vals <= high if i==9 else fw_vals < high)
        n_p = int(np.sum(in_b))
        pct_p = n_p / len(del_vals) * 100
        if n_p > 0:
            m_a_cls = float(np.mean(ma_vals[in_b]))
            m_b_cls = float(np.mean(mb_vals[in_b]))
            m_del_cls = float(np.mean(del_vals[in_b]))
            med_del_cls = float(np.median(del_vals[in_b]))
        else:
            m_a_cls, m_b_cls, m_del_cls, med_del_cls = 0.0, 0.0, 0.0, 0.0
        class_table.append((bin_labels[i], n_p, pct_p, m_a_cls, m_b_cls, m_del_cls, med_del_cls))
        print(f"| {bin_labels[i]} | {n_p:,} | {pct_p:.1f} % | {m_a_cls:+.4f} | {m_b_cls:+.4f} | **{m_del_cls:+.4f}** | **{med_del_cls:+.4f}** |")

    # Separation of Truncation Effect vs Composition Effect
    # Pooled means:
    total_obs_a = np.sum(cnt_a[qual_mask])
    total_obs_b = np.sum(cnt_b[qual_mask])
    pooled_mean_a = np.sum(sum_a[qual_mask]) / total_obs_a
    pooled_mean_b = np.sum(sum_b[qual_mask]) / total_obs_b
    pooled_delta = pooled_mean_b - pooled_mean_a
    
    # Composition effect = Pooled Delta - Mean Within-Pixel Delta
    composition_effect = pooled_delta - mean_delta_pixels
    
    print("\n" + "="*80)
    print("DECOMPOSITION : EFFET DE TRONCATURE LOCALE VS EFFET DE COMPOSITION")
    print("="*80)
    print(f"Différence poolée globale (b - a)         : {pooled_delta:+.4f} m3/m3 (100.0 %)")
    print(f"1. Effet de troncature intra-pixel moyen  : {mean_delta_pixels:+.4f} m3/m3 ({mean_delta_pixels/pooled_delta*100:.1f} % de l'écart total)")
    print(f"2. Effet de composition spatiale          : {composition_effect:+.4f} m3/m3 ({composition_effect/pooled_delta*100:.1f} % de l'écart total)")
    
    # Plot Maps
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=180)
    
    # Map 1: Fraction rejected by wilting
    cmap1 = matplotlib.colormaps["YlOrRd"].copy()
    cmap1.set_bad(color="lightgrey")
    
    plot_fw = np.ma.masked_invalid(frac_wilt)
    im1 = ax1.imshow(plot_fw, origin="lower", cmap=cmap1, vmin=0, vmax=1.0)
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Fraction d'obs rejetées (flétrissement)", fontsize=10, fontweight="bold")
    ax1.set_title("Fraction rejetée par smobs - smcwlt < 0.02\n(Juillet-Août 2016-2020, hors forêts)", fontsize=11, fontweight="bold")
    ax1.axis("off")
    
    # Map 2: Delta (b - a) intra-pixel
    cmap2 = matplotlib.colormaps["Spectral_r"].copy()
    cmap2.set_bad(color="lightgrey")
    
    plot_delta = np.ma.masked_invalid(delta)
    # Clip visualization between -0.01 and +0.05
    im2 = ax2.imshow(plot_delta, origin="lower", cmap=cmap2, vmin=0.0, vmax=0.04)
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label(r"Différence intra-pixel $(b) - (a)$ (m³/m³)", fontsize=10, fontweight="bold")
    ax2.set_title(r"Effet de troncature locale : $\overline{(SMAP-OL)}_{QC} - \overline{(SMAP-OL)}_{All}$" + f"\n(Moyenne = {mean_delta_pixels:+.4f}, Médiane = {median_delta_pixels:+.4f})", fontsize=11, fontweight="bold")
    ax2.axis("off")
    
    plt.tight_layout()
    out_png = "/home/mohammad.elaabaribao/.gemini/antigravity-ide/brain/f92c66df-785d-4977-8b4d-c2f5a0bda26d/figure_truncation_pixel_analysis.png"
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"\nCarte sauvegardée avec succès dans : {out_png}")

if __name__ == "__main__":
    run_pixel_analysis()
