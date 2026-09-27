import numpy as np
import pandas as pd

def assign_temporal_split(date_series: pd.Series) -> pd.Series:
    """
    Assigns each date to 'train', 'validation', or 'test'.
    
    TRAIN: 2016-01-08 through 2018-12-31
    VALIDATION: 2019-01-01 through 2019-12-31
    TEST: 2020-01-01 through 2020-12-31
    """
    date_dt = pd.to_datetime(date_series)
    split = pd.Series(index=date_series.index, data='unknown', dtype=object)
    
    # Train
    train_mask = (date_dt >= '2016-01-08') & (date_dt <= '2018-12-31')
    split.loc[train_mask] = 'train'
    
    # Validation
    val_mask = (date_dt >= '2019-01-01') & (date_dt <= '2019-12-31')
    split.loc[val_mask] = 'validation'
    
    # Test
    test_mask = (date_dt >= '2020-01-01') & (date_dt <= '2020-12-31')
    split.loc[test_mask] = 'test'
    
    return split

def get_temporal_fold_bounds(fold: str) -> tuple:
    """
    Returns (train_start, train_end, val_start, val_end) for a given fold.
    """
    folds = {
        "fold_1": ("2016-01-08", "2016-12-31", "2017-01-01", "2017-12-31"),
        "fold_2": ("2016-01-08", "2017-12-31", "2018-01-01", "2018-12-31"),
        "fold_3": ("2016-01-08", "2018-12-31", "2019-01-01", "2019-12-31"),
    }
    if fold not in folds:
        raise ValueError(f"Unknown temporal fold: {fold}")
    return folds[fold]

def assign_spatial_block(lat_series: pd.Series, lon_series: pd.Series, block_size_degrees: float = 1.0) -> pd.Series:
    """
    Assigns spatial blocks conceptually as floor(coord / block_size).
    Anchor blocks to integer-degree geographic boundaries.
    """
    lat_block = np.floor(lat_series / block_size_degrees).astype(int)
    lon_block = np.floor(lon_series / block_size_degrees).astype(int)
    
    block_id = lat_block.astype(str) + "_" + lon_block.astype(str)
    return block_id

def create_balanced_spatial_folds(df_noahmp: pd.DataFrame, df_gleam: pd.DataFrame, n_folds: int = 5) -> pd.DataFrame:
    """
    Creates a deterministic balanced block assignment based on geometric support.
    Returns a DataFrame mapping spatial_block_id to spatial_fold.
    """
    # Count cells per block
    noah_counts = df_noahmp.groupby('spatial_block_id').size().rename('n_noahmp_cells')
    gleam_counts = df_gleam.groupby('spatial_block_id').size().rename('n_gleam_cells')
    
    blocks = pd.DataFrame({'n_noahmp_cells': noah_counts, 'n_gleam_cells': gleam_counts}).fillna(0)
    
    total_noahmp = blocks['n_noahmp_cells'].sum()
    total_gleam = blocks['n_gleam_cells'].sum()
    
    # Compute block weight
    blocks['block_weight'] = (blocks['n_noahmp_cells'] / total_noahmp) + (blocks['n_gleam_cells'] / total_gleam)
    
    # Sort deterministically
    blocks = blocks.reset_index()
    blocks = blocks.sort_values(by=['block_weight', 'spatial_block_id'], ascending=[False, True])
    
    # Greedy assignment
    fold_weights = {i: 0.0 for i in range(n_folds)}
    block_to_fold = {}
    
    for _, row in blocks.iterrows():
        block_id = row['spatial_block_id']
        weight = row['block_weight']
        
        # Find fold with smallest weight, tie-break by smallest fold id
        best_fold = min(fold_weights.keys(), key=lambda k: (fold_weights[k], k))
        
        block_to_fold[block_id] = best_fold
        fold_weights[best_fold] += weight
        
    blocks['spatial_fold'] = blocks['spatial_block_id'].map(block_to_fold)
    
    return blocks[['spatial_block_id', 'spatial_fold', 'n_noahmp_cells', 'n_gleam_cells', 'block_weight']]
