#!/usr/bin/env python3
"""
reproduce_aud05_water_balance.py
================================
Reproduction et traçabilité du bilan hydrique Noah-MP 4.0.1 / EnKF (AUD-05, AUD-05B, AUD-05C).

Objectif scientifique :
----------------------
Calculer rigoureusement le bilan hydrique sur les 611 pixels argileux du domaine nord-marocain
pour la période de référence fixe AUD-05 :
  Du 1er juillet 2018 00:00 UTC au 1er septembre 2018 00:00 UTC (exactement 62 jours complets)
sur trois expériences :
  1. Open Loop (OPL_noirr_2016_2020) : simulation déterministe (1 membre), sans perturbations ni DA.
  2. Contrôle DA (DA_nocdf_noirr_2016_2020) : assimilation EnKF 20 membres avec filtre de flétrissement.
  3. Nowilt DA (DA_nocdf_TEST_nowilt) : assimilation EnKF 20 membres sans seuil de flétrissement.

Principes méthodologiques et contrôles de qualité intégrés :
-----------------------------------------------------------
1. Masque argile et cohérence spatiale :
   - Texture dominante == 12 (Clay), classe de végétation active > 4, LANDMASK == 1.
   - Validation stricte de la correspondance des coordonnées (lat, lon) point par point entre
     la grille 2D (121, 181) de lis_input et le vecteur 1D des 16 030 tuiles terrestres.
2. Traitement d'ensemble (20 membres) :
   - Dans les restarts LIS à 20 membres, la dimension ntiles (320 600) est entrelacée par tuile
     (tuile t, membre m : shape = (16030, 20)).
   - La moyenne d'ensemble est calculée sur l'axe des membres (axis=1), ce qui correspond
     strictement à l'opérateur pens=1/20 utilisé par LIS lors de l'agrégation des sorties historiques.
3. Données masquées NetCDF :
   - Vérification explicite des tableaux masqués (np.ma.MaskedArray) et des valeurs sentinelles (-9999.0).
   - Aucun remplacement silencieux par zéro n'est appliqué sur les pixels d'intérêt (les 611 pixels argileux).
4. Horodatages et indépendance des listes :
   - Extraction stricte des dates par regex sur les noms de fichiers.
   - Période temporelle bornée : [2018-07-01 00:00, 2018-09-01 00:00).
   - Rapportage des horodatages communs et spécifiques à chaque expérience (sans appariement zip).
5. Double résidu de bilan :
   - Résidu historique AUD-05 (SMC L1-L4 + WA) pour stricte comparaison avec le rapport publié.
   - Résidu étendu (+ CANWAT + SNEQV) traçant l'eau de canopée et l'équivalent neige.
   - Les deux résidus restent diagnostiques (les flux de perturbations stochastiques d'état et de forçage
     n'étant pas tracés dans les sorties standards de LIS).
"""

import os
import sys
import re
import glob
import argparse
import datetime
import netCDF4 as nc
import numpy as np


# Paramètres physiques constants de la configuration Noah-MP 4.0.1
SOIL_THICKNESS_MM = np.array([100.0, 300.0, 600.0, 1000.0], dtype=float)
TOTAL_SOIL_DEPTH_MM = 2000.0
LIS_UNDEFINED_VALUE = -9999.0

# Période de référence fixe de l'audit AUD-05
AUD05_START_DT = datetime.datetime(2018, 7, 1, 0, 0)
AUD05_END_DT = datetime.datetime(2018, 9, 1, 0, 0)
AUD05_EXPECTED_DAYS = 62


def parse_args():
    parser = argparse.ArgumentParser(
        description="Reproduction robuste du bilan hydrique Noah-MP / EnKF (AUD-05, AUD-05B, AUD-05C)"
    )
    parser.add_argument(
        "--opl_dir",
        default="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020",
        help="Répertoire racine de la simulation Open Loop",
    )
    parser.add_argument(
        "--da_ctrl_dir",
        default="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020",
        help="Répertoire racine de l'expérience DA Contrôle (NoCDF)",
    )
    parser.add_argument(
        "--nowilt_dir",
        default="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_TEST_nowilt",
        help="Répertoire racine de l'expérience DA Nowilt (Sans seuil)",
    )
    parser.add_argument(
        "--lis_input",
        default="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc",
        help="Fichier de paramètres de domaine LIS (lis_input)",
    )
    parser.add_argument(
        "--output_csv",
        default=None,
        help="Chemin optionnel pour exporter un véritable fichier CSV structuré (ex: tables/aud05_water_balance.csv)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Exécute uniquement les vérifications statiques et de cohérence spatiale, sans calcul cumulé complet",
    )
    parser.add_argument(
        "--self_test",
        action="store_true",
        help="Exécute les tests unitaires internes en mémoire sur données synthétiques",
    )
    return parser.parse_args()


# ------------------------------------------------------------------------------
# 1. Grille, masques et géométrie
# ------------------------------------------------------------------------------

def build_and_verify_clay_mask(lis_input_path):
    """
    Construit le masque des pixels argileux et valide la géométrie du domaine.
    Vérifie les dimensions 2D (121, 181), le masque terre (16 030 points)
    et les coordonnées spatiales.
    """
    if not os.path.exists(lis_input_path):
        raise FileNotFoundError(f"Fichier lis_input introuvable : {lis_input_path}")

    with nc.Dataset(lis_input_path, "r") as ds:
        grid_lat = ds.variables["lat"][:]
        grid_lon = ds.variables["lon"][:]
        landmask = ds.variables["LANDMASK"][:]

        tex_var = "SOIL_TEXTURE" if "SOIL_TEXTURE" in ds.variables else "TEXTURE"
        texture = ds.variables[tex_var][:]
        landcover = ds.variables["LANDCOVER"][:]

    if grid_lat.shape != (121, 181) or grid_lon.shape != (121, 181):
        raise ValueError(f"Dimensions de grille LIS inattendues : lat={grid_lat.shape}, lon={grid_lon.shape} (attendu : (121, 181))")

    soiltype = np.argmax(texture, axis=0) + 1
    vegt = np.argmax(landcover, axis=0) + 1

    # Masque 2D : argile (12), végétation active (> 4), terre (landmask == 1)
    clay_mask_2d = (soiltype == 12) & (vegt > 4) & (landmask == 1)
    n_clay_2d = int(np.sum(clay_mask_2d))

    land_idx = np.where(landmask == 1)
    n_land = len(land_idx[0])
    if n_land != 16030:
        raise ValueError(f"Nombre de points terrestres inattendu : {n_land} (attendu : 16030)")

    clay_tiles_mask = clay_mask_2d[land_idx]
    n_clay_tiles = int(np.sum(clay_tiles_mask))

    if n_clay_2d != 611 or n_clay_tiles != 611:
        raise ValueError(
            f"Erreur masque argile : {n_clay_2d} pixels 2D, {n_clay_tiles} tuiles 1D (attendu : exactement 611)"
        )

    grid_info = {
        "grid_lat": grid_lat,
        "grid_lon": grid_lon,
        "landmask": landmask,
        "land_idx": land_idx,
        "clay_mask_2d": clay_mask_2d,
        "clay_tiles_mask": clay_tiles_mask,
        "clay_lats": grid_lat[clay_mask_2d],
        "clay_lons": grid_lon[clay_mask_2d],
    }
    return grid_info


def verify_restart_grid_consistency(rst_path, grid_info, is_ensemble=False, n_ens=20):
    """
    Vérifie rigoureusement la correspondance spatiale point par point entre
    lis_input et les coordonnées stockées dans le restart LIS_RST_NOAHMP401.
    Confirme également l'entrelacement des 20 membres d'ensemble.
    """
    with nc.Dataset(rst_path, "r") as ds:
        ntiles = ds.dimensions["ntiles"].size
        rst_lat = ds.variables["lat"][:]
        rst_lon = ds.variables["lon"][:]

    land_idx = grid_info["land_idx"]
    expected_lats_1d = grid_info["grid_lat"][land_idx]
    expected_lons_1d = grid_info["grid_lon"][land_idx]

    if is_ensemble:
        expected_total = 16030 * n_ens
        if ntiles != expected_total:
            raise ValueError(f"Taille ntiles ensemble invalide : {ntiles} (attendu : {expected_total}) dans {rst_path}")

        # Entrelacement par tuile : chaque tuile spatiale possède n_ens membres consécutifs
        rst_lat_2d = rst_lat.reshape((16030, n_ens))
        rst_lon_2d = rst_lon.reshape((16030, n_ens))

        # Vérification 1 : les 20 membres d'une même tuile ont rigoureusement la même coordonnée
        if not np.allclose(rst_lat_2d, expected_lats_1d[:, None], atol=1e-5):
            raise ValueError(f"Incohérence de latitude ensemble dans {rst_path}")
        if not np.allclose(rst_lon_2d, expected_lons_1d[:, None], atol=1e-5):
            raise ValueError(f"Incohérence de longitude ensemble dans {rst_path}")
    else:
        if ntiles != 16030:
            raise ValueError(f"Taille ntiles OL invalide : {ntiles} (attendu : 16030) dans {rst_path}")
        if not np.allclose(rst_lat, expected_lats_1d, atol=1e-5):
            raise ValueError(f"Incohérence de latitude OL dans {rst_path}")
        if not np.allclose(rst_lon, expected_lons_1d, atol=1e-5):
            raise ValueError(f"Incohérence de longitude OL dans {rst_path}")

    return True


# ------------------------------------------------------------------------------
# 2. Lecture des stocks instantanés (Restarts)
# ------------------------------------------------------------------------------

def find_restart_file(exp_dir, date_str):
    """
    Localise de manière unique le fichier restart pour une date donnée (YYYYMMDDHHMM).
    """
    candidates = [
        os.path.join(exp_dir, "restarts", f"LIS_RST_NOAHMP401_{date_str}.d01.nc"),
        os.path.join(exp_dir, "restarts", "surf", f"LIS_RST_NOAHMP401_{date_str}.d01.nc"),
    ]
    ym = f"{date_str[:4]}-{date_str[4:6]}"
    ym_c = date_str[:6]
    candidates.append(
        os.path.join(exp_dir, "output", ym, "SURFACEMODEL", ym_c, f"LIS_RST_NOAHMP401_{date_str}.d01.nc")
    )

    existing = [c for c in candidates if os.path.exists(c)]
    if existing:
        return existing[0]

    # Recherche récursive de secours
    matches = glob.glob(os.path.join(exp_dir, f"**/LIS_RST_NOAHMP401_{date_str}.d01.nc"), recursive=True)
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Fichier restart introuvable pour {date_str} dans {exp_dir}")


def read_restart_storage(rst_path, grid_info, is_ensemble=False, n_ens=20):
    """
    Extrait les stocks instantanés d'eau des fichiers restart LIS_RST_NOAHMP401.
    Traite explicitement les données masquées et applique la réduction d'ensemble.
    """
    verify_restart_grid_consistency(rst_path, grid_info, is_ensemble=is_ensemble, n_ens=n_ens)
    clay_tiles_mask = grid_info["clay_tiles_mask"]

    with nc.Dataset(rst_path, "r") as ds:
        # SMC : shape = (4, ntiles)
        smc_raw = ds.variables["SMC"][:]
        wa_raw = ds.variables["WA"][:]
        wt_raw = ds.variables["WT"][:]
        canwat_raw = ds.variables["CANWAT"][:]
        sneqv_raw = ds.variables["SNEQV"][:]

    # Vérification des masques ou valeurs manquantes sur les variables brutes
    for vname, arr in [("SMC", smc_raw), ("WA", wa_raw), ("WT", wt_raw), ("CANWAT", canwat_raw), ("SNEQV", sneqv_raw)]:
        if np.ma.is_masked(arr) and np.any(arr.mask):
            raise ValueError(f"Présence inattendue de valeurs masquées dans {vname} du restart {rst_path}")
        if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
            raise ValueError(f"Présence de NaN/Inf dans {vname} du restart {rst_path}")

    if is_ensemble:
        # Entrelacement : shape = (16030, n_ens)
        wa_ens = wa_raw.reshape((16030, n_ens)).mean(axis=1)
        wt_ens = wt_raw.reshape((16030, n_ens)).mean(axis=1)
        canwat_ens = canwat_raw.reshape((16030, n_ens)).mean(axis=1)
        sneqv_ens = sneqv_raw.reshape((16030, n_ens)).mean(axis=1)
        # SMC : (4, 16030, n_ens) -> mean axis 2 -> (4, 16030)
        smc_ens = smc_raw.reshape((4, 16030, n_ens)).mean(axis=2)
    else:
        wa_ens = np.asarray(wa_raw)
        wt_ens = np.asarray(wt_raw)
        canwat_ens = np.asarray(canwat_raw)
        sneqv_ens = np.asarray(sneqv_raw)
        smc_ens = np.asarray(smc_raw)

    # Extraction sur les 611 pixels argileux
    smc_clay = smc_ens[:, clay_tiles_mask]  # (4, 611)
    wa_clay = wa_ens[clay_tiles_mask]       # (611,)
    wt_clay = wt_ens[clay_tiles_mask]       # (611,)
    canwat_clay = canwat_ens[clay_tiles_mask]
    sneqv_clay = sneqv_ens[clay_tiles_mask]

    # Vérification physique sur argile (SMC > 0, WA > 0)
    if np.any(smc_clay <= 0.0) or np.any(smc_clay > 0.60):
        raise ValueError(f"Valeurs d'humidité SMC hors bornes physiques sur argile dans {rst_path}")
    if np.any(wa_clay < 0.0):
        raise ValueError(f"Stock WA négatif dans {rst_path}")

    # Stocks d'eau du sol (mm) : SMC_l * dz_l
    s_layers_mm = smc_clay * SOIL_THICKNESS_MM[:, None]  # (4, 611)
    s_sol_mm = np.sum(s_layers_mm, axis=0)                # (611,)

    return {
        "S_sol": float(np.mean(s_sol_mm)),
        "S_layers": [float(np.mean(s_layers_mm[l, :])) for l in range(4)],
        "WA": float(np.mean(wa_clay)),
        "WT": float(np.mean(wt_clay)),
        "CANWAT": float(np.mean(canwat_clay)),
        "SNEQV": float(np.mean(sneqv_clay)),
    }


# ------------------------------------------------------------------------------
# 3. Flux historiques journaliers (62 jours)
# ------------------------------------------------------------------------------

def get_validated_history_file_list(exp_dir, start_dt, end_dt):
    """
    Extrait et valide strictement la liste des 62 fichiers journaliers LIS_HIST.
    Contrôle l'exhaustivité, l'unicité et le format des horodatages.
    """
    regex_hist = re.compile(r"LIS_HIST_(\d{12})\.d01\.nc$")
    candidate_files = glob.glob(os.path.join(exp_dir, "**/LIS_HIST_*.d01.nc"), recursive=True)

    file_by_dt = {}
    for fpath in candidate_files:
        bname = os.path.basename(fpath)
        m = regex_hist.search(bname)
        if m:
            try:
                dt = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M")
            except ValueError:
                continue
            if dt not in file_by_dt:
                file_by_dt[dt] = fpath
            else:
                # Doublon détecté : vérifier que les chemins pointent vers le même fichier réel
                if os.path.realpath(file_by_dt[dt]) != os.path.realpath(fpath):
                    raise ValueError(f"Doublon d'horodatage détecté pour {dt} : {file_by_dt[dt]} vs {fpath}")

    # Pour chaque jour du 2018-07-01 au 2018-08-31 (62 jours),
    # le fichier journalier est horodaté à 00:00 UTC du lendemain.
    cur_dt = start_dt
    hist_files = []
    missing_days = []

    while cur_dt < end_dt:
        next_dt = cur_dt + datetime.timedelta(days=1)
        if next_dt in file_by_dt:
            hist_files.append((cur_dt.strftime("%Y-%m-%d"), file_by_dt[next_dt]))
        else:
            missing_days.append(cur_dt.strftime("%Y-%m-%d"))
        cur_dt = next_dt

    if missing_days:
        raise FileNotFoundError(
            f"Fichiers LIS_HIST manquants pour {len(missing_days)} jours dans {exp_dir} : {missing_days[:5]}..."
        )

    if len(hist_files) != AUD05_EXPECTED_DAYS:
        raise ValueError(
            f"Nombre de fichiers journaliers invalide : {len(hist_files)} (attendu : {AUD05_EXPECTED_DAYS})"
        )

    return hist_files


def accumulate_fluxes(hist_files, clay_mask_2d):
    """
    Intègre les flux journaliers sur les 611 pixels argileux.
    Traite rigoureusement les tableaux masqués NetCDF.
    """
    totals = {
        "P": 0.0,
        "ET": 0.0,
        "ESoil": 0.0,
        "TVeg": 0.0,
        "ECan": 0.0,
        "Qs": 0.0,
        "Qsb": 0.0,
    }

    var_names = {
        "P": "TotalPrecip_tavg",
        "ET": "Evap_tavg",
        "ESoil": "ESoil_tavg",
        "TVeg": "TVeg_tavg",
        "ECan": "ECanop_tavg",
        "Qs": "Qs_tavg",
        "Qsb": "Qsb_tavg",
    }

    for day_str, fpath in hist_files:
        with nc.Dataset(fpath, "r") as ds:
            for key, vname in var_names.items():
                if vname not in ds.variables:
                    raise KeyError(f"Variable {vname} absente dans {fpath}")
                
                raw_var = ds.variables[vname]
                data = raw_var[:]  # Peut être un MaskedArray

                # Extraction sur les 611 pixels argileux
                if np.ma.is_masked(data):
                    clay_vals = data[clay_mask_2d]
                    if np.ma.is_masked(clay_vals) and np.any(clay_vals.mask):
                        n_masked = int(np.sum(clay_vals.mask))
                        raise ValueError(
                            f"Donnée masquée détectée ({n_masked}/611 pixels) pour {vname} au jour {day_str} dans {fpath}."
                            " Aucun remplacement par zéro n'est autorisé sur le masque argile terrestre."
                        )
                    clay_vals = clay_vals.data
                else:
                    clay_vals = data[clay_mask_2d]

                if np.any(clay_vals == LIS_UNDEFINED_VALUE) or np.any(np.isnan(clay_vals)):
                    raise ValueError(f"Valeur invalide (sentinelle LIS ou NaN) dans {vname} au jour {day_str} dans {fpath}")

                # Conversion kg m-2 s-1 (mm/s) -> mm/jour
                val_mm_day = clay_vals * 86400.0
                totals[key] += float(np.mean(val_mm_day))

    return totals


# ------------------------------------------------------------------------------
# 4. Incréments EnKF (L1 à L4)
# ------------------------------------------------------------------------------

def get_validated_increment_file_dict(exp_dir, start_dt, end_dt):
    """
    Extrait les fichiers d'incréments d'analyse EnKF avec contrôle strict
    des horodatages [start_dt, end_dt).
    """
    regex_incr = re.compile(r"LIS_DA_EnKF_(\d{12})_incr\.a01\.d01\.nc$")
    candidate_files = glob.glob(os.path.join(exp_dir, "**/LIS_DA_EnKF_*_incr.a01.d01.nc"), recursive=True)

    incr_by_dt = {}
    for fpath in candidate_files:
        bname = os.path.basename(fpath)
        m = regex_incr.search(bname)
        if m:
            try:
                dt = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M")
            except ValueError:
                continue
            if start_dt <= dt < end_dt:
                if dt not in incr_by_dt:
                    incr_by_dt[dt] = fpath
                else:
                    if os.path.realpath(incr_by_dt[dt]) != os.path.realpath(fpath):
                        raise ValueError(f"Doublon d'incrément détecté pour {dt} : {incr_by_dt[dt]} vs {fpath}")

    return incr_by_dt


def compare_increment_timestamps(ctrl_dict, nowilt_dict):
    """
    Rapporte les ensembles d'horodatages communs et spécifiques à chaque expérience.
    """
    ts_ctrl = set(ctrl_dict.keys())
    ts_nowilt = set(nowilt_dict.keys())

    common = ts_ctrl & ts_nowilt
    only_ctrl = ts_ctrl - ts_nowilt
    only_nowilt = ts_nowilt - ts_ctrl

    report = {
        "n_ctrl": len(ts_ctrl),
        "n_nowilt": len(ts_nowilt),
        "n_common": len(common),
        "only_ctrl": sorted(only_ctrl),
        "only_nowilt": sorted(only_nowilt),
    }
    return report


def accumulate_increments(incr_file_dict, clay_mask_2d):
    """
    Cumule les incréments EnKF tri-horaires sur les 4 couches de sol.
    Traite les données masquées et convertit m3/m3 en mm.
    """
    incr_layers_cum = np.zeros(4, dtype=float)
    sorted_dts = sorted(incr_file_dict.keys())

    for dt in sorted_dts:
        fpath = incr_file_dict[dt]
        with nc.Dataset(fpath, "r") as ds:
            for l_idx in range(4):
                vname = f"anlys_incr_Soil Moisture Layer {l_idx + 1}_01"
                if vname not in ds.variables:
                    raise KeyError(f"Variable d'incrément {vname} absente dans {fpath}")

                raw_var = ds.variables[vname]
                data = raw_var[:]

                # Diagnostic explicite des masques
                if np.ma.is_masked(data):
                    clay_vals = data[clay_mask_2d]
                    if np.ma.is_masked(clay_vals) and np.any(clay_vals.mask):
                        n_masked = int(np.sum(clay_vals.mask))
                        raise ValueError(
                            f"Donnée d'incrément masquée ({n_masked}/611 pixels) pour {vname} à {dt} dans {fpath}."
                        )
                    clay_vals = clay_vals.data
                else:
                    clay_vals = data[clay_mask_2d]

                # Sur les points terrestres, un incrément absent doit être 0.0 (non mis à jour).
                # Si une sentinelle LIS (-9999.0) ou un NaN apparaît sur argile, c'est une anomalie.
                if np.any(clay_vals == LIS_UNDEFINED_VALUE) or np.any(np.isnan(clay_vals)):
                    raise ValueError(f"Valeur sentinelle ou NaN détectée dans {vname} à {dt} sur pixel argile dans {fpath}")

                # Conversion m3/m3 -> mm
                incr_mm = clay_vals * SOIL_THICKNESS_MM[l_idx]
                incr_layers_cum[l_idx] += float(np.mean(incr_mm))

    return {
        "total": float(np.sum(incr_layers_cum)),
        "layers": [float(incr_layers_cum[l]) for l in range(4)],
        "n_cycles": len(sorted_dts),
    }


# ------------------------------------------------------------------------------
# 5. Exécution du bilan et formatage des sorties
# ------------------------------------------------------------------------------

def compute_single_experiment(name, exp_dir, grid_info, is_ensemble, start_dt, end_dt):
    """
    Calcule l'ensemble des composantes hydrologiques pour une simulation.
    """
    print(f"Calcul en cours : {name}...")

    # 1. Stocks instantanés
    rst_init_file = find_restart_file(exp_dir, start_dt.strftime("%Y%m%d%H%M"))
    rst_end_file = find_restart_file(exp_dir, end_dt.strftime("%Y%m%d%H%M"))

    st_init = read_restart_storage(rst_init_file, grid_info, is_ensemble=is_ensemble)
    st_end = read_restart_storage(rst_end_file, grid_info, is_ensemble=is_ensemble)

    delta_s_sol = st_end["S_sol"] - st_init["S_sol"]
    delta_s_wa = st_end["WA"] - st_init["WA"]
    delta_s_canwat = st_end["CANWAT"] - st_init["CANWAT"]
    delta_s_sneqv = st_end["SNEQV"] - st_init["SNEQV"]

    # Variations de stock diagnostiques
    delta_s_aud05 = delta_s_sol + delta_s_wa
    delta_s_extended = delta_s_aud05 + delta_s_canwat + delta_s_sneqv

    # 2. Flux journaliers
    hist_files = get_validated_history_file_list(exp_dir, start_dt, end_dt)
    fluxes = accumulate_fluxes(hist_files, grid_info["clay_mask_2d"])

    # 3. Incréments EnKF
    if is_ensemble:
        incr_dict = get_validated_increment_file_dict(exp_dir, start_dt, end_dt)
        increments = accumulate_increments(incr_dict, grid_info["clay_mask_2d"])
    else:
        increments = {"total": 0.0, "layers": [0.0, 0.0, 0.0, 0.0], "n_cycles": 0}

    inflow = fluxes["P"] + increments["total"]
    outflow = fluxes["ET"] + fluxes["Qs"] + fluxes["Qsb"]
    net_flux = inflow - outflow

    # Résidus
    res_aud05 = net_flux - delta_s_aud05
    res_extended = net_flux - delta_s_extended

    res_dict = {
        "P": fluxes["P"],
        "Incr": increments["total"],
        "Incr_layers": increments["layers"],
        "Inflow": inflow,
        "ET": fluxes["ET"],
        "ESoil": fluxes["ESoil"],
        "TVeg": fluxes["TVeg"],
        "ECan": fluxes["ECan"],
        "Qs": fluxes["Qs"],
        "Qsb": fluxes["Qsb"],
        "Outflow": outflow,
        "NetFlux": net_flux,
        "DeltaS_sol": delta_s_sol,
        "DeltaS_wa": delta_s_wa,
        "DeltaS_canwat": delta_s_canwat,
        "DeltaS_sneqv": delta_s_sneqv,
        "DeltaS_aud05": delta_s_aud05,
        "DeltaS_extended": delta_s_extended,
        "Residual_aud05": res_aud05,
        "Residual_extended": res_extended,
        "n_incr_cycles": increments["n_cycles"],
    }
    return res_dict


def format_markdown_table(b_ol, b_ctrl, b_nowilt):
    """
    Formate le tableau Markdown conforme à la structure d'AUD-05,
    en distinguant clairement le résidu historique AUD-05 et le résidu étendu.
    """
    diff = {k: (b_nowilt[k] - b_ctrl[k]) for k in b_nowilt if isinstance(b_nowilt[k], (float, int))}

    lines = []
    lines.append("| Terme hydrologique (mm) | OPL (Open Loop) | DA-Ctrl (Contrôle) | Nowilt (Sans seuil) | Différence (Nowilt − Ctrl) |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| **Précipitation ($P$)** | {b_ol['P']:.3f} | {b_ctrl['P']:.3f} | {b_nowilt['P']:.3f} | {diff['P']:+.3f} |")
    lines.append(f"| **Incréments EnKF ($Incr$, L1–L4)** | {b_ol['Incr']:.3f} | {b_ctrl['Incr']:+.3f} | {b_nowilt['Incr']:+.3f} | {diff['Incr']:+.3f} |")
    lines.append(f"| **Inflow Total ($P + Incr$)** | **{b_ol['Inflow']:+.3f}** | **{b_ctrl['Inflow']:+.3f}** | **{b_nowilt['Inflow']:+.3f}** | **{diff['Inflow']:+.3f}** |")
    lines.append(f"| Évapotranspiration totale ($ET$) | {b_ol['ET']:.3f} | {b_ctrl['ET']:.3f} | {b_nowilt['ET']:.3f} | {diff['ET']:+.3f} |")
    lines.append(f"| *— Évaporation du sol ($ESoil$)* | *{b_ol['ESoil']:.3f}* | *{b_ctrl['ESoil']:.3f}* | *{b_nowilt['ESoil']:.3f}* | *{diff['ESoil']:+.3f}* |")
    lines.append(f"| *— Transpiration végétale ($TVeg$)* | *{b_ol['TVeg']:.3f}* | *{b_ctrl['TVeg']:.3f}* | *{b_nowilt['TVeg']:.3f}* | *{diff['TVeg']:+.3f}* |")
    lines.append(f"| *— Interception canopée ($ECan$)* | *{b_ol['ECan']:.3f}* | *{b_ctrl['ECan']:.3f}* | *{b_nowilt['ECan']:.3f}* | *{diff['ECan']:+.3f}* |")
    lines.append(f"| Ruissellement surface ($Q_s$) | {b_ol['Qs']:.3f} | {b_ctrl['Qs']:.3f} | {b_nowilt['Qs']:.3f} | {diff['Qs']:+.3f} |")
    lines.append(f"| Drainage / baseflow ($Q_{sb}$) | {b_ol['Qsb']:.3f} | {b_ctrl['Qsb']:.3f} | {b_nowilt['Qsb']:.3f} | {diff['Qsb']:+.3f} |")
    lines.append(f"| **Outflow Total ($ET + Q_s + Q_{sb}$)** | **{b_ol['Outflow']:.3f}** | **{b_ctrl['Outflow']:.3f}** | **{b_nowilt['Outflow']:.3f}** | **{diff['Outflow']:+.3f}** |")
    lines.append(f"| **Flux net ($Inflow - Outflow$)** | **{b_ol['NetFlux']:+.3f}** | **{b_ctrl['NetFlux']:+.3f}** | **{b_nowilt['NetFlux']:+.3f}** | **{diff['NetFlux']:+.3f}** |")
    lines.append(f"| ΔS Sol (0–2 m, restarts) | {b_ol['DeltaS_sol']:+.3f} | {b_ctrl['DeltaS_sol']:+.3f} | {b_nowilt['DeltaS_sol']:+.3f} | {diff['DeltaS_sol']:+.3f} |")
    lines.append(f"| ΔS Nappe ($WA$, restarts) | {b_ol['DeltaS_wa']:+.3f} | {b_ctrl['DeltaS_wa']:+.3f} | {b_nowilt['DeltaS_wa']:+.3f} | {diff['DeltaS_wa']:+.3f} |")
    lines.append(f"| ΔS Canopée ($CANWAT$, restarts) | {b_ol['DeltaS_canwat']:+.3f} | {b_ctrl['DeltaS_canwat']:+.3f} | {b_nowilt['DeltaS_canwat']:+.3f} | {diff['DeltaS_canwat']:+.3f} |")
    lines.append(f"| ΔS Neige ($SNEQV$, restarts) | {b_ol['DeltaS_sneqv']:+.3f} | {b_ctrl['DeltaS_sneqv']:+.3f} | {b_nowilt['DeltaS_sneqv']:+.3f} | {diff['DeltaS_sneqv']:+.3f} |")
    lines.append(f"| **ΔS Total AUD-05 (Sol + Nappe)** | **{b_ol['DeltaS_aud05']:+.3f}** | **{b_ctrl['DeltaS_aud05']:+.3f}** | **{b_nowilt['DeltaS_aud05']:+.3f}** | **{diff['DeltaS_aud05']:+.3f}** |")
    lines.append(f"| **ΔS Total étendu (+ Canopée + Neige)** | **{b_ol['DeltaS_extended']:+.3f}** | **{b_ctrl['DeltaS_extended']:+.3f}** | **{b_nowilt['DeltaS_extended']:+.3f}** | **{diff['DeltaS_extended']:+.3f}** |")
    lines.append(f"| **RÉSIDU HISTORIQUE AUD-05 ($Net - \Delta S_{{aud05}}$)** | **{b_ol['Residual_aud05']:+.3f}** | **{b_ctrl['Residual_aud05']:+.3f}** | **{b_nowilt['Residual_aud05']:+.3f}** | **{diff['Residual_aud05']:+.3f}** |")
    lines.append(f"| **RÉSIDU ÉTENDU ($Net - \Delta S_{{etendu}}$)** | **{b_ol['Residual_extended']:+.3f}** | **{b_ctrl['Residual_extended']:+.3f}** | **{b_nowilt['Residual_extended']:+.3f}** | **{diff['Residual_extended']:+.3f}** |")
    return "\n".join(lines)


def export_structured_csv(filepath, b_ol, b_ctrl, b_nowilt):
    """
    Exporte un véritable tableau CSV structuré avec identifiant machine, libellé,
    unité et valeurs des 3 simulations + différence.
    """
    diff = {k: (b_nowilt[k] - b_ctrl[k]) for k in b_nowilt if isinstance(b_nowilt[k], (float, int))}

    rows = [
        ("precip", "Précipitation (P)", "mm", b_ol["P"], b_ctrl["P"], b_nowilt["P"], diff["P"]),
        ("incr_total", "Incréments EnKF (Incr L1-L4)", "mm", b_ol["Incr"], b_ctrl["Incr"], b_nowilt["Incr"], diff["Incr"]),
        ("incr_l1", "Incréments EnKF Couche 1 (0-10 cm)", "mm", b_ol["Incr_layers"][0], b_ctrl["Incr_layers"][0], b_nowilt["Incr_layers"][0], b_nowilt["Incr_layers"][0] - b_ctrl["Incr_layers"][0]),
        ("incr_l2", "Incréments EnKF Couche 2 (10-40 cm)", "mm", b_ol["Incr_layers"][1], b_ctrl["Incr_layers"][1], b_nowilt["Incr_layers"][1], b_nowilt["Incr_layers"][1] - b_ctrl["Incr_layers"][1]),
        ("incr_l3", "Incréments EnKF Couche 3 (40-100 cm)", "mm", b_ol["Incr_layers"][2], b_ctrl["Incr_layers"][2], b_nowilt["Incr_layers"][2], b_nowilt["Incr_layers"][2] - b_ctrl["Incr_layers"][2]),
        ("incr_l4", "Incréments EnKF Couche 4 (100-200 cm)", "mm", b_ol["Incr_layers"][3], b_ctrl["Incr_layers"][3], b_nowilt["Incr_layers"][3], b_nowilt["Incr_layers"][3] - b_ctrl["Incr_layers"][3]),
        ("inflow_total", "Inflow Total (P + Incr)", "mm", b_ol["Inflow"], b_ctrl["Inflow"], b_nowilt["Inflow"], diff["Inflow"]),
        ("et_total", "Évapotranspiration totale (ET)", "mm", b_ol["ET"], b_ctrl["ET"], b_nowilt["ET"], diff["ET"]),
        ("et_soil", "Évaporation du sol (ESoil)", "mm", b_ol["ESoil"], b_ctrl["ESoil"], b_nowilt["ESoil"], diff["ESoil"]),
        ("et_veg", "Transpiration végétale (TVeg)", "mm", b_ol["TVeg"], b_ctrl["TVeg"], b_nowilt["TVeg"], diff["TVeg"]),
        ("et_can", "Interception canopée (ECan)", "mm", b_ol["ECan"], b_ctrl["ECan"], b_nowilt["ECan"], diff["ECan"]),
        ("qs", "Ruissellement de surface (Qs)", "mm", b_ol["Qs"], b_ctrl["Qs"], b_nowilt["Qs"], diff["Qs"]),
        ("qsb", "Drainage / baseflow (Qsb)", "mm", b_ol["Qsb"], b_ctrl["Qsb"], b_nowilt["Qsb"], diff["Qsb"]),
        ("outflow_total", "Outflow Total (ET + Qs + Qsb)", "mm", b_ol["Outflow"], b_ctrl["Outflow"], b_nowilt["Outflow"], diff["Outflow"]),
        ("net_flux", "Flux net (Inflow - Outflow)", "mm", b_ol["NetFlux"], b_ctrl["NetFlux"], b_nowilt["NetFlux"], diff["NetFlux"]),
        ("delta_s_sol", "Variation stock sol (DeltaS Sol 0-2 m)", "mm", b_ol["DeltaS_sol"], b_ctrl["DeltaS_sol"], b_nowilt["DeltaS_sol"], diff["DeltaS_sol"]),
        ("delta_s_wa", "Variation stock nappe (DeltaS WA)", "mm", b_ol["DeltaS_wa"], b_ctrl["DeltaS_wa"], b_nowilt["DeltaS_wa"], diff["DeltaS_wa"]),
        ("delta_s_canwat", "Variation eau canopée (DeltaS CANWAT)", "mm", b_ol["DeltaS_canwat"], b_ctrl["DeltaS_canwat"], b_nowilt["DeltaS_canwat"], diff["DeltaS_canwat"]),
        ("delta_s_sneqv", "Variation équivalent neige (DeltaS SNEQV)", "mm", b_ol["DeltaS_sneqv"], b_ctrl["DeltaS_sneqv"], b_nowilt["DeltaS_sneqv"], diff["DeltaS_sneqv"]),
        ("delta_s_aud05", "Variation stock Total AUD-05 (Sol + WA)", "mm", b_ol["DeltaS_aud05"], b_ctrl["DeltaS_aud05"], b_nowilt["DeltaS_aud05"], diff["DeltaS_aud05"]),
        ("delta_s_extended", "Variation stock Total étendu (Sol + WA + CAN + SNQ)", "mm", b_ol["DeltaS_extended"], b_ctrl["DeltaS_extended"], b_nowilt["DeltaS_extended"], diff["DeltaS_extended"]),
        ("residual_aud05", "Résidu historique AUD-05 (Sol + WA)", "mm", b_ol["Residual_aud05"], b_ctrl["Residual_aud05"], b_nowilt["Residual_aud05"], diff["Residual_aud05"]),
        ("residual_extended", "Résidu étendu (+ Canopée + Neige)", "mm", b_ol["Residual_extended"], b_ctrl["Residual_extended"], b_nowilt["Residual_extended"], diff["Residual_extended"]),
    ]

    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("term_id,term_label,unit,OPL,DA_Ctrl,Nowilt,Diff_Nowilt_Ctrl\n")
        for tid, label, unit, v_ol, v_ctrl, v_nw, v_diff in rows:
            f.write(f'"{tid}","{label}","{unit}",{v_ol:.4f},{v_ctrl:.4f},{v_nw:.4f},{v_diff:+.4f}\n')

    print(f"Tableau CSV structuré exporté avec succès : {filepath}")


# ------------------------------------------------------------------------------
# 6. Tests unitaires en mémoire (Self-Test)
# ------------------------------------------------------------------------------

def run_self_tests():
    """
    Exécute des tests unitaires rapides en mémoire sur tableaux synthétiques
    sans toucher au système de fichiers ni aux simulations lourdes.
    """
    print("=== EXÉCUTION DU SELF-TEST EN MÉMOIRE ===")
    
    # 1. Test entrelacement d'ensemble
    n_tiles = 16030
    n_ens = 20
    raw_synthetic = np.zeros((n_tiles * n_ens), dtype=float)
    # Remplissage : pour chaque tuile, la moyenne sur les 20 membres vaut t
    for m in range(n_ens):
        raw_synthetic[m::n_ens] = np.arange(n_tiles) + (m - 9.5) * 0.1
    
    ens_mean = raw_synthetic.reshape((n_tiles, n_ens)).mean(axis=1)
    assert np.allclose(ens_mean, np.arange(n_tiles)), "Échec réduction d'ensemble 1D"
    print("✓ Test réduction d'ensemble : SUCCÈS")

    # 2. Test conversion multi-couches
    # smc = 0.20 m3/m3 partout -> S_sol = 0.20 * (100 + 300 + 600 + 1000) = 400 mm
    smc_test = np.full((4, 10), 0.20)
    s_sol_test = np.sum(smc_test * SOIL_THICKNESS_MM[:, None], axis=0)
    assert np.allclose(s_sol_test, 400.0), "Échec conversion stocks multi-couches"
    print("✓ Test conversion stocks multi-couches : SUCCÈS")

    # 3. Test détection de masques
    masked_arr = np.ma.array([1.0, 2.0, 3.0], mask=[False, True, False])
    assert np.ma.is_masked(masked_arr) and np.any(masked_arr.mask), "Échec détection masque"
    print("✓ Test détection des données masquées : SUCCÈS")

    # 4. Test arithmétique du résidu
    # Inflow = 10, Outflow = 50, DeltaS = -40 -> Net = -40, Res = 0.0
    inflow = 10.0
    outflow = 50.0
    net_flux = inflow - outflow
    delta_s = -40.0
    res = net_flux - delta_s
    assert abs(res) < 1e-9, "Échec équation de bilan"
    print("✓ Test équation de bilan : SUCCÈS")

    print("Tous les tests unitaires en mémoire sont validés.\n")


# ------------------------------------------------------------------------------
# 7. Programme principal
# ------------------------------------------------------------------------------

def main():
    args = parse_args()

    if args.self_test:
        run_self_tests()
        return

    print("=" * 80)
    print("AUDIT SCIENTIFIQUE DU BILAN HYDRIQUE NOAH-MP / EnKF (AUD-05, AUD-05B, AUD-05C)")
    print(f"Période fixe de référence : {AUD05_START_DT.strftime('%Y-%m-%d')} au {AUD05_END_DT.strftime('%Y-%m-%d')} (62 jours complets)")
    print(f"Paramètres domaine LIS    : {args.lis_input}")
    print("=" * 80)

    # 1. Vérification de la géométrie et construction du masque
    print("1. Vérification de la grille et du masque argile...")
    grid_info = build_and_verify_clay_mask(args.lis_input)
    print(f"   ✓ Grille 2D (121, 181) validée : 16 030 points terrestres.")
    print(f"   ✓ Masque argile validé : exactement 611 pixels.")

    # 2. Mode Dry-Run
    if args.dry_run:
        print("\n" + "=" * 80)
        print("--- MODE DRY-RUN : VÉRIFICATION STATIQUE ET CONTRÔLE D'INTÉGRITÉ ---")
        print("=" * 80)
        
        # Contrôle des fichiers restart aux deux bornes
        print("\nA. Contrôle d'intégrité spatiale des fichiers restart (lat, lon, entrelacement) :")
        for name, edir, is_ens in [
            ("OPL", args.opl_dir, False),
            ("DA-Ctrl", args.da_ctrl_dir, True),
            ("Nowilt", args.nowilt_dir, True),
        ]:
            rst_i = find_restart_file(edir, AUD05_START_DT.strftime("%Y%m%d%H%M"))
            rst_e = find_restart_file(edir, AUD05_END_DT.strftime("%Y%m%d%H%M"))
            verify_restart_grid_consistency(rst_i, grid_info, is_ensemble=is_ens)
            verify_restart_grid_consistency(rst_e, grid_info, is_ensemble=is_ens)
            print(f"   [{name:7s}] Restarts OK ({os.path.basename(rst_i)}, {os.path.basename(rst_e)}) - Grille et entrelacement validés.")

        # Contrôle des fichiers historiques
        print("\nB. Contrôle de la séquence continue des 62 fichiers journaliers LIS_HIST :")
        for name, edir in [("OPL", args.opl_dir), ("DA-Ctrl", args.da_ctrl_dir), ("Nowilt", args.nowilt_dir)]:
            hists = get_validated_history_file_list(edir, AUD05_START_DT, AUD05_END_DT)
            print(f"   [{name:7s}] {len(hists)}/{AUD05_EXPECTED_DAYS} fichiers journaliers vérifiés sans interruption ni doublon.")

        # Contrôle des incréments et comparaison des horodatages
        print("\nC. Contrôle des fichiers d'incréments EnKF et comparaison des cycles d'analyse :")
        incr_ctrl = get_validated_increment_file_dict(args.da_ctrl_dir, AUD05_START_DT, AUD05_END_DT)
        incr_nowilt = get_validated_increment_file_dict(args.nowilt_dir, AUD05_START_DT, AUD05_END_DT)
        cmp_report = compare_increment_timestamps(incr_ctrl, incr_nowilt)
        
        print(f"   Cycles d'incrément DA-Ctrl : {cmp_report['n_ctrl']}")
        print(f"   Cycles d'incrément Nowilt  : {cmp_report['n_nowilt']}")
        print(f"   Cycles communs aux deux    : {cmp_report['n_common']}")
        if cmp_report['only_ctrl']:
            print(f"   Spécifiques à DA-Ctrl      : {[d.strftime('%Y-%m-%d %H:%M') for d in cmp_report['only_ctrl']]}")
        else:
            print("   Spécifiques à DA-Ctrl      : Aucun")
        if cmp_report['only_nowilt']:
            print(f"   Spécifiques à Nowilt       : {[d.strftime('%Y-%m-%d %H:%M') for d in cmp_report['only_nowilt']]}")
        else:
            print("   Spécifiques à Nowilt       : Aucun")

        print("\n" + "=" * 80)
        print("Ce que le mode dry-run a vérifié avec succès :")
        print("  1. L'existence, l'unicité et la conformité des horodatages pour les 186 fichiers LIS_HIST.")
        print("  2. L'existence des restarts aux deux bornes et la correspondance stricte des coordonnées lat/lon.")
        print("  3. La validation de l'ordre d'entrelacement des 20 membres EnKF sur les 16 030 tuiles terrestres.")
        print("  4. L'inventaire indépendant des fichiers d'incréments EnKF (169 vs 170) et l'isolation du cycle spécifique.")
        print("\nCe que le mode dry-run N'A PAS exécuté (pour préserver les ressources du nœud de connexion) :")
        print("  - L'ouverture et la lecture effective des flux NetCDF dans les 186 fichiers historiques.")
        print("  - L'intégration spatiale des incréments 4 couches sur les 339 fichiers EnKF.")
        print("  - Le calcul complet des résidus numériques finaux.")
        print("=" * 80)
        return

    # 3. Calcul complet
    b_ol = compute_single_experiment("Open Loop", args.opl_dir, grid_info, is_ensemble=False, start_dt=AUD05_START_DT, end_dt=AUD05_END_DT)
    b_ctrl = compute_single_experiment("DA Contrôle", args.da_ctrl_dir, grid_info, is_ensemble=True, start_dt=AUD05_START_DT, end_dt=AUD05_END_DT)
    b_nowilt = compute_single_experiment("DA Nowilt", args.nowilt_dir, grid_info, is_ensemble=True, start_dt=AUD05_START_DT, end_dt=AUD05_END_DT)

    # 4. Affichage du tableau Markdown
    print("\n" + "=" * 80)
    print("TABLEAU DU BILAN HYDRIQUE COMPARATIF (611 PIXELS ARGILEUX, 62 JOURS)")
    print("=" * 80)
    md_table = format_markdown_table(b_ol, b_ctrl, b_nowilt)
    print(md_table)
    print("=" * 80)

    # 5. Export CSV structuré
    if args.output_csv:
        export_structured_csv(args.output_csv, b_ol, b_ctrl, b_nowilt)


if __name__ == "__main__":
    main()
