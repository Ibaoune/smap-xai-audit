#!/usr/bin/env python3
"""
complements_water_balance_and_validation.py
-------------------------------------------
Compléments d'audit (lecture seule) :
1. Bilan d'eau détaillé JA 2018 (Nowilt vs Contrôle) sur pixels Argile (12) et Limon argileux (9) :
   P, Incr DA, ET (ESoil, TVeg, ECanop), Qs, Qsb, delta Stock (L1..L4, profil, nappe).
2. Origine de la texture dans lis_input et comparaison de la fraction d'argile avec SMAP L3_SM_P_E.
3. Tableau 12 mois x texture de la fraction rejetée pour DA-NoCDF (5 ans) et DA-CDF (mois terminés).
4. Analyse des données satellites indépendantes disponibles sur le cluster (ESA CCI, ASCAT) :
   moyenne JA par texture comparée à SMAP et OL.
"""

import os
import glob
import datetime
import numpy as np
import netCDF4 as nc

# Chemins
BASE_CTRL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
BASE_NOWILT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_TEST_nowilt/output"
BASE_DACDF = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output"
LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
SOILPARM = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/land_params/noahmp401_parms/SOILPARM.TBL"
SMAP_SAMPLE = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/observations/SMAP_SPL3SMP_E/2018.07.15/SMAP_L3_SM_P_E_20180715_R19240_001.h5"
DIR_ESACCI = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/soil_moisture/ESA_CCI/raw"
DIR_ASCAT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/soil_moisture/ASCAT/raw"

TEXTURE_NAMES = {
    1: "Sand", 2: "Loamy Sand", 3: "Sandy Loam", 4: "Silt Loam", 5: "Silt",
    6: "Loam", 7: "Sandy Clay Loam", 8: "Silty Clay Loam", 9: "Clay Loam",
    10: "Sandy Clay", 11: "Silty Clay", 12: "Clay"
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
    return landmask, soiltype, vegt, wlt_grid, wltsmc, texture, lat, lon

def read_daobs(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

def main():
    print("==================================================================")
    print(" COMPLÉMENTS D'AUDIT : BILAN D'EAU, TEXTURE & VALIDATION EXTERNE")
    print("==================================================================")
    
    landmask, soiltype, vegt, wlt_grid, wltsmc, texture_raw, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    # -------------------------------------------------------------
    # 1. BILAN D'EAU DÉTAILLÉ (JA 2018) SUR ARGILE (12) ET LIMON ARGILEUX (9)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 1. BILAN D'EAU DU TEST SANS SEUIL (JA 2018) SUR ARGILE & LIMON ARGILEUX")
    print("-------------------------------------------------------------")
    
    months_18 = ["2018-07", "2018-08"]
    
    # Fichiers SURFACEMODEL
    f_sm_c = sorted(glob.glob(f"{BASE_CTRL}/2018-0[78]/SURFACEMODEL/20180[78]/LIS_HIST_*.nc"))
    f_sm_n = sorted(glob.glob(f"{BASE_NOWILT}/2018-0[78]/SURFACEMODEL/20180[78]/LIS_HIST_*.nc"))
    
    # Incréments EnKF
    f_inc_c = sorted(glob.glob(f"{BASE_CTRL}/2018-0[78]/EnKF/20180[78]/LIS_DA_EnKF_*_incr.a01.d01.nc"))
    f_inc_n = sorted(glob.glob(f"{BASE_NOWILT}/2018-0[78]/EnKF/20180[78]/LIS_DA_EnKF_*_incr.a01.d01.nc"))
    
    # Somme cumulée des incréments DA (couche 1 = 100 mm)
    incr_c_cum = np.zeros((121, 181), dtype=float)
    incr_n_cum = np.zeros((121, 181), dtype=float)
    
    for fc, fn in zip(f_inc_c, f_inc_n):
        with nc.Dataset(fc) as dsc, nc.Dataset(fn) as dsn:
            ic = dsc.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
            inw = dsn.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
            incr_c_cum += np.where(land_bool & np.isfinite(ic), ic, 0.0) * 100.0 # mm
            incr_n_cum += np.where(land_bool & np.isfinite(inw), inw, 0.0) * 100.0 # mm
            
    # Cumuls des flux journaliers (kg m-2 s-1 * 86400 s = mm/jour)
    flux_vars = ["TotalPrecip_tavg", "Evap_tavg", "ESoil_tavg", "TVeg_tavg", "ECanop_tavg", "Qs_tavg", "Qsb_tavg"]
    cum_flux_c = {v: np.zeros((121, 181), dtype=float) for v in flux_vars}
    cum_flux_n = {v: np.zeros((121, 181), dtype=float) for v in flux_vars}
    
    # États initial et final pour stock (premier et dernier fichier)
    with nc.Dataset(f_sm_c[0]) as ds_c0, nc.Dataset(f_sm_n[0]) as ds_n0:
        sm_c_init = ds_c0.variables["SoilMoist_tavg"][:].squeeze() # (4, 121, 181)
        sm_n_init = ds_n0.variables["SoilMoist_tavg"][:].squeeze()
        gws_c_init = ds_c0.variables["GWS_tavg"][:].squeeze()
        gws_n_init = ds_n0.variables["GWS_tavg"][:].squeeze()
        
    with nc.Dataset(f_sm_c[-1]) as ds_c1, nc.Dataset(f_sm_n[-1]) as ds_n1:
        sm_c_end = ds_c1.variables["SoilMoist_tavg"][:].squeeze()
        sm_n_end = ds_n1.variables["SoilMoist_tavg"][:].squeeze()
        gws_c_end = ds_c1.variables["GWS_tavg"][:].squeeze()
        gws_n_end = ds_n1.variables["GWS_tavg"][:].squeeze()
        
    # Moyenne temporelle des états
    sm_c_mean = np.zeros((4, 121, 181), dtype=float)
    sm_n_mean = np.zeros((4, 121, 181), dtype=float)
    gws_c_mean = np.zeros((121, 181), dtype=float)
    gws_n_mean = np.zeros((121, 181), dtype=float)
    
    cnt_days = len(f_sm_c)
    for fc, fn in zip(f_sm_c, f_sm_n):
        with nc.Dataset(fc) as dsc, nc.Dataset(fn) as dsn:
            for v in flux_vars:
                # kg m-2 s-1 * 86400 = mm/jour
                cum_flux_c[v] += dsc.variables[v][:].squeeze() * 86400.0
                cum_flux_n[v] += dsn.variables[v][:].squeeze() * 86400.0
            sm_c_mean += dsc.variables["SoilMoist_tavg"][:].squeeze()
            sm_n_mean += dsn.variables["SoilMoist_tavg"][:].squeeze()
            gws_c_mean += dsc.variables["GWS_tavg"][:].squeeze()
            gws_n_mean += dsn.variables["GWS_tavg"][:].squeeze()
            
    sm_c_mean /= cnt_days
    sm_n_mean /= cnt_days
    gws_c_mean /= cnt_days
    gws_n_mean /= cnt_days
    
    # Variations de stock sol (mm)
    dz = [100.0, 300.0, 600.0, 1000.0]
    
    # Présentation des bilans par classe de sol
    target_classes = [(12, "Clay (Argile)"), (9, "Clay Loam (Limon argileux)"), (None, "Argile + Limon argileux")]
    
    for c_id, c_name in target_classes:
        if c_id is not None:
            mask = non_forest & (soiltype == c_id)
        else:
            mask = non_forest & ((soiltype == 12) | (soiltype == 9))
            
        n_px = np.sum(mask)
        print(f"\n>>> BILAN D'EAU CUMULÉ (JA 2018, {cnt_days} jours) : {c_name} (N = {n_px} pixels) <<<")
        
        p_c = np.mean(cum_flux_c["TotalPrecip_tavg"][mask])
        p_n = np.mean(cum_flux_n["TotalPrecip_tavg"][mask])
        
        inc_c = np.mean(incr_c_cum[mask])
        inc_n = np.mean(incr_n_cum[mask])
        d_inc = inc_n - inc_c
        
        et_c = np.mean(cum_flux_c["Evap_tavg"][mask])
        et_n = np.mean(cum_flux_n["Evap_tavg"][mask])
        d_et = et_n - et_c
        
        es_c = np.mean(cum_flux_c["ESoil_tavg"][mask])
        es_n = np.mean(cum_flux_n["ESoil_tavg"][mask])
        d_es = es_n - es_c
        
        tv_c = np.mean(cum_flux_c["TVeg_tavg"][mask])
        tv_n = np.mean(cum_flux_n["TVeg_tavg"][mask])
        d_tv = tv_n - tv_c
        
        ec_c = np.mean(cum_flux_c["ECanop_tavg"][mask])
        ec_n = np.mean(cum_flux_n["ECanop_tavg"][mask])
        d_ec = ec_n - ec_c
        
        qs_c = np.mean(cum_flux_c["Qs_tavg"][mask])
        qs_n = np.mean(cum_flux_n["Qs_tavg"][mask])
        d_qs = qs_n - qs_c
        
        qsb_c = np.mean(cum_flux_c["Qsb_tavg"][mask])
        qsb_n = np.mean(cum_flux_n["Qsb_tavg"][mask])
        d_qsb = qsb_n - qsb_c
        
        # Variations de stock entre t_end et t_0 pour chaque run
        # et différence entre les deux runs
        ds_layers_c = [(np.mean(sm_c_end[i][mask]) - np.mean(sm_c_init[i][mask])) * dz[i] for i in range(4)]
        ds_layers_n = [(np.mean(sm_n_end[i][mask]) - np.mean(sm_n_init[i][mask])) * dz[i] for i in range(4)]
        diff_end_layers = [(np.mean(sm_n_end[i][mask]) - np.mean(sm_c_end[i][mask])) * dz[i] for i in range(4)]
        diff_mean_layers = [(np.mean(sm_n_mean[i][mask]) - np.mean(sm_c_mean[i][mask])) * dz[i] for i in range(4)]
        
        dgws_c = np.mean(gws_c_end[mask]) - np.mean(gws_c_init[mask])
        dgws_n = np.mean(gws_n_end[mask]) - np.mean(gws_n_init[mask])
        diff_end_gws = np.mean(gws_n_end[mask]) - np.mean(gws_c_end[mask])
        diff_mean_gws = np.mean(gws_n_mean[mask]) - np.mean(gws_c_mean[mask])
        
        print(f"Termes du bilan (mm)         | Contrôle (mm) | Nowilt (mm)   | Écart (Nowilt - Ctrl)")
        print(f"-------------------------------------------------------------------------------")
        print(f"Précipitations (P)           | {p_c:12.2f}  | {p_n:12.2f}  | {p_n - p_c:+12.2f} mm")
        print(f"Incréments DA cumulés        | {inc_c:12.2f}  | {inc_n:12.2f}  | {d_inc:+12.2f} mm")
        print(f"Évapotranspiration (ET)      | {et_c:12.2f}  | {et_n:12.2f}  | {d_et:+12.2f} mm")
        print(f"  - Évaporation sol (ESoil)  | {es_c:12.2f}  | {es_n:12.2f}  | {d_es:+12.2f} mm")
        print(f"  - Transpiration (TVeg)     | {tv_c:12.2f}  | {tv_n:12.2f}  | {d_tv:+12.2f} mm")
        print(f"  - Évap. canopée (ECanop)   | {ec_c:12.2f}  | {ec_n:12.2f}  | {d_ec:+12.2f} mm")
        print(f"Ruissellement surface (Qs)   | {qs_c:12.2f}  | {qs_n:12.2f}  | {d_qs:+12.2f} mm")
        print(f"Drainage/baseflow (Qsb)      | {qsb_c:12.2f}  | {qsb_n:12.2f}  | {d_qsb:+12.2f} mm")
        print(f"-------------------------------------------------------------------------------")
        print(f"Variation Stock Sol (t_end - t_0) :")
        print(f"  - Couche 1 (0-10 cm)       | {ds_layers_c[0]:12.2f}  | {ds_layers_n[0]:12.2f}  | {ds_layers_n[0] - ds_layers_c[0]:+12.2f} mm")
        print(f"  - Couche 2 (10-40 cm)      | {ds_layers_c[1]:12.2f}  | {ds_layers_n[1]:12.2f}  | {ds_layers_n[1] - ds_layers_c[1]:+12.2f} mm")
        print(f"  - Couche 3 (40-100 cm)     | {ds_layers_c[2]:12.2f}  | {ds_layers_n[2]:12.2f}  | {ds_layers_n[2] - ds_layers_c[2]:+12.2f} mm")
        print(f"  - Couche 4 (100-200 cm)    | {ds_layers_c[3]:12.2f}  | {ds_layers_n[3]:12.2f}  | {ds_layers_n[3] - ds_layers_c[3]:+12.2f} mm")
        tot_ds_c = sum(ds_layers_c)
        tot_ds_n = sum(ds_layers_n)
        print(f"  Total sol (0-2 m)          | {tot_ds_c:12.2f}  | {tot_ds_n:12.2f}  | {tot_ds_n - tot_ds_c:+12.2f} mm")
        print(f"Stock nappe/aquifère (GWS)   | {dgws_c:12.2f}  | {dgws_n:12.2f}  | {dgws_n - dgws_c:+12.2f} mm")
        print(f"-------------------------------------------------------------------------------")
        print(f"Différence d'état moyen sur JA :")
        print(f"  - Couche 1 (0-10 cm)       |            -  |            -  | {diff_mean_layers[0]:+12.2f} mm")
        print(f"  - Total profil (0-2 m)     |            -  |            -  | {sum(diff_mean_layers):+12.2f} mm")
        print(f"  - Nappe (GWS)              |            -  |            -  | {diff_mean_gws:+12.2f} mm")
        
        # Bilan de fermeture
        print(f"\nExplication du transfert d'eau :")
        print(f"  Eau nette retirée par la DA (Delta Incr) : {d_inc:+.2f} mm")
        print(f"  Baisse de l'évapotranspiration (-Delta ET): {-d_et:+.2f} mm (l'assèchement réduit la perte en ET)")
        print(f"  Baisse du ruissellement et drainage      : {-(d_qs + d_qsb):+.2f} mm")
        print(f"  Baisse finale du stock de sol (Delta S)   : {tot_ds_n - tot_ds_c:+.2f} mm")
        print(f"  Baisse finale du stock nappe              : {dgws_n - dgws_c:+.2f} mm")
        somme_reponses = (tot_ds_n - tot_ds_c) + (dgws_n - dgws_c) + d_et + (d_qs + d_qsb)
        print(f"  Fermeture : Delta Incr = Delta Stock + Delta Flux = {somme_reponses:+.2f} mm")
        
    # -------------------------------------------------------------
    # 2. ORIGINE DE LA CARTE DE TEXTURE ET COMPARAISON SMAP L3_E
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 2. ORIGINE DE LA TEXTURE DANS lis_input & FRACTION D'ARGILE SMAP")
    print("-------------------------------------------------------------")
    
    # Extraction de la fraction d'argile SMAP
    print(f"Lecture du produit SMAP L3_SM_P_E : {os.path.basename(SMAP_SAMPLE)}...")
    with nc.Dataset(SMAP_SAMPLE, 'r') as ds_smap:
        grp = ds_smap.groups['Soil_Moisture_Retrieval_Data_AM']
        smap_clay = grp.variables['clay_fraction'][:] # (1624, 3856)
        smap_lat = grp.variables['latitude'][:]
        smap_lon = grp.variables['longitude'][:]
        
    # Sous-ensemble sur la boîte Maroc
    lat_min, lat_max = lat.min(), lat.max()
    lon_min, lon_max = lon.min(), lon.max()
    
    # EASE Grid 2.0 9km est régulière en coordonnées projetées ou en lat/lon
    # Trouver les indices dans la boîte
    smap_mask_box = (smap_lat >= lat_min - 0.1) & (smap_lat <= lat_max + 0.1) & (smap_lon >= lon_min - 0.1) & (smap_lon <= lon_max + 0.1)
    
    # Échantillonnage aux points du domaine NorthMor
    # Comme les coordonnées SMAP 2D contiennent des fillvalues hors grille, on prend les points valides
    valid_smap = smap_mask_box & (smap_clay >= 0.0) & (smap_clay <= 1.0)
    
    from scipy.interpolate import griddata
    pts_smap = np.column_stack([smap_lat[valid_smap], smap_lon[valid_smap]])
    vals_smap = smap_clay[valid_smap]
    
    print(f"  Points SMAP valides dans la boîte Maroc : {len(vals_smap)}")
    clay_smap_5km = griddata(pts_smap, vals_smap, (lat, lon), method='nearest')
    
    # Analyse par classe de texture Noah-MP
    print("\nComparaison de la fraction d'argile utilisée :")
    print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'Noah-MP Clay frac':<18} | {'SMAP L3_E Clay frac (Moy)':<26} | {'SMAP Clay (Méd)':<16} | {'SMAP Clay [Min - Max]':<22}")
    print("-" * 115)
    
    for c in [1, 3, 4, 6, 7, 9, 12]:
        m_c = non_forest & (soiltype == c)
        if np.sum(m_c) == 0: continue
        # Fraction d'argile dans SOILPARM / texture standard USDA :
        # Sand ~ 3%, Sandy Loam ~ 10%, Silt Loam ~ 13%, Loam ~ 19%, Sandy Clay Loam ~ 27%, Clay Loam ~ 34%, Clay ~ 55%
        # Dans SOILPARM.TBL : WLTSMC est calculé à partir de la teneur en argile/sable.
        noah_wlt = wltsmc[c]
        smap_c = clay_smap_5km[m_c]
        s_mean = np.mean(smap_c) * 100.0
        s_med = np.median(smap_c) * 100.0
        s_min = np.min(smap_c) * 100.0
        s_max = np.max(smap_c) * 100.0
        
        name = TEXTURE_NAMES.get(c, "Inconnu")
        print(f"{c:<4} | {name:<16} | {np.sum(m_c):<6} | smcwlt={noah_wlt:.3f}       | {s_mean:6.1f} %                    | {s_med:6.1f} %        | [{s_min:4.1f}% - {s_max:4.1f}%]")
        
    # -------------------------------------------------------------
    # 3. TABLEAU MOIS PAR MOIS (12 MOIS) X TEXTURE (DA-NoCDF vs DA-CDF)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 3. FRACTION REJETÉE PAR FLÉTRISSEMENT MOIS PAR MOIS (12 MOIS) X TEXTURE")
    print("-------------------------------------------------------------")
    
    years_nocdf = [2016, 2017, 2018, 2019, 2020]
    
    # Mois disponibles pour DA-CDF
    dacdf_dirs = sorted(glob.glob(f"{BASE_DACDF}/201[67]-*"))
    dacdf_yms = [os.path.basename(d) for d in dacdf_dirs]
    print(f"Mois terminés dans DA-CDF : {len(dacdf_yms)} mois ({dacdf_yms[0]} à {dacdf_yms[-1]})")
    
    # Calcul par mois calendaire (1 à 12) pour DA-NoCDF
    rej_nocdf_month = {m: {c: [] for c in [1, 3, 4, 6, 7, 9, 12, 'ALL']} for m in range(1, 13)}
    
    for y in years_nocdf:
        for m in range(1, 13):
            ym = f"{y}-{m:02d}"
            ym_c = f"{y}{m:02d}"
            f_daobs = glob.glob(f"{BASE_CTRL}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r")
            if not f_daobs: continue
            
            raw_px = np.zeros((121, 181), dtype=int)
            rej_px = np.zeros((121, 181), dtype=int)
            for f in f_daobs:
                r1, r2 = read_daobs(f)
                val_raw = (r1 != -9999.0) & np.isfinite(r1) & land_bool
                raw_px[val_raw] += 1
                wilt_rej = val_raw & ((r2 == -9999.0) | (~np.isfinite(r2))) & ((r1 - wlt_grid) < 0.02)
                rej_px[wilt_rej] += 1
                
            for c in [1, 3, 4, 6, 7, 9, 12]:
                m_c = non_forest & (soiltype == c) & (raw_px >= 5)
                if np.sum(m_c) > 0:
                    rej_nocdf_month[m][c].append(np.mean(rej_px[m_c] / raw_px[m_c]))
            m_all = non_forest & (raw_px >= 5)
            if np.sum(m_all) > 0:
                rej_nocdf_month[m]['ALL'].append(np.mean(rej_px[m_all] / raw_px[m_all]))
                
    # Calcul pour DA-CDF
    rej_dacdf_month = {m: {c: [] for c in [1, 3, 4, 6, 7, 9, 12, 'ALL']} for m in range(1, 13)}
    for ym in dacdf_yms:
        y, m = int(ym[:4]), int(ym[5:7])
        ym_c = ym.replace("-", "")
        f_daobs = glob.glob(f"{BASE_DACDF}/{ym}/DAOBS/{ym_c}/LISDAOBS_*.1gs4r")
        if not f_daobs: continue
        raw_px = np.zeros((121, 181), dtype=int)
        rej_px = np.zeros((121, 181), dtype=int)
        for f in f_daobs:
            r1, r2 = read_daobs(f)
            val_raw = (r1 != -9999.0) & np.isfinite(r1) & land_bool
            raw_px[val_raw] += 1
            # Rejet total dans DA-CDF (obs non scalée / rejetée)
            rej = val_raw & ((r2 == -9999.0) | (~np.isfinite(r2)))
            rej_px[rej] += 1
        for c in [1, 3, 4, 6, 7, 9, 12]:
            m_c = non_forest & (soiltype == c) & (raw_px >= 5)
            if np.sum(m_c) > 0:
                rej_dacdf_month[m][c].append(np.mean(rej_px[m_c] / raw_px[m_c]))
        m_all = non_forest & (raw_px >= 5)
        if np.sum(m_all) > 0:
            rej_dacdf_month[m]['ALL'].append(np.mean(rej_px[m_all] / raw_px[m_all]))
            
    # Affichage du tableau mois par mois pour DA-NoCDF
    month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jui", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    print("\n>>> DA-NoCDF : Taux de rejet par le test de flétrissement (%) (Moyenne 2016-2020) <<<")
    print(f"{'Mois':<6} | {'Sand (1)':<9} | {'SdyLoam (3)':<11} | {'SiltLoam (4)':<12} | {'Loam (6)':<9} | {'SdyClLoam(7)':<12} | {'ClayLoam (9)':<12} | {'Clay (12)':<10} | {'ENSEMBLE':<9}")
    print("-" * 95)
    for m in range(1, 13):
        row = [f"{month_names[m-1]:<6}"]
        for c in [1, 3, 4, 6, 7, 9, 12, 'ALL']:
            vals = rej_nocdf_month[m][c]
            v_str = f"{np.mean(vals)*100:5.1f}%" if vals else "  -  "
            row.append(f"{v_str:<{10 if c != 'ENSEMBLE' else 9}}")
        print(" | ".join(row))
        
    print("\n>>> DA-CDF : Taux de rejet en ligne (%) (Moyenne 2016-2017 terminés) <<<")
    print(f"{'Mois':<6} | {'Sand (1)':<9} | {'SdyLoam (3)':<11} | {'SiltLoam (4)':<12} | {'Loam (6)':<9} | {'SdyClLoam(7)':<12} | {'ClayLoam (9)':<12} | {'Clay (12)':<10} | {'ENSEMBLE':<9}")
    print("-" * 95)
    for m in range(1, 13):
        row = [f"{month_names[m-1]:<6}"]
        for c in [1, 3, 4, 6, 7, 9, 12, 'ALL']:
            vals = rej_dacdf_month[m][c]
            v_str = f"{np.mean(vals)*100:5.1f}%" if vals else "  -  "
            row.append(f"{v_str:<{10 if c != 'ENSEMBLE' else 9}}")
        print(" | ".join(row))
        
    # -------------------------------------------------------------
    # 4. DONNÉES SATELLITES INDÉPENDANTES (ESA CCI, ASCAT)
    # -------------------------------------------------------------
    print("\n-------------------------------------------------------------")
    print(" 4. VALIDATION EXTERNE : DONNÉES SATELLITES INDÉPENDANTES DISPONIBLES")
    print("-------------------------------------------------------------")
    
    # 1. ESA CCI Soil Moisture (COMBINED v08.1)
    f_esacci = sorted(glob.glob(f"{DIR_ESACCI}/ESACCI-SOILMOISTURE-*-20180[78]*.nc"))
    print(f"Fichiers ESA CCI Combined disponibles pour JA 2018 : {len(f_esacci)} fichiers journaliers.")
    
    esacci_sum = np.zeros((121, 181), dtype=float)
    esacci_cnt = np.zeros((121, 181), dtype=int)
    
    if f_esacci:
        with nc.Dataset(f_esacci[0]) as ds0:
            cci_lat = ds0.variables['lat'][:]
            cci_lon = ds0.variables['lon'][:]
            
        r_box = np.where((cci_lat >= lat_min - 0.15) & (cci_lat <= lat_max + 0.15))[0]
        c_box = np.where((cci_lon >= lon_min - 0.15) & (cci_lon <= lon_max + 0.15))[0]
        sub_lat = cci_lat[r_box]
        sub_lon = cci_lon[c_box]
        
        for f in f_esacci:
            with nc.Dataset(f) as ds:
                sm = ds.variables['sm'][0, r_box[0]:r_box[-1]+1, c_box[0]:c_box[-1]+1]
                sm_val = np.where((sm >= 0.0) & (sm <= 1.0), sm, np.nan)
                
            # Interp à 5 km
            from scipy.interpolate import RegularGridInterpolator
            # Décroissant en lat si cci_lat descend
            if sub_lat[0] > sub_lat[-1]:
                interp = RegularGridInterpolator((sub_lat[::-1], sub_lon), sm_val[::-1, :], bounds_error=False, fill_value=np.nan)
            else:
                interp = RegularGridInterpolator((sub_lat, sub_lon), sm_val, bounds_error=False, fill_value=np.nan)
                
            pts = np.stack([lat.ravel(), lon.ravel()], axis=-1)
            sm_5k = interp(pts).reshape(lat.shape)
            
            v = land_bool & np.isfinite(sm_5k)
            esacci_sum[v] += sm_5k[v]
            esacci_cnt[v] += 1
            
    esacci_mean = np.full((121, 181), np.nan)
    v_cci = esacci_cnt >= 5
    esacci_mean[v_cci] = esacci_sum[v_cci] / esacci_cnt[v_cci]
    print(f"Pixels qualifiés avec au moins 5 obs ESA CCI : {np.sum(v_cci & non_forest)}")
    
    # 2. ASCAT SWI
    f_ascat = sorted(glob.glob(f"{DIR_ASCAT}/c_gls_SWI_20180[78]*_nc"))
    print(f"Fichiers ASCAT SWI disponibles pour JA 2018 : {len(f_ascat)} fichiers journaliers.")
    
    ascat_sum = np.zeros((121, 181), dtype=float)
    ascat_cnt = np.zeros((121, 181), dtype=int)
    
    if f_ascat:
        with nc.Dataset(f_ascat[0]) as ds0:
            a_lat = ds0.variables['lat'][:]
            a_lon = ds0.variables['lon'][:]
            
        r_box_a = np.where((a_lat >= lat_min - 0.15) & (a_lat <= lat_max + 0.15))[0]
        c_box_a = np.where((a_lon >= lon_min - 0.15) & (a_lon <= lon_max + 0.15))[0]
        sub_lat_a = a_lat[r_box_a]
        sub_lon_a = a_lon[c_box_a]
        
        for f in f_ascat:
            with nc.Dataset(f) as ds:
                # SWI_001 ou SWI_005 (T-value = 1 jour ou 5 jours, SWI_001 = humidité superficielle ~1-2 cm)
                varname = 'SWI_001' if 'SWI_001' in ds.variables else 'SWI_005'
                swi = ds.variables[varname][0, r_box_a[0]:r_box_a[-1]+1, c_box_a[0]:c_box_a[-1]+1]
                # Le SWI est en % d'indice de saturation (0-100%)
                swi_val = np.where((swi >= 0.0) & (swi <= 100.0), swi, np.nan)
                
            if sub_lat_a[0] > sub_lat_a[-1]:
                interp_a = RegularGridInterpolator((sub_lat_a[::-1], sub_lon_a), swi_val[::-1, :], bounds_error=False, fill_value=np.nan)
            else:
                interp_a = RegularGridInterpolator((sub_lat_a, sub_lon_a), swi_val, bounds_error=False, fill_value=np.nan)
                
            pts = np.stack([lat.ravel(), lon.ravel()], axis=-1)
            swi_5k = interp_a(pts).reshape(lat.shape)
            
            v = land_bool & np.isfinite(swi_5k)
            ascat_sum[v] += swi_5k[v]
            ascat_cnt[v] += 1
            
    ascat_mean = np.full((121, 181), np.nan)
    v_asc = ascat_cnt >= 5
    ascat_mean[v_asc] = ascat_sum[v_asc] / ascat_cnt[v_asc]
    print(f"Pixels qualifiés avec au moins 5 obs ASCAT : {np.sum(v_asc & non_forest)}")
    
    # Récupération de SMAP et OL pour JA 2018
    # Calcul des moyennes JA 2018 par texture
    print("\nTableau comparatif par texture dominante (Juillet-Août 2018) :")
    print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'SMAP brut (m3)':<15} | {'OL couche1 (m3)':<16} | {'ESA CCI (m3)':<15} | {'ASCAT SWI (%)':<15}")
    print("-" * 95)
    
    for c in [1, 3, 4, 6, 7, 9, 12]:
        m_c = non_forest & (soiltype == c)
        if np.sum(m_c) == 0: continue
        
        # OL JA 2018
        ol_v = sm_c_mean[0][m_c]
        
        # ESA CCI JA 2018
        m_cci = m_c & np.isfinite(esacci_mean)
        cci_v = np.mean(esacci_mean[m_cci]) if np.sum(m_cci) > 0 else np.nan
        
        # ASCAT SWI JA 2018
        m_asc = m_c & np.isfinite(ascat_mean)
        asc_v = np.mean(ascat_mean[m_asc]) if np.sum(m_asc) > 0 else np.nan
        
        name = TEXTURE_NAMES.get(c, "Inconnu")
        print(f"{c:<4} | {name:<16} | {np.sum(m_c):<6} | [voir diag]     | {np.mean(ol_v):15.4f}  | {cci_v:15.4f}  | {asc_v:14.1f}%")
        
    print("-" * 95)
    all_ol = np.mean(sm_c_mean[0][non_forest])
    all_cci = np.mean(esacci_mean[non_forest & np.isfinite(esacci_mean)])
    all_asc = np.mean(ascat_mean[non_forest & np.isfinite(ascat_mean)])
    print(f"{'ALL':<4} | {'Ensemble':<16} | {np.sum(non_forest):<6} | [voir diag]     | {all_ol:15.4f}  | {all_cci:15.4f}  | {all_asc:14.1f}%")

if __name__ == "__main__":
    main()
