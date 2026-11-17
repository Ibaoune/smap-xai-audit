import os
import pandas as pd
from pathlib import Path
import hashlib

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    print("Running RF-06B RESULT CONSOLIDATION AUDIT...")
    
    # Check target distributions
    td_path = Path("reports/modeling/final_2020/target_distributions/final_target_distributions_2020.csv")
    assert td_path.exists(), "Target distributions file missing"
    
    td_df = pd.read_csv(td_path)
    exps = td_df["experiment"].unique()
    assert "da_cdf" in exps and "da_nocdf" in exps, "Missing CDF or NoCDF in target distributions"
    
    # Check seasonal summaries
    seasonal_path = Path("data/processed/modeling/xai/final_2020/summaries/seasonal_group_summary_2020.csv")
    assert seasonal_path.exists(), "Seasonal summary missing"
    seas_df = pd.read_csv(seasonal_path)
    models = seas_df["model_key"].unique()
    assert len(models) == 12, f"Expected 12 models in seasonal summary, found {len(models)}"
    
    # Check spatial summaries
    spatial_path = Path("data/processed/modeling/xai/final_2020/summaries/spatial_group_stability_2020.csv")
    assert spatial_path.exists(), "Spatial summary missing"
    spat_df = pd.read_csv(spatial_path)
    assert len(spat_df["model_key"].unique()) == 12, "Missing models in spatial summary"
    
    # Check dependence summaries
    dep_path = Path("data/processed/modeling/xai/final_2020/summaries/dependence_summary_2020.csv")
    assert dep_path.exists(), "Dependence summary missing"
    dep_df = pd.read_csv(dep_path)
    
    # Check config checksums
    assert get_md5("configs/modeling/models.yaml") == "6ad55edc495c89328e368546b317fd74"
    assert get_md5("configs/xai/rf_xai.yaml") == "703b2b28fc892f6648b3202b5aa376ef"
    assert get_md5("configs/xai/feature_groups.yaml") == "7816dfed4aecc15a177c6e09fb7e7b2c"
    assert get_md5("configs/modeling/splits.yaml") == "feb391f1cfe306ec36fa7c462b40b5f0"
    
    print("RF-06B RESULT CONSOLIDATION AUDIT PASSED")

if __name__ == "__main__":
    main()
