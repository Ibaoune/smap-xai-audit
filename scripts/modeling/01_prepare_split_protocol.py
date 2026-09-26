import os
import sys
import pandas as pd
import pyarrow.parquet as pq

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from smap_xai.modeling.splits import assign_spatial_block, create_balanced_spatial_folds

def get_unique_coords(base_path, is_gleam=False):
    """Scan partitioned parquet directory to get unique coordinates."""
    import glob
    files = glob.glob(os.path.join(base_path, '**/*.parquet'), recursive=True)
    if not files:
        print(f"Warning: No parquet files found in {base_path}")
        return pd.DataFrame()
        
    df_list = []
    if is_gleam:
        columns = ['lat', 'lon', 'gleam_y_index', 'gleam_x_index']
    else:
        columns = ['lat', 'lon', 'y_index', 'x_index']
        
    for f in files:
        df_part = pd.read_parquet(f, columns=columns)
        df_part = df_part.drop_duplicates()
        df_list.append(df_part)
        
    df_all = pd.concat(df_list, ignore_index=True).drop_duplicates()
    return df_all

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    data_dir = os.path.join(project_root, 'data', 'processed', 'modeling')
    out_dir = os.path.join(project_root, 'data', 'processed', 'modeling', 'splits')
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Noah-MP unique grid (from TRANSFER)
    print("Processing Noah-MP unique coordinates...")
    transfer_path = os.path.join(data_dir, 'transfer', 'da_cdf')
    df_noahmp = get_unique_coords(transfer_path, is_gleam=False)
    if not df_noahmp.empty:
        df_noahmp['spatial_block_id'] = assign_spatial_block(df_noahmp['lat'], df_noahmp['lon'])
        
    # 2. GLEAM unique grid (from VALUE)
    print("Processing GLEAM unique coordinates...")
    value_path = os.path.join(data_dir, 'value', 'da_cdf')
    df_gleam = get_unique_coords(value_path, is_gleam=True)
    if not df_gleam.empty:
        df_gleam['spatial_block_id'] = assign_spatial_block(df_gleam['lat'], df_gleam['lon'])
        
    if not df_noahmp.empty and not df_gleam.empty:
        print("Calculating balanced spatial folds...")
        block_mapping = create_balanced_spatial_folds(df_noahmp, df_gleam)
        
        # Merge fold assignments back
        df_noahmp = pd.merge(df_noahmp, block_mapping[['spatial_block_id', 'spatial_fold']], on='spatial_block_id', how='left')
        df_gleam = pd.merge(df_gleam, block_mapping[['spatial_block_id', 'spatial_fold']], on='spatial_block_id', how='left')
        
        out_noahmp = os.path.join(out_dir, 'noahmp_spatial_blocks.parquet')
        df_noahmp.to_parquet(out_noahmp, index=False)
        print(f"Saved Noah-MP mapping: {out_noahmp}")
        
        out_gleam = os.path.join(out_dir, 'gleam_spatial_blocks.parquet')
        df_gleam.to_parquet(out_gleam, index=False)
        print(f"Saved GLEAM mapping: {out_gleam}")
        
        out_mapping = os.path.join(out_dir, 'balanced_block_mapping.csv')
        block_mapping.to_csv(out_mapping, index=False)
        print(f"Saved Block mapping stats: {out_mapping}")
        
    print("Done generating spatial block mappings.")

if __name__ == "__main__":
    main()
