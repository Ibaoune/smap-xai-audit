import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
OUTPUT_DIR = os.path.join(AUDIT_DIR, "reports/audits/drydown_point1_uncensored")
events_file = os.path.join(OUTPUT_DIR, "drydown_events_uncensored_n3.csv")
df_base = pd.read_csv(events_file)

NOMINAL_CLAY_FRACTION = {
    1: 0.03,
    2: 0.06,
    3: 0.10,
    4: 0.13,
    5: 0.06,
    6: 0.19,
    7: 0.27,
    8: 0.34,
    9: 0.34,
    10: 0.42,
    11: 0.47,
    12: 0.58,
}
df_base["clay_fraction"] = df_base["soil_id"].map(NOMINAL_CLAY_FRACTION)

def block_bootstrap_slope(df_data, x_col, y_col, block_col="block_id", n_boot=500, ci=95, seed=42):
    blocks = df_data[block_col].unique()
    n_blocks = len(blocks)
    if n_blocks < 2 or len(df_data) < 5:
        return np.nan, np.nan, np.nan
        
    p_obs = np.polyfit(df_data[x_col].values, df_data[y_col].values, 1)[0]
    
    rng = np.random.default_rng(seed)
    block_indices = [np.where(df_data[block_col].values == b)[0] for b in blocks]
    x_arr = df_data[x_col].values
    y_arr = df_data[y_col].values
    
    boot_slopes = np.empty(n_boot)
    for i in range(n_boot):
        chosen = rng.choice(len(block_indices), size=n_blocks, replace=True)
        idx_sample = np.concatenate([block_indices[c] for c in chosen])
        xs = x_arr[idx_sample]
        ys = y_arr[idx_sample]
        if len(xs) >= 5 and np.std(xs) > 1e-4:
            boot_slopes[i] = np.polyfit(xs, ys, 1)[0]
        else:
            boot_slopes[i] = np.nan
            
    valid = boot_slopes[np.isfinite(boot_slopes)]
    alpha = (100.0 - ci) / 2.0
    low = np.percentile(valid, alpha) if len(valid) > 0 else np.nan
    high = np.percentile(valid, 100.0 - alpha) if len(valid) > 0 else np.nan
    return float(p_obs), float(low), float(high)

slope_rows = []
for subset_name, df_data in [
    ("Avec Sable (Toutes textures)", df_base),
    ("Sans Sable (Exclusion Sand #1)", df_base[df_base["soil_id"] != 1])
]:
    for season in ["MAM", "JJA", "SON", "DJF", "ALL"]:
        sub = df_data if season == "ALL" else df_data[df_data["season"] == season]
        p_smap, lo_smap, hi_smap = block_bootstrap_slope(sub, "clay_fraction", "tau_smap")
        p_ol, lo_ol, hi_ol = block_bootstrap_slope(sub, "clay_fraction", "tau_ol")
        slope_rows.append({
            "subset": subset_name,
            "season": season,
            "n_events": len(sub),
            "slope_smap_d_per_pct": round(p_smap / 100.0, 3), # d per % clay
            "slope_smap_ci95_low": round(lo_smap / 100.0, 3),
            "slope_smap_ci95_high": round(hi_smap / 100.0, 3),
            "slope_ol_d_per_pct": round(p_ol / 100.0, 3),
            "slope_ol_ci95_low": round(lo_ol / 100.0, 3),
            "slope_ol_ci95_high": round(hi_ol / 100.0, 3),
        })

df_slopes = pd.DataFrame(slope_rows)
out_slopes_csv = os.path.join(OUTPUT_DIR, "tau_vs_clay_slopes_no_sand.csv")
df_slopes.to_csv(out_slopes_csv, index=False)
print("--- TABLE DES PENTES TAU VS ARGILE ---")
print(df_slopes.to_string())

# Plot updated MAM figure without Sand
df_medians = pd.read_csv(os.path.join(OUTPUT_DIR, "tau_class_medians_with_ci.csv"))
med_mam = df_medians[(df_medians["season"] == "MAM") & (df_medians["soil_id"] != 1)]
sub_mam_nosand = df_base[(df_base["season"] == "MAM") & (df_base["soil_id"] != 1)]

fig, ax = plt.subplots(figsize=(8.5, 6))
yerr_smap = [
    med_mam["tau_smap_median"] - med_mam["tau_smap_ci95_low"],
    med_mam["tau_smap_ci95_high"] - med_mam["tau_smap_median"]
]
yerr_ol = [
    med_mam["tau_ol_median"] - med_mam["tau_ol_ci95_low"],
    med_mam["tau_ol_ci95_high"] - med_mam["tau_ol_median"]
]

ax.errorbar(med_mam["clay_fraction_pct"] - 0.4, med_mam["tau_smap_median"], yerr=yerr_smap,
            fmt="o", color="#2980b9", ecolor="#2980b9", elinewidth=1.5, capsize=4,
            label="SMAP uncensored (médiane ± IC 95%)", zorder=3)
ax.errorbar(med_mam["clay_fraction_pct"] + 0.4, med_mam["tau_ol_median"], yerr=yerr_ol,
            fmt="s", color="#e67e22", ecolor="#e67e22", elinewidth=1.5, capsize=4,
            label="Noah-MP OL (médiane ± IC 95%)", zorder=3)

# Regressions without sand
fit_s = np.polyfit(sub_mam_nosand["clay_fraction"], sub_mam_nosand["tau_smap"], 1)
fit_o = np.polyfit(sub_mam_nosand["clay_fraction"], sub_mam_nosand["tau_ol"], 1)
x_grid = np.linspace(0.08, 0.60, 50)

row_mam_nosand = df_slopes[(df_slopes["subset"] == "Sans Sable (Exclusion Sand #1)") & (df_slopes["season"] == "MAM")].iloc[0]
p_s_val = row_mam_nosand["slope_smap_d_per_pct"]
p_o_val = row_mam_nosand["slope_ol_d_per_pct"]

ax.plot(x_grid * 100.0, np.polyval(fit_s, x_grid), color="#2980b9", linestyle="-", linewidth=2,
        label=f"SMAP régression : {p_s_val:+.3f} j/%argile [{row_mam_nosand['slope_smap_ci95_low']:+.3f}, {row_mam_nosand['slope_smap_ci95_high']:+.3f}]")
ax.plot(x_grid * 100.0, np.polyval(fit_o, x_grid), color="#e67e22", linestyle="--", linewidth=2,
        label=f"OL régression : {p_o_val:+.3f} j/%argile [{row_mam_nosand['slope_ol_ci95_low']:+.3f}, {row_mam_nosand['slope_ol_ci95_high']:+.3f}]")

for _, r in med_mam.iterrows():
    ax.annotate(r["texture"], (r["clay_fraction_pct"], max(r["tau_smap_median"], r["tau_ol_median"]) + 0.45),
                ha="center", fontsize=8.5, color="#333333", fontweight="semibold")

ax.set_xlabel("Fraction nominale d'argile (%)", fontsize=11, fontweight="bold")
ax.set_ylabel("Constante de temps de séchage tau (jours)", fontsize=11, fontweight="bold")
ax.set_title("Sensibilité tau vs argile au printemps (MAM) — Sans le sable (#1)\nMédianes par classe avec IC 95% (bootstrap blocs 7×7)", fontsize=12, fontweight="bold")
ax.legend(fontsize=9.5, loc="upper left")
ax.grid(True, linestyle="--", alpha=0.5)
ax.set_ylim(bottom=0, top=14)
plt.tight_layout()
out_fig = os.path.join(OUTPUT_DIR, "tau_vs_clay_regression_mam_no_sand.png")
plt.savefig(out_fig, dpi=300)
plt.close()
print(f"[A2] Figure sauvegardée dans {out_fig}")
