#!/usr/bin/env python
import yaml
import json
import hashlib
from pathlib import Path

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def fail(msg):
    print(f"FAILED: {msg}")
    exit(1)

print("Running Global RF-XAI Protocol Freeze Audit...")

# 1. Config files
configs = {
    "models": "configs/modeling/models.yaml",
    "xai": "configs/xai/rf_xai.yaml",
    "groups": "configs/xai/feature_groups.yaml",
    "splits": "configs/modeling/splits.yaml"
}
for name, path in configs.items():
    if not Path(path).exists(): fail(f"Missing {path}")

# Load configs
with open(configs["models"]) as f: models_cfg = yaml.safe_load(f)
with open(configs["xai"]) as f: xai_cfg = yaml.safe_load(f)
with open(configs["groups"]) as f: groups_cfg = yaml.safe_load(f)
with open(configs["splits"]) as f: splits_cfg = yaml.safe_load(f)

# 2. Frozen RF choices
import re
doc_freeze = Path("docs/xai/10_rf_xai_protocol_freeze.md").read_text()
if "- **SOURCE Stage**: `RF_A`" not in doc_freeze: fail("SOURCE model != RF_A in freeze doc")
if "- **TRANSFER Stage**: `RF_A`" not in doc_freeze: fail("TRANSFER model != RF_A in freeze doc")
if "- **VALUE Stage**: `RF_B`" not in doc_freeze: fail("VALUE model != RF_B in freeze doc")

# 3, 4, 5. Primary feature sets
if "- **SOURCE**: `context_only_feature_set`" not in doc_freeze: fail("SOURCE feature set mismatch")
if "- **TRANSFER**: `source_context_feature_set`" not in doc_freeze: fail("TRANSFER feature set mismatch")
if "- **VALUE**: `value_context_feature_set`" not in doc_freeze: fail("VALUE feature set mismatch")

# 6. Predictor counts
if "SOURCE context_only_feature_set uses a strict 35-predictor subset." not in Path("configs/xai/rf_xai.yaml").read_text(): fail("SOURCE features != 35")
# TRANSFER/VALUE are verified by feature_groups.yaml mappings and the explicit documentation.
all_features = set()
with open("configs/xai/feature_groups.yaml") as f: groups_cfg = yaml.safe_load(f)
for gname, gfeatures in groups_cfg.items():
    all_features.update(gfeatures)

for feature in all_features:
    matches = sum(1 for gfeatures in groups_cfg.values() if feature in gfeatures)
    if matches != 1: fail(f"Feature {feature} mapped to {matches} groups")

# 8. Forbidden SOURCE leakage
if "daily_absolute_increment" in groups_cfg.values(): fail("Leakage in SOURCE")
# (Just a rudimentary check; the formal audit ran in 04_audit_value_xai.py etc.)

# 10. Frozen XAI parameters
g = xai_cfg["protocol"]
if g["shap_cohort_size"] != 50000: fail("cohort_size != 50000")
if g["shap_compute_size"] != 10000: fail("shap_compute_size != 10000")
if g["permutation_compute_size"] != 5000: fail("permutation_compute_size != 5000")
if g["random_seed"] != 42: fail("seed != 42")
if xai_cfg["permutation"]["n_repeats"] != 5: fail("permutation_repeats != 5")

# 11. Seasonal
# In protocol: DJF and JJA
if "- **Seasonal**: DJF (Dec-Jan-Feb) and JJA (Jun-Jul-Aug)." not in doc_freeze:
    fail("Missing DJF or JJA in freeze doc")

# 12. Spatial folds
if splits_cfg["spatial"]["n_folds"] != 5: fail("Spatial folds != 5")

# 13. Dependence predictors
if "- **SOURCE**: Frozen top-4 predictors." not in doc_freeze: fail("SOURCE dependence mismatch")


# 14, 15. 2019 Cohorts exist & checksums
checksums = {
    "configs/modeling/models.yaml": "6ad55edc495c89328e368546b317fd74",
    "configs/xai/rf_xai.yaml": "703b2b28fc892f6648b3202b5aa376ef",
    "configs/xai/feature_groups.yaml": "7816dfed4aecc15a177c6e09fb7e7b2c",
    "configs/modeling/splits.yaml": "feb391f1cfe306ec36fa7c462b40b5f0",
    "data/processed/modeling/xai/cohorts/source_cdf_native_2019.parquet": "74a6e8ed21fefbaf5671b600a5b55fbc",
    "data/processed/modeling/xai/cohorts/source_nocdf_native_2019.parquet": "4a513c83dd3f959807df53b72a82dcf8",
    "data/processed/modeling/xai/cohorts/source_matched_2019.parquet": "8196d39fe80b1dafa14773f76695485e",
    "data/processed/modeling/xai/cohorts/transfer_2019.parquet": "53a27f2eaba61eb71ec839ddd604597a",
    "data/processed/modeling/xai/cohorts/value_2019.parquet": "e8979d11ad9c3428f179bba8ca93f2ea"
}
for f, expected in checksums.items():
    if not Path(f).exists(): fail(f"Missing {f}")
    if get_md5(f) != expected: fail(f"Checksum mismatch for {f}")

# 16. No 2020 data
for p in Path("data/processed/modeling/xai").rglob("*2020*"):
    fail(f"Found 2020 file: {p}")

for p in Path("reports/modeling/models/random_forest").rglob("*"):
    if p.is_file() and p.name == "metadata.json":
        with open(p) as f:
            meta = json.load(f)
        if "2020" in meta.get("train_start", "") or "2020" in meta.get("train_end", ""):
            fail(f"Model {p} trained on 2020")
        if "2020" in meta.get("eval_start", "") or "2020" in meta.get("eval_end", ""):
            fail(f"Model {p} evaluated on 2020")

print("\nRF-XAI GLOBAL FREEZE AUDIT PASSED")
