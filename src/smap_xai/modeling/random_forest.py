import joblib
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
from typing import Dict, Any, Optional

from smap_xai.modeling.model_interface import BaseModel

class RandomForestModel(BaseModel):
    def __init__(self, **kwargs):
        self.params = kwargs
        self.model = RandomForestRegressor(**kwargs)
        self.feature_names = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.model.fit(X, y)
        self.feature_names = list(X.columns)

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self.model.predict(X), index=X.index)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_family": "random_forest",
            "hyperparameters": self.params,
            "fitted_features": self.feature_names
        }

    def save(self, path: str) -> None:
        joblib.dump(self.model, path)

    def load(self, path: str) -> None:
        self.model = joblib.load(path)
