import numpy as np
import pandas as pd

class BaselineZero:
    def fit(self, y, **kwargs):
        pass
    def predict(self, df):
        return np.zeros(len(df))

class BaselineTrainMean:
    def __init__(self):
        self.mean = 0.0
    def fit(self, y, **kwargs):
        self.mean = np.nanmean(y)
    def predict(self, df):
        return np.full(len(df), self.mean)

class BaselineTrainMedian:
    def __init__(self):
        self.median = 0.0
    def fit(self, y, **kwargs):
        self.median = np.nanmedian(y)
    def predict(self, df):
        return np.full(len(df), self.median)

class BaselineMonthlyTrainMean:
    def __init__(self):
        self.monthly_means = {}
        self.global_mean = 0.0
        
    def fit(self, y, months, **kwargs):
        df = pd.DataFrame({'y': y, 'month': months})
        self.monthly_means = df.groupby('month')['y'].mean().to_dict()
        self.global_mean = np.nanmean(y)
        
    def predict(self, df):
        months = pd.to_datetime(df['date']).dt.month
        preds = months.map(self.monthly_means).fillna(self.global_mean).values
        return preds

class BaselineMonthlyTrainMedian:
    def __init__(self):
        self.monthly_medians = {}
        self.global_median = 0.0
        
    def fit(self, y, months, **kwargs):
        df = pd.DataFrame({'y': y, 'month': months})
        self.monthly_medians = df.groupby('month')['y'].median().to_dict()
        self.global_median = np.nanmedian(y)
        
    def predict(self, df):
        months = pd.to_datetime(df['date']).dt.month
        preds = months.map(self.monthly_medians).fillna(self.global_median).values
        return preds

class BaselinePersistenceLag1:
    def __init__(self, target):
        self.lag_col = target + "_lag1"
        
    def fit(self, y, **kwargs):
        pass
        
    def predict(self, df):
        if self.lag_col in df.columns:
            return df[self.lag_col].values
        return np.full(len(df), np.nan)

class BaselineScalarEnKFGainProxy:
    def __init__(self):
        self.R = 0.0016
        
    def fit(self, y, **kwargs):
        pass
        
    def predict(self, df):
        # We need innovation and forecast_variance
        innov = df['innovation'].values
        f_var = df['forecast_variance'].values
        
        K_proxy = f_var / (f_var + self.R)
        signed_proxy = K_proxy * innov
        return np.abs(signed_proxy)
