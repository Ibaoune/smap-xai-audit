#!/usr/bin/env python
import json
import yaml
import hashlib
import pandas as pd
from pathlib import Path

def fail(msg):
    print(f"FAILED: {msg}")
    exit(1)

def main():
    print("Running RF-06 FINAL 2020 EVALUATION AUDIT...")

    freeze_sha = "bb777c91889d76ecab02067520c9a9f948f3563e"
    refit_sha = "99de23e70503ff7151192e414ff66f7ec2e52c6d"
    
    # 25. Check config checksums
    def check_md5(path, expected):
        with open(path, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()
        if h != expected:
            fail(f"Checksum mismatch for {path}. Expected {expected}, got {h}")

    check_md5("configs/modeling/models.yaml", "6ad55edc495c89328e368546b317fd74")
    check_md5("configs/xai/rf_xai.yaml", "703b2b28fc892f6648b3202b5aa376ef")
    check_md5("configs/xai/feature_groups.yaml", "7816dfed4aecc15a177c6e09fb7e7b2c")
    check_md5("configs/modeling/splits.yaml", "feb391f1cfe306ec36fa7c462b40b5f0")
    
    out_dir = Path("reports/modeling/final_2020")
    if not out_dir.exists():
        fail("final_2020 metrics directory does not exist")

    # Metrics
    metrics_file = out_dir / "final_metrics_2020.csv"
    if not metrics_file.exists():
        fail("final_metrics_2020.csv missing")
    
    df_metrics = pd.read_csv(metrics_file)
    if len(df_metrics) != 14:
        fail(f"Expected 14 evaluated models, found {len(df_metrics)}")
        
    for col in ["MAE", "RMSE", "R2", "pearson_r", "MAE_skill", "RMSE_skill"]:
        if df_metrics[col].isnull().any() or not (df_metrics[col] != float('inf')).all():
            fail(f"Non-finite metric in {col}")
            
    # Target Distributions
    dists_file = out_dir / "target_distributions" / "target_distributions_2020.csv"
    if not dists_file.exists():
        fail("target_distributions_2020.csv missing")
        
    df_dists = pd.read_csv(dists_file)
    if len(df_dists) != 14:
        fail(f"Expected 14 target distributions, found {len(df_dists)}")

    # Check 2020 data and artifacts
    xai_dir = Path("data/processed/modeling/xai/final_2020")
    if not xai_dir.exists():
        fail("XAI final_2020 directory missing")
        
    perm_files = list((xai_dir / "permutation").glob("*.json"))
    if len(perm_files) != 14:
        fail(f"Expected 14 permutation JSONs, found {len(perm_files)}")
        
    source_matched_fps = []
    
    for pf in perm_files:
        with open(pf) as f:
            meta = json.load(f)
            
        # 14 & 15. Check sizes
        if meta["representative_cohort_size"] > 50000: fail("Representative cohort > 50k")
        if meta["shap_cohort_size"] > 10000: fail("SHAP cohort > 10k")
        if meta["cohort_size"] > 5000: fail("Permutation cohort > 5k")
        if meta["n_repeats"] != 5: fail("Permutation repeats != 5")
        
        if "SOURCE" in pf.name and "matched" in pf.name:
            source_matched_fps.append(meta["cohort_fingerprint"])
            
    if len(source_matched_fps) != 2:
        fail(f"Expected 2 matched SOURCE permutations, found {len(source_matched_fps)}")
    if source_matched_fps[0] != source_matched_fps[1]:
        fail("SOURCE matched CDF and NoCDF do NOT have identical test XAI keys")

    # 24. No RF-04/05 artifacts overwritten
    if len(list(Path("reports/modeling/models/final_refit_2016_2019").rglob("metadata.json"))) != 14:
        fail("RF-05 models were altered or deleted!")
    if len(list(Path("reports/modeling/models/random_forest").rglob("metadata.json"))) == 0:
        fail("RF-04 models were altered or deleted!")

    # 21 & 22. DJF/JJA and Spatial summaries exist
    djf_files = list((xai_dir / "seasonal").glob("*djf*"))
    jja_files = list((xai_dir / "seasonal").glob("*jja*"))
    spatial_files = list((xai_dir / "spatial").glob("*.csv"))
    
    if len(djf_files) == 0: fail("No DJF summaries found")
    if len(jja_files) == 0: fail("No JJA summaries found")
    if len(spatial_files) == 0: fail("No Spatial summaries found")

    print("\nRF-06 FINAL 2020 EVALUATION AUDIT PASSED")

if __name__ == "__main__":
    main()
