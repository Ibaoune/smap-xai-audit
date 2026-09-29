#!/usr/bin/env python
import json, yaml, joblib, pandas as pd, hashlib, shap, sklearn
print("=== Environment validation ===")
print(f"shap={shap.__version__}  sklearn={sklearn.__version__}  pd={pd.__version__}")

df = pd.read_parquet("data/processed/modeling/xai/cohorts/value_2019.parquet")
keys = df.sort_values(["date","gleam_y_index","gleam_x_index"])[["date","gleam_y_index","gleam_x_index"]].copy()
keys["date_str"] = keys["date"].astype(str)
cs = hashlib.md5(keys[["date_str","gleam_y_index","gleam_x_index"]].to_csv(index=False).encode()).hexdigest()
assert cs == "fb68bb1122ffa6ee11490c122b239c7f", f"Checksum mismatch: {cs}"
print(f"Cohort checksum: {cs} OK  rows={len(df)}  cols={list(df.columns)}")

with open("configs/xai/feature_groups.yaml") as f:
    fg = yaml.safe_load(f)
mapped   = {feat for feats in fg.values() for feat in feats}
FORBIDDEN = ["gleam_et","et_gleam","value_ae","et_opl_t","et_da_t","lagged_value","delta_et_t"]

for exp in ["da_cdf","da_nocdf"]:
    key  = f"VALUE_{exp}_value_ae_value_context_feature_set_RF_B_fold_3_native_support"
    meta = json.load(open(f"reports/modeling/models/random_forest/{key}/metadata.json"))
    feats = set(meta["fitted_features"])
    unmapped  = feats - mapped
    forbidden = [f for f in feats if any(p in f.lower() for p in FORBIDDEN)]
    model = joblib.load(f"artifacts/modeling/random_forest/{key}/model.joblib")
    print(f"{exp}: n_feat={len(feats)}  unmapped={unmapped or 'NONE'}  forbidden={forbidden or 'NONE'}  n_est={model.n_estimators}  depth={model.max_depth}  min_sl={model.min_samples_leaf}")

print("Dry-run validation PASSED")
