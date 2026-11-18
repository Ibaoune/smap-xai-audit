import os
import pandas as pd
import numpy as np

AUDIT_DIR = "/srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
DIR_WB = os.path.join(AUDIT_DIR, "reports/audits/baseflow_link")

old_wb_csv = os.path.join(DIR_WB, "seasonal_water_balance_da_minus_ol.csv")
df_old = pd.read_csv(old_wb_csv)

# Rename net_flux_drain_cum_mm -> net_water_added_by_filter_mm (with opposite sign or exact balance?)
# In water balance: Storage_change = Precip - ET - Qs - Qsb + Filter_water
# Hence Filter_water = ET + Qs + Qsb - Precip + Storage_change
# In the previous CSV, net_flux_drain_cum_mm was: delta_et + delta_total_runoff - delta_precip = Net water exported
# So the net water that the filter had to supply to sustain that extra flux drain is exactly net_flux_drain_cum_mm (assuming storage change is small over 5 years).
# But wait: if filter removes water (negative increments), then net_water_added_by_filter is negative!
# Let's check: in NoCDF, MAM has delta_et = -96 mm, delta_runoff = +21 mm -> net_flux_drain = -75 mm.
# If net_flux_drain = -75 mm, it means 75 mm less flux was evacuated, so model became drier by 75 mm.
# That matches a negative water addition by filter (-75 mm)!

# Let's align direct increments:
direct_increments_seasonal = {
    ("NoCDF", "DJF"): -142.00,
    ("NoCDF", "MAM"): -213.09,
    ("NoCDF", "JJA"): +2.78,
    ("NoCDF", "SON"): -134.58,
    ("CDF", "DJF"): -61.51,
    ("CDF", "MAM"): -60.32,
    ("CDF", "JJA"): -15.38,
    ("CDF", "SON"): -69.78,
}

direct_increments_annual = {
    ("NoCDF", 2016): -92.96,
    ("NoCDF", 2017): -78.64,
    ("NoCDF", 2018): -165.37,
    ("NoCDF", 2019): -68.75,
    ("NoCDF", 2020): -81.18,
    ("CDF", 2016): -25.38,
    ("CDF", 2017): -29.20,
    ("CDF", 2018): -105.20,
    ("CDF", 2019): -21.25,
    ("CDF", 2020): -25.94,
}

# Update seasonal water balance CSV
# Rename column net_flux_drain_cum_mm -> net_water_added_by_filter_wb_residual_mm
df_old = df_old.rename(columns={"net_flux_drain_cum_mm": "net_water_added_by_filter_wb_residual_mm"})
# Invert sign if it was defined as flux drain (ET + Q - P), so net water added is P - ET - Q = - (ET + Q - P)
# Let's store both: residual_water_added_mm and direct_increments_mm
df_old["direct_increments_4layers_mm"] = [
    direct_increments_seasonal[(r["da_experiment"], r["season"])] for _, r in df_old.iterrows()
]
df_old["discrepancy_wb_minus_direct_mm"] = df_old["net_water_added_by_filter_wb_residual_mm"] - df_old["direct_increments_4layers_mm"]

out_updated_wb = os.path.join(DIR_WB, "seasonal_water_balance_da_minus_ol.csv")
df_old.to_csv(out_updated_wb, index=False)
print("Updated seasonal water balance saved.")

# Create comprehensive comparison table
rows_comp = []
for da_exp in ["NoCDF", "CDF"]:
    for season in ["DJF", "MAM", "JJA", "SON"]:
        sub = df_old[(df_old["da_experiment"] == da_exp) & (df_old["season"] == season)].iloc[0]
        rows_comp.append({
            "experiment": da_exp,
            "period_type": "Seasonal",
            "period": season,
            "wb_residual_water_added_mm": sub["net_water_added_by_filter_wb_residual_mm"],
            "direct_increments_4layers_mm": sub["direct_increments_4layers_mm"],
            "discrepancy_mm": round(sub["discrepancy_wb_minus_direct_mm"], 2)
        })
    # Annual totals
    tot_wb = df_old[df_old["da_experiment"] == da_exp]["net_water_added_by_filter_wb_residual_mm"].sum()
    tot_dir = sum(direct_increments_annual[(da_exp, y)] for y in range(2016, 2021))
    rows_comp.append({
        "experiment": da_exp,
        "period_type": "Annual Total (2016-2020)",
        "period": "ALL",
        "wb_residual_water_added_mm": round(tot_wb, 2),
        "direct_increments_4layers_mm": round(tot_dir, 2),
        "discrepancy_mm": round(tot_wb - tot_dir, 2)
    })

df_comp = pd.DataFrame(rows_comp)
out_comp_csv = os.path.join(DIR_WB, "water_balance_vs_direct_increments.csv")
df_comp.to_csv(out_comp_csv, index=False)
print(f"Comparison saved to {out_comp_csv}")
print(df_comp.to_string())
