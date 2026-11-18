import os, datetime
import numpy as np
import pandas as pd
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import uniform_filter

BASE_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUTPUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/drydown_point1_uncensored")
INTERIM_DIR = os.path.join(AUDIT_DIR, "data/interim/noahmp")
LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")
GMIA_PATH = os.path.join(BASE_DIR, "data/land_params/GMIA/gmia_v5_aei_pct.asc")

CACHE_FILE = os.path.join(OUTPUT_DIR, "daily_cache_uncensored_2016_2020.npz")
CENSOR_CACHE = os.path.join(OUTPUT_DIR, "censorship_budget_2016_2020.npz")

# 1. Load static
with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
    texture = ds.variables["TEXTURE"][:]
    lat = ds.variables["lat"][:]
    lon = ds.variables["lon"][:]

soiltype = np.argmax(texture, axis=0) + 1
mask_land = (landmask == 1)

TEXTURE_NAMES = {
    1: "Sand", 2: "Loamy Sand", 3: "Sandy Loam", 4: "Silt Loam", 5: "Silt",
    6: "Loam", 7: "Sandy Clay Loam", 8: "Silty Clay Loam", 9: "Clay Loam",
    10: "Sandy Clay", 11: "Silty Clay", 12: "Clay",
}

# 2. Load GMIA
def load_gmia_grid(target_lat, target_lon, landmask):
    with open(GMIA_PATH, "r") as f:
        header = {}
        for _ in range(6):
            parts = f.readline().split()
            header[parts[0].lower()] = float(parts[1])
    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    xll = header["xllcorner"]
    yll = header["yllcorner"]
    cs = header["cellsize"]
    
    gmia_lats = yll + cs * np.arange(nrows)[::-1]
    gmia_lons = xll + cs * np.arange(ncols)
    
    lat_min, lat_max = target_lat.min() - 0.2, target_lat.max() + 0.2
    lon_min, lon_max = target_lon.min() - 0.2, target_lon.max() + 0.2
    
    r_idx = np.where((gmia_lats >= lat_min) & (gmia_lats <= lat_max))[0]
    c_idx = np.where((gmia_lons >= lon_min) & (gmia_lons <= lon_max))[0]
    
    bin_path = GMIA_PATH.replace(".asc", ".bin")
    if os.path.exists(bin_path):
        gmia_full = np.fromfile(bin_path, dtype=np.float32).reshape(nrows, ncols)
    else:
        gmia_full = np.loadtxt(GMIA_PATH, skiprows=6)
        
    gmia_sub = gmia_full[r_idx[0]:r_idx[-1]+1, c_idx[0]:c_idx[-1]+1]
    sub_lats = gmia_lats[r_idx[0]:r_idx[-1]+1]
    sub_lons = gmia_lons[c_idx[0]:c_idx[-1]+1]
    gmia_sub[gmia_sub < 0] = 0.0
    
    interp = RegularGridInterpolator((sub_lats[::-1], sub_lons), gmia_sub[::-1, :], bounds_error=False, fill_value=0.0)
    pts = np.vstack([target_lat.ravel(), target_lon.ravel()]).T
    gmia_5km = interp(pts).reshape(target_lat.shape)
    gmia_5km[landmask == 0] = 0.0
    return gmia_5km

gmia_5km = load_gmia_grid(lat, lon, landmask)

# 3. Load daily cache
data_cache = np.load(CACHE_FILE)
ol_daily = data_cache["ol_daily"] # (1827, 121, 181)
smap_cens = data_cache["smap_censored_daily"] # (1827, 121, 181)
smap_uncens = data_cache["smap_uncensored_daily"] # (1827, 121, 181)
dates_list = [datetime.date.fromisoformat(d) for d in data_cache["dates_str"]]
months_arr = np.array([d.month for d in dates_list])

# 4. Monthly analysis of (SMAP - OL) accepted vs uncensored
monthly_comp_rows = []
for m in range(1, 13):
    idx_m = np.where(months_arr == m)[0]
    o_uncens_m = smap_uncens[idx_m]
    o_cens_m = smap_cens[idx_m]
    f_ol_m = ol_daily[idx_m]
    
    valid_uncens = np.isfinite(o_uncens_m) & np.isfinite(f_ol_m) & (f_ol_m > 0)
    valid_cens = np.isfinite(o_cens_m) & np.isfinite(f_ol_m) & (f_ol_m > 0)
    
    inn_uncens_all = (o_uncens_m - f_ol_m)[valid_uncens]
    inn_cens_all = (o_cens_m - f_ol_m)[valid_cens]
    
    m_uncens = float(np.mean(inn_uncens_all)) if len(inn_uncens_all)>0 else np.nan
    m_cens = float(np.mean(inn_cens_all)) if len(inn_cens_all)>0 else np.nan
    
    monthly_comp_rows.append({
        "month": m,
        "soil_class": "Domaine Entier",
        "n_obs_uncens": len(inn_uncens_all),
        "n_obs_accepted": len(inn_cens_all),
        "mean_smap_uncens_minus_ol": round(m_uncens, 4),
        "mean_smap_accepted_minus_ol": round(m_cens, 4),
        "selection_bias_accepted_minus_uncens": round(m_cens - m_uncens, 4)
    })
    
    for st in [3, 6, 7, 9, 12]:
        mask_st = (soiltype == st) & mask_land
        v_u_st = valid_uncens[:, mask_st]
        v_c_st = valid_cens[:, mask_st]
        
        inn_u_st = (o_uncens_m[:, mask_st] - f_ol_m[:, mask_st])[v_u_st]
        inn_c_st = (o_cens_m[:, mask_st] - f_ol_m[:, mask_st])[v_c_st]
        
        mu_st = float(np.mean(inn_u_st)) if len(inn_u_st)>0 else np.nan
        mc_st = float(np.mean(inn_c_st)) if len(inn_c_st)>0 else np.nan
        
        monthly_comp_rows.append({
            "month": m,
            "soil_class": TEXTURE_NAMES[st],
            "n_obs_uncens": len(inn_u_st),
            "n_obs_accepted": len(inn_c_st),
            "mean_smap_uncens_minus_ol": round(mu_st, 4),
            "mean_smap_accepted_minus_ol": round(mc_st, 4),
            "selection_bias_accepted_minus_uncens": round(mc_st - mu_st, 4)
        })

df_e5_monthly = pd.DataFrame(monthly_comp_rows)

# 5. Summer Delta theta 1 (DA - OL) crossed with Censorship Quintiles and Irrigation
def load_ssm(exp):
    cubes = []
    for y in range(2016, 2021):
        fp = os.path.join(INTERIM_DIR, exp, "ssm", f"ssm_{y}.nc")
        with nc.Dataset(fp) as ds:
            cubes.append(ds.variables["ssm"][:])
    return np.concatenate(cubes, axis=0)

ssm_da = load_ssm("da_nocdf")
ssm_ol = load_ssm("opl")

jja_idx = [i for i, d in enumerate(dates_list) if d.month in [6, 7, 8]]
jja_delta_theta1 = np.nanmean(ssm_da[jja_idx] - ssm_ol[jja_idx], axis=0) # (121, 181)

data_censor = np.load(CENSOR_CACHE)
nocdf_rej = data_censor["nocdf_wilt_rej_monthly"]
nocdf_val = data_censor["nocdf_valid_monthly"]

jja_rej = np.sum(nocdf_rej[5:8], axis=0)
jja_val = np.sum(nocdf_val[5:8], axis=0)
cens_rate_jja = np.zeros((121, 181), dtype=float)
v_cens = (jja_val > 0) & mask_land
cens_rate_jja[v_cens] = (jja_rej[v_cens] / jja_val[v_cens]) * 100.0

cens_vals_land = cens_rate_jja[mask_land]
# Use non-zero quintiles or strict quintiles
q_bins = np.percentile(cens_vals_land[cens_vals_land > 0], [0, 25, 50, 75, 100])
# 5 classes: 0% censorship, then 4 quartiles of positive censorship
classes_censor = [
    ("Taux = 0%", cens_vals_land == 0.0),
    (f"1–{q_bins[1]:.0f}%", (cens_vals_land > 0.0) & (cens_vals_land <= q_bins[1])),
    (f"{q_bins[1]:.0f}–{q_bins[2]:.0f}%", (cens_vals_land > q_bins[1]) & (cens_vals_land <= q_bins[2])),
    (f"{q_bins[2]:.0f}–{q_bins[3]:.0f}%", (cens_vals_land > q_bins[2]) & (cens_vals_land <= q_bins[3])),
    (f">{q_bins[3]:.0f}%", (cens_vals_land > q_bins[3])),
]

irrig_land = gmia_5km[mask_land]
delta_theta_land = jja_delta_theta1[mask_land]

cross_rows = []
for c_name, mask_q in classes_censor:
    d_q_all = delta_theta_land[mask_q]
    mask_rainfed = mask_q & (irrig_land < 1.0)
    d_q_rainfed = delta_theta_land[mask_rainfed]
    mask_irrig = mask_q & (irrig_land >= 1.0)
    d_q_irrig = delta_theta_land[mask_irrig]
    
    cross_rows.append({
        "censorship_class": c_name,
        "n_pixels_total": int(mask_q.sum()),
        "mean_delta_theta1_all": round(float(np.mean(d_q_all)), 5),
        "n_pixels_rainfed": int(mask_rainfed.sum()),
        "mean_delta_theta1_rainfed": round(float(np.mean(d_q_rainfed)), 5) if len(d_q_rainfed)>0 else np.nan,
        "n_pixels_irrigated": int(mask_irrig.sum()),
        "mean_delta_theta1_irrigated": round(float(np.mean(d_q_irrig)), 5) if len(d_q_irrig)>0 else np.nan,
    })

df_cross = pd.DataFrame(cross_rows)

out_csv = os.path.join(OUTPUT_DIR, "e5_selection_bias_summary.csv")
with open(out_csv, "w") as f:
    f.write("# PARTIE A : BIAIS DE SELECTION MENSUEL (O_accepted - OL) vs (O_uncensored - OL)\n")
    df_e5_monthly.to_csv(f, index=False)
    f.write("\n# PARTIE B : CROISEMENT DELTA THETA 1 ESTIVAL (JJA, DA - OL) x CLASSES DE CENSURE x FRACTION IRRIGUEE (GMIA)\n")
    df_cross.to_csv(f, index=False)

print(f"[E5] Tableau de synthèse sauvegardé dans {out_csv}")
print("\n--- PARTIE B : CROISEMENT CENSURE x IRRIGATION ---")
print(df_cross.to_string())

# 6. Generate Figure
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Panel (a): Monthly Innovation Comparison
sub_dom = df_e5_monthly[df_e5_monthly["soil_class"] == "Domaine Entier"]
months_vals = sub_dom["month"].values
inn_u_vals = sub_dom["mean_smap_uncens_minus_ol"].values
inn_c_vals = sub_dom["mean_smap_accepted_minus_ol"].values

ax = axes[0]
ax.plot(months_vals, inn_u_vals, marker="o", color="#2980b9", linewidth=2.2, label="SMAP non censuré − OL (toutes obs)")
ax.plot(months_vals, inn_c_vals, marker="s", color="#e74c3c", linewidth=2.2, linestyle="--", label="SMAP accepté − OL (après QC seuil)")
ax.axhline(0, color="black", linestyle=":", alpha=0.7)
ax.fill_between(months_vals, inn_u_vals, inn_c_vals, color="#e74c3c", alpha=0.2, label="Biais de sélection positif (+ humidifiant)")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
ax.set_xlabel("Mois", fontsize=11, fontweight="bold")
ax.set_ylabel("Innovation moyenne (m³/m³)", fontsize=11, fontweight="bold")
ax.set_title("(a) Effet du seuil de flétrissement sur l'innovation moyenne\nDA-NoCDF vs Prévision OL (2016–2020)", fontsize=12, fontweight="bold")
ax.legend(fontsize=9.5, loc="upper right")
ax.grid(True, linestyle="--", alpha=0.5)

# Annotate summer selection bias
jja_bias = np.mean(inn_c_vals[5:8] - inn_u_vals[5:8])
ax.annotate(f"Biais de sélection estival (JJA) :\n+{jja_bias:+.4f} m³/m³", xy=(7, inn_c_vals[6]), xytext=(7.5, 0.025),
            arrowprops=dict(facecolor="#e74c3c", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold", color="#c0392b", bbox=dict(boxstyle="round,pad=0.3", fc="#fadbd8", ec="#e74c3c", alpha=0.8))

# Panel (b): Delta theta 1 JJA vs Censorship Classes
ax2 = axes[1]
x = np.arange(len(df_cross))
width = 0.35
y_rainfed = df_cross["mean_delta_theta1_rainfed"].values * 1000.0
y_irrig = df_cross["mean_delta_theta1_irrigated"].values * 1000.0

ax2.bar(x - width/2, y_rainfed, width=width, color="#27ae60", label="Pluvial (GMIA < 1%)", zorder=3)
ax2.bar(x + width/2, y_irrig, width=width, color="#8e44ad", label="Irrigué (GMIA ≥ 1%)", zorder=3)
ax2.set_xticks(x)
ax2.set_xticklabels(df_cross["censorship_class"].values, rotation=15, ha="right", fontsize=9.5)
ax2.set_xlabel("Classes de taux de censure estival (JJA)", fontsize=11, fontweight="bold")
ax2.set_ylabel("Humidification estivale Δθ₁ DA − OL (10⁻³ m³/m³)", fontsize=11, fontweight="bold")
ax2.set_title("(b) Δθ₁ estival en fonction du taux de censure\nCroisement avec l'irrigation GMIA", fontsize=12, fontweight="bold")
ax2.legend(fontsize=10)
ax2.grid(True, linestyle="--", alpha=0.4, axis="y")
ax2.axhline(0, color="black", linewidth=0.8)

plt.tight_layout()
out_fig = os.path.join(OUTPUT_DIR, "figure_e5_selection_bias.png")
plt.savefig(out_fig, dpi=300)
plt.close()
print(f"[E5] Figure sauvegardée dans {out_fig}")
