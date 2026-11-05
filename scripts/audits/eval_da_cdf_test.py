#!/usr/bin/env python3
"""
eval_da_cdf_test.py
-------------------
Script d'évaluation et de contrôle pour l'expérience DA_cdf_TEST (janvier et août 2018).
Contrôles 4a à 4e :
  4a. Fichiers CDF lus dans les logs (les nouveaux uniquement)
  4b. Depuis les DAOBS : % d'obs valides rejetées au scaling, R, pente, décalage moyen,
      et saturation sur la première / dernière borne de la CDF modèle.
  4c. Innovations : nombre d'innovations finies vs DA-NoCDF, moyenne et std O-F,
      pour le mois complet, jours 1–10 et jours 11–fin.
  4d. Incréments de surface (Layer 1) : moyenne signée et absolue vs DA-NoCDF,
      pour le mois complet, jours 1–10 et jours 11–fin.
  4e. Monotonie de Spearman par pixel (pixels avec >= 5 obs dans le mois) :
      médiane, 5e percentile, % pixels avec Spearman < 0.95, et décompte à part
      des pixels à observation scalée constante avec brute variable.
"""

import os
import glob
import argparse
import numpy as np
import netCDF4 as nc
from scipy.stats import spearmanr

BASE_TEST = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/tests/DA_cdf_TEST"
BASE_NOCDF = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
MODEL_CDF_FILE = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_model_NorthMor/noahmp_model_cdf_NorthMor.nc"

def check_4a_logs(label, log_subdir):
    log_file = os.path.join(BASE_TEST, "logs", log_subdir, f"lislog_{label}.0000")
    print(f"\n--- [4a] Contrôle des fichiers CDF lus pour {label} ---")
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    cdf_lines = []
    with open(log_file, "r") as f:
        for line in f:
            if "CDF file" in line:
                cdf_lines.append(line.strip())
                
    unique_cdf_files = set()
    for l in cdf_lines:
        parts = l.split("CDF file")
        if len(parts) > 1:
            fname = parts[1].strip()
            unique_cdf_files.add(fname)
            
    print("Fichiers CDF référencés dans lislog.0000 :")
    for u in sorted(unique_cdf_files):
        print(f"  -> {u}")
        
    has_old = any("OUTPUT_noirr/smap_cdf.nc" in u for u in unique_cdf_files)
    has_new_mod = any("OUTPUT_model_NorthMor/noahmp_model_cdf_NorthMor.nc" in u for u in unique_cdf_files)
    has_new_obs = any("OUTPUT_obs_NorthMor/smap_obs_cdf_NorthMor.nc" in u for u in unique_cdf_files)
    
    if not has_old and has_new_mod and has_new_obs:
        print("  -> CONFORME : Uniquement les nouveaux fichiers CDF NorthMor ont été chargés.")
    else:
        print(f"  -> ANOMALIE : has_old={has_old}, has_new_mod={has_new_mod}, has_new_obs={has_new_obs}")

def check_4b_and_4e_daobs(label, month_compact, landmask):
    daobs_pattern = os.path.join(BASE_TEST, "output", label, "DAOBS", month_compact, "LISDAOBS_*.1gs4r")
    files = sorted(glob.glob(daobs_pattern))
    print(f"\n--- [4b & 4e] Analyse des DAOBS et Monotonie pour {label} ---")
    print(f"Nombre de fichiers DAOBS trouvés : {len(files)}")
    
    if not files:
        print("Aucun fichier DAOBS disponible pour le moment.")
        return
        
    # Charger bornes de la CDF modèle pour le mois
    m_idx = 0 if label == "2018-01" else 7
    with nc.Dataset(MODEL_CDF_FILE) as ds_mod:
        mod_min = ds_mod.variables["SoilMoist_xrange"][0, 0, m_idx, :]
        mod_max = ds_mod.variables["SoilMoist_xrange"][99, 0, m_idx, :]

    land_indices_1d = np.where(landmask.ravel() == 1)[0]
    grid2land = np.full(len(landmask.ravel()), -1, dtype=int)
    grid2land[land_indices_1d] = np.arange(len(land_indices_1d))
    
    all_raw = []
    all_scaled = []
    total_valid_raw = 0
    total_rejected = 0
    total_sat_min = 0
    total_sat_max = 0
    
    pixel_series = [[] for _ in range(21901)]
    
    for fpath in files:
        with open(fpath, "rb") as f:
            _ = np.fromfile(f, dtype=">i4", count=1)
            rec1 = np.fromfile(f, dtype=">f4", count=21901)
            _ = np.fromfile(f, dtype=">i4", count=2)
            rec2 = np.fromfile(f, dtype=">f4", count=21901)
            
        valid_raw = (rec1 != -9999.0) & np.isfinite(rec1)
        valid_sc = (rec2 != -9999.0) & np.isfinite(rec2)
        
        valid_raw_land = valid_raw & (landmask.ravel() == 1)
        valid_sc_land = valid_sc & (landmask.ravel() == 1)
        
        n_raw = int(np.sum(valid_raw_land))
        n_sc = int(np.sum(valid_sc_land))
        n_rej = int(np.sum(valid_raw_land & (~valid_sc_land)))
        
        total_valid_raw += n_raw
        total_rejected += n_rej
        
        common_idx = np.where(valid_raw_land & valid_sc_land)[0]
        l_idx = grid2land[common_idx]
        sc_vals = rec2[common_idx]
        
        sat_min = np.isclose(sc_vals, mod_min[l_idx], atol=1e-5)
        sat_max = np.isclose(sc_vals, mod_max[l_idx], atol=1e-5)
        total_sat_min += int(np.sum(sat_min))
        total_sat_max += int(np.sum(sat_max))
        
        for idx in common_idx:
            r_val = float(rec1[idx])
            s_val = float(rec2[idx])
            all_raw.append(r_val)
            all_scaled.append(s_val)
            pixel_series[idx].append((r_val, s_val))
            
    all_raw = np.array(all_raw)
    all_scaled = np.array(all_scaled)
    
    # 4b. Statistiques DAOBS
    pct_rejected = (total_rejected / total_valid_raw * 100) if total_valid_raw > 0 else 0.0
    print(f"\n[4b] Métriques DAOBS globales :")
    print(f"  - Total observations SMAP brutes valides : {total_valid_raw}")
    print(f"  - Observations rejetées après scaling    : {total_rejected} ({pct_rejected:.2f} %)")
    print(f"  - Observations scalées valides           : {len(all_scaled)}")
    
    if len(all_scaled) > 1:
        corr = float(np.corrcoef(all_raw, all_scaled)[0, 1])
        slope, intercept = np.polyfit(all_raw, all_scaled, deg=1)
        mean_raw = float(np.mean(all_raw))
        mean_scaled = float(np.mean(all_scaled))
        mean_shift = mean_scaled - mean_raw
        
        print(f"  - Corrélation R (scalée vs brute)        : {corr:.4f}")
        print(f"  - Pente de régression                    : {slope:.4f} (intercept = {intercept:.4f})")
        print(f"  - Moyenne obs brute                      : {mean_raw:.4f} m3/m3")
        print(f"  - Moyenne obs scalée                     : {mean_scaled:.4f} m3/m3")
        print(f"  - Décalage moyen (scalée - brute)        : {mean_shift:+.4f} m3/m3")
        
        pct_sat_min = (total_sat_min / len(all_scaled) * 100) if len(all_scaled) > 0 else 0.0
        pct_sat_max = (total_sat_max / len(all_scaled) * 100) if len(all_scaled) > 0 else 0.0
        total_sat = total_sat_min + total_sat_max
        pct_sat_tot = (total_sat / len(all_scaled) * 100) if len(all_scaled) > 0 else 0.0
        print(f"  - Saturation sur bornes CDF modèle :")
        print(f"      * Borne inf (min_bin)                : {total_sat_min} ({pct_sat_min:.2f} %)")
        print(f"      * Borne sup (max_bin)                : {total_sat_max} ({pct_sat_max:.2f} %)")
        print(f"      * Total saturé (min + max)           : {total_sat} ({pct_sat_tot:.2f} %)")
        
    # 4e. Contrôle de monotonie par pixel
    print(f"\n[4e] Contrôle de monotonie par pixel (pixels avec >= 5 observations) :")
    spearman_coeffs = []
    n_qualifying = 0
    n_const_sc_varying_raw = 0
    n_const_both = 0
    
    for idx in land_indices_1d:
        series = pixel_series[idx]
        if len(series) >= 5:
            n_qualifying += 1
            r_vals = [pt[0] for pt in series]
            s_vals = [pt[1] for pt in series]
            ptp_r = np.ptp(r_vals)
            ptp_s = np.ptp(s_vals)
            
            if ptp_r < 1e-6 and ptp_s < 1e-6:
                n_const_both += 1
            elif ptp_r >= 1e-6 and ptp_s < 1e-6:
                n_const_sc_varying_raw += 1
            else:
                rho, _ = spearmanr(r_vals, s_vals)
                if not np.isnan(rho):
                    spearman_coeffs.append(rho)
            
    spearman_coeffs = np.array(spearman_coeffs)
    print(f"  - Nombre de pixels avec >= 5 observations         : {n_qualifying}")
    pct_const_sc = (n_const_sc_varying_raw / n_qualifying * 100) if n_qualifying > 0 else 0.0
    print(f"  - Pixels obs scalée constante (brute variable)    : {n_const_sc_varying_raw} ({pct_const_sc:.2f} % des qualifiés)")
    if n_const_both > 0:
        print(f"  - Pixels avec brute et scalée toutes deux constantes : {n_const_both}")
    print(f"  - Pixels évalués pour le Spearman rho             : {len(spearman_coeffs)}")
    
    if len(spearman_coeffs) > 0:
        med_rho = float(np.median(spearman_coeffs))
        p05_rho = float(np.percentile(spearman_coeffs, 5))
        pct_sub95 = float(np.mean(spearman_coeffs < 0.95) * 100)
        
        print(f"  - Médiane de Spearman rho                         : {med_rho:.4f}")
        print(f"  - 5e percentile de Spearman rho                   : {p05_rho:.4f}")
        print(f"  - % de pixels avec Spearman rho < 0.95            : {pct_sub95:.2f} %")

def check_4c_innovations(label, month_compact):
    test_pattern = os.path.join(BASE_TEST, "output", label, "EnKF", month_compact, "LIS_DA_EnKF_*_innov.a01.d01.nc")
    nocdf_pattern = os.path.join(BASE_NOCDF, "output", label, "EnKF", month_compact, "LIS_DA_EnKF_*_innov.a01.d01.nc")
    
    test_files_all = sorted(glob.glob(test_pattern))
    nocdf_files_all = sorted(glob.glob(nocdf_pattern))
    
    print(f"\n--- [4c] Analyse des Innovations (O - F) pour {label} ---")
    print(f"Fichiers innov DA_cdf_TEST : {len(test_files_all)} | DA_nocdf : {len(nocdf_files_all)}")
    
    if not test_files_all:
        print("Aucun fichier d'innovation DA_cdf_TEST disponible pour le moment.")
        return
        
    def extract_innovations(file_list):
        vals = []
        for f in file_list:
            with nc.Dataset(f) as ds:
                inv = ds.variables["innov_01"][:]
                valid = (inv != -9999.0) & np.isfinite(inv)
                if np.sum(valid) > 0:
                    vals.extend(inv[valid].tolist())
        return np.array(vals)
        
    def filter_period(files, ptype):
        res = []
        for f in files:
            fname = os.path.basename(f)
            dstr = fname.split("_")[3][:8]
            day = int(dstr[6:8])
            if ptype == "all":
                res.append(f)
            elif ptype == "1-10" and day <= 10:
                res.append(f)
            elif ptype == "11-end" and day >= 11:
                res.append(f)
        return res

    periods = [
        ("Mois complet", "all"),
        ("Jours 1–10 (transitoire initial)", "1-10"),
        ("Jours 11–fin de mois (régime établi)", "11-end")
    ]
    
    for pname, ptype in periods:
        t_files = filter_period(test_files_all, ptype)
        n_files = filter_period(nocdf_files_all, ptype)
        
        t_inv = extract_innovations(t_files)
        n_inv = extract_innovations(n_files)
        
        print(f"\n  >> Période : {pname} (Fichiers test : {len(t_files)} | nocdf : {len(n_files)})")
        print(f"     - Innovations finies (DA_cdf_TEST) : {len(t_inv)}")
        print(f"     - Innovations finies (DA-NoCDF)     : {len(n_inv)}")
        if len(n_inv) > 0:
            ratio = len(t_inv) / len(n_inv) * 100
            print(f"     - Ratio DA_cdf_TEST / DA-NoCDF      : {ratio:.2f} %")
        if len(t_inv) > 0:
            print(f"     - Moyenne O - F (DA_cdf_TEST)        : {np.mean(t_inv):+.4f} m3/m3")
            print(f"     - Écart-type O - F (DA_cdf_TEST)     : {np.std(t_inv):.4f} m3/m3")
        if len(n_inv) > 0:
            print(f"     - Moyenne O - F (DA-NoCDF)           : {np.mean(n_inv):+.4f} m3/m3")
            print(f"     - Écart-type O - F (DA-NoCDF)        : {np.std(n_inv):.4f} m3/m3")

def check_4d_increments(label, month_compact, landmask):
    test_pattern = os.path.join(BASE_TEST, "output", label, "EnKF", month_compact, "LIS_DA_EnKF_*_incr.a01.d01.nc")
    nocdf_pattern = os.path.join(BASE_NOCDF, "output", label, "EnKF", month_compact, "LIS_DA_EnKF_*_incr.a01.d01.nc")
    
    test_files_all = sorted(glob.glob(test_pattern))
    nocdf_files_all = sorted(glob.glob(nocdf_pattern))
    
    print(f"\n--- [4d] Analyse des Incréments de Surface (Layer 1) pour {label} ---")
    print(f"Fichiers incr DA_cdf_TEST : {len(test_files_all)} | DA_nocdf : {len(nocdf_files_all)}")
    
    if not test_files_all:
        print("Aucun fichier d'incréments DA_cdf_TEST disponible pour le moment.")
        return
        
    land_bool = (landmask == 1)
    
    def extract_increments(file_list):
        signed_means = []
        abs_means = []
        for f in file_list:
            with nc.Dataset(f) as ds:
                incr = ds.variables["anlys_incr_Soil Moisture Layer 1_01"][:]
                valid = land_bool & (incr != -9999.0) & np.isfinite(incr)
                if np.sum(valid) > 0:
                    signed_means.append(float(np.mean(incr[valid])))
                    abs_means.append(float(np.mean(np.abs(incr[valid]))))
        return np.array(signed_means), np.array(abs_means)
        
    def filter_period(files, ptype):
        res = []
        for f in files:
            fname = os.path.basename(f)
            dstr = fname.split("_")[3][:8]
            day = int(dstr[6:8])
            if ptype == "all":
                res.append(f)
            elif ptype == "1-10" and day <= 10:
                res.append(f)
            elif ptype == "11-end" and day >= 11:
                res.append(f)
        return res

    periods = [
        ("Mois complet", "all"),
        ("Jours 1–10 (transitoire initial)", "1-10"),
        ("Jours 11–fin de mois (régime établi)", "11-end")
    ]
    
    for pname, ptype in periods:
        t_files = filter_period(test_files_all, ptype)
        n_files = filter_period(nocdf_files_all, ptype)
        
        t_signed, t_abs = extract_increments(t_files)
        n_signed, n_abs = extract_increments(n_files)
        
        print(f"\n  >> Période : {pname} (Pas DA test : {len(t_signed)} | nocdf : {len(n_signed)})")
        if len(t_signed) > 0:
            print(f"     - DA_cdf_TEST Moyenne domaine signée  : {np.mean(t_signed):+.6f} m3/m3")
            print(f"     - DA_cdf_TEST Moyenne domaine absolue : {np.mean(t_abs):.6f} m3/m3")
        if len(n_signed) > 0:
            print(f"     - DA-NoCDF    Moyenne domaine signée  : {np.mean(n_signed):+.6f} m3/m3")
            print(f"     - DA-NoCDF    Moyenne domaine absolue : {np.mean(n_abs):.6f} m3/m3")

def main():
    parser = argparse.ArgumentParser(description="Évaluation DA_cdf_TEST (4a-4e)")
    parser.add_argument("--month", choices=["2018-01", "2018-08", "all"], default="all")
    parser.add_argument("--base-test", default=None, help="Chemin du run test")
    parser.add_argument("--model-cdf", default=None, help="Chemin de la CDF modèle")
    args = parser.parse_args()
    
    global BASE_TEST, MODEL_CDF_FILE
    if args.base_test:
        BASE_TEST = args.base_test
    if args.model_cdf:
        MODEL_CDF_FILE = args.model_cdf
    
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze()
        
    months_to_run = ["2018-01", "2018-08"] if args.month == "all" else [args.month]
    
    for m in months_to_run:
        compact = m.replace("-", "")
        log_sub = "012018" if m == "2018-01" else "082018"
        print("\n" + "=" * 70)
        print(f"ÉVALUATION COMPLETE DU MOIS {m}")
        print("=" * 70)
        check_4a_logs(m, log_sub)
        check_4b_and_4e_daobs(m, compact, landmask)
        check_4c_innovations(m, compact)
        check_4d_increments(m, compact, landmask)

if __name__ == "__main__":
    main()
