import os
import glob
import pandas as pd
import numpy as np

def main():
    raw_dir = "reports/modeling/baselines/raw"
    out_dir = "reports/modeling/baselines"
    
    # Process temporal/spatial outputs
    files = glob.glob(f"{raw_dir}/*.csv")
    
    dfs = []
    matched_df = None
    
    for f in files:
        if "matched_support" in f:
            matched_df = pd.read_csv(f)
            continue
            
        df = pd.read_csv(f)
        dfs.append(df)
        
    if not dfs:
        print("No raw metric files found!")
        return
        
    full_df = pd.concat(dfs, ignore_index=True)
    
    # deduplicate
    full_df = full_df.drop_duplicates(subset=['dataset', 'experiment', 'target', 'baseline', 'type', 'fold'])
    
    # Validate expected schemas
    temporal_df = full_df[full_df['type'] == 'temporal'].copy()
    spatial_df = full_df[full_df['type'] == 'spatial'].copy()
    
    # Defensive check: ensure metrics.py mathematically resolved NaN for constant baselines
    constant_baselines = ['zero', 'train_mean', 'train_median']
    if not temporal_df.loc[temporal_df['baseline'].isin(constant_baselines), 'Pearson'].isna().all():
        print("WARNING: Some constant baselines have non-NaN Pearson. This indicates metrics.py is bypassed or has scale issues.")
    if not spatial_df.loc[spatial_df['baseline'].isin(constant_baselines), 'Pearson'].isna().all():
        print("WARNING: Some constant baselines have non-NaN Pearson in spatial folds.")
    
    # Save
    temporal_df.sort_values(by=['dataset', 'experiment', 'target', 'baseline', 'fold']).to_csv(f"{out_dir}/temporal_baseline_metrics.csv", index=False)
    spatial_df.sort_values(by=['dataset', 'experiment', 'target', 'baseline', 'fold']).to_csv(f"{out_dir}/spatial_baseline_metrics.csv", index=False)
    
    if matched_df is not None:
        matched_df.to_csv(f"{out_dir}/source_matched_support_metrics.csv", index=False)
        
    # Baseline summary
    mean_df = temporal_df.groupby(['dataset', 'experiment', 'target', 'baseline'])[['MAE', 'RMSE', 'bias', 'R2', 'Pearson']].mean().reset_index()
    mean_df.to_csv(f"{out_dir}/baseline_summary.csv", index=False)
    print("Merge complete.")

if __name__ == "__main__":
    main()
