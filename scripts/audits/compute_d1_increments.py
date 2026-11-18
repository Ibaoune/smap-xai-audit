import os, glob
import netCDF4 as nc
import numpy as np
import pandas as pd
from collections import defaultdict
import multiprocessing as mp

BASE_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUTPUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/baseflow_link")
LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")

with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(bool)

n_land = landmask.sum()
dz = np.array([100.0, 300.0, 600.0, 1000.0]) # mm

def process_file(fp):
    try:
        bn = os.path.basename(fp)
        dt_str = bn.split("_")[3]
        year = int(dt_str[:4])
        month = int(dt_str[4:6])
        if month in [12, 1, 2]:
            season = "DJF"
        elif month in [3, 4, 5]:
            season = "MAM"
        elif month in [6, 7, 8]:
            season = "JJA"
        else:
            season = "SON"
            
        with nc.Dataset(fp, "r") as ds:
            inc1 = ds.variables["anlys_incr_Soil Moisture Layer 1_01"][:].squeeze()
            inc2 = ds.variables["anlys_incr_Soil Moisture Layer 2_01"][:].squeeze()
            inc3 = ds.variables["anlys_incr_Soil Moisture Layer 3_01"][:].squeeze()
            inc4 = ds.variables["anlys_incr_Soil Moisture Layer 4_01"][:].squeeze()
            
        inc1[~landmask] = 0.0
        inc2[~landmask] = 0.0
        inc3[~landmask] = 0.0
        inc4[~landmask] = 0.0
        
        # total depth in mm domain mean
        w_mm = (inc1 * dz[0] + inc2 * dz[1] + inc3 * dz[2] + inc4 * dz[3]).sum() / n_land
        return year, season, w_mm
    except Exception as e:
        return None

def compute_experiment_increments(exp_dir, exp_name):
    patt = os.path.join(exp_dir, "*/EnKF/*/LIS_DA_EnKF_*_incr.a01.d01.nc")
    files = sorted(glob.glob(patt))
    print(f"[{exp_name}] Traitement de {len(files)} fichiers d'incréments...")
    
    with mp.Pool(processes=min(16, mp.cpu_count())) as pool:
        results = pool.map(process_file, files)
        
    by_season = defaultdict(float)
    by_year = defaultdict(float)
    total_mm = 0.0
    
    for res in results:
        if res is not None:
            yr, s, w = res
            by_season[s] += w
            by_year[yr] += w
            total_mm += w
            
    return by_season, by_year, total_mm

if __name__ == "__main__":
    dir_nocdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output")
    dir_cdf = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/DA_cdf_noirr_2016_2020/output")
    
    s_nocdf, y_nocdf, tot_nocdf = compute_experiment_increments(dir_nocdf, "DA-NoCDF")
    s_cdf, y_cdf, tot_cdf = compute_experiment_increments(dir_cdf, "DA-CDF")
    
    print("\n=== INCÉMENTS DIRECTS CUMULÉS PAR SAISON (mm) ===")
    for s in ["DJF", "MAM", "JJA", "SON"]:
        print(f"  {s}: NoCDF = {s_nocdf[s]:+.2f} mm | CDF = {s_cdf[s]:+.2f} mm")
        
    print("\n=== INCÉMENTS DIRECTS CUMULÉS PAR AN (mm) ===")
    for y in range(2016, 2021):
        print(f"  {y}: NoCDF = {y_nocdf[y]:+.2f} mm | CDF = {y_cdf[y]:+.2f} mm")
    print(f"  TOTAL 2016-2020: NoCDF = {tot_nocdf:+.2f} mm | CDF = {tot_cdf:+.2f} mm")
