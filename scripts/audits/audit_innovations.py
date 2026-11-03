#!/usr/bin/env python3
"""
audit_innovations.py
Audit of DA innovations (O - F) for DA-CDF and DA-NoCDF experiments (2016-2020).
Computes for each month (60 months):
  - Number of finite innovations (count)
  - Domain-wide mean innovation (O - F)
"""

import os
import glob
import time
from concurrent.futures import ProcessPoolExecutor
import netCDF4 as nc
import numpy as np
import pandas as pd

def process_month(args):
    exp_name, month_str, exp_dir = args
    pattern = os.path.join(exp_dir, f"output/{month_str}/EnKF/*/*innov*.nc")
    files = sorted(glob.glob(pattern))
    
    total_count = 0
    total_sum = 0.0
    
    for f in files:
        try:
            with nc.Dataset(f, "r") as ds:
                if "innov_01" in ds.variables:
                    data = ds.variables["innov_01"][:]
                    mask = (data != -9999.0) & np.isfinite(data)
                    cnt = int(np.sum(mask))
                    if cnt > 0:
                        total_count += cnt
                        total_sum += float(np.sum(data[mask]))
        except Exception as e:
            pass
            
    mean_val = (total_sum / total_count) if total_count > 0 else np.nan
    return {
        "exp": exp_name,
        "month": month_str,
        "n_files": len(files),
        "count": total_count,
        "mean_innov": mean_val
    }

def main():
    base_dir = "../NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020"
    exp_cdf_dir = os.path.join(base_dir, "DA_cdf_noirr_2016_2020")
    exp_nocdf_dir = os.path.join(base_dir, "DA_nocdf_noirr_2016_2020")
    
    years = range(2016, 2021)
    months = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
    
    tasks = []
    for m in months:
        tasks.append(("DA-CDF", m, exp_cdf_dir))
        tasks.append(("DA-NoCDF", m, exp_nocdf_dir))
        
    print(f"Processing {len(tasks)} month-experiments in parallel...")
    t0 = time.time()
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_month, tasks))
        
    dt = time.time() - t0
    print(f"Completed in {dt:.2f} seconds.")
    
    df = pd.DataFrame(results)
    df_pivot = df.pivot(index="month", columns="exp", values=["count", "mean_innov"])
    
    # Save CSV
    out_csv = "tables/audit/innovations_monthly_audit.csv"
    os.makedirs("tables/audit", exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Saved raw results to {out_csv}")
    
    # Print formatted comparison table
    print("\n" + "=" * 92)
    print(f"{'Mois':<8} | {'N_innov (DA-CDF)':<18} | {'Moy O-F (CDF)':<16} | {'N_innov (NoCDF)':<18} | {'Moy O-F (NoCDF)':<16}")
    print("-" * 92)
    
    for m in months:
        cdf_row = df[(df["month"] == m) & (df["exp"] == "DA-CDF")].iloc[0]
        nocdf_row = df[(df["month"] == m) & (df["exp"] == "DA-NoCDF")].iloc[0]
        print(f"{m:<8} | {cdf_row['count']:<18} | {cdf_row['mean_innov']:<16.5f} | {nocdf_row['count']:<18} | {nocdf_row['mean_innov']:<16.5f}")
        
    print("=" * 92)
    
    # Annual and global summary
    df["year"] = df["month"].apply(lambda x: x[:4])
    print("\n--- SYNTHÈSE ANNUELLE ET GLOBALE ---")
    for exp in ["DA-CDF", "DA-NoCDF"]:
        sub = df[df["exp"] == exp]
        tot_cnt = sub["count"].sum()
        # weighted mean
        w_mean = (sub["count"] * sub["mean_innov"]).sum() / tot_cnt
        print(f"\nExpérience: {exp}")
        print(f"  Total innovations finies (2016-2020): {tot_cnt:,}")
        print(f"  Moyenne globale O - F (2016-2020):   {w_mean:+.6f} m3/m3")
        for y in sorted(df["year"].unique()):
            y_sub = sub[sub["year"] == y]
            y_cnt = y_sub["count"].sum()
            y_mean = (y_sub["count"] * y_sub["mean_innov"]).sum() / y_cnt
            print(f"    Année {y}: N = {y_cnt:8,d} | Moyenne O - F = {y_mean:+.6f} m3/m3")

if __name__ == "__main__":
    main()
