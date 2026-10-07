import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path

# --- CONFIGURATION ---
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

MAIN_DIR = Path("figures/main")
SUPP_DIR = Path("figures/supplement")
MAIN_DIR.mkdir(parents=True, exist_ok=True)
SUPP_DIR.mkdir(parents=True, exist_ok=True)

# Formatting Dicts
EXP_MAP = {"da_cdf": "CDF", "da_nocdf": "NoCDF"}
TARG_MAP = {
    "daily_absolute_increment": "SOURCE update magnitude",
    "delta_rzsm": "RZSM",
    "delta_et": "ET",
    "delta_surface_runoff": "Surface runoff",
    "delta_baseflow": "Baseflow",
    "value_ae": "VALUE"
}
GROUP_MAP = {
    "antecedent_land_surface_fluxes": "Antecedent fluxes",
    "antecedent_soil_moisture_state": "Antecedent soil moisture",
    "assimilation_diagnostics_or_history": "Assimilation history",
    "forcing_perturbation_controls": "Forcing-discrepancy controls",
    "land_cover_or_vegetation": "Land cover",
    "meteorological_forcing": "Meteorological forcing",
    "soil_properties": "Soil properties",
    "temporal_context": "Temporal context",
    "topography": "Topography"
}

PRED_MAP = {
    "ssm_lag1": "Antecedent SSM (t−1)",
    "precip_lag1": "Precipitation (t−1)",
    "rzsm_lag1": "Antecedent RZSM (t−1)",
    "tair_lag1": "Air temperature (t−1)",
    "precip_pre3d_sum": "Precipitation, previous 3 d",
    "precip_pre7d_sum": "Precipitation, previous 7 d",
    "day_of_year": "Day of year",
    "doy_sin": "DOY sine",
    "doy_cos": "DOY cosine",
    "elevation": "Elevation",
    "land_cover_fraction_16": "Land-cover fraction 16",
    "soil_texture_fraction_1": "Soil-texture fraction 1"
}

PALETTE = {"CDF": "blue", "NoCDF": "orange"}
TARG_ORDER = ["SOURCE", "RZSM", "ET", "Surface runoff", "Baseflow", "VALUE"]

def clean_label(key):
    parts = key.split("_")
    block = parts[0]
    if block == "SOURCE":
        exp = EXP_MAP.get(f"{parts[1]}_{parts[2]}", key)
        return f"SOURCE — {exp} matched" if "matched" in key else f"SOURCE — {exp} native"
    elif block == "TRANSFER":
        exp = EXP_MAP.get(f"{parts[1]}_{parts[2]}", key)
        targ = "_".join(parts[3:-2])
        if targ in TARG_MAP: targ = TARG_MAP[targ]
        return f"{targ} — {exp}"
    elif block == "VALUE":
        exp = EXP_MAP.get(f"{parts[1]}_{parts[2]}", key)
        return f"VALUE — {exp}"
    return key

def clean_target_for_fig4(df):
    if "support_mode" in df.columns:
        support_col = "support_mode"
    elif "support" in df.columns:
        support_col = "support"
    else:
        support_col = None
        
    df["experiment"] = df["experiment"].map(EXP_MAP).fillna(df["experiment"])
    df["target"] = df["target"].map(TARG_MAP).fillna(df["target"])
    
    if support_col:
        df.loc[(df["block"]=="SOURCE") & (df[support_col]=="native_support"), "target"] = "DROP"
    df.loc[(df["block"]=="SOURCE"), "target"] = "SOURCE"
    
    # ensure string types
    df = df[df["target"] != "DROP"].copy()
    return df

def save_fig(fig, path_without_ext):
    fig.tight_layout()
    fig.savefig(f"{path_without_ext}.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.png", dpi=300, bbox_inches='tight')
    plt.close(fig)

def get_real_data(path, is_parquet=False):
    if not os.path.exists(path):
        print(f"Missing canonical data: {path}")
        return None
    if is_parquet: return pd.read_parquet(path)
    return pd.read_csv(path)

def open_mfdataset(paths):
    if not paths: return None
    datasets = [xr.open_dataset(p) for p in paths]
    return xr.concat(datasets, dim='time')

def generate_figure_3():
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    
    base_dir = Path("data/processed/daily_enkf")
    
    def get_paths(exp, var):
        return sorted(list((base_dir / exp / var).glob("*.nc")))

    try:
        # Load datasets
        ds_nocdf_inn = open_mfdataset(get_paths("da_nocdf", "daily_innovation"))
        ds_cdf_inn = open_mfdataset(get_paths("da_cdf", "daily_innovation"))
        ds_nocdf_inc = open_mfdataset(get_paths("da_nocdf", "daily_signed_increment"))
        ds_cdf_inc = open_mfdataset(get_paths("da_cdf", "daily_signed_increment"))
        ds_nocdf_abs = open_mfdataset(get_paths("da_nocdf", "daily_absolute_increment"))
        ds_cdf_abs = open_mfdataset(get_paths("da_cdf", "daily_absolute_increment"))

        if any(ds is None for ds in [ds_nocdf_inn, ds_cdf_inn, ds_nocdf_inc, ds_cdf_inc, ds_nocdf_abs, ds_cdf_abs]):
            print("Missing spatial NC data for Fig 3.")
            return

        lon = ds_nocdf_inn.lon.values
        lat = ds_nocdf_inn.lat.values
        extent = [lon.min(), lon.max(), lat.min(), lat.max()]

        # (a) Spatial frequency (count of valid NoCDF innovations over time)
        count_map = ds_nocdf_inn["daily_innovation"].count(dim="time").values
        im1 = axes[0].imshow(count_map, extent=extent, origin='lower', cmap='viridis')
        axes[0].set_title("(a) Innovation availability (count)", loc='left')
        plt.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)

        # (b) Mean NoCDF innovation
        mean_nocdf_inn = ds_nocdf_inn["daily_innovation"].mean(dim="time").values
        im2 = axes[1].imshow(mean_nocdf_inn, extent=extent, origin='lower', cmap='RdBu', vmin=-0.05, vmax=0.05)
        axes[1].set_title("(b) Mean innovation (NoCDF) [m³ m⁻³]", loc='left')
        plt.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)

        # (c) Innovation distributions
        nocdf_vals = ds_nocdf_inn["daily_innovation"].values.flatten()
        cdf_vals = ds_cdf_inn["daily_innovation"].values.flatten()
        nocdf_vals = nocdf_vals[~np.isnan(nocdf_vals)]
        cdf_vals = cdf_vals[~np.isnan(cdf_vals)]
        
        # Take a random sample if too large to plot efficiently
        sns.kdeplot(np.random.choice(cdf_vals, min(len(cdf_vals), 50000)), label="CDF", color=PALETTE["CDF"], ax=axes[2], fill=True, alpha=0.3)
        sns.kdeplot(np.random.choice(nocdf_vals, min(len(nocdf_vals), 50000)), label="NoCDF", color=PALETTE["NoCDF"], ax=axes[2], fill=True, alpha=0.3)
        axes[2].set_title("(c) Innovation distributions", loc='left')
        axes[2].set_xlabel("Innovation [m³ m⁻³]")
        axes[2].legend()

        # (d) Mean signed increment NoCDF
        mean_nocdf_inc = ds_nocdf_inc["daily_signed_increment"].mean(dim="time").values
        im4 = axes[3].imshow(mean_nocdf_inc, extent=extent, origin='lower', cmap='RdBu', vmin=-0.01, vmax=0.01)
        axes[3].set_title("(d) Mean analysis increment (NoCDF) [m³ m⁻³]", loc='left')
        plt.colorbar(im4, ax=axes[3], fraction=0.046, pad=0.04)

        # (e) Mean signed increment CDF
        mean_cdf_inc = ds_cdf_inc["daily_signed_increment"].mean(dim="time").values
        im5 = axes[4].imshow(mean_cdf_inc, extent=extent, origin='lower', cmap='RdBu', vmin=-0.01, vmax=0.01)
        axes[4].set_title("(e) Mean analysis increment (CDF) [m³ m⁻³]", loc='left')
        plt.colorbar(im5, ax=axes[4], fraction=0.046, pad=0.04)

        # (f) Seasonal increment magnitude
        nocdf_seas = ds_nocdf_abs["daily_absolute_increment"].groupby("time.season").mean(dim=["time", "lat", "lon"]).to_dataframe().reset_index()
        cdf_seas = ds_cdf_abs["daily_absolute_increment"].groupby("time.season").mean(dim=["time", "lat", "lon"]).to_dataframe().reset_index()
        
        nocdf_seas["Experiment"] = "NoCDF"
        cdf_seas["Experiment"] = "CDF"
        seas_df = pd.concat([cdf_seas, nocdf_seas])
        # Reorder seasons to match normal presentation if needed
        sns.barplot(data=seas_df, x="season", y="daily_absolute_increment", hue="Experiment", ax=axes[5], palette=PALETTE)
        axes[5].set_title("(f) Seasonal increment magnitude", loc='left')
        axes[5].set_ylabel("Mean |increment| [m³ m⁻³]")
        axes[5].set_xlabel("")
        axes[5].legend()

        for ax in [axes[0], axes[1], axes[3], axes[4]]:
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

    except Exception as e:
        print(f"Failed to generate Figure 3 properly: {e}")
        return

    save_fig(fig, str(MAIN_DIR / "Figure_3_assimilation_diagnostics"))

def generate_figure_4():
    df_temp_src = get_real_data("reports/modeling/models/random_forest/rf03b/rf03b_source_matched_metrics.csv")
    df_temp_prim = get_real_data("reports/modeling/models/random_forest/rf03b/rf03b_primary_metrics.csv")
    df_temp = pd.concat([df_temp_src, df_temp_prim]) if df_temp_src is not None and df_temp_prim is not None else None
    
    df_spat_val = get_real_data("reports/modeling/models/random_forest/rf02/rf02_value_fold_metrics.csv")
    df_spat_src = get_real_data("reports/modeling/models/random_forest/rf02/rf02_source_fold_metrics.csv")
    df_spat_tr = get_real_data("reports/modeling/models/random_forest/rf02/rf02_transfer_fold_metrics.csv")
    dfs = []
    if df_spat_val is not None: dfs.append(df_spat_val)
    if df_spat_src is not None: dfs.append(df_spat_src)
    if df_spat_tr is not None: dfs.append(df_spat_tr)
    df_spat = pd.concat(dfs) if dfs else None
    
    df_final = get_real_data("reports/modeling/final_2020/final_metrics_2020.csv")
    
    if df_temp is None or df_spat is None or df_final is None:
        print("FIGURE 4 INCOMPLETE")
        return
        
    df_temp = clean_target_for_fig4(df_temp)
    df_spat = clean_target_for_fig4(df_spat)
    df_final = clean_target_for_fig4(df_final)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    sns.barplot(data=df_temp, y="target", x="MAE_skill", hue="experiment", ax=axes[0], palette=PALETTE, order=TARG_ORDER)
    axes[0].set_title("(a) 2019 Temporal Validation MAE Skill", loc='left')
    axes[0].set_ylabel("")
    axes[0].set_xlabel("MAE Skill")
    axes[0].legend(title="")
    
    sns.barplot(data=df_spat, y="target", x="MAE_skill", hue="experiment", ax=axes[1], errorbar='sd', palette=PALETTE, order=TARG_ORDER)
    axes[1].set_title("(b) Five-fold spatial block CV — selected CDF models", loc='left')
    axes[1].set_ylabel("")
    axes[1].set_xlabel("MAE Skill")
    axes[1].legend(title="")
    
    sns.barplot(data=df_final, y="target", x="MAE_skill", hue="experiment", ax=axes[2], palette=PALETTE, order=TARG_ORDER)
    axes[2].set_title("(c) Final 2020 Holdout MAE Skill", loc='left')
    axes[2].set_ylabel("")
    axes[2].set_xlabel("MAE Skill")
    axes[2].legend().remove()
    
    sns.barplot(data=df_final, y="target", x="R2", hue="experiment", ax=axes[3], palette=PALETTE, order=TARG_ORDER)
    axes[3].set_title("(d) Final 2020 Holdout R²", loc='left')
    axes[3].set_ylabel("")
    axes[3].set_xlabel("R²")
    axes[3].legend().remove()
    
    save_fig(fig, str(MAIN_DIR / "Figure_4_RF_performance"))

def generate_figure_5():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    df_pred = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_predictor_summary.csv")
    
    if df_grp is None or df_pred is None: return
        
    df_grp = df_grp[(df_grp["model_key"].str.contains("SOURCE")) & (df_grp["model_key"].str.contains("matched"))].copy()
    df_pred = df_pred[(df_pred["model_key"].str.contains("SOURCE")) & (df_pred["model_key"].str.contains("matched"))].copy()
    
    df_grp["Experiment"] = df_grp["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    df_grp["Group"] = df_grp["group"].map(GROUP_MAP).fillna(df_grp["group"])
    df_grp["Importance (%)"] = df_grp["normalized_group_importance"] * 100
    
    df_pred["Experiment"] = df_pred["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    df_pred["feature_label"] = df_pred["feature"].map(PRED_MAP).fillna(df_pred["feature"])
    
    top_preds = df_pred.groupby("Experiment").head(10)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    sns.barplot(data=df_grp, y="Group", x="Importance (%)", hue="Experiment", ax=axes[0,0], palette=PALETTE)
    axes[0,0].set_title("(a) Grouped mean |SHAP| — matched support", loc='left')
    axes[0,0].set_ylabel("")
    
    sns.barplot(data=top_preds, y="feature_label", x="mean_abs_shap", hue="Experiment", ax=axes[0,1], palette=PALETTE)
    axes[0,1].set_title("(b) Top predictors", loc='left')
    axes[0,1].set_ylabel("")
    axes[0,1].set_xlabel("Mean |SHAP|")
    
    cdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_cdf_daily_absolute_increment_matched_support_cohort.parquet", is_parquet=True)
    nocdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_nocdf_daily_absolute_increment_matched_support_cohort.parquet", is_parquet=True)
    
    if cdf_shap is not None and nocdf_shap is not None:
        s_cdf = cdf_shap.sample(n=min(5000, len(cdf_shap)), random_state=42)
        s_nocdf = nocdf_shap.sample(n=min(5000, len(nocdf_shap)), random_state=42)
        
        for ax, pred in zip([axes[1,0], axes[1,1]], ["ssm_lag1", "precip_lag1"]):
            if f"value__{pred}" in s_cdf.columns and f"shap__{pred}" in s_cdf.columns:
                ax.scatter(s_cdf[f"value__{pred}"], s_cdf[f"shap__{pred}"], label="CDF", alpha=0.3, s=10, color=PALETTE["CDF"])
                ax.scatter(s_nocdf[f"value__{pred}"], s_nocdf[f"shap__{pred}"], label="NoCDF", alpha=0.3, s=10, color=PALETTE["NoCDF"])
                ax.set_title(f"({chr(99 + ['ssm_lag1', 'precip_lag1'].index(pred))}) {pred} dependence", loc='left')
                ax.set_xlabel(PRED_MAP.get(pred, pred))
                ax.set_ylabel("SHAP value")
                ax.legend()
            
    save_fig(fig, str(MAIN_DIR / "Figure_5_SOURCE_XAI"))

def generate_figure_6():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    if df_grp is None: return
        
    df_tr = df_grp[df_grp["model_key"].str.contains("TRANSFER")].copy()
    df_tr["Model"] = df_tr["model_key"].apply(clean_label)
    df_tr["Group"] = df_tr["group"].map(GROUP_MAP).fillna(df_tr["group"])
    df_tr["Importance (%)"] = df_tr["normalized_group_importance"] * 100
    
    pivot = df_tr.pivot_table(index="Model", columns="Group", values="Importance (%)")
    
    row_order = [
        "RZSM — CDF", "RZSM — NoCDF",
        "ET — CDF", "ET — NoCDF",
        "Surface runoff — CDF", "Surface runoff — NoCDF",
        "Baseflow — CDF", "Baseflow — NoCDF"
    ]
    row_order = [r for r in row_order if r in pivot.index]
    pivot = pivot.loc[row_order]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax, cbar_kws={'label': 'Normalized mean |SHAP| (%)'})
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title("Predictive attribution of DA–OPL responses across land-surface variables", loc='left')
    save_fig(fig, str(MAIN_DIR / "Figure_6_TRANSFER_XAI"))

def generate_figure_7():
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    cdf_cohort = get_real_data("data/processed/modeling/xai/final_2020/cohorts/VALUE_da_cdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    nocdf_cohort = get_real_data("data/processed/modeling/xai/final_2020/cohorts/VALUE_da_nocdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    
    if cdf_cohort is not None and nocdf_cohort is not None:
        sns.kdeplot(cdf_cohort["value_ae"], label="CDF", ax=axes[0], color=PALETTE["CDF"])
        sns.kdeplot(nocdf_cohort["value_ae"], label="NoCDF", ax=axes[0], color=PALETTE["NoCDF"])
        axes[0].axvline(0, color='red', linestyle='--')
        
        # Exact frozen numbers
        axes[0].text(0.05, 0.95, f"CDF > 0: 35.42%\nNoCDF > 0: 41.18%", 
                     transform=axes[0].transAxes, verticalalignment='top')
        axes[0].set_title("(a) VALUE distribution\n(>0: lower absolute ET disagreement)", loc='left')
        axes[0].set_xlabel("VALUE")
        axes[0].legend()
        
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    df_pred = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_predictor_summary.csv")
    
    if df_grp is not None and df_pred is not None:
        df_v = df_grp[df_grp["model_key"].str.contains("VALUE")].copy()
        df_v["Experiment"] = df_v["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
        df_v["Group"] = df_v["group"].map(GROUP_MAP).fillna(df_v["group"])
        df_v["Importance (%)"] = df_v["normalized_group_importance"] * 100
        sns.barplot(data=df_v, y="Group", x="Importance (%)", hue="Experiment", ax=axes[1], palette=PALETTE)
        axes[1].set_title("(b) Grouped normalized SHAP", loc='left')
        axes[1].set_ylabel("")
        
        df_p = df_pred[df_pred["model_key"].str.contains("VALUE")].copy()
        df_p["Experiment"] = df_p["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
        df_p["feature_label"] = df_p["feature"].map(PRED_MAP).fillna(df_p["feature"])
        top_preds = df_p.groupby("Experiment").head(10)
        sns.barplot(data=top_preds, y="feature_label", x="mean_abs_shap", hue="Experiment", ax=axes[2], palette=PALETTE)
        axes[2].set_title("(c) Top predictors", loc='left')
        axes[2].set_xlabel("Mean |SHAP|")
        axes[2].set_ylabel("")
        
    cdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_cdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    nocdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_nocdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    
    if cdf_shap is not None and nocdf_shap is not None:
        s_cdf = cdf_shap.sample(n=min(5000, len(cdf_shap)), random_state=42)
        s_nocdf = nocdf_shap.sample(n=min(5000, len(nocdf_shap)), random_state=42)
        
        preds_to_plot = ["et_opl_lag1", "tair_t", "land_cover_fraction_16"]
        for i, pred in enumerate(preds_to_plot):
            if f"value__{pred}" in s_cdf.columns and f"shap__{pred}" in s_cdf.columns:
                axes[3+i].scatter(s_cdf[f"value__{pred}"], s_cdf[f"shap__{pred}"], label="CDF", alpha=0.3, s=10, color=PALETTE["CDF"])
                axes[3+i].scatter(s_nocdf[f"value__{pred}"], s_nocdf[f"shap__{pred}"], label="NoCDF", alpha=0.3, s=10, color=PALETTE["NoCDF"])
                axes[3+i].set_title(f"({chr(100+i)}) {pred} dependence", loc='left')
                axes[3+i].set_xlabel(PRED_MAP.get(pred, pred))
                axes[3+i].set_ylabel("SHAP value")
                axes[3+i].legend()

    save_fig(fig, str(MAIN_DIR / "Figure_7_VALUE_XAI"))

def generate_figure_8():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    if df_grp is None: return
        
    df_grp = df_grp[~((df_grp["model_key"].str.contains("SOURCE")) & (df_grp["model_key"].str.contains("native")))].copy()
    
    df_grp["Model"] = df_grp["model_key"].apply(clean_label)
    df_grp["Group"] = df_grp["group"].map(GROUP_MAP).fillna(df_grp["group"])
    df_grp["Importance (%)"] = df_grp["normalized_group_importance"] * 100
    
    pivot = df_grp.pivot_table(index="Model", columns="Group", values="Importance (%)")
    
    row_order = [
        "SOURCE — CDF matched", "SOURCE — NoCDF matched",
        "RZSM — CDF", "RZSM — NoCDF",
        "ET — CDF", "ET — NoCDF",
        "Surface runoff — CDF", "Surface runoff — NoCDF",
        "Baseflow — CDF", "Baseflow — NoCDF",
        "VALUE — CDF", "VALUE — NoCDF"
    ]
    row_order = [r for r in row_order if r in pivot.index]
    pivot = pivot.loc[row_order]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax, cbar_kws={'label': 'Normalized mean |SHAP| (%)'})
    
    ax.axhline(2, color='black', lw=2)
    for i in range(4, 11, 2):
        ax.axhline(i, color='gray', lw=1, linestyle='--')
    ax.axhline(10, color='black', lw=2)
    
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title("Reorganization of predictive attribution across the SOURCE–TRANSFER–VALUE pathway", loc='left')
    save_fig(fig, str(MAIN_DIR / "Figure_8_pathway_synthesis"))

if __name__ == "__main__":
    generate_figure_3()
    generate_figure_4()
    generate_figure_5()
    generate_figure_6()
    generate_figure_7()
    generate_figure_8()
