import json
import glob
from collections import defaultdict
import yaml

with open("configs/xai/feature_groups.yaml", "r") as f:
    groups = yaml.safe_load(f)

# reverse map
feat_to_group = {}
for g, feats in groups.items():
    for feat in feats:
        feat_to_group[feat] = g

GROUP_MAP = {
    "antecedent_land_surface_fluxes": "Antecedent fluxes",
    "antecedent_soil_moisture_state": "Antecedent soil moisture",
    "assimilation_diagnostics_or_history": "Assimilation history",
    "forcing_perturbation_controls": "Forcing-discrepancy controls",
    "land_cover_or_vegetation": "Land cover",
    "meteorological_forcing": "Meteorological forcing",
    "soil_properties": "Soil properties",
    "temporal_context": "Temporal context",
    "topography": "Topography"
}

PRED_MAP = {
    "ssm_lag1": "Antecedent SSM (t−1)",
    "precip_lag1": "Precipitation (t−1)",
    "rzsm_lag1": "Antecedent RZSM (t−1)",
    "tair_lag1": "Air temperature (t−1)",
    "precip_pre3d_sum": "Precipitation, previous 3 d",
    "precip_pre7d_sum": "Precipitation, previous 7 d",
    "day_of_year": "Day of year",
    "doy_sin": "DOY sine",
    "doy_cos": "DOY cosine",
    "elevation": "Elevation",
    "land_cover_fraction_16": "Land-cover fraction 16",
    "soil_texture_fraction_1": "Soil-texture fraction 1",
    "rzsm_opl_lag1": "Antecedent OPL RZSM (t-1)",
    "baseflow_opl_lag1": "Antecedent OPL Baseflow (t-1)",
    "et_opl_lag1": "Antecedent OPL ET (t-1)",
    "ssm_opl_lag1": "Antecedent OPL SSM (t-1)",
    "source_signed_increment_pre7d_sum": "Signed DA increment, previous 7 d",
    "precip_t": "Precipitation (t)",
    "soil_texture_fraction_6": "Soil-texture fraction 6",
    "tair_t": "Air temperature (t)"
}

model_files = glob.glob("reports/modeling/models/random_forest/*/metadata.json")

model_feats = defaultdict(set)
removed_feats = set()
requested_feats = set()

for mf in model_files:
    with open(mf, "r") as f:
        meta = json.load(f)
    block = meta["block"]
    target = meta["target"]
    exp = meta["experiment"]
    
    # Store by (block, target, exp)
    key = (block, target, exp)
    model_feats[key].update(meta.get("fitted_features", []))
    removed_feats.update(meta.get("removed_zero_variance_features", []))
    requested_feats.update(meta.get("requested_features", []))

# Identify SOURCE
source_feats = set()
for k, v in model_feats.items():
    if k[0] == "SOURCE": source_feats.update(v)

# Identify TRANSFER
transfer_feats = defaultdict(set)
for k, v in model_feats.items():
    if k[0] == "TRANSFER":
        transfer_feats[k[1]].update(v)

# Identify VALUE
value_cdf = set()
value_nocdf = set()
for k, v in model_feats.items():
    if k[0] == "VALUE":
        if k[2] == "da_cdf": value_cdf.update(v)
        else: value_nocdf.update(v)

all_fitted = set()
for feats in model_feats.values():
    all_fitted.update(feats)

print("A. Total unique fitted:", len(all_fitted))
print("B. SOURCE predictor count:", len(source_feats))
print("C. TRANSFER predictor counts:")
for t, fts in transfer_feats.items():
    print(f"   {t}: {len(fts)}")
print("D. VALUE predictor count: CDF=", len(value_cdf), "NoCDF=", len(value_nocdf))
print("E. Predictors removed (zero var):", ", ".join(removed_feats))
print("F. Predictors requested but NOT fitted anywhere:", ", ".join(requested_feats - all_fitted - removed_feats))

print("H. Forcing discrepancy controls present:")
fdc = [f for f in all_fitted if "delta_precip_forcing" in f]
print("   ", fdc)

def get_temp_def(f):
    if "pre3d" in f: return "previous 3-day window"
    if "pre7d" in f: return "previous 7-day window"
    if "lag1" in f: return "lag 1 day"
    if "_t" in f or "precip_t" == f or "tair_t" == f: return "same day t"
    if "month" in f or "day" in f or "doy" in f: return "temporal/calendar"
    if "elevation" in f or "fraction" in f: return "static"
    return "static"

import csv
import sys

writer = csv.writer(sys.stdout)
headers = ["Repository Name", "Publication Label", "Group", "Temporal Definition", "SOURCE", "TRANSFER_rzsm", "TRANSFER_et", "TRANSFER_sr", "TRANSFER_bf", "VALUE_CDF", "VALUE_NoCDF"]
writer.writerow(headers)

for f in sorted(all_fitted):
    pub_label = PRED_MAP.get(f, f.replace("_", " ").title())
    grp = GROUP_MAP.get(feat_to_group.get(f, ""), "Unknown")
    temp = get_temp_def(f)
    src = "Yes" if f in source_feats else "No"
    t_rzsm = "Yes" if f in transfer_feats.get("delta_rzsm", set()) else "No"
    t_et = "Yes" if f in transfer_feats.get("delta_et", set()) else "No"
    t_sr = "Yes" if f in transfer_feats.get("delta_surface_runoff", set()) else "No"
    t_bf = "Yes" if f in transfer_feats.get("delta_baseflow", set()) else "No"
    v_cdf = "Yes" if f in value_cdf else "No"
    v_nocdf = "Yes" if f in value_nocdf else "No"
    
    writer.writerow([f, pub_label, grp, temp, src, t_rzsm, t_et, t_sr, t_bf, v_cdf, v_nocdf])

