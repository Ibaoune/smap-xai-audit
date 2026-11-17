#!/usr/bin/env python3
"""
compute_gmia_signature.py
-------------------------
Prompt B Point 3: Irrigation signature analysis on GMIA 0.05 deg (gmia_5km).
Computes mean innovation and mean signed increment by irrigation fraction class:
- Classes: 0%, 0-10%, 10-30%, >30%
- Seasons: Wet (Oct-May) and Summer (Jun-Aug)
- Experiments: da_cdf and da_nocdf over 2016-2020
Outputs:
- Full metrics table with pixel-day counts
- Figure: figures/cdf_v2/irrigation_signature.png and .pdf
"""

import os
import glob
from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import RegularGridInterpolator

# Paths
ROOT = Path("/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao")
SMAP_XAI = ROOT / "smap-xai-audit"
GMIA_PATH = ROOT / "NoahMP_Morocco/data/land_params/GMIA/gmia_v5_aei_pct.asc"
OUT_DIR = SMAP_XAI / "figures/cdf_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_gmia_5km(target_lat, target_lon):
    """Interpolate GMIA to 0.05 deg grid matching target_lat and target_lon."""
    with open(GMIA_PATH, "r") as f:
        header = {}
        for _ in range(6):
            p = f.readline().split()
            header[p[0].lower()] = float(p[1])
            
    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    xll = header["xllcorner"]
    yll = header["yllcorner"]
    cell = header["cellsize"]

    gmia_lons = xll + (np.arange(ncols) + 0.5) * cell
    gmia_lats = (yll + nrows * cell) - (np.arange(nrows) + 0.5) * cell

    lat_min, lat_max = target_lat.min() - 0.2, target_lat.max() + 0.2
    lon_min, lon_max = target_lon.min() - 0.2, target_lon.max() + 0.2

    r_idx = np.where((gmia_lats >= lat_min) & (gmia_lats <= lat_max))[0]
    c_idx = np.where((gmia_lons >= lon_min) & (gmia_lons <= lon_max))[0]

    bin_path = str(GMIA_PATH).replace(".asc", ".bin")
    if os.path.exists(bin_path):
        gmia_full = np.fromfile(bin_path, dtype=np.float32).reshape(nrows, ncols)
    else:
        gmia_full = np.loadtxt(GMIA_PATH, skiprows=6)

    gmia_sub = gmia_full[r_idx[0]:r_idx[-1]+1, c_idx[0]:c_idx[-1]+1]
    sub_lats = gmia_lats[r_idx[0]:r_idx[-1]+1]
    sub_lons = gmia_lons[c_idx[0]:c_idx[-1]+1]
    gmia_sub[gmia_sub < 0] = 0.0

    interp = RegularGridInterpolator((sub_lats[::-1], sub_lons), gmia_sub[::-1, :],
                                     bounds_error=False, fill_value=0.0)
    lon_grid, lat_grid = np.meshgrid(target_lon, target_lat)
    pts = np.stack([lat_grid.ravel(), lon_grid.ravel()], axis=-1)
    gmia_5km = interp(pts).reshape(lat_grid.shape)
    return gmia_5km

def main():
    print("=== Computing Irrigation Signature Analysis (GMIA 5km) ===")
    
    # 1. Load canonical daily innovation and increment (2016-2020)
    def load_var_series(exp, var_name):
        pattern = str(SMAP_XAI / f"data/processed/daily_enkf/{exp}/{var_name}/{var_name}_*.nc")
        files = sorted(glob.glob(pattern))
        print(f"Loading {len(files)} files for {exp} {var_name}...")
        ds_list = [xr.open_dataset(f) for f in files]
        return xr.concat(ds_list, dim="time")

    ds_nocdf_inn = load_var_series("da_nocdf", "daily_innovation")
    ds_cdf_inn = load_var_series("da_cdf", "daily_innovation")
    ds_nocdf_inc = load_var_series("da_nocdf", "daily_signed_increment")
    ds_cdf_inc = load_var_series("da_cdf", "daily_signed_increment")

    target_lat = ds_nocdf_inn.lat.values
    target_lon = ds_nocdf_inn.lon.values
    gmia_5km = load_gmia_5km(target_lat, target_lon)
    print(f"GMIA 5km loaded: shape={gmia_5km.shape}, min={gmia_5km.min():.2f}%, max={gmia_5km.max():.2f}%")

    # Define classes
    classes = [
        ("0", gmia_5km == 0.0),
        ("0–10 %", (gmia_5km > 0.0) & (gmia_5km <= 10.0)),
        ("10–30 %", (gmia_5km > 10.0) & (gmia_5km <= 30.0)),
        ("> 30 %", gmia_5km > 30.0)
    ]
    for cname, mask in classes:
        print(f"Class '{cname}': {np.sum(mask)} pixels ({100*np.mean(mask):.1f}%)")

    # Seasons definition
    # Wet season: Oct-May (months [10, 11, 12, 1, 2, 3, 4, 5])
    # Summer: Jun-Aug (months [6, 7, 8])
    time_series = pd.to_datetime(ds_nocdf_inn.time.values)
    months = time_series.month
    wet_mask = np.isin(months, [10, 11, 12, 1, 2, 3, 4, 5])
    summer_mask = np.isin(months, [6, 7, 8])

    seasons = [
        ("Humide (Oct–Mai)", wet_mask),
        ("Été (Juin–Août)", summer_mask)
    ]

    records = []
    
    experiments = [
        ("NoCDF", ds_nocdf_inn["daily_innovation"].values, ds_nocdf_inc["daily_signed_increment"].values),
        ("CDF", ds_cdf_inn["daily_innovation"].values, ds_cdf_inc["daily_signed_increment"].values)
    ]

    for exp_name, inn_arr, inc_arr in experiments:
        for seas_name, s_mask in seasons:
            # Subset along time
            inn_s = inn_arr[s_mask, :, :]
            inc_s = inc_arr[s_mask, :, :]
            
            for cname, cmask in classes:
                # Select pixels of this class across time
                inn_c = inn_s[:, cmask]
                inc_c = inc_s[:, cmask]
                
                # Valid points
                valid_inn = inn_c[~np.isnan(inn_c)]
                valid_inc = inc_c[~np.isnan(inc_c)]
                
                n_px_days = len(valid_inn)
                mean_inn = float(np.mean(valid_inn)) if n_px_days > 0 else np.nan
                std_inn = float(np.std(valid_inn)) if n_px_days > 0 else np.nan
                mean_inc = float(np.mean(valid_inc)) if len(valid_inc) > 0 else np.nan
                std_inc = float(np.std(valid_inc)) if len(valid_inc) > 0 else np.nan
                
                records.append({
                    "Experience": exp_name,
                    "Saison": seas_name,
                    "Classe GMIA": cname,
                    "Pixel-jours": n_px_days,
                    "Innovation Moyenne": mean_inn,
                    "Innovation Ecart-type": std_inn,
                    "Increment Signe Moyen": mean_inc,
                    "Increment Signe Ecart-type": std_inc
                })

    df_res = pd.DataFrame(records)
    csv_out = OUT_DIR / "irrigation_signature_table.csv"
    df_res.to_csv(csv_out, index=False)
    print(f"\nSaved metrics to {csv_out}")
    print("\n" + df_res.to_string(index=False))

    # --------------------------------------------------------------------------
    # Plotting: figures/cdf_v2/irrigation_signature.png & .pdf
    # --------------------------------------------------------------------------
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    
    palette_seasons = {
        "Humide (Oct–Mai)": "#1f77b4",  # blue
        "Été (Juin–Août)": "#d62728"    # red
    }
    
    exps = ["CDF", "NoCDF"]
    for i, exp in enumerate(exps):
        ax = axes[i]
        df_sub = df_res[df_res["Experience"] == exp]
        
        sns.barplot(
            data=df_sub,
            x="Classe GMIA",
            y="Innovation Moyenne",
            hue="Saison",
            palette=palette_seasons,
            ax=ax
        )
        
        ax.axhline(0, color='black', linestyle='--', linewidth=0.9, alpha=0.7)
        ax.set_title(f"({chr(97+i)}) {exp}", fontsize=13, weight='bold', loc='left')
        ax.set_xlabel("Classe d'irrigation GMIA (0.05°)", fontsize=11)
        if i == 0:
            ax.set_ylabel("Innovation moyenne (SMAP − Modèle) [m³ m⁻³]", fontsize=11)
        else:
            ax.set_ylabel("")
            
        ax.grid(True, linestyle=":", alpha=0.6)
        
        # In-bar value labels
        for p in ax.patches:
            val = p.get_height()
            if not np.isnan(val) and val != 0:
                y_pos = val + (0.0008 if val >= 0 else -0.0016)
                sign = "+" if val > 0 else ""
                ax.annotate(f"{sign}{val:.4f}",
                            (p.get_x() + p.get_width() / 2., y_pos),
                            ha='center', va='center',
                            fontsize=8.5, color='#222222',
                            rotation=0)
                            
        if i == 0:
            ax.legend(title="Saison", loc="lower left", framealpha=0.9)
        else:
            ax.legend().remove()
            
    fig.suptitle("Signature de l'irrigation GMIA sur l'innovation moyenne SMAP (2016–2020)", fontsize=14, y=1.02)
    fig.tight_layout()
    
    png_path = OUT_DIR / "irrigation_signature.png"
    pdf_path = OUT_DIR / "irrigation_signature.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {png_path} and {pdf_path}")

if __name__ == "__main__":
    main()
