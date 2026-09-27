import pyarrow.dataset as ds
import pyarrow.compute as pc
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import time

from smap_xai.modeling.model_interface import BaseModel
from smap_xai.modeling.random_forest import RandomForestModel

def get_model(model_family: str, params: dict) -> BaseModel:
    if model_family == "random_forest":
        return RandomForestModel(**params)
    raise ValueError(f"Unknown model_family: {model_family}")

def audit_leakage(features: List[str], target: str, block: str):
    # Rule 7: Leakage audit before fit
    # Assert target absent from predictors, date absent, year absent
    forbidden = {target, "date", "year", "lat", "lon", "y_index", "x_index", "gleam_y_index", "gleam_x_index"}
    if block == "TRANSFER":
        forbidden.update({"same-day DA RZSM", "analysis_residual", "value_ae", "GLEAM ET"})
    elif block == "SOURCE":
        forbidden.update({"analysis_residual", "value_ae", "GLEAM ET", "delta_rzsm"})

    for f in features:
        if f in forbidden or f == target:
            raise ValueError(f"Leakage audit failed: forbidden feature '{f}' found in predictors.")

def load_data(block: str, experiment: str, target: str, features: List[str], start_date: str, end_date: str, meta_cols: List[str] = None) -> pd.DataFrame:
    path = f"data/processed/modeling/{block.lower()}/{experiment}"
    dataset = ds.dataset(path, format="parquet", ignore_prefixes=['.', '_', 'README.md'])
    
    if meta_cols is None:
        meta_cols = ["date"]
        
    cols = list(set([target] + features + meta_cols))
    
    filter_expr = (pc.field("date") >= pd.to_datetime(start_date)) & (pc.field("date") <= pd.to_datetime(end_date))
    
    df = dataset.to_table(columns=cols, filter=filter_expr).to_pandas()
    
    # 2020 isolation
    df["date"] = pd.to_datetime(df["date"])
    if (df["date"].dt.year == 2020).sum() > 0:
        raise ValueError("2020 data leaked!")
        
    # Convert to float32
    float_cols = [c for c in df.columns if c not in meta_cols and df[c].dtype == np.float64]
    if float_cols:
        df[float_cols] = df[float_cols].astype(np.float32)
        
    return df

def train_model(model: BaseModel, X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    start = time.time()
    model.fit(X_train, y_train)
    walltime = time.time() - start
    
    meta = model.get_metadata()
    meta["fit_walltime_seconds"] = walltime
    meta["N_train"] = len(X_train)
    return meta
