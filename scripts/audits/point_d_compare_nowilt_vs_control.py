#!/usr/bin/env python3
"""
point_d_compare_nowilt_vs_control.py
------------------------------------
Compare DA_nocdf_TEST_nowilt (sans seuil de flétrissement) face au contrôle standard
(DA_nocdf_noirr_2016_2020) pour Juillet-Août 2018 :
1. Statistiques d'observations et rejets dans DAOBS.
2. Incréments d'assimilation EnKF (moyens globaux et par classe de rejet de flétrissement).
3. Part de pixels qui s'assèchent (incréments négatifs, baisse de l'humidité du sol).
4. Différence spatiale d'humidité du sol couche 1 (nowilt - control) et tracé de cartes.
"""

import os
import glob
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DIR_NOWILT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_TEST_nowilt/output"
DIR_CTRL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "figures", "assimilation")

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
    return landmask, soiltype, vegt, wlt_grid, lat, lon

def read_daobs(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def run_comparison():
    print("==================================================================")
    print(" POINT D : COMPARAISON DA_nocdf_TEST_nowilt VS CONTRÔLE (JA 2018)")
    print("==================================================================")
    landmask, soiltype, vegt, wlt_grid, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    # 1. Analyse des observations et rejets dans DAOBS
    months = ["2018-07", "2018-08"]
    
    n_raw_ctrl, n_acc_ctrl = 0, 0
    n_raw_nowilt, n_acc_nowilt = 0, 0
    
    # Accumulateurs pour fraction rejetée par flétrissement dans le contrôle
    cnt_raw_ctrl_px = np.zeros((121, 181), dtype=int)
    cnt_wilt_rej_px = np.zeros((121, 181), dtype=int)
    
    for ym in months:
        ym_c = ym.replace("-", "")
        f_ctrl = sorted(glob.glob(f"{DIR_CTRL}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r"))
        f_nowilt = sorted(glob.glob(f"{DIR_NOWILT}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r"))
        
        for fc, fn in zip(f_ctrl, f_nowilt):
            r1_c, r2_c = read_daobs(fc)
            r1_n, r2_n = read_daobs(fn)
            
            val_raw_c = (r1_c != -9999.0) & np.isfinite(r1_c) & land_bool
            val_acc_c = (r2_c != -9999.0) & np.isfinite(r2_c) & land_bool
            
            val_raw_n = (r1_n != -9999.0) & np.isfinite(r1_n) & land_bool
            val_acc_n = (r2_n != -9999.0) & np.isfinite(r2_n) & land_bool
            
            n_raw_ctrl += np.sum(val_raw_c)
            n_acc_ctrl += np.sum(val_acc_c)
            
            n_raw_nowilt += np.sum(val_raw_n)
            n_acc_nowilt += np.sum(val_acc_n)
            
            cnt_raw_ctrl_px[val_raw_c] += 1
            wilt_rej = val_raw_c & ((r2_c == -9999.0) | (~np.isfinite(r2_c))) & ((r1_c - wlt_grid) < 0.02)
            cnt_wilt_rej_px[wilt_rej] += 1
            
    print("\n--- 1. BILAN DES OBSERVATIONS (DAOBS, JUILLET-AOÛT 2018) ---")
    print(f"Contrôle standard (DA-NoCDF) :")
    print(f"  Obs brutes valides : {n_raw_ctrl:,}")
    print(f"  Obs acceptées QC   : {n_acc_ctrl:,} ({100*n_acc_ctrl/n_raw_ctrl:.1f}%)")
    print(f"  Obs rejetées       : {n_raw_ctrl - n_acc_ctrl:,} ({100*(n_raw_ctrl - n_acc_ctrl)/n_raw_ctrl:.1f}%)")
    
    print(f"\nTest Sans Seuil (DA_nocdf_TEST_nowilt) :")
    print(f"  Obs brutes valides : {n_raw_nowilt:,}")
    print(f"  Obs acceptées QC   : {n_acc_nowilt:,} ({100*n_acc_nowilt/n_raw_nowilt:.1f}%)")
    print(f"  Obs rejetées       : {n_raw_nowilt - n_acc_nowilt:,} ({100*(n_raw_nowilt - n_acc_nowilt)/n_raw_nowilt:.1f}%)")
    print(f"  Gain net d'obs acceptées : +{n_acc_nowilt - n_acc_ctrl:,} (+{100*(n_acc_nowilt - n_acc_ctrl)/n_raw_ctrl:.1f}% des obs brutes)")
    
    # Fraction de rejet par flétrissement au contrôle
    wilt_frac_px = np.zeros((121, 181), dtype=float)
    val_px = cnt_raw_ctrl_px >= 20
    wilt_frac_px[val_px] = cnt_wilt_rej_px[val_px] / cnt_raw_ctrl_px[val_px]
    
    # 2. Analyse des Incréments EnKF
    print("\n--- 2. ANALYSE DES INCRÉMENTS D'ASSIMILATION (EnKF _incr.nc) ---")
    incr_ctrl_sum = np.zeros((121, 181), dtype=float)
    incr_ctrl_cnt = np.zeros((121, 181), dtype=int)
    incr_ctrl_pos = np.zeros((121, 181), dtype=int)
    incr_ctrl_neg = np.zeros((121, 181), dtype=int)
    
    incr_nowilt_sum = np.zeros((121, 181), dtype=float)
    incr_nowilt_cnt = np.zeros((121, 181), dtype=int)
    incr_nowilt_pos = np.zeros((121, 181), dtype=int)
    incr_nowilt_neg = np.zeros((121, 181), dtype=int)
    
    for ym in months:
        ym_c = ym.replace("-", "")
        f_inc_ctrl = sorted(glob.glob(f"{DIR_CTRL}/{ym}/EnKF/{ym_c}/LIS_DA_EnKF_*_incr.a01.d01.nc"))
        f_inc_nowilt = sorted(glob.glob(f"{DIR_NOWILT}/{ym}/EnKF/{ym_c}/LIS_DA_EnKF_*_incr.a01.d01.nc"))
        
        for fc, fn in zip(f_inc_ctrl, f_inc_nowilt):
            with nc.Dataset(fc) as dsc, nc.Dataset(fn) as dsn:
                # SoilMoist incr couche 1
                ic = dsc.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
                inw = dsn.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
                
                # Masques valides non nuls
                vc = land_bool & np.isfinite(ic) & (ic != 0.0)
                vn = land_bool & np.isfinite(inw) & (inw != 0.0)
                
                incr_ctrl_sum[vc] += ic[vc]
                incr_ctrl_cnt[vc] += 1
                incr_ctrl_pos[vc & (ic > 0)] += 1
                incr_ctrl_neg[vc & (ic < 0)] += 1
                
                incr_nowilt_sum[vn] += inw[vn]
                incr_nowilt_cnt[vn] += 1
                incr_nowilt_pos[vn & (inw > 0)] += 1
                incr_nowilt_neg[vn & (inw < 0)] += 1

    # Incrément moyen par analyse
    m_inc_ctrl = np.full((121, 181), np.nan)
    m_inc_nowilt = np.full((121, 181), np.nan)
    
    v_c = incr_ctrl_cnt > 0
    m_inc_ctrl[v_c] = incr_ctrl_sum[v_c] / incr_ctrl_cnt[v_c]
    
    v_n = incr_nowilt_cnt > 0
    m_inc_nowilt[v_n] = incr_nowilt_sum[v_n] / incr_nowilt_cnt[v_n]
    
    # Part des incréments négatifs (qui assèchent)
    pct_neg_ctrl = np.zeros((121, 181), dtype=float)
    pct_neg_ctrl[v_c] = 100.0 * incr_ctrl_neg[v_c] / incr_ctrl_cnt[v_c]
    
    pct_neg_nowilt = np.zeros((121, 181), dtype=float)
    pct_neg_nowilt[v_n] = 100.0 * incr_nowilt_neg[v_n] / incr_nowilt_cnt[v_n]
    
    qual = non_forest & val_px & v_c & v_n
    
    print(f"Sur pixels qualifiés non-forêt (N={np.sum(qual)}) :")
    print(f"  Contrôle : Incrément moyen = {m_inc_ctrl[qual].mean():+.6f} m3/m3, % analyses asséchantes (<0) = {pct_neg_ctrl[qual].mean():.1f}%")
    print(f"  Nowilt   : Incrément moyen = {m_inc_nowilt[qual].mean():+.6f} m3/m3, % analyses asséchantes (<0) = {pct_neg_nowilt[qual].mean():.1f}%")
    print(f"  Variation nette de l'incrément moyen : {m_inc_nowilt[qual].mean() - m_inc_ctrl[qual].mean():+.6f} m3/m3")
    print(f"  Augmentation de la part d'analyses asséchantes : +{pct_neg_nowilt[qual].mean() - pct_neg_ctrl[qual].mean():.1f}%")

    print("\n--- INCRÉMENTS PAR DÉCILE DE FRACTION REJETÉE PAR FLÉTRISSEMENT ---")
    print(f"{'Décile rejet':<15} | {'N px':<6} | {'Incr Contrôle':<16} | {'Incr Nowilt':<16} | {'Diff (Nowilt-Ctrl)':<18} | {'% asséchant: Ctrl -> Nowilt':<28}")
    print("-" * 110)
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    for i in range(len(bins)-1):
        b_lo, b_hi = bins[i], bins[i+1]
        m = qual & (wilt_frac_px >= b_lo) & (wilt_frac_px < b_hi)
        n_p = np.sum(m)
        if n_p > 0:
            ic_m = m_inc_ctrl[m].mean()
            in_m = m_inc_nowilt[m].mean()
            diff_m = in_m - ic_m
            p_c = pct_neg_ctrl[m].mean()
            p_n = pct_neg_nowilt[m].mean()
            lbl = f"[{b_lo*100:02.0f}% - {min(b_hi*100, 100):02.0f}%["
            print(f"{lbl:<15} | {n_p:<6} | {ic_m:+.6f} m3/m3 | {in_m:+.6f} m3/m3 | {diff_m:+.6f} m3/m3      | {p_c:4.1f}% -> {p_n:4.1f}% (+{p_n-p_c:4.1f}%)")

    # 3. Différence sur l'humidité du sol simulée (SURFACEMODEL)
    print("\n--- 3. ÉCART SUR L'HUMIDITÉ DU SOL SIMULÉE (Couche 1, 0-10 cm) ---")
    sm_ctrl_all = []
    sm_nowilt_all = []
    
    for ym in months:
        fc = sorted(glob.glob(f"{DIR_CTRL}/{ym}/SURFACEMODEL/*/LIS_HIST_*.d01.nc"))
        fn = sorted(glob.glob(f"{DIR_NOWILT}/{ym}/SURFACEMODEL/*/LIS_HIST_*.d01.nc"))
        
        for f1, f2 in zip(fc, fn):
            with nc.Dataset(f1) as d1, nc.Dataset(f2) as d2:
                s1 = d1.variables["SoilMoist_tavg"][0, :, :].squeeze()
                s2 = d2.variables["SoilMoist_tavg"][0, :, :].squeeze()
                sm_ctrl_all.append(s1)
                sm_nowilt_all.append(s2)
                
    mean_sm_ctrl = np.mean(np.stack(sm_ctrl_all, axis=0), axis=0)
    mean_sm_nowilt = np.mean(np.stack(sm_nowilt_all, axis=0), axis=0)
    delta_sm = mean_sm_nowilt - mean_sm_ctrl
    
    # Pixels qui s'assèchent au niveau de l'état moyen
    dry_px = qual & (delta_sm < 0.0)
    pct_dry_px = 100.0 * np.sum(dry_px) / np.sum(qual)
    
    print(f"Humidité du sol moyenne couche 1 (Juillet-Août 2018) :")
    print(f"  Contrôle : {mean_sm_ctrl[qual].mean():.5f} m3/m3")
    print(f"  Nowilt   : {mean_sm_nowilt[qual].mean():.5f} m3/m3")
    print(f"  Différence moyenne (Nowilt - Contrôle) : {delta_sm[qual].mean():+.6f} m3/m3")
    print(f"  Part des pixels qui s'assèchent globalement : {pct_dry_px:.1f}% ({np.sum(dry_px)}/{np.sum(qual)} pixels)")
    
    # 4. Tracé des Figures
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    
    # A. Fraction rejetée au contrôle
    im0 = axes[0].imshow(np.where(land_bool, wilt_frac_px * 100, np.nan), cmap="YlOrRd", vmin=0, vmax=100, origin="lower")
    axes[0].set_title("A. Fraction d'obs rejetées par flétrissement (Contrôle, %)", fontsize=11, fontweight="bold")
    plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
    
    # B. Augmentation des analyses asséchantes
    im1 = axes[1].imshow(np.where(qual, pct_neg_nowilt - pct_neg_ctrl, np.nan), cmap="Greens", vmin=0, vmax=60, origin="lower")
    axes[1].set_title("B. Gain d'analyses asséchantes (+% d'analyses < 0)", fontsize=11, fontweight="bold")
    plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
    
    # C. Différence d'humidité du sol simulée
    im2 = axes[2].imshow(np.where(land_bool, delta_sm, np.nan), cmap="BrBG", vmin=-0.015, vmax=+0.015, origin="lower")
    axes[2].set_title("C. Différence SoilMoist couche 1 (Nowilt − Contrôle, m³/m³)", fontsize=11, fontweight="bold")
    plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
    
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        
    plt.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    fig_path = os.path.join(OUT_DIR, "figure_point_d_nowilt_vs_control.png")
    plt.savefig(fig_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"\nFigure sauvegardée : {fig_path}")

if __name__ == "__main__":
    run_comparison()
