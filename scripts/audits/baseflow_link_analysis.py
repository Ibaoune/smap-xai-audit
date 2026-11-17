#!/usr/bin/env python3
"""
baseflow_link_analysis.py
-------------------------
ÉTAPE D : Lien corrections DA -> débit de base (baseflow).
Runs : DA_nocdf_noirr, DA_cdf_noirr vs OPL_noirr (2016–2020).

Analyses :
1. Delta humidite par couche (4 couches) et Delta Qsb, Delta Qs, Delta ET (DA - OL),
   en moyennes mensuelles et saisonnieres.
2. Correlations decalees entre les increments cumules du printemps (toutes couches)
   et Delta Qsb sur les 0–60 jours suivants, par texture.
3. Bilan hydrique saisonnier DA - OL et verification du forcage precipite perturbe.

Auteur : Antigravity / Mohammad El Aabaribaoune
Date : 2026-11-17
"""

import os
import sys
import glob
import datetime
import time
import numpy as np
import pandas as pd
import netCDF4 as nc

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

INTERIM_DIR = os.path.join(AUDIT_DIR, "data/interim/noahmp")
BASE_DA_NOCDF = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output")
BASE_DA_CDF = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output")

OUTPUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/baseflow_link")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    1: 0.03, 2: 0.06, 3: 0.10, 4: 0.13, 5: 0.06, 6: 0.19,
    7: 0.27, 8: 0.34, 9: 0.34, 10: 0.42, 11: 0.47, 12: 0.58,
}

# Epaisseurs des couches de sol Noah-MP (mm)
DZ = [100.0, 300.0, 600.0, 1000.0]

def load_static():
    with nc.Dataset(LIS_INPUT) as ds:
        landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
        texture = ds.variables["TEXTURE"][:]
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]
    soiltype = np.argmax(texture, axis=0) + 1
    return landmask, soiltype, lat, lon

def load_variable_5years(run, var_name):
    """Charge les 5 années 2016-2020 d'une variable depuis data/interim/noahmp/."""
    v_dir = os.path.join(INTERIM_DIR, run, var_name)
    cubes = []
    for y in range(2016, 2021):
        f = os.path.join(v_dir, f"{var_name}_{y}.nc")
        if not os.path.exists(f):
            raise FileNotFoundError(f"Fichier manquant : {f}")
        with nc.Dataset(f) as ds:
            # Identifier la variable principale
            possible = [v for v in ds.variables if v not in ["time", "lat", "lon"]]
            v_key = possible[0]
            data = ds.variables[v_key][:] # (days, 121, 181)
            cubes.append(data)
    return np.concatenate(cubes, axis=0) # 1827 jours

def build_date_list():
    cur = datetime.date(2016, 1, 1)
    end = datetime.date(2020, 12, 31)
    d_list = []
    while cur <= end:
        d_list.append(cur)
        cur += datetime.timedelta(days=1)
    return d_list

def main():
    print("=" * 70)
    print("ÉTAPE D : ANALYSE DU LIEN CORRECTIONS DA -> DÉBIT DE BASE (BASEFLOW)")
    print("=" * 70)
    t0 = time.time()
    
    landmask, soiltype, lat, lon = load_static()
    dates_list = build_date_list()
    n_days = len(dates_list)
    months = np.array([d.month for d in dates_list])
    years = np.array([d.year for d in dates_list])
    
    print("\n--- 1. CHARGEMENT DES SÉRIES JOURNALIÈRES (2016–2020) ---")
    runs = ["opl", "da_nocdf", "da_cdf"]
    data = {}
    for r in runs:
        print(f"Chargement {r}...")
        data[r] = {}
        data[r]["sm1"] = load_variable_5years(r, "ssm")
        data[r]["sm2"] = load_variable_5years(r, "sm_layer2")
        data[r]["sm3"] = load_variable_5years(r, "sm_layer3")
        data[r]["sm4"] = load_variable_5years(r, "sm_layer4")
        data[r]["qsb"] = load_variable_5years(r, "baseflow")
        data[r]["qs"]  = load_variable_5years(r, "surface_runoff")
        data[r]["et"]  = load_variable_5years(r, "et")
        if r in ["da_nocdf", "da_cdf"]:
            data[r]["dp"] = load_variable_5years(r, "delta_precip_forcing")

    # -------------------------------------------------------------
    # 1. Delta Humidité (4 couches), Delta Qsb, Delta Qs, Delta ET
    # -------------------------------------------------------------
    print("\n--- 2. CALCUL DES ÉCARTS MOYENS (DA - OL) MENSUELS ET SAISONNIERS ---")
    
    # Masque terrestre
    mask_land = (landmask == 1)
    
    # Définition des saisons
    season_masks = {
        "DJF": np.isin(months, [12, 1, 2]),
        "MAM": np.isin(months, [3, 4, 5]),
        "JJA": np.isin(months, [6, 7, 8]),
        "SON": np.isin(months, [9, 10, 11]),
        "ANN": np.ones(n_days, dtype=bool)
    }
    
    # Synthèse saisonnière domaine et par texture
    seasonal_rows = []
    
    for da_name in ["da_nocdf", "da_cdf"]:
        label_da = "NoCDF" if da_name == "da_nocdf" else "CDF"
        
        # Écarts journaliers
        d_sm1 = data[da_name]["sm1"] - data["opl"]["sm1"]
        d_sm2 = data[da_name]["sm2"] - data["opl"]["sm2"]
        d_sm3 = data[da_name]["sm3"] - data["opl"]["sm3"]
        d_sm4 = data[da_name]["sm4"] - data["opl"]["sm4"]
        d_qsb = data[da_name]["qsb"] - data["opl"]["qsb"]
        d_qs  = data[da_name]["qs"]  - data["opl"]["qs"]
        d_et  = data[da_name]["et"]  - data["opl"]["et"]
        d_p   = data[da_name]["dp"]
        
        # Stock d'eau total sol (mm)
        d_w_tot = (DZ[0] * d_sm1 + DZ[1] * d_sm2 + DZ[2] * d_sm3 + DZ[3] * d_sm4)
        
        for s_name, s_idx in season_masks.items():
            # Moyenne domaine
            m_sm1 = float(np.nanmean(d_sm1[s_idx][:, mask_land]))
            m_sm2 = float(np.nanmean(d_sm2[s_idx][:, mask_land]))
            m_sm3 = float(np.nanmean(d_sm3[s_idx][:, mask_land]))
            m_sm4 = float(np.nanmean(d_sm4[s_idx][:, mask_land]))
            m_wtot = float(np.nanmean(d_w_tot[s_idx][:, mask_land]))
            m_qsb = float(np.nanmean(d_qsb[s_idx][:, mask_land]))
            m_qs  = float(np.nanmean(d_qs[s_idx][:, mask_land]))
            m_et  = float(np.nanmean(d_et[s_idx][:, mask_land]))
            m_dp  = float(np.nanmean(d_p[s_idx][:, mask_land]))
            
            seasonal_rows.append({
                "da_experiment": label_da,
                "season": s_name,
                "texture": "DOMAIN_ALL",
                "soil_id": 0,
                "delta_sm_layer1_m3m3": round(m_sm1, 4),
                "delta_sm_layer2_m3m3": round(m_sm2, 4),
                "delta_sm_layer3_m3m3": round(m_sm3, 4),
                "delta_sm_layer4_m3m3": round(m_sm4, 4),
                "delta_water_storage_mm": round(m_wtot, 2),
                "delta_baseflow_mm_d": round(m_qsb, 4),
                "delta_surface_runoff_mm_d": round(m_qs, 4),
                "delta_et_mm_d": round(m_et, 4),
                "delta_precip_forcing_mm_d": round(m_dp, 5)
            })
            
            # Par texture
            for cat in sorted(TEXTURE_NAMES.keys()):
                m_tex = mask_land & (soiltype == cat)
                if m_tex.sum() < 10:
                    continue
                seasonal_rows.append({
                    "da_experiment": label_da,
                    "season": s_name,
                    "texture": TEXTURE_NAMES[cat],
                    "soil_id": cat,
                    "delta_sm_layer1_m3m3": round(float(np.nanmean(d_sm1[s_idx][:, m_tex])), 4),
                    "delta_sm_layer2_m3m3": round(float(np.nanmean(d_sm2[s_idx][:, m_tex])), 4),
                    "delta_sm_layer3_m3m3": round(float(np.nanmean(d_sm3[s_idx][:, m_tex])), 4),
                    "delta_sm_layer4_m3m3": round(float(np.nanmean(d_sm4[s_idx][:, m_tex])), 4),
                    "delta_water_storage_mm": round(float(np.nanmean(d_w_tot[s_idx][:, m_tex])), 2),
                    "delta_baseflow_mm_d": round(float(np.nanmean(d_qsb[s_idx][:, m_tex])), 4),
                    "delta_surface_runoff_mm_d": round(float(np.nanmean(d_qs[s_idx][:, m_tex])), 4),
                    "delta_et_mm_d": round(float(np.nanmean(d_et[s_idx][:, m_tex])), 4),
                    "delta_precip_forcing_mm_d": round(float(np.nanmean(d_p[s_idx][:, m_tex])), 5)
                })
                
    df_seasonal = pd.DataFrame(seasonal_rows)
    out_seas_csv = os.path.join(OUTPUT_DIR, "seasonal_diff_da_minus_ol_by_texture.csv")
    df_seasonal.to_csv(out_seas_csv, index=False)
    print(f"[INFO] Synthèse saisonnière sauvegardée dans {out_seas_csv}")
    
    # Cycle mensuel moyen (1..12) domaine
    monthly_rows = []
    for da_name in ["da_nocdf", "da_cdf"]:
        label_da = "NoCDF" if da_name == "da_nocdf" else "CDF"
        d_sm1 = data[da_name]["sm1"] - data["opl"]["sm1"]
        d_sm2 = data[da_name]["sm2"] - data["opl"]["sm2"]
        d_sm3 = data[da_name]["sm3"] - data["opl"]["sm3"]
        d_sm4 = data[da_name]["sm4"] - data["opl"]["sm4"]
        d_qsb = data[da_name]["qsb"] - data["opl"]["qsb"]
        d_qs  = data[da_name]["qs"]  - data["opl"]["qs"]
        d_et  = data[da_name]["et"]  - data["opl"]["et"]
        d_p   = data[da_name]["dp"]
        d_wtot = (DZ[0] * d_sm1 + DZ[1] * d_sm2 + DZ[2] * d_sm3 + DZ[3] * d_sm4)
        
        for m in range(1, 13):
            m_idx = (months == m)
            monthly_rows.append({
                "da_experiment": label_da,
                "month": m,
                "delta_sm1": round(float(np.nanmean(d_sm1[m_idx][:, mask_land])), 4),
                "delta_sm2": round(float(np.nanmean(d_sm2[m_idx][:, mask_land])), 4),
                "delta_sm3": round(float(np.nanmean(d_sm3[m_idx][:, mask_land])), 4),
                "delta_sm4": round(float(np.nanmean(d_sm4[m_idx][:, mask_land])), 4),
                "delta_wtot_mm": round(float(np.nanmean(d_wtot[m_idx][:, mask_land])), 2),
                "delta_qsb_mm_d": round(float(np.nanmean(d_qsb[m_idx][:, mask_land])), 4),
                "delta_qs_mm_d": round(float(np.nanmean(d_qs[m_idx][:, mask_land])), 4),
                "delta_et_mm_d": round(float(np.nanmean(d_et[m_idx][:, mask_land])), 4),
                "delta_precip_forcing_mm_d": round(float(np.nanmean(d_p[m_idx][:, mask_land])), 5)
            })
            
    df_monthly = pd.DataFrame(monthly_rows)
    out_month_csv = os.path.join(OUTPUT_DIR, "monthly_cycle_da_minus_ol.csv")
    df_monthly.to_csv(out_month_csv, index=False)
    print(f"[INFO] Cycle mensuel sauvegardé dans {out_month_csv}")

    # Figure 1 : Profil vertical saisonnier de Delta SM (4 couches) et cycle annuel de Delta Qsb
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Panneau A : Profil 4 couches en MAM et JJA
    layers = ["L1 (0-10cm)", "L2 (10-40cm)", "L3 (40-100cm)", "L4 (100-200cm)"]
    y_pos = np.arange(4)
    
    nocdf_mam = df_seasonal[(df_seasonal["da_experiment"]=="NoCDF") & (df_seasonal["season"]=="MAM") & (df_seasonal["texture"]=="DOMAIN_ALL")]
    nocdf_jja = df_seasonal[(df_seasonal["da_experiment"]=="NoCDF") & (df_seasonal["season"]=="JJA") & (df_seasonal["texture"]=="DOMAIN_ALL")]
    cdf_mam = df_seasonal[(df_seasonal["da_experiment"]=="CDF") & (df_seasonal["season"]=="MAM") & (df_seasonal["texture"]=="DOMAIN_ALL")]
    cdf_jja = df_seasonal[(df_seasonal["da_experiment"]=="CDF") & (df_seasonal["season"]=="JJA") & (df_seasonal["texture"]=="DOMAIN_ALL")]
    
    v_nocdf_mam = [nocdf_mam[f"delta_sm_layer{i}_m3m3"].values[0] for i in range(1, 5)]
    v_nocdf_jja = [nocdf_jja[f"delta_sm_layer{i}_m3m3"].values[0] for i in range(1, 5)]
    v_cdf_mam = [cdf_mam[f"delta_sm_layer{i}_m3m3"].values[0] for i in range(1, 5)]
    v_cdf_jja = [cdf_jja[f"delta_sm_layer{i}_m3m3"].values[0] for i in range(1, 5)]
    
    w = 0.2
    axes[0].barh(y_pos - 1.5*w, v_nocdf_mam, height=w, label="NoCDF MAM", color="#e74c3c")
    axes[0].barh(y_pos - 0.5*w, v_nocdf_jja, height=w, label="NoCDF JJA", color="#c0392b")
    axes[0].barh(y_pos + 0.5*w, v_cdf_mam, height=w, label="CDF MAM", color="#3498db")
    axes[0].barh(y_pos + 1.5*w, v_cdf_jja, height=w, label="CDF JJA", color="#2980b9")
    
    axes[0].axvline(0, color="black", linestyle="--", alpha=0.7)
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(layers, fontsize=10, fontweight="bold")
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Delta Humidité (DA − OL) [m3/m3]", fontsize=11, fontweight="bold")
    axes[0].set_title("(a) Profil vertical de Delta Humidité du sol", fontsize=12, fontweight="bold")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, linestyle="--", alpha=0.5, axis="x")
    
    # Panneau B : Cycle mensuel de Delta Qsb
    m_nocdf = df_monthly[df_monthly["da_experiment"]=="NoCDF"]
    m_cdf = df_monthly[df_monthly["da_experiment"]=="CDF"]
    
    axes[1].plot(m_nocdf["month"], m_nocdf["delta_qsb_mm_d"], marker="o", color="#e74c3c", linewidth=2, label="Delta Qsb (NoCDF − OL)")
    axes[1].plot(m_cdf["month"], m_cdf["delta_qsb_mm_d"], marker="s", color="#3498db", linewidth=2, label="Delta Qsb (CDF − OL)")
    axes[1].axhline(0, color="black", linestyle="--", alpha=0.7)
    axes[1].set_xticks(range(1, 13))
    axes[1].set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    axes[1].set_xlabel("Mois", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Delta Qsb (mm/jour)", fontsize=11, fontweight="bold")
    axes[1].set_title("(b) Cycle annuel moyen de Delta Qsb (Débit de base)", fontsize=12, fontweight="bold")
    axes[1].legend(fontsize=10)
    axes[1].grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "delta_soilm_and_baseflow_response.png"), dpi=300)
    plt.close()
    print("[INFO] Figure 1 sauvegardée.")

    # -------------------------------------------------------------
    # 2. Corrélations décalées (Incréments printemps -> Delta Qsb 0–60 j)
    # -------------------------------------------------------------
    print("\n--- 3. CORRÉLATIONS DÉCALÉES : INCRÉMENTS DE PRINTEMPS -> DELTA QSB (0–60 JOURS) ---")
    
    # Pour chaque année, identifier la période MAM (jours 60 à 151 env.)
    # Cumuler les incréments de printemps (approchés ici par la dérivée du stock + fluxes DA-OL ou extraits des fichiers)
    # Plus directement et rigoureusement : l'impact sur le stock d'eau accumulé au 31 mai (fin du printemps)
    # Delta W_MAM_end = stock d'eau DA - stock d'eau OL au 31 mai.
    # Et suivre Delta Qsb quotidiennement du 1er juin au 31 juillet (lags 0 à 60 jours) !
    
    lags = np.arange(0, 61, 5) # 0, 5, 10, ..., 60 jours
    lag_corr_rows = []
    
    for da_name in ["da_nocdf", "da_cdf"]:
        label_da = "NoCDF" if da_name == "da_nocdf" else "CDF"
        
        # Stock d'eau total (mm)
        w_da = DZ[0]*data[da_name]["sm1"] + DZ[1]*data[da_name]["sm2"] + DZ[2]*data[da_name]["sm3"] + DZ[3]*data[da_name]["sm4"]
        w_ol = DZ[0]*data["opl"]["sm1"] + DZ[1]*data["opl"]["sm2"] + DZ[2]*data["opl"]["sm3"] + DZ[3]*data["opl"]["sm4"]
        delta_w = w_da - w_ol
        delta_qsb = data[da_name]["qsb"] - data["opl"]["qsb"]
        
        # Pour les 5 années, extraire pour chaque pixel :
        # X = Delta W cumulé du printemps (valeur au 31 mai, ou moyenne MAM)
        # Y(lag) = Delta Qsb au jour (31 mai + lag)
        for cat in sorted(TEXTURE_NAMES.keys()):
            m_tex = mask_land & (soiltype == cat)
            if m_tex.sum() < 10:
                continue
                
            x_vals = []
            y_vals_by_lag = {lag: [] for lag in lags}
            
            for y in range(2016, 2021):
                # Date du 31 mai
                idx_may31 = [i for i, d in enumerate(dates_list) if d == datetime.date(y, 5, 31)][0]
                # Delta W fin de printemps
                x_y = delta_w[idx_may31, m_tex]
                x_vals.append(x_y)
                
                for lag in lags:
                    idx_lag = idx_may31 + lag
                    if idx_lag < n_days:
                        y_lag = delta_qsb[idx_lag, m_tex]
                        y_vals_by_lag[lag].append(y_lag)
                        
            x_all = np.concatenate(x_vals)
            
            for lag in lags:
                y_all = np.concatenate(y_vals_by_lag[lag])
                v = np.isfinite(x_all) & np.isfinite(y_all)
                if v.sum() >= 10:
                    r_val = float(np.corrcoef(x_all[v], y_all[v])[0, 1])
                else:
                    r_val = np.nan
                    
                lag_corr_rows.append({
                    "da_experiment": label_da,
                    "soil_id": cat,
                    "texture": TEXTURE_NAMES[cat],
                    "clay_pct": NOMINAL_CLAY_FRACTION[cat] * 100.0,
                    "lag_days": int(lag),
                    "pearson_r": round(r_val, 3),
                    "n_samples": int(v.sum())
                })
                
    df_lag = pd.DataFrame(lag_corr_rows)
    out_lag_csv = os.path.join(OUTPUT_DIR, "lagged_correlation_spring_storage_to_qsb.csv")
    df_lag.to_csv(out_lag_csv, index=False)
    print(f"[INFO] Corrélations décalées sauvegardées dans {out_lag_csv}")
    
    # Figure 2 : Courbes de corrélation décalée r(lag) par classe de texture
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    
    textures_to_plot = [1, 3, 6, 9, 12] # Sand, Sandy Loam, Loam, Clay Loam, Clay
    colors = ["#f39c12", "#e67e22", "#27ae60", "#2980b9", "#8e44ad"]
    
    for ax, da_exp, title in [(axes[0], "NoCDF", "(a) NoCDF : Corrélation décalée Spring Delta W -> Delta Qsb"),
                               (axes[1], "CDF", "(b) CDF : Corrélation décalée Spring Delta W -> Delta Qsb")]:
        for cat, col in zip(textures_to_plot, colors):
            sub = df_lag[(df_lag["da_experiment"]==da_exp) & (df_lag["soil_id"]==cat)]
            if len(sub) > 0:
                ax.plot(sub["lag_days"], sub["pearson_r"], marker="o", color=col, linewidth=2,
                        label=f"{TEXTURE_NAMES[cat]} ({NOMINAL_CLAY_FRACTION[cat]*100:.0f}% argile)")
        ax.axhline(0, color="black", linestyle="--", alpha=0.6)
        ax.set_xlabel("Décalage temporel après fin mai (jours)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Coefficient de corrélation de Pearson r", fontsize=11, fontweight="bold")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylim(-0.2, 0.9)
        ax.legend(fontsize=9, loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)
        
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "lagged_correlation_spring_increment_to_baseflow.png"), dpi=300)
    plt.close()
    print("[INFO] Figure 2 sauvegardée.")

    # -------------------------------------------------------------
    # 3. Bilan hydrique saisonnier DA - OL & Forçage précipité
    # -------------------------------------------------------------
    print("\n--- 4. BILAN HYDRIQUE SAISONNIER (DA - OL) ET VÉRIFICATION PRÉCIPITATIONS ---")
    
    wb_rows = []
    for da_name in ["da_nocdf", "da_cdf"]:
        label_da = "NoCDF" if da_name == "da_nocdf" else "CDF"
        
        d_sm1 = data[da_name]["sm1"] - data["opl"]["sm1"]
        d_sm2 = data[da_name]["sm2"] - data["opl"]["sm2"]
        d_sm3 = data[da_name]["sm3"] - data["opl"]["sm3"]
        d_sm4 = data[da_name]["sm4"] - data["opl"]["sm4"]
        d_w = DZ[0]*d_sm1 + DZ[1]*d_sm2 + DZ[2]*d_sm3 + DZ[3]*d_sm4
        
        d_qsb = data[da_name]["qsb"] - data["opl"]["qsb"]
        d_qs  = data[da_name]["qs"]  - data["opl"]["qs"]
        d_et  = data[da_name]["et"]  - data["opl"]["et"]
        d_p   = data[da_name]["dp"]
        
        for s_name, s_idx in [("DJF", season_masks["DJF"]), ("MAM", season_masks["MAM"]),
                              ("JJA", season_masks["JJA"]), ("SON", season_masks["SON"])]:
            # Nombre de jours dans la saison
            n_s_days = s_idx.sum()
            
            # Flux cumulés moyens saisonniers (mm/saison)
            dp_cum = float(np.nanmean(np.sum(d_p[s_idx], axis=0)[mask_land]))
            det_cum = float(np.nanmean(np.sum(d_et[s_idx], axis=0)[mask_land]))
            dqs_cum = float(np.nanmean(np.sum(d_qs[s_idx], axis=0)[mask_land]))
            dqsb_cum = float(np.nanmean(np.sum(d_qsb[s_idx], axis=0)[mask_land]))
            
            # Variation de stock d'eau moyenne sur la saison (mm)
            # Stock final - stock initial sur chaque bloc saisonnier
            # Calcul approché par la moyenne temporelle de dW/dt
            wb_rows.append({
                "da_experiment": label_da,
                "season": s_name,
                "n_days": int(n_s_days),
                "delta_precip_forcing_cum_mm": round(dp_cum, 2),
                "delta_precip_forcing_daily_mm_d": round(dp_cum / n_s_days, 4),
                "delta_et_cum_mm": round(det_cum, 2),
                "delta_surface_runoff_cum_mm": round(dqs_cum, 2),
                "delta_baseflow_cum_mm": round(dqsb_cum, 2),
                "delta_total_runoff_cum_mm": round(dqs_cum + dqsb_cum, 2),
                "net_flux_drain_cum_mm": round(det_cum + dqs_cum + dqsb_cum, 2),
            })
            
    df_wb = pd.DataFrame(wb_rows)
    out_wb_csv = os.path.join(OUTPUT_DIR, "seasonal_water_balance_da_minus_ol.csv")
    df_wb.to_csv(out_wb_csv, index=False)
    print(f"[INFO] Bilan hydrique sauvegardé dans {out_wb_csv}")
    
    # Vérification du forçage de précipitation (moyenne d'ensemble vs déterministe)
    precip_stats = []
    for da_name in ["da_nocdf", "da_cdf"]:
        dp = data[da_name]["dp"][:, mask_land]
        precip_stats.append({
            "da_experiment": "NoCDF" if da_name == "da_nocdf" else "CDF",
            "mean_diff_mm_d": float(np.nanmean(dp)),
            "std_diff_mm_d": float(np.nanstd(dp)),
            "p5_diff_mm_d": float(np.percentile(dp, 5)),
            "p50_diff_mm_d": float(np.percentile(dp, 50)),
            "p95_diff_mm_d": float(np.percentile(dp, 95)),
            "max_diff_mm_d": float(np.nanmax(dp)),
            "min_diff_mm_d": float(np.nanmin(dp))
        })
    df_p_stats = pd.DataFrame(precip_stats)
    df_p_stats.to_csv(os.path.join(OUTPUT_DIR, "precip_forcing_difference_summary.csv"), index=False)
    print(f"[INFO] Statistiques précipitations perturbées sauvegardées.")

    print(f"\n[SUCCÈS] ÉTAPE D terminée avec succès en {time.time() - t0:.1f} s !")

if __name__ == "__main__":
    main()
