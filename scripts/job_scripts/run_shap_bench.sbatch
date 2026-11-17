#!/bin/bash
#SBATCH --job-name=shap_bench
#SBATCH --output=logs/slurm/shap_bench_%j.out
#SBATCH --error=logs/slurm/shap_bench_%j.err
#SBATCH --mem=64G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute

source ~/.bashrc
conda activate smap-xai-audit

python - <<'EOF'
import joblib, shap, time, numpy as np, pandas as pd, json
from smap_xai.modeling.training import load_data

exp    = "da_cdf"
TARGET = "value_ae"
key    = f"VALUE_{exp}_{TARGET}_value_context_feature_set_RF_B_fold_3_native_support"
meta   = json.load(open(f"reports/modeling/models/random_forest/{key}/metadata.json"))
fitted_features = meta["fitted_features"]
model  = joblib.load(f"artifacts/modeling/random_forest/{key}/model.joblib")
print(f"n_est={model.n_estimators}  max_depth={model.max_depth}  n_feat={len(fitted_features)}")

df = load_data("VALUE", exp, TARGET, fitted_features,
               "2019-01-01", "2019-12-31",
               meta_cols=["date","gleam_y_index","gleam_x_index"])
for col in ["month","spatial_fold"]:
    if col in df.columns: df = df.drop(columns=[col])

X = df[fitted_features].head(500)
explainer = shap.TreeExplainer(model, feature_perturbation="tree_path_dependent", model_output="raw")

for batch in [100, 250, 500]:
    Xb = X.head(batch)
    t0 = time.time()
    sv = explainer.shap_values(Xb)
    elapsed = time.time() - t0
    rate = batch / elapsed
    print(f"batch={batch:4d}  elapsed={elapsed:.1f}s  rate={rate:.2f} rows/s  "
          f"est_2k={2000/rate:.0f}s  est_5k={5000/rate:.0f}s  est_10k={10000/rate:.0f}s")
EOF
