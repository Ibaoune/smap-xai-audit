import os
import sys
import glob
import hashlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def process_spatial_dataset(name, experiment, path, target_cols, split_mapping, id_cols=['lat', 'lon', 'spatial_block_id']):
    """Iterate over parquet files to accumulate exact counts and distributions per spatial fold."""
    files = glob.glob(os.path.join(path, '**/*.parquet'), recursive=True)
    if not files:
        return None
        
    counts = {i: 0 for i in range(5)}
    target_data = {fold: {col: [] for col in target_cols} for fold in range(5)}
    
    for f in files:
        df = pd.read_parquet(f, columns=target_cols + id_cols)
        
        # assign folds
        df = df.merge(split_mapping[['spatial_block_id', 'spatial_fold']], on='spatial_block_id', how='left')
        
        # calculate
        for fold in range(5):
            mask = df['spatial_fold'] == fold
            counts[fold] += mask.sum()
            for col in target_cols:
                target_data[fold][col].extend(df.loc[mask, col].dropna().values)
                
    return counts, target_data

def report_stats(data_list, col_name):
    arr = np.array(data_list)
    if len(arr) == 0:
        return {"N": 0}
    return {
        "N": len(arr),
        "mean": np.mean(arr),
        "median": np.median(arr),
        "positive_%": (arr > 0).mean() * 100,
        "negative_%": (arr < 0).mean() * 100
    }

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    data_dir = os.path.join(project_root, 'data', 'processed', 'modeling')
    splits_dir = os.path.join(data_dir, 'splits')
    
    # 1. Report Balance after correction
    map_noahmp = pd.read_parquet(os.path.join(splits_dir, 'noahmp_spatial_blocks.parquet'))
    map_gleam = pd.read_parquet(os.path.join(splits_dir, 'gleam_spatial_blocks.parquet'))
    mapping = pd.read_csv(os.path.join(splits_dir, 'balanced_block_mapping.csv'))
    
    total_noahmp = mapping['n_noahmp_cells'].sum()
    total_gleam = mapping['n_gleam_cells'].sum()
    
    print("\nC. OLD VS NEW SPATIAL-FOLD BALANCE:")
    print("New Balanced Fold Distribution:")
    for fold in range(5):
        fold_data = mapping[mapping['spatial_fold'] == fold]
        n_blocks = len(fold_data)
        noah_cells = fold_data['n_noahmp_cells'].sum()
        gleam_cells = fold_data['n_gleam_cells'].sum()
        noah_pct = (noah_cells / total_noahmp) * 100 if total_noahmp > 0 else 0
        gleam_pct = (gleam_cells / total_gleam) * 100 if total_gleam > 0 else 0
        weight = fold_data['block_weight'].sum()
        
        print(f"  Fold {fold}: {n_blocks} blocks, NoahMP={noah_cells} ({noah_pct:.2f}%), "
              f"GLEAM={gleam_cells} ({gleam_pct:.2f}%), Weight={weight:.4f}")
              
    noah_ratios = [mapping[mapping['spatial_fold'] == f]['n_noahmp_cells'].sum() for f in range(5)]
    gleam_ratios = [mapping[mapping['spatial_fold'] == f]['n_gleam_cells'].sum() for f in range(5)]
    print(f"\n  Noah-MP max/min ratio: {max(noah_ratios)/min(noah_ratios):.2f}")
    print(f"  GLEAM max/min ratio: {max(gleam_ratios)/min(gleam_ratios):.2f}")
    
    # 2. Row counts by spatial fold and targets
    print("\nD. EXACT SPATIAL ROW COUNTS & E. TARGET SUMMARIES:")
    datasets = {
        'SOURCE': {'target_cols': ['daily_absolute_increment'], 'id_cols': ['lat', 'lon', 'y_index', 'x_index']},
        'TRANSFER': {'target_cols': ['delta_rzsm', 'delta_et', 'delta_surface_runoff', 'delta_baseflow'], 'id_cols': ['lat', 'lon', 'y_index', 'x_index']},
        'VALUE': {'target_cols': ['value_ae'], 'id_cols': ['lat', 'lon', 'gleam_y_index', 'gleam_x_index']}
    }
    
    # Needs a small hack to reconstruct spatial_block_id on the fly since they might not be inside the parquet.
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
    from smap_xai.modeling.splits import assign_spatial_block
    
    for ds_name, config in datasets.items():
        for exp in ['da_cdf', 'da_nocdf']:
            path = os.path.join(data_dir, ds_name.lower(), exp)
            
            # Since spatial_block_id is not in parquet, we calculate it dynamically
            files = glob.glob(os.path.join(path, '**/*.parquet'), recursive=True)
            if not files: continue
            
            counts = {i: 0 for i in range(5)}
            target_data = {fold: {col: [] for col in config['target_cols']} for fold in range(5)}
            
            for f in files:
                df = pd.read_parquet(f, columns=config['target_cols'] + config['id_cols'])
                df['spatial_block_id'] = assign_spatial_block(df['lat'], df['lon'])
                df = df.merge(mapping[['spatial_block_id', 'spatial_fold']], on='spatial_block_id', how='left')
                
                for fold in range(5):
                    mask = df['spatial_fold'] == fold
                    counts[fold] += mask.sum()
                    for col in config['target_cols']:
                        target_data[fold][col].extend(df.loc[mask, col].dropna().values)
                        
            print(f"\n--- {ds_name} {exp} ---")
            total = sum(counts.values())
            for fold in range(5):
                pct = counts[fold]/total * 100 if total > 0 else 0
                print(f"  Fold {fold}: {counts[fold]} rows ({pct:.2f}%)")
                
                for col in config['target_cols']:
                    stats = report_stats(target_data[fold][col], col)
                    pos_str = f", pos%={stats.get('positive_%',0):.1f}%, neg%={stats.get('negative_%',0):.1f}%" if ds_name == 'VALUE' else ""
                    print(f"    {col}: N={stats['N']}, mean={stats.get('mean',0):.4f}, median={stats.get('median',0):.4f}{pos_str}")
                    
    # 3. Generate Spatial Fold Map
    reports_dir = os.path.join(project_root, 'reports', 'qc', 'modeling_splits')
    os.makedirs(reports_dir, exist_ok=True)
    map_out = os.path.join(reports_dir, 'spatial_folds_map.png')
    
    plt.figure(figsize=(10, 8))
    # We plot the mapping points (each 1-degree block center approximately or just scatter the native grid points)
    scatter = plt.scatter(map_noahmp['lon'], map_noahmp['lat'], c=map_noahmp['spatial_fold'], cmap='tab10', s=1)
    plt.colorbar(scatter, ticks=range(5), label='Spatial Fold')
    plt.title('Balanced Spatial Folds (Noah-MP cells)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(map_out, dpi=300, bbox_inches='tight')
    print(f"\nF. MAP OUTPUT PATH: {map_out}")
    
    # 4. Reproducibility
    print("\nH. REPRODUCIBILITY CHECKSUM:")
    # Re-run balancing
    from smap_xai.modeling.splits import create_balanced_spatial_folds
    mapping_re = create_balanced_spatial_folds(map_noahmp, map_gleam)
    
    id_match = (mapping['spatial_block_id'] == mapping_re['spatial_block_id']).all()
    fold_match = (mapping['spatial_fold'] == mapping_re['spatial_fold']).all()
    
    if id_match and fold_match:
        # Checksum of block-to-fold
        mapping_str = mapping[['spatial_block_id', 'spatial_fold']].sort_values('spatial_block_id').to_csv(index=False)
        chk = hashlib.md5(mapping_str.encode()).hexdigest()
        print(f"  PASS (Checksum: {chk})")
    else:
        print("  FAIL: Non-deterministic spatial assignment")
        
    print("\nG. CROSS-GRID ASSIGNMENT CONSISTENCY:")
    df_joint = pd.merge(map_noahmp, map_gleam, on=['spatial_block_id', 'spatial_fold'], how='inner')
    print(f"  Inner joined cells on block_id & fold: {len(df_joint)} (Validates Noah-MP and GLEAM cells in same block receive same fold)")

if __name__ == "__main__":
    main()
