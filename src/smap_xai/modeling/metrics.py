import numpy as np

class ChunkedRegressionMetrics:
    def __init__(self):
        self.n = 0
        self.sum_err = 0.0
        self.sum_abs_err = 0.0
        self.sum_sq_err = 0.0
        
        # For R2 and Pearson (Welford's online algorithm)
        self.mean_y = 0.0
        self.mean_yp = 0.0
        self.M2_y = 0.0
        self.M2_yp = 0.0
        self.C_y_yp = 0.0

    def update(self, y_true, y_pred):
        y_true = np.asarray(y_true, dtype=np.float64)
        y_pred = np.asarray(y_pred, dtype=np.float64)
        
        valid = ~np.isnan(y_true) & ~np.isnan(y_pred)
        if not np.any(valid):
            return
            
        yt = y_true[valid]
        yp = y_pred[valid]
        
        self.n += len(yt)
        err = yp - yt
        self.sum_err += np.sum(err)
        self.sum_abs_err += np.sum(np.abs(err))
        self.sum_sq_err += np.sum(err**2)
        
        n_B = len(yt)
        mean_y_B = np.mean(yt)
        mean_yp_B = np.mean(yp)
        M2_y_B = np.sum((yt - mean_y_B)**2)
        M2_yp_B = np.sum((yp - mean_yp_B)**2)
        C_y_yp_B = np.sum((yt - mean_y_B) * (yp - mean_yp_B))
        
        n_A = self.n
        n = n_A + n_B
        
        if n_A == 0:
            self.mean_y = mean_y_B
            self.mean_yp = mean_yp_B
            self.M2_y = M2_y_B
            self.M2_yp = M2_yp_B
            self.C_y_yp = C_y_yp_B
        else:
            delta_y = mean_y_B - self.mean_y
            delta_yp = mean_yp_B - self.mean_yp
            
            self.mean_y += delta_y * n_B / n
            self.mean_yp += delta_yp * n_B / n
            
            self.M2_y += M2_y_B + (delta_y**2) * n_A * n_B / n
            self.M2_yp += M2_yp_B + (delta_yp**2) * n_A * n_B / n
            self.C_y_yp += C_y_yp_B + delta_y * delta_yp * n_A * n_B / n
            
        self.n = n

    def compute(self):
        if self.n == 0:
            return {"MAE": np.nan, "RMSE": np.nan, "bias": np.nan, "R2": np.nan, "Pearson": np.nan, "N": 0}
            
        mae = self.sum_abs_err / self.n
        rmse = np.sqrt(self.sum_sq_err / self.n)
        bias = self.sum_err / self.n
        
        # Variance tolerances (scale-aware)
        tol_y = 1e-12 * self.n * max(1.0, self.mean_y**2)
        tol_yp = 1e-12 * self.n * max(1.0, self.mean_yp**2)
        
        # R2
        if self.M2_y > tol_y:
            r2 = 1.0 - (self.sum_sq_err / self.M2_y)
        else:
            r2 = np.nan
            
        # Pearson
        if self.M2_y > tol_y and self.M2_yp > tol_yp:
            pearson = self.C_y_yp / np.sqrt(self.M2_y * self.M2_yp)
        else:
            pearson = np.nan
            
        return {
            "MAE": mae,
            "RMSE": rmse,
            "bias": bias,
            "R2": r2,
            "Pearson": pearson,
            "N": self.n
        }

def compute_relative_skill(model_metrics, ref_metrics):
    skill = {}
    for met in ["MAE", "RMSE"]:
        m_val = model_metrics.get(met, np.nan)
        r_val = ref_metrics.get(met, np.nan)
        
        if np.isnan(m_val) or np.isnan(r_val) or r_val == 0:
            skill[f"{met}_skill"] = np.nan
        else:
            skill[f"{met}_skill"] = 1.0 - (m_val / r_val)
    return skill
