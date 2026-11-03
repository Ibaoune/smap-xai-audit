#!/usr/bin/env python3
"""
point2_point4_analysis.py
-------------------------
Audit DA-NoCDF (Juillet-Août 2016-2020) :
Point 2 : Comparaison homogène SMAP brut - OL sur (a) toutes les obs valides
          et (b) les seules obs acceptées par le QC.
Point 4 : Incrément moyen de juillet-août par classe de fraction rejetée
          par le test de flétrissement (déciles).
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
        
    soiltype = np.argmax(texture, axis=0) + 1
    vegt = np.argmax(landcover, axis=0) + 1
    
    # Read WLTSMC from SOILPARM.TBL (STAS section)
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
        
    return landmask, soiltype, vegt, smcwlt_grid

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

def run_analysis():
    print("Chargement des paramètres statiques...")
    landmask, soiltype, vegt, smcwlt_grid = load_static_params()
    land_bool = (landmask == 1)
    
    years = [2016, 2017, 2018, 2019, 2020]
    months = [7, 8]
    
    # Structures for Point 2
    # stats per (year, month): list of differences for (a) and (b)
    p2_results = {}
    
    # Pool structures per month across 2016-2020
    pool_a_month = {7: [], 8: []}
    pool_b_month = {7: [], 8: []}
    
    # Structures for Point 4 (pixel-level accumulations)
    n_raw_all = np.zeros((121, 181), dtype=int)
    n_wilt_rej_all = np.zeros((121, 181), dtype=int)
    
    n_raw_2018 = np.zeros((121, 181), dtype=int)
    n_wilt_rej_2018 = np.zeros((121, 181), dtype=int)
    
    incr_sum_all = np.zeros((121, 181), dtype=float)
    incr_cnt_all = np.zeros((121, 181), dtype=int)
    
    incr_sum_2018 = np.zeros((121, 181), dtype=float)
    incr_cnt_2018 = np.zeros((121, 181), dtype=int)
    
    print("\n" + "="*80)
    print("POINT 2 : COMPARAISON HOMOGENE SMAP BRUT - OL (DA-NoCDF 2016-2020)")
    print("="*80)
    
    for y in years:
        for m in months:
            ym_str = f"{y}-{m:02d}"
            ym_compact = f"{y}{m:02d}"
            daobs_dir = os.path.join(BASE_DA, ym_str, "DAOBS", ym_compact)
            daobs_files = sorted(glob.glob(os.path.join(daobs_dir, "LISDAOBS_*.1gs4r")))
            
            diff_a_list = []
            diff_b_list = []
            
            # Cache OL daily fields for this month
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
                
                # Condition (a): valid raw observation on land
                valid_a = (rec1 != -9999.0) & np.isfinite(rec1) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                # Condition (b): QC accepted observation on land
                valid_b = (rec2 != -9999.0) & np.isfinite(rec2) & land_bool & (ol_sm != -9999.0) & np.isfinite(ol_sm)
                
                diff_a = rec1[valid_a] - ol_sm[valid_a]
                diff_b = rec1[valid_b] - ol_sm[valid_b]
                
                diff_a_list.extend(diff_a.tolist())
                diff_b_list.extend(diff_b.tolist())
                
                pool_a_month[m].extend(diff_a.tolist())
                pool_b_month[m].extend(diff_b.tolist())
                
                # Point 4 accumulations
                raw_mask = (rec1 != -9999.0) & np.isfinite(rec1) & land_bool
                n_raw_all[raw_mask] += 1
                if y == 2018:
                    n_raw_2018[raw_mask] += 1
                    
                # Rejected specifically by wilting: raw is valid, but rejected (rec2 invalid)
                # AND (rec1 - smcwlt) < 0.02, with non-forest (vegt > 4)
                wilt_rej = raw_mask & (vegt > 4) & ((rec2 == -9999.0) | (~np.isfinite(rec2))) & ((rec1 - smcwlt_grid) < 0.02)
                n_wilt_rej_all[wilt_rej] += 1
                if y == 2018:
                    n_wilt_rej_2018[wilt_rej] += 1
                    
            # Increments for Point 4 from EnKF files
            enkf_dir = os.path.join(BASE_DA, ym_str, "EnKF", ym_compact)
            incr_files = sorted(glob.glob(os.path.join(enkf_dir, "LIS_DA_EnKF_*_incr.a01.d01.nc")))
            for incf in incr_files:
                with nc.Dataset(incf) as ds:
                    incr = ds.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
                    v_inc = land_bool & (incr != -9999.0) & np.isfinite(incr)
                    incr_sum_all[v_inc] += incr[v_inc]
                    incr_cnt_all[v_inc] += 1
                    if y == 2018:
                        incr_sum_2018[v_inc] += incr[v_inc]
                        incr_cnt_2018[v_inc] += 1
                        
            diff_a_arr = np.array(diff_a_list)
            diff_b_arr = np.array(diff_b_list)
            
            p2_results[(y, m)] = {
                "n_a": len(diff_a_arr),
                "mean_a": float(np.mean(diff_a_arr)) if len(diff_a_arr)>0 else np.nan,
                "median_a": float(np.median(diff_a_arr)) if len(diff_a_arr)>0 else np.nan,
                "pos_a": float(np.sum(diff_a_arr > 0) / len(diff_a_arr) * 100) if len(diff_a_arr)>0 else np.nan,
                "n_b": len(diff_b_arr),
                "mean_b": float(np.mean(diff_b_arr)) if len(diff_b_arr)>0 else np.nan,
                "median_b": float(np.median(diff_b_arr)) if len(diff_b_arr)>0 else np.nan,
                "pos_b": float(np.sum(diff_b_arr > 0) / len(diff_b_arr) * 100) if len(diff_b_arr)>0 else np.nan,
            }
            
            res = p2_results[(y, m)]
            d_mean = res["mean_b"] - res["mean_a"]
            d_med = res["median_b"] - res["median_a"]
            d_pos = res["pos_b"] - res["pos_a"]
            print(f"[{ym_str}]")
            print(f"  (a) Toutes obs valides (N={res['n_a']:,}) : Moyenne={res['mean_a']:+.4f}, Médiane={res['median_a']:+.4f}, %pos={res['pos_a']:.1f}%")
            print(f"  (b) QC acceptées       (N={res['n_b']:,}) : Moyenne={res['mean_b']:+.4f}, Médiane={res['median_b']:+.4f}, %pos={res['pos_b']:.1f}%")
            print(f"  Différence (b) - (a) : Delta_Moy={d_mean:+.4f}, Delta_Med={d_med:+.4f}, Delta_%pos={d_pos:+.1f}%\n")

    # Save Point 2 table to CSV / print formatted markdown
    print("\n" + "="*80)
    print("TABLE RECAPITULATIVE POINT 2 : SMAP BRUT - OL PAR MOIS ET PAR ANNEE")
    print("="*80)
    header = "| Année | Mois | N(a) Brutes | Moy(a) | Méd(a) | %pos(a) | N(b) QC | Moy(b) | Méd(b) | %pos(b) | Diff Moy (b-a) | Diff Méd (b-a) | Diff %pos (b-a) |"
    print(header)
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for y in years:
        for m in months:
            r = p2_results[(y, m)]
            d_mean = r["mean_b"] - r["mean_a"]
            d_med = r["median_b"] - r["median_a"]
            d_pos = r["pos_b"] - r["pos_a"]
            mstr = "07 (Juil)" if m == 7 else "08 (Août)"
            print(f"| {y} | {mstr} | {r['n_a']:,} | {r['mean_a']:+.4f} | {r['median_a']:+.4f} | {r['pos_a']:.1f}% | {r['n_b']:,} | {r['mean_b']:+.4f} | {r['median_b']:+.4f} | {r['pos_b']:.1f}% | **{d_mean:+.4f}** | **{d_med:+.4f}** | **{d_pos:+.1f}%** |")
            
    # Print Multi-year pooled summary per month
    print("\n--- SYNTHESE MULTI-ANNUELLE 2016-2020 ---")
    for m in [7, 8]:
        pa = np.array(pool_a_month[m])
        pb = np.array(pool_b_month[m])
        m_mean_a = np.mean(pa)
        m_med_a = np.median(pa)
        m_pos_a = np.sum(pa > 0) / len(pa) * 100
        m_mean_b = np.mean(pb)
        m_med_b = np.median(pb)
        m_pos_b = np.sum(pb > 0) / len(pb) * 100
        d_mean = m_mean_b - m_mean_a
        d_med = m_med_b - m_med_a
        d_pos = m_pos_b - m_pos_a
        mstr = "Juillet (2016-2020)" if m == 7 else "Août (2016-2020)"
        print(f"| Pool {mstr} | {len(pa):,} | {m_mean_a:+.4f} | {m_med_a:+.4f} | {m_pos_a:.1f}% | {len(pb):,} | {m_mean_b:+.4f} | {m_med_b:+.4f} | {m_pos_b:.1f}% | **{d_mean:+.4f}** | **{d_med:+.4f}** | **{d_pos:+.1f}%** |")

    # -------------------------------------------------------------
    # POINT 4 : FRACTION REJETEE PAR FLETRISSEMENT ET INCREMENT MOYEN
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("POINT 4 : INCREMENT MOYEN PAR CLASSE DE FRACTION REJETEE PAR FLETRISSEMENT")
    print("="*80)
    
    # Calculate pixel fraction rejected
    valid_pixels_all = land_bool & (n_raw_all >= 5) & (vegt > 4)
    frac_wilt_all = np.full((121, 181), np.nan)
    frac_wilt_all[valid_pixels_all] = n_wilt_rej_all[valid_pixels_all] / n_raw_all[valid_pixels_all]
    
    mean_incr_all = np.full((121, 181), np.nan)
    has_incr_all = valid_pixels_all & (incr_cnt_all > 0)
    mean_incr_all[has_incr_all] = incr_sum_all[has_incr_all] / incr_cnt_all[has_incr_all]
    mean_incr_all[valid_pixels_all & (incr_cnt_all == 0)] = 0.0
    
    bins = np.linspace(0.0, 1.0, 11)
    bin_labels = [f"[{bins[i]:.1f} - {bins[i+1]:.1f}]" for i in range(10)]
    
    f_vals = frac_wilt_all[valid_pixels_all]
    inc_vals = mean_incr_all[valid_pixels_all]
    
    print("\n--- Répartition par classes de fraction rejetée (Juillet-Août 2016-2020, hors forêts) ---")
    print("| Classe Fraction Rejetée | Nb Pixels | % Pixels Non-Forestiers | Incrément Moyen (m3/m3) | Incrément Médian (m3/m3) | Incrément Absolu Moyen |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: |")
    
    class_stats = []
    for i in range(10):
        low, high = bins[i], bins[i+1]
        if i == 9:
            in_bin = (f_vals >= low) & (f_vals <= high)
        else:
            in_bin = (f_vals >= low) & (f_vals < high)
            
        n_pix = int(np.sum(in_bin))
        pct_pix = n_pix / np.sum(valid_pixels_all) * 100
        if n_pix > 0:
            m_inc = float(np.mean(inc_vals[in_bin]))
            med_inc = float(np.median(inc_vals[in_bin]))
            m_abs_inc = float(np.mean(np.abs(inc_vals[in_bin])))
        else:
            m_inc, med_inc, m_abs_inc = 0.0, 0.0, 0.0
            
        class_stats.append((bin_labels[i], n_pix, pct_pix, m_inc, med_inc, m_abs_inc))
        print(f"| {bin_labels[i]} | {n_pix:,} | {pct_pix:.1f} % | {m_inc:+.6f} | {med_inc:+.6f} | {m_abs_inc:.6f} |")
        
    # Plot Point 4 figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)
    
    # Subplot 1: Barplot mean increment by fraction bin
    x_pos = np.arange(10)
    bar_inc = [cs[3]*1000 for cs in class_stats] # in 10^-3 m3/m3
    bar_pix = [cs[1] for cs in class_stats]
    
    color = 'tab:blue'
    ax1.set_xlabel('Fraction rejetée par le test de flétrissement (Classes)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Incrément moyen Layer 1 (10⁻³ m³/m³)', color=color, fontsize=11, fontweight='bold')
    bars = ax1.bar(x_pos, bar_inc, color=color, alpha=0.7, edgecolor='navy', width=0.6, label="Incrément moyen")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(bin_labels, rotation=45, ha='right', fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.5, axis='y')
    ax1.axhline(0, color='black', linewidth=0.8)
    
    ax1_twin = ax1.twinx()
    color_twin = 'tab:red'
    ax1_twin.set_ylabel('Nombre de pixels', color=color_twin, fontsize=11, fontweight='bold')
    line = ax1_twin.plot(x_pos, bar_pix, color=color_twin, marker='o', linewidth=2, markersize=6, label="Nb pixels")
    ax1_twin.tick_params(axis='y', labelcolor=color_twin)
    ax1.set_title('Incrément moyen et Nb de pixels par classe de rejet (2016-2020)', fontsize=12, fontweight='bold')
    
    # Subplot 2: 2018 specific comparison
    valid_pixels_2018 = land_bool & (n_raw_2018 >= 3) & (vegt > 4)
    f_vals_18 = (n_wilt_rej_2018[valid_pixels_2018] / n_raw_2018[valid_pixels_2018])
    inc_vals_18 = np.zeros(np.sum(valid_pixels_2018))
    c_18 = incr_cnt_2018[valid_pixels_2018]
    s_18 = incr_sum_2018[valid_pixels_2018]
    has_inc_18 = (c_18 > 0)
    inc_vals_18[has_inc_18] = s_18[has_inc_18] / c_18[has_inc_18]
    
    bar_inc_18 = []
    bar_pix_18 = []
    for i in range(10):
        low, high = bins[i], bins[i+1]
        in_b = (f_vals_18 >= low) & (f_vals_18 <= high if i==9 else f_vals_18 < high)
        n_p = int(np.sum(in_b))
        bar_pix_18.append(n_p)
        bar_inc_18.append(float(np.mean(inc_vals_18[in_b]))*1000 if n_p > 0 else 0.0)
        
    ax2.set_xlabel('Fraction rejetée par le test de flétrissement (Classes)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Incrément moyen Layer 1 (10⁻³ m³/m³)', color='tab:green', fontsize=11, fontweight='bold')
    ax2.bar(x_pos, bar_inc_18, color='tab:green', alpha=0.7, edgecolor='darkgreen', width=0.6)
    ax2.tick_params(axis='y', labelcolor='tab:green')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(bin_labels, rotation=45, ha='right', fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.5, axis='y')
    ax2.axhline(0, color='black', linewidth=0.8)
    
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Nombre de pixels', color=color_twin, fontsize=11, fontweight='bold')
    ax2_twin.plot(x_pos, bar_pix_18, color=color_twin, marker='s', linewidth=2, markersize=6)
    ax2_twin.tick_params(axis='y', labelcolor=color_twin)
    ax2.set_title('Focus : Juillet-Août 2018', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    out_png = "/home/mohammad.elaabaribao/.gemini/antigravity-ide/brain/f92c66df-785d-4977-8b4d-c2f5a0bda26d/figure_increment_vs_wilt_rejection.png"
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"\nGraphique sauvegardé avec succès dans : {out_png}")

if __name__ == "__main__":
    run_analysis()
