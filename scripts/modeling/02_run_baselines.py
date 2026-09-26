import os
import sys
import yaml
import glob
import argparse
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from smap_xai.modeling.metrics import ChunkedRegressionMetrics
from smap_xai.modeling.baselines import (
    BaselineZero, BaselineTrainMean, BaselineTrainMedian, 
    BaselineMonthlyTrainMean, BaselineMonthlyTrainMedian, 
    BaselinePersistenceLag1
)
from smap_xai.modeling.splits import assign_spatial_block

def load_config(path='configs/modeling/baselines.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_splits(path='configs/modeling/splits.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def evaluate_baselines(dataset_path, targets, baselines, splits, time_col, 
                       spatial_folds_map_path=None, do_temporal=True, do_spatial=True):
    parquet_files = glob.glob(f"{dataset_path}/**/*.parquet", recursive=True)
    if not parquet_files:
        parquet_files = glob.glob(f"{dataset_path}/*.parquet")
    dataset = ds.dataset(parquet_files, format="parquet")
    results = []

    baseline_map = {
        'zero': BaselineZero,
        'train_mean': BaselineTrainMean,
        'train_median': BaselineTrainMedian,
        'monthly_train_mean': BaselineMonthlyTrainMean,
        'monthly_train_median': BaselineMonthlyTrainMedian,
        'persistence_lag1': BaselinePersistenceLag1
    }

    def get_train_data(start, end, target_col):
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        expr = (pc.field(time_col) >= start_ts) & (pc.field(time_col) <= end_ts)
        cols = [target_col, time_col, f"{target_col}_lag1"]
        if spatial_folds_map_path:
            cols.extend(['lat', 'lon', 'spatial_block_id'])
        cols = [c for c in cols if c in dataset.schema.names]
        df = dataset.to_table(filter=expr, columns=cols).to_pandas()
        return df

    if do_temporal:
        for fold_name, fold_dates in splits['pretest_temporal_cv'].items():
            train_start, train_end = fold_dates['train']['start'], fold_dates['train']['end']
            val_start, val_end = fold_dates['validation']['start'], fold_dates['validation']['end']
            
            for target in targets:
                train_df = get_train_data(train_start, train_end, target)
                models = {}
                for b in baselines:
                    if b == 'persistence_lag1':
                        model = BaselinePersistenceLag1(target)
                    else:
                        model = baseline_map[b]()
                        
                    if b in ['persistence_lag1', 'zero']:
                        model.fit(None)
                    else:
                        y_train = train_df[target].values
                        months = pd.to_datetime(train_df[time_col]).dt.month.values
                        model.fit(y_train, months=months)
                    models[b] = model
                
                val_expr = (pc.field(time_col) >= pd.Timestamp(val_start)) & (pc.field(time_col) <= pd.Timestamp(val_end))
                accumulators = {b: ChunkedRegressionMetrics() for b in baselines}
                
                for batch in dataset.to_batches(filter=val_expr):
                    batch_df = batch.to_pandas()
                    if target not in batch_df.columns: continue
                    y_true = batch_df[target].values
                    for b, model in models.items():
                        y_pred = model.predict(batch_df)
                        accumulators[b].update(y_true, y_pred)
                
                for b, acc in accumulators.items():
                    mets = acc.compute()
                    mets.update({'fold': fold_name, 'target': target, 'baseline': b, 'type': 'temporal'})
                    results.append(mets)

    if do_spatial:
        if spatial_folds_map_path:
            spatial_map = pd.read_csv(spatial_folds_map_path)
            train_end = "2019-12-31"
            
            for target in targets:
                all_train_df = get_train_data("2016-01-01", train_end, target)
                if 'spatial_block_id' not in all_train_df.columns:
                    all_train_df['spatial_block_id'] = assign_spatial_block(all_train_df['lat'], all_train_df['lon'])
                all_train_df = all_train_df.merge(spatial_map[['spatial_block_id', 'spatial_fold']], on='spatial_block_id', how='left')
                
                for fold in range(5):
                    train_mask = all_train_df['spatial_fold'] != fold
                    val_mask = all_train_df['spatial_fold'] == fold
                    
                    train_df = all_train_df[train_mask]
                    val_df = all_train_df[val_mask]
                    
                    models = {}
                    for b in baselines:
                        if b == 'persistence_lag1':
                            model = BaselinePersistenceLag1(target)
                        else:
                            model = baseline_map[b]()
                        
                        if b in ['persistence_lag1', 'zero']:
                            model.fit(None)
                        else:
                            y_train = train_df[target].values
                            months = pd.to_datetime(train_df[time_col]).dt.month.values
                            model.fit(y_train, months=months)
                        models[b] = model
                        
                    accumulators = {b: ChunkedRegressionMetrics() for b in baselines}
                    if len(val_df) > 0:
                        y_true = val_df[target].values
                        for b, model in models.items():
                            y_pred = model.predict(val_df)
                            accumulators[b].update(y_true, y_pred)
                            
                    for b, acc in accumulators.items():
                        mets = acc.compute()
                        mets.update({'fold': f"spatial_{fold}", 'target': target, 'baseline': b, 'type': 'spatial'})
                        results.append(mets)

    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Run SMAP-XAI baselines")
    parser.add_argument('--block', type=str, choices=['source', 'transfer', 'value', 'matched'], required=True)
    parser.add_argument('--experiment', type=str, choices=['da_cdf', 'da_nocdf'], required=False)
    parser.add_argument('--target', type=str, required=False, help="Required for transfer targets")
    parser.add_argument('--protocol', type=str, choices=['temporal', 'spatial', 'all'], required=True)
    parser.add_argument('--config', type=str, default='configs/modeling/baselines.yaml')
    args = parser.parse_args()

    config = load_config(args.config)
    splits = load_splits(config['splits_reference'])
    
    spatial_map_file = "data/processed/modeling/splits/balanced_block_mapping.csv"
    
    do_temp = args.protocol in ['temporal', 'all']
    do_spat = args.protocol in ['spatial', 'all']

    if args.block == 'source':
        targets = [config['source']['target']]
        baselines = config['source']['baselines']
    elif args.block == 'transfer':
        if not args.target:
            raise ValueError("--target is required for transfer block")
        targets = [args.target]
        baselines = config['transfer']['baselines']
    elif args.block == 'value':
        targets = [config['value']['target']]
        baselines = config['value']['baselines']
        
    if args.block == 'matched':
        # Matched support
        cdf_files = glob.glob("data/processed/modeling/source/da_cdf/**/*.parquet", recursive=True) or glob.glob("data/processed/modeling/source/da_cdf/*.parquet")
        df_cdf = ds.dataset(cdf_files, format="parquet").to_table(
            columns=['date', 'y_index', 'x_index', 'daily_absolute_increment']).to_pandas()
        nocdf_files = glob.glob("data/processed/modeling/source/da_nocdf/**/*.parquet", recursive=True) or glob.glob("data/processed/modeling/source/da_nocdf/*.parquet")
        df_nocdf = ds.dataset(nocdf_files, format="parquet").to_table(
            columns=['date', 'y_index', 'x_index', 'daily_absolute_increment']).to_pandas()
        
        df_matched = df_cdf.merge(df_nocdf, on=['date', 'y_index', 'x_index'], suffixes=('_cdf', '_nocdf'))
        
        matched_results = []
        val_start = splits['pretest_temporal_cv']['fold_3']['validation']['start']
        val_end = splits['pretest_temporal_cv']['fold_3']['validation']['end']
        
        val_start_ts = pd.Timestamp(val_start)
        val_end_ts = pd.Timestamp(val_end)
        
        val_mask = (pd.to_datetime(df_matched['date']) >= val_start_ts) & (pd.to_datetime(df_matched['date']) <= val_end_ts)
        train_mask = pd.to_datetime(df_matched['date']) < val_start_ts
        
        for exp_suffix in ['_cdf', '_nocdf']:
            target = f'daily_absolute_increment{exp_suffix}'
            y_train = df_matched[train_mask][target].values
            y_val = df_matched[val_mask][target].values
            
            zero_mae = np.mean(np.abs(y_val))
            zero_rmse = np.sqrt(np.mean(y_val**2))
            
            med = np.nanmedian(y_train)
            med_mae = np.mean(np.abs(y_val - med))
            med_rmse = np.sqrt(np.mean((y_val - med)**2))
            
            df_train = df_matched[train_mask].copy()
            df_train['month'] = pd.to_datetime(df_train['date']).dt.month
            monthly_meds = df_train.groupby('month')[target].median()
            
            df_val = df_matched[val_mask].copy()
            df_val['month'] = pd.to_datetime(df_val['date']).dt.month
            y_pred_mtm = df_val['month'].map(monthly_meds).values
            
            mtm_mae = np.mean(np.abs(y_val - y_pred_mtm))
            mtm_rmse = np.sqrt(np.mean((y_val - y_pred_mtm)**2))
            
            matched_results.append({
                'experiment': exp_suffix.replace('_', 'da_'),
                'row_count': len(y_val),
                'zero_MAE': zero_mae,
                'zero_RMSE': zero_rmse,
                'train_median_MAE': med_mae,
                'train_median_RMSE': med_rmse,
                'monthly_train_median_MAE': mtm_mae,
                'monthly_train_median_RMSE': mtm_rmse
            })
            
        out_dir = "reports/modeling/baselines/raw"
        os.makedirs(out_dir, exist_ok=True)
        pd.DataFrame(matched_results).to_csv(f"{out_dir}/source_matched_support.csv", index=False)
        print("Saved source_matched_support.csv")
        return
        
    dataset_path = f"data/processed/modeling/{args.block}/{args.experiment}"
    
    res_df = evaluate_baselines(
        dataset_path, targets, baselines, splits, 'date',
        spatial_folds_map_path=spatial_map_file,
        do_temporal=do_temp, do_spatial=do_spat
    )
    
    res_df['experiment'] = args.experiment
    res_df['dataset'] = args.block.upper()
    
    out_dir = "reports/modeling/baselines/raw"
    os.makedirs(out_dir, exist_ok=True)
    
    if args.block == 'transfer':
        out_name = f"{args.block}_{args.experiment}_{args.target}.csv"
    else:
        out_name = f"{args.block}_{args.experiment}.csv"
        
    res_df.to_csv(os.path.join(out_dir, out_name), index=False)
    print(f"Saved {out_name}")

if __name__ == "__main__":
    main()
