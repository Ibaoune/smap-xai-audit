#!/usr/bin/env python
import json
import joblib
import yaml
from pathlib import Path

def fail(msg):
    print(f"FAILED: {msg}")
    exit(1)

print("Running RF-05 FINAL REFIT AUDIT...")

freeze_sha = "bb777c91889d76ecab02067520c9a9f948f3563e"
out_dir = Path("reports/modeling/models/final_refit_2016_2019")

if not out_dir.exists():
    fail("final_refit_2016_2019 directory does not exist")

meta_files = list(out_dir.rglob("metadata.json"))

# 1. Exactly 14 models
if len(meta_files) != 14:
    fail(f"Expected 14 final models, found {len(meta_files)}")

# 16. Ensure development models weren't overwritten
old_dev_models = list(Path("reports/modeling/models/random_forest").rglob("metadata.json"))
if len(old_dev_models) == 0:
    fail("Development artifacts were overwritten or deleted!")

# Track fingerprints for matching
source_matched_fps = []

# Load expected features
# Removed missing features.yaml load

with open("configs/modeling/models.yaml") as f:
    models_cfg = yaml.safe_load(f)

rf_a_params = models_cfg["models"]["random_forest"]["RF_A"]
rf_b_params = models_cfg["models"]["random_forest"]["RF_B"]

for meta_path in meta_files:
    with open(meta_path) as f:
        meta = json.load(f)
    
    # 2. Stage RF-05
    if meta.get("stage") != "RF-05": fail(f"Model {meta_path} is not stage RF-05")
    
    # 3. training_end <= 2019-12-31
    if meta.get("training_end") > "2019-12-31": fail(f"Model {meta_path} trained beyond 2019-12-31")
    
    # 4. No 2020 training date
    if "2020" in meta.get("training_start") or "2020" in meta.get("training_end"):
        fail(f"Model {meta_path} has 2020 training date")
    
    # 13. RF-04C freeze commit
    if meta.get("freeze_commit") != freeze_sha:
        fail(f"Model {meta_path} missing correct freeze commit")
    
    block = meta.get("diagnostic_block")
    features = meta.get("fitted_features")
    
    # 5 & 8-10. Verify architectures and features
    if block == "SOURCE":
        if meta.get("rf_configuration") != "RF_A": fail(f"SOURCE model != RF_A")
        if meta.get("n_features") != 35: fail(f"SOURCE features != 35")
        if meta.get("support_mode") == "matched_support":
            source_matched_fps.append(meta.get("training_support_fingerprint"))
    elif block == "TRANSFER":
        if meta.get("rf_configuration") != "RF_A": fail(f"TRANSFER model != RF_A")
        if meta.get("n_features") != 52: fail(f"TRANSFER features != 52")
    elif block == "VALUE":
        if meta.get("rf_configuration") != "RF_B": fail(f"VALUE model != RF_B")
        if meta.get("n_features") != 52: fail(f"VALUE features != 52")

    # 11 & 12. Model load and feature count check
    model_path = meta_path.parent / "model.joblib"
    if not model_path.exists(): fail(f"Missing model binary at {model_path}")
    
    try:
        model = joblib.load(model_path)
    except Exception as e:
        fail(f"Failed to load {model_path}: {e}")
        
    if model.model.n_features_in_ != meta.get("n_features"):
        fail(f"Model {model_path} exposes {model.model.n_features_in_} but metadata says {meta.get('n_features')}")
        
    # 12 & 13 Hyperparameters
    params = meta.get("model_parameters")
    if meta.get("rf_configuration") == "RF_A":
        expected = rf_a_params
    else:
        expected = rf_b_params
        
    for k, v in expected.items():
        if k == "save_model": continue
        if k == "n_jobs": continue
        if params.get(k) != v:
            fail(f"Hyperparameter mismatch in {meta_path}: {k}={params.get(k)} != {v}")

# 10. Matched SOURCE CDF/NoCDF identical keys
if len(source_matched_fps) != 2:
    fail(f"Expected 2 matched SOURCE models, found {len(source_matched_fps)}")
if source_matched_fps[0] != source_matched_fps[1]:
    fail("SOURCE matched CDF and NoCDF do NOT have identical training keys")

# 15. No 2020 predictions or XAI outputs
for p in Path("reports/modeling").rglob("*2020*"):
    if not "final" in str(p) and not "test" in str(p):
        fail(f"Found 2020 artifact: {p}")
for p in Path("data/processed/modeling/xai").rglob("*2020*"):
    if not "final" in str(p) and not "test" in str(p):
        fail(f"Found 2020 artifact: {p}")

print("\nRF-05 FINAL REFIT AUDIT PASSED")
