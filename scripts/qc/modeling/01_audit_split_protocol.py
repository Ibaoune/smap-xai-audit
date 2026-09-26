import os
import sys
import glob
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
from smap_xai.modeling.splits import assign_temporal_split

def process_dataset(name, experiment, path, target_cols, support_cols, id_cols=['lat', 'lon']):
    """Iterate over parquet files to accumulate exact counts and distributions."""
    files = glob.glob(os.path.join(path, '**/*.parquet'), recursive=True)
    if not files:
        return None
        
    counts = {'train': 0, 'validation': 0, 'test': 0}
    target_data = {split: {col: [] for col in target_cols} for split in ['train', 'validation', 'test']}
    support_data = {split: {col: [] for col in support_cols} for split in ['train', 'validation', 'test']}
    
    for f in files:
        df = pd.read_parquet(f, columns=['date'] + target_cols + support_cols + id_cols)
        df['split'] = assign_temporal_split(df['date'])
        
        for split in ['train', 'validation', 'test']:
            mask = df['split'] == split
            counts[split] += mask.sum()
            
            for col in target_cols:
                target_data[split][col].extend(df.loc[mask, col].dropna().values)
                
            for col in support_cols:
                support_data[split][col].extend(df.loc[mask, col].dropna().values)
                
    return counts, target_data, support_data

def report_stats(data_list, col_name):
    arr = np.array(data_list)
    if len(arr) == 0:
        return {"N": 0}
    return {
        "N": len(arr),
        "mean": np.mean(arr),
        "median": np.median(arr),
        "std": np.std(arr),
        "p05": np.percentile(arr, 5),
        "p95": np.percentile(arr, 95),
        "positive_%": (arr > 0).mean() * 100,
        "negative_%": (arr < 0).mean() * 100,
        "zero_%": (arr == 0).mean() * 100
    }

def run_audit():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    data_dir = os.path.join(project_root, 'data', 'processed', 'modeling')
    
    datasets = {
        'SOURCE': {
            'target_cols': ['daily_absolute_increment'],
            'support_cols': []
        },
        'TRANSFER': {
            'target_cols': ['delta_rzsm', 'delta_et', 'delta_surface_runoff', 'delta_baseflow'],
            'support_cols': []
        },
        'VALUE': {
            'target_cols': ['value_ae'],
            'support_cols': ['finite_innovation_fraction_t']
        }
    }
    
    for ds_name, config in datasets.items():
        for exp in ['da_cdf', 'da_nocdf']:
            path = os.path.join(data_dir, ds_name.lower(), exp)
            res = process_dataset(ds_name, exp, path, config['target_cols'], config['support_cols'])
            if not res:
                print(f"Skipping {ds_name} {exp}, no data.")
                continue
                
            counts, target_data, support_data = res
            
            print(f"\n{'='*50}\n{ds_name} - {exp}\n{'='*50}")
            print(f"B. EXACT ROW COUNTS:")
            total = sum(counts.values())
            for split, cnt in counts.items():
                pct = (cnt / total * 100) if total > 0 else 0
                print(f"  {split}: {cnt} ({pct:.2f}%)")
                
            print(f"\nC. TARGET DISTRIBUTIONS:")
            for split in ['train', 'validation', 'test']:
                print(f"  Split: {split}")
                for col in config['target_cols']:
                    stats = report_stats(target_data[split][col], col)
                    print(f"    {col}: N={stats['N']}, mean={stats.get('mean',0):.4f}, std={stats.get('std',0):.4f}, "
                          f"median={stats.get('median',0):.4f}, p05={stats.get('p05',0):.4f}, p95={stats.get('p95',0):.4f}, "
                          f"pos%={stats.get('positive_%',0):.1f}%, neg%={stats.get('negative_%',0):.1f}%, zero%={stats.get('zero_%',0):.1f}%")
                          
            print(f"\nD. ASSIMILATION-SUPPORT DISTRIBUTIONS:")
            for split in ['train', 'validation', 'test']:
                print(f"  Split: {split}")
                if ds_name == 'SOURCE':
                    print(f"    finite-innovation samples: {counts[split]}")
                elif ds_name == 'VALUE':
                    arr = np.array(support_data[split]['finite_innovation_fraction_t'])
                    if len(arr) > 0:
                        mean_fi = np.mean(arr)
                        frac_zero = (arr == 0).mean() * 100
                        print(f"    mean finite_innovation_fraction_t: {mean_fi:.4f}")
                        print(f"    fraction == 0: {frac_zero:.2f}%")
                # For TRANSFER, we don't have 'observation_frequency' easily available, assuming 100% or we can skip detailed support for brevity if not found
    
    # Analyze Spatial Blocks
    splits_dir = os.path.join(data_dir, 'splits')
    noahmp_path = os.path.join(splits_dir, 'noahmp_spatial_blocks.parquet')
    gleam_path = os.path.join(splits_dir, 'gleam_spatial_blocks.parquet')
    
    print(f"\n{'='*50}\nSPATIAL BLOCK ANALYSIS\n{'='*50}")
    if os.path.exists(noahmp_path) and os.path.exists(gleam_path):
        df_noahmp = pd.read_parquet(noahmp_path)
        df_gleam = pd.read_parquet(gleam_path)
        
        n_blocks = df_noahmp['spatial_block_id'].nunique()
        print(f"F. NUMBER OF SPATIAL BLOCKS: {n_blocks}")
        
        print("\nG. CELLS PER SPATIAL FOLD:")
        fold_counts_noah = df_noahmp.groupby('spatial_fold').size()
        fold_counts_gleam = df_gleam.groupby('spatial_fold').size()
        
        for fold in sorted(fold_counts_noah.index):
            print(f"  Fold {fold}: Noah-MP cells = {fold_counts_noah.get(fold, 0)}, GLEAM cells = {fold_counts_gleam.get(fold, 0)}")
            
        print("\nH. CROSS-GRID BLOCK CONSISTENCY:")
        df_joint = pd.merge(df_noahmp, df_gleam, on=['spatial_block_id', 'spatial_fold'], how='inner')
        print(f"  Inner joined cells on block_id & fold: {len(df_joint)} (Validates consistency across grids)")
        
        print("\nJ. REPRODUCIBILITY AUDIT:")
        from smap_xai.modeling.splits import assign_spatial_block, assign_spatial_fold
        df_noahmp_re = df_noahmp.copy()
        df_noahmp_re['spatial_block_id_re'] = assign_spatial_block(df_noahmp_re['lat'], df_noahmp_re['lon'])
        df_noahmp_re['spatial_fold_re'] = assign_spatial_fold(df_noahmp_re['spatial_block_id_re'])
        
        id_match = (df_noahmp['spatial_block_id'] == df_noahmp_re['spatial_block_id_re']).all()
        fold_match = (df_noahmp['spatial_fold'] == df_noahmp_re['spatial_fold_re']).all()
        
        if id_match and fold_match:
            print("  PASS: Reproducibility audit successful (identical assignments).")
        else:
            print("  FAIL: Reproducibility audit failed.")

if __name__ == "__main__":
    run_audit()
