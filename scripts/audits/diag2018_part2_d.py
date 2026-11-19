#!/usr/bin/env python3
"""
diag2018_part2_d.py
Partie 2.d : Analyse des simulations horaires complètes (année 2018).
1. Dynamique de séchage (tau, P5, comparaison face à SMCWLT) OL_rsf2 (Sellers 1992) vs OL_ctrl (Sakaguchi & Zeng 2009).
2. Biais d'échantillonnage temporel : passage SMAP (06h / 18h) vs moyenne journalière 24h.
"""
import os
import glob
import datetime
import time
import multiprocessing as mp
import numpy as np
import pandas as pd
import netCDF4 as nc
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco"
AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/diag2018_janmay")
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

LIS_INPUT = os.path.join(BASE_DIR, "data/lis_input/lis_input_NorthMor_5km.nc")
SOILPARM_PATH = os.path.join(BASE_DIR, "data/land_params/noahmp401_parms/SOILPARM.TBL")

# Static data
with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(bool)
    texture_3d = ds.variables["TEXTURE"][:]
    soiltype = np.argmax(texture_3d, axis=0) + 1

smcwlt_table = {}
with open(SOILPARM_PATH, "r") as f:
    in_stas = False
    for line in f:
        if "STAS" in line and not "STAS-RUC" in line:
            in_stas = True
            continue
        if "STAS-RUC" in line:
            break
        if in_stas and line.strip() and line.strip()[0].isdigit():
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 10:
                smcwlt_table[int(parts[0])] = float(parts[9])

smcwlt_grid = np.zeros_like(soiltype, dtype=float)
for cid in smcwlt_table:
    smcwlt_grid[soiltype == cid] = smcwlt_table[cid]

TEXTURE_NAMES = {
    1: "Sand", 2: "Loamy Sand", 3: "Sandy Loam", 4: "Silt Loam", 5: "Silt",
    6: "Loam", 7: "Sandy Clay Loam", 8: "Silty Clay Loam", 9: "Clay Loam",
    10: "Sandy Clay", 11: "Silty Clay", 12: "Clay"
}
NOMINAL_CLAY = {
    1: 3.0, 2: 6.0, 3: 10.0, 4: 13.0, 5: 6.0, 6: 19.0,
    7: 27.0, 8: 34.0, 9: 34.0, 10: 42.0, 11: 47.0, 12: 58.0
}

# Exponential decay for drydown
def exp_decay(t, theta_res, delta_theta, tau):
    return theta_res + delta_theta * np.exp(-t / tau)

def fit_single_drydown(t_obs, sm_obs):
    if len(t_obs) < 4:
        return None
    ss_tot = np.sum((sm_obs - np.mean(sm_obs))**2)
    if ss_tot < 1e-7:
        return None
    lb = [0.001, 0.001, 0.5]
    ub = [0.55, 0.50, 60.0]
    p0 = [min(sm_obs), max(sm_obs) - min(sm_obs), 5.0]
    p0[0] = max(lb[0], min(ub[0], p0[0]))
    p0[1] = max(lb[1], min(ub[1], p0[1]))
    try:
        popt, _ = curve_fit(exp_decay, t_obs, sm_obs, p0=p0, bounds=(lb, ub), maxfev=600)
        theta_res, delta_theta, tau = popt
        pred = exp_decay(t_obs, *popt)
        ss_res = np.sum((sm_obs - pred)**2)
        r2 = 1.0 - (ss_res / ss_tot)
        if r2 >= 0.5 and delta_theta > 0.002 and (0.5 <= tau <= 60.0):
            return {"theta_res": float(theta_res), "delta_theta": float(delta_theta), "tau": float(tau), "r2": float(r2)}
        return None
    except Exception:
        return None

# Load precipitation from OPL_noirr_2016_2020 (daily)
print("[INFO] Loading daily precipitation for 2018...")
opl_files = sorted(glob.glob(os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output/2018-*/SURFACEMODEL/*/LIS_HIST_2018*.nc")))
date_precip = {}
for fp in opl_files:
    fname = os.path.basename(fp)
    dstr = fname.split("_")[2][:8] # YYYYMMDD
    dt_end = datetime.datetime.strptime(dstr, "%Y%m%d")
    dt_sim = dt_end - datetime.timedelta(days=1)
    sim_dstr = dt_sim.strftime("%Y%m%d")
    with nc.Dataset(fp) as ds:
        p = ds.variables["TotalPrecip_tavg"][:].squeeze() * 86400.0 # mm/day
        date_precip[sim_dstr] = p

print(f"[INFO] Loaded precipitation for {len(date_precip)} days.")

# Days of 2018
start_date = datetime.date(2018, 1, 1)
end_date = datetime.date(2018, 12, 31)
all_dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
dates_str = [d.strftime("%Y%m%d") for d in all_dates]

n_days = len(dates_str)
precip_cube = np.zeros((n_days, 121, 181), dtype=np.float32)
for i, ds_str in enumerate(dates_str):
    if ds_str in date_precip:
        precip_cube[i] = date_precip[ds_str]

# Fast extraction of hourly files for OL_ctrl and OL_rsf2
print("[INFO] Processing hourly files for OL_ctrl and OL_rsf2...")
dir_ctrl = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_ctrl_hourly_2018/output/SURFACEMODEL")
dir_rsf2 = os.path.join(BASE_DIR, "experiments/NorthMor/matrix_2016_2020/sensitivity_2018/OL_rsf2_hourly_2018/output/SURFACEMODEL")

ctrl_daily_mean = np.full((n_days, 121, 181), np.nan, dtype=np.float32)
ctrl_06h = np.full((n_days, 121, 181), np.nan, dtype=np.float32)
ctrl_18h = np.full((n_days, 121, 181), np.nan, dtype=np.float32)
rsf2_daily_mean = np.full((n_days, 121, 181), np.nan, dtype=np.float32)

t0 = time.time()

def process_day(i):
    dt = all_dates[i]
    dstr = dates_str[i]
    ym = dstr[:6]
    next_dt = dt + datetime.timedelta(days=1)
    next_dstr = next_dt.strftime("%Y%m%d")
    next_ym = next_dstr[:6]
    
    flist_ctrl = [os.path.join(dir_ctrl, ym, f"LIS_HIST_{dstr}{h:02d}00.d01.nc") for h in range(1, 24)]
    flist_ctrl.append(os.path.join(dir_ctrl, next_ym, f"LIS_HIST_{next_dstr}0000.d01.nc"))
    
    flist_rsf2 = [os.path.join(dir_rsf2, ym, f"LIS_HIST_{dstr}{h:02d}00.d01.nc") for h in range(1, 24)]
    flist_rsf2.append(os.path.join(dir_rsf2, next_ym, f"LIS_HIST_{next_dstr}0000.d01.nc"))
    
    if not all(os.path.exists(f) for f in flist_ctrl):
        return i, None, None, None, None
        
    c_hourly = []
    c_06 = None
    c_18 = None
    for h_idx, f in enumerate(flist_ctrl):
        with nc.Dataset(f) as ds:
            sm1 = ds.variables["SoilMoist_tavg"][0].squeeze()
            c_hourly.append(sm1)
            if h_idx == 5:
                c_06 = sm1
            elif h_idx == 17:
                c_18 = sm1
                
    r_hourly = []
    for f in flist_rsf2:
        with nc.Dataset(f) as ds:
            r_hourly.append(ds.variables["SoilMoist_tavg"][0].squeeze())
            
    c_mean = np.mean(c_hourly, axis=0)
    r_mean = np.mean(r_hourly, axis=0)
    return i, c_mean, c_06, c_18, r_mean

print("[INFO] Running parallel extraction with 16 workers...")
with mp.Pool(16) as pool:
    results = pool.map(process_day, range(n_days))

for i, c_mean, c_06, c_18, r_mean in results:
    if c_mean is not None:
        ctrl_daily_mean[i] = c_mean
        ctrl_06h[i] = c_06
        ctrl_18h[i] = c_18
        rsf2_daily_mean[i] = r_mean

print(f"[INFO] Daily cubes ready in {time.time() - t0:.1f} s.")

# -------------------------------------------------------------
# 1. P5 Analysis and comparison with SMCWLT
# -------------------------------------------------------------
print("[INFO] Computing P5 percentiles and comparison with SMCWLT...")
p5_rows = []

seasons = {
    'ANN': list(range(n_days)),
    'MAM': [i for i, d in enumerate(all_dates) if d.month in [3, 4, 5]],
    'JJA': [i for i, d in enumerate(all_dates) if d.month in [6, 7, 8]],
}

for tid in range(1, 13):
    tmask = (soiltype == tid) & landmask
    n_pix = int(np.sum(tmask))
    if n_pix < 10:
        continue
    wlt_val = float(np.mean(smcwlt_grid[tmask]))
    clay_pct = NOMINAL_CLAY.get(tid, np.nan)
    
    for s_name, s_idx in seasons.items():
        ctrl_sub = ctrl_daily_mean[s_idx][:, tmask]
        rsf2_sub = rsf2_daily_mean[s_idx][:, tmask]
        
        p5_ctrl = float(np.nanpercentile(ctrl_sub, 5))
        p5_rsf2 = float(np.nanpercentile(rsf2_sub, 5))
        
        freq_below_wlt_ctrl = float(np.mean(ctrl_sub <= (wlt_val + 1e-4)) * 100.0)
        freq_below_wlt_rsf2 = float(np.mean(rsf2_sub <= (wlt_val + 1e-4)) * 100.0)
        
        p5_rows.append({
            'season': s_name,
            'soil_id': tid,
            'texture_name': TEXTURE_NAMES[tid],
            'clay_pct': clay_pct,
            'smcwlt': round(wlt_val, 3),
            'n_pixels': n_pix,
            'P5_ctrl': round(p5_ctrl, 4),
            'P5_rsf2': round(p5_rsf2, 4),
            'delta_P5_rsf2_minus_ctrl': round(p5_rsf2 - p5_ctrl, 4),
            'P5_minus_smcwlt_ctrl': round(p5_ctrl - wlt_val, 4),
            'P5_minus_smcwlt_rsf2': round(p5_rsf2 - wlt_val, 4),
            'freq_below_wlt_ctrl_pct': round(freq_below_wlt_ctrl, 2),
            'freq_below_wlt_rsf2_pct': round(freq_below_wlt_rsf2, 2)
        })

df_p5 = pd.DataFrame(p5_rows)

# -------------------------------------------------------------
# 2. Drydown Episodes and Exponential Fitting (tau) - Parallelized
# -------------------------------------------------------------
print("[INFO] Identifying drydown events and fitting exponential decay...")
pixel_coords_sub = np.argwhere(landmask)[::3]

def process_pixel_drydown(idx):
    r, c = pixel_coords_sub[idx]
    st = soiltype[r, c]
    wlt = smcwlt_grid[r, c]
    p_ser = precip_cube[:, r, c]
    c_ser = ctrl_daily_mean[:, r, c]
    r_ser = rsf2_daily_mean[:, r, c]
    
    events = []
    i = 0
    while i < n_days - 7:
        if p_ser[i] >= 5.0 and np.isfinite(p_ser[i]):
            dry_len = 0
            k = i + 1
            while k < n_days and (p_ser[k] < 1.0) and np.isfinite(p_ser[k]):
                dry_len += 1
                k += 1
                
            if dry_len >= 7:
                t_idx = np.arange(1, dry_len + 1)
                c_win = c_ser[i + 1 : i + 1 + dry_len]
                r_win = r_ser[i + 1 : i + 1 + dry_len]
                
                fit_c = fit_single_drydown(t_idx, c_win)
                fit_r = fit_single_drydown(t_idx, r_win)
                
                if fit_c is not None and fit_r is not None:
                    ev_date = all_dates[i + 1]
                    m = ev_date.month
                    season = "MAM" if m in [3,4,5] else ("JJA" if m in [6,7,8] else ("SON" if m in [9,10,11] else "DJF"))
                    
                    events.append({
                        'soil_id': st,
                        'texture_name': TEXTURE_NAMES[st],
                        'clay_pct': NOMINAL_CLAY.get(st, np.nan),
                        'smcwlt': wlt,
                        'date': ev_date.isoformat(),
                        'season': season,
                        'dry_len': dry_len,
                        'tau_ctrl': fit_c['tau'],
                        'theta_res_ctrl': fit_c['theta_res'],
                        'r2_ctrl': fit_c['r2'],
                        'tau_rsf2': fit_r['tau'],
                        'theta_res_rsf2': fit_r['theta_res'],
                        'r2_rsf2': fit_r['r2']
                    })
            i = k
        else:
            i += 1
    return events

with mp.Pool(16) as pool:
    list_of_events = pool.map(process_pixel_drydown, range(len(pixel_coords_sub)))

drydown_events = [ev for sublist in list_of_events for ev in sublist]
df_events = pd.DataFrame(drydown_events)
print(f"[INFO] Fitted {len(df_events)} paired drydown events.")

# Texture summary for drydown
df_events_summary = df_events.groupby(['soil_id', 'texture_name', 'clay_pct']).agg(
    n_events=('tau_ctrl', 'count'),
    tau_ctrl_median=('tau_ctrl', 'median'),
    tau_rsf2_median=('tau_rsf2', 'median'),
    theta_res_ctrl_median=('theta_res_ctrl', 'median'),
    theta_res_rsf2_median=('theta_res_rsf2', 'median'),
    r2_ctrl_mean=('r2_ctrl', 'mean'),
    r2_rsf2_mean=('r2_rsf2', 'mean')
).reset_index()

df_events_summary['delta_tau_median'] = df_events_summary['tau_rsf2_median'] - df_events_summary['tau_ctrl_median']
df_events_summary['delta_theta_res_median'] = df_events_summary['theta_res_rsf2_median'] - df_events_summary['theta_res_ctrl_median']

# Merge P5 into drydown summary
p5_ann = df_p5[df_p5['season'] == 'ANN'][['soil_id', 'smcwlt', 'P5_ctrl', 'P5_rsf2', 'delta_P5_rsf2_minus_ctrl', 'P5_minus_smcwlt_ctrl', 'P5_minus_smcwlt_rsf2', 'freq_below_wlt_ctrl_pct', 'freq_below_wlt_rsf2_pct']]
df_drydown_full = pd.merge(df_events_summary, p5_ann, on='soil_id').sort_values('clay_pct')

out_csv_drydown = os.path.join(OUT_DIR, "ol_hourly_drydown_comparison.csv")
df_drydown_full.to_csv(out_csv_drydown, index=False)
print(f"[INFO] Saved {out_csv_drydown}")

# -------------------------------------------------------------
# 3. SMAP Overpass Sampling Bias (06h / 18h vs 24h Daily Mean)
# -------------------------------------------------------------
print("[INFO] Computing SMAP overpass sampling biases...")
bias_rows = []

for tid in range(1, 13):
    tmask = (soiltype == tid) & landmask
    if np.sum(tmask) < 10:
        continue
    clay_pct = NOMINAL_CLAY.get(tid, np.nan)
    
    for s_name, s_idx in seasons.items():
        mean_24h = ctrl_daily_mean[s_idx][:, tmask]
        sm_06h = ctrl_06h[s_idx][:, tmask]
        sm_18h = ctrl_18h[s_idx][:, tmask]
        
        diff_06 = sm_06h - mean_24h
        diff_18 = sm_18h - mean_24h
        
        bias_rows.append({
            'season': s_name,
            'soil_id': tid,
            'texture_name': TEXTURE_NAMES[tid],
            'clay_pct': clay_pct,
            'bias_06h_mean': round(float(np.nanmean(diff_06)), 5),
            'bias_06h_std': round(float(np.nanstd(diff_06)), 5),
            'bias_18h_mean': round(float(np.nanmean(diff_18)), 5),
            'bias_18h_std': round(float(np.nanstd(diff_18)), 5),
            'diurnal_amplitude': round(float(np.nanmean(sm_06h - sm_18h)), 5)
        })

df_bias = pd.DataFrame(bias_rows)
out_csv_bias = os.path.join(OUT_DIR, "ol_smap_overpass_sampling_bias.csv")
df_bias.to_csv(out_csv_bias, index=False)
print(f"[INFO] Saved {out_csv_bias}")

# -------------------------------------------------------------
# Figures for Part 2.d
# -------------------------------------------------------------
print("[INFO] Generating figures...")
# Figure 1: Drydown tau and P5 comparison: OL_rsf2 vs OL_ctrl
plt.figure(figsize=(13, 5))

# Subplot 1: Tau vs Clay
plt.subplot(1, 2, 1)
plt.plot(df_drydown_full['clay_pct'].to_numpy(), df_drydown_full['tau_ctrl_median'].to_numpy(), 'o-', color='#e41a1c', lw=2.2, label='OL_ctrl (OPT_RSF=1 Sakaguchi & Zeng)')
plt.plot(df_drydown_full['clay_pct'].to_numpy(), df_drydown_full['tau_rsf2_median'].to_numpy(), 's--', color='#377eb8', lw=2.2, label='OL_rsf2 (OPT_RSF=2 Sellers 1992)')
for _, r in df_drydown_full.iterrows():
    plt.annotate(r['texture_name'], (r['clay_pct'], r['tau_rsf2_median']), textcoords='offset points', xytext=(0, 7), ha='center', fontsize=7.5)
plt.xlabel('Teneur nominale en argile (%)')
plt.ylabel('Temps caractéristique de séchage τ (jours)')
plt.title('Temps de ressuyage post-pluviale (τ median) par texture')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: P5 vs SMCWLT
plt.subplot(1, 2, 2)
plt.plot(df_drydown_full['clay_pct'].to_numpy(), df_drydown_full['smcwlt'].to_numpy() * 100, 'k--', lw=2.0, label='SMCWLT (Point de flétrissement)')
plt.plot(df_drydown_full['clay_pct'].to_numpy(), df_drydown_full['P5_ctrl'].to_numpy() * 100, 'o-', color='#e41a1c', lw=2.2, label='P5 OL_ctrl (plancher artificiel)')
plt.plot(df_drydown_full['clay_pct'].to_numpy(), df_drydown_full['P5_rsf2'].to_numpy() * 100, 's-', color='#377eb8', lw=2.2, label='P5 OL_rsf2 (séchage sans plancher)')
for _, r in df_drydown_full.iterrows():
    plt.annotate(r['texture_name'], (r['clay_pct'], r['P5_rsf2'] * 100), textcoords='offset points', xytext=(0, -12), ha='center', fontsize=7.5)
plt.xlabel('Teneur nominale en argile (%)')
plt.ylabel('Humidité volumique (vol. %)')
plt.title('Plancher de dessèchement (P5 annuel) face à SMCWLT')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
fig1_p = os.path.join(FIG_DIR, "fig_ol_rsf2_vs_ctrl_drydown_tau_p5.png")
plt.savefig(fig1_p, dpi=200)
plt.close()

# Figure 2: SMAP Overpass Sampling Bias vs 24h Mean
plt.figure(figsize=(10, 5))
ann_bias = df_bias[df_bias['season'] == 'ANN'].sort_values('clay_pct')
x = np.arange(len(ann_bias))
width = 0.35

plt.bar(x - width/2, ann_bias['bias_06h_mean'].to_numpy() * 100, width, label='Passage 06:00 UTC − Moyenne 24h', color='#4575b4')
plt.bar(x + width/2, ann_bias['bias_18h_mean'].to_numpy() * 100, width, label='Passage 18:00 UTC − Moyenne 24h', color='#d73027')
plt.axhline(0, color='black', lw=1)
plt.xticks(x, ann_bias['texture_name'].tolist(), rotation=30, ha='right')
plt.ylabel('Biais d\'échantillonnage temporel (vol. %)')
plt.title('Impact du cycle diurne : échantillonnage à l\'heure de passage SMAP vs moyenne 24h')
plt.legend(frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fig2_p = os.path.join(FIG_DIR, "fig_ol_overpass_vs_daily_mean.png")
plt.savefig(fig2_p, dpi=200)
plt.close()

print(f"[SUCCÈS] Partie 2.d terminée. Figures et CSV sauvegardés dans {OUT_DIR}.")
