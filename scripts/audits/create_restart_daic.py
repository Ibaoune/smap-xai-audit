#!/usr/bin/env python3
"""
create_restart_daic.py
Construit l'état initial 1 membre pour OL_DAIC_2018 à partir de :
DA_nocdf_noirr_2016_2020/restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc
Règle : pour chaque maille, sélectionner le membre dont l'humidité de colonne
est la plus proche de la moyenne d'ensemble, et copier toutes ses variables.
"""
import os
import netCDF4 as nc
import numpy as np

BASE_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
f_src = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/restarts/surf/LIS_RST_NOAHMP401_201801010000.d01.nc")
f_tpl = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/restarts/LIS_RST_NOAHMP401_201801010000.d01.nc")
f_dst = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_DAIC_2018/restart/LIS_RST_NOAHMP401_201801010000.d01.nc")

print(f"[INFO] Source (20 ens) : {f_src}")
print(f"[INFO] Template (1 mem) : {f_tpl}")
print(f"[INFO] Destination     : {f_dst}")

with nc.Dataset(f_src, 'r') as ds_src, nc.Dataset(f_tpl, 'r') as ds_tpl:
    n_tiles = len(ds_tpl.dimensions['ntiles'])
    n_ens = 20
    assert len(ds_src.dimensions['ntiles']) == n_tiles * n_ens
    
    # SMC: shape (4, 320600)
    print("[INFO] Lecture de SMC et calcul de l'humidité de colonne...")
    smc = ds_src.variables['SMC'][:]
    dz = np.array([0.1, 0.3, 0.6, 1.0], dtype=np.float32)
    
    # Reshape to (4, n_tiles, n_ens)
    smc_cube = smc.reshape((4, n_tiles, n_ens))
    
    # theta_col for each member: sum_l (dz[l] * smc[l, i, m])
    theta_col = np.tensordot(dz, smc_cube, axes=([0], [0])) # shape (n_tiles, n_ens)
    
    # Ensemble mean column moisture
    mean_col = np.mean(theta_col, axis=1, keepdims=True) # shape (n_tiles, 1)
    
    # Find closest member
    diff_from_mean = np.abs(theta_col - mean_col)
    best_m = np.argmin(diff_from_mean, axis=1) # shape (n_tiles,)
    
    # Distribution of best members
    counts = np.bincount(best_m, minlength=20)
    print(f"[INFO] Distribution des membres sélectionnés (min {np.min(counts)}, max {np.max(counts)}, mean {np.mean(counts):.1f}) :")
    print(counts)
    
    # Global index for each tile
    best_idx = np.arange(n_tiles) * 20 + best_m
    
    # Verification of lat/lon
    lat_src = ds_src.variables['lat'][:]
    lon_src = ds_src.variables['lon'][:]
    lat_tpl = ds_tpl.variables['lat'][:]
    lon_tpl = ds_tpl.variables['lon'][:]
    assert np.allclose(lat_src[best_idx], lat_tpl), "Erreur cohérence latitude !"
    assert np.allclose(lon_src[best_idx], lon_tpl), "Erreur cohérence longitude !"
    print("[INFO] Cohérence spatiale lat/lon validée à 100%.")
    
    print("[INFO] Écriture du restart 1 membre...")
    if os.path.exists(f_dst):
        os.remove(f_dst)
        
    with nc.Dataset(f_dst, 'w', format=ds_tpl.file_format) as ds_dst:
        # Global attributes
        for att in ds_tpl.ncattrs():
            ds_dst.setncattr(att, ds_tpl.getncattr(att))
            
        # Dimensions
        for dname, dim in ds_tpl.dimensions.items():
            ds_dst.createDimension(dname, len(dim) if not dim.isunlimited() else None)
            
        # Variables
        for vname, var_tpl in ds_tpl.variables.items():
            var_src = ds_src.variables[vname]
            fill_val = getattr(var_tpl, '_FillValue', None)
            var_dst = ds_dst.createVariable(vname, var_tpl.dtype, var_tpl.dimensions, zlib=True, fill_value=fill_val)
            for att in var_tpl.ncattrs():
                if att != '_FillValue':
                    var_dst.setncattr(att, var_tpl.getncattr(att))
                
            if vname == 'time':
                var_dst[:] = var_src[:]
            elif 'ntiles' in var_tpl.dimensions:
                if var_tpl.ndim == 1:
                    var_dst[:] = var_src[:][best_idx]
                elif var_tpl.ndim == 2:
                    var_dst[:] = var_src[:, best_idx]
                else:
                    raise ValueError(f"Dimension inattendue pour {vname}")
            else:
                var_dst[:] = var_src[:]

print(f"[SUCCÈS] Restart 1 membre créé avec succès : {f_dst} ({os.path.getsize(f_dst) / 1e6:.2f} Mo)")
