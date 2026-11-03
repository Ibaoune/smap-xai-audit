#!/usr/bin/env python3
"""
audit_cdf_validity.py
Audit of CDF validity across the North Morocco domain (0.05 deg, Noah-MP 4.0.1).
Computes the percentage of terrestrial pixels with a valid CDF (non-missing, non-constant)
for each of the 12 calendar months, for both observation and model CDF files.
"""

import sys
import numpy as np
import netCDF4 as nc

def check_cdf_validity(cdf_file, domain_file):
    with nc.Dataset(domain_file) as ds_dom:
        landmask = ds_dom.variables["LANDMASK"][:]
        total_land_points = int(np.sum(landmask == 1))

    with nc.Dataset(cdf_file) as ds:
        # Dimensions: (nbins, levels, ntimes, ngrid)
        xrange = ds.variables["SoilMoist_xrange"][:]
        mu = ds.variables["SoilMoist_mu"][:]
        sigma = ds.variables["SoilMoist_sigma"][:]

    nbins, nlevels, ntimes, ngrid = xrange.shape
    assert ngrid == total_land_points, f"ngrid ({ngrid}) != total land points ({total_land_points})"

    results = []
    for m in range(ntimes):
        mu_m = mu[0, m, :]
        sig_m = sigma[0, m, :]
        xr_m = xrange[:, 0, m, :]  # shape: (nbins, ngrid)

        # Valid criteria:
        # 1. mu != -9999
        # 2. sigma != -9999 and sigma > 0
        # 3. xrange is not all -9999 and ptp (max - min) > 1e-6 (non-constant)
        is_not_missing = (mu_m != -9999.0) & (sig_m != -9999.0) & (sig_m > 0)
        xr_span = np.ptp(xr_m, axis=0)
        is_non_constant = xr_span > 1e-6
        valid = is_not_missing & is_non_constant

        valid_count = int(np.sum(valid))
        valid_pct = (valid_count / total_land_points) * 100.0

        results.append({
            "month": m + 1,
            "valid_count": valid_count,
            "total_land": total_land_points,
            "valid_pct": valid_pct
        })
    return results

if __name__ == "__main__":
    cdf_file = "../NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_noirr/smap_cdf.nc"
    domain_file = "../NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_noirr/smap_cdf_domain.nc"

    print("=" * 65)
    print("AUDIT CDF - VALIDITÉ MENSUELLE DES PIXELS TERRESTRES")
    print(f"Fichier CDF:    {cdf_file}")
    print(f"Fichier Domaine: {domain_file}")
    print("=" * 65)

    res = check_cdf_validity(cdf_file, domain_file)

    print(f"{'Mois':<6} | {'Pixels Valides':<16} | {'Total Terrestre':<16} | {'% Valide':<10}")
    print("-" * 65)
    for r in res:
        print(f"{r['month']:02d}     | {r['valid_count']:<16} | {r['total_land']:<16} | {r['valid_pct']:.2f}%")
    print("=" * 65)
