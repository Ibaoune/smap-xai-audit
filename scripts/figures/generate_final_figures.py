import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
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
    "antecedent_soil_moisture_state": "Antecedent SM",
    "meteorological_forcing": "Met Forcing",
    "soil_properties": "Soil Prop",
    "land_cover_or_vegetation": "Land Cover",
    "temporal_context": "Temporal",
    "topography": "Topography",
    "antecedent_land_surface_fluxes": "Antecedent Flux",
    "assimilation_diagnostics_or_history": "DA History",
    "forcing_perturbation_controls": "Forcing Perturbation"
}

def clean_label(key):
    # key e.g.: SOURCE_da_cdf_daily_absolute_increment_matched_support
    parts = key.split("_")
    block = parts[0]
    if block == "SOURCE":
        exp = EXP_MAP[f"{parts[1]}_{parts[2]}"]
        supp = "Matched support" if "matched" in key else "Native support"
        return f"SOURCE — {exp} matched" if "matched" in key else f"SOURCE — {exp} native"
    elif block == "TRANSFER":
        exp = EXP_MAP[f"{parts[1]}_{parts[2]}"]
        targ = "_".join(parts[3:-2])
        if targ in TARG_MAP:
            targ = TARG_MAP[targ]
        return f"{targ} — {exp}"
    elif block == "VALUE":
        exp = EXP_MAP[f"{parts[1]}_{parts[2]}"]
        return f"VALUE — {exp}"
    return key

def save_fig(fig, path_without_ext):
    fig.tight_layout()
    fig.savefig(f"{path_without_ext}.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.png", dpi=300, bbox_inches='tight')
    plt.close(fig)

def get_real_data(path, is_parquet=False):
    if not os.path.exists(path):
        print(f"Missing canonical data: {path}")
        return None
    if is_parquet:
        return pd.read_parquet(path)
    return pd.read_csv(path)

def generate_figure_3():
    # Figure 3 requires canonical spatial maps which are scattered or not directly accessible 
    # as single clear files. The instructions say to STOP for that panel and report the missing source.
    print("FIGURE 3 INCOMPLETE: Missing explicit consolidated spatial map grids for (a), (b), (d), (e). Stopping generation for Fig 3.")
    # We leave Figure 3 ungenerated rather than inventing incomplete data.
    pass

def generate_figure_4():
    # 2019 Temporal Validation (RF03b)
    df_temp_src = get_real_data("reports/modeling/models/random_forest/rf03b/rf03b_source_matched_metrics.csv")
    df_temp_prim = get_real_data("reports/modeling/models/random_forest/rf03b/rf03b_primary_metrics.csv")
    df_temp = pd.concat([df_temp_src, df_temp_prim]) if df_temp_src is not None and df_temp_prim is not None else None
    
    # Five-fold spatial block CV (RF02)
    df_spat_val = get_real_data("reports/modeling/models/random_forest/rf02/rf02_value_fold_metrics.csv")
    df_spat_src = get_real_data("reports/modeling/models/random_forest/rf02/rf02_source_fold_metrics.csv")
    df_spat_tr = get_real_data("reports/modeling/models/random_forest/rf02/rf02_transfer_fold_metrics.csv")
    df_spat = pd.concat([df_spat_val, df_spat_src, df_spat_tr]) if df_spat_val is not None else None
    
    # Final 2020 (RF06)
    df_final = get_real_data("reports/modeling/final_2020/final_metrics_2020.csv")
    
    if df_temp is None or df_spat is None or df_final is None:
        print("FIGURE 4 INCOMPLETE: Missing CV or final metric canonical data.")
        return
        
    # Clean up labels
    for df in [df_temp, df_spat, df_final]:
        df["experiment"] = df["experiment"].map(EXP_MAP)
        df["target"] = df["target"].map(TARG_MAP)
        # Filter for matched support for SOURCE
        if "support_mode" in df.columns:
            support_col = "support_mode"
        elif "support" in df.columns:
            support_col = "support"
        else:
            support_col = None
            
        if support_col:
            df.loc[(df["block"]=="SOURCE") & (df[support_col]=="native_support"), "target"] = "DROP"
        df.loc[(df["block"]=="SOURCE"), "target"] = "SOURCE"
    
    df_temp = df_temp[df_temp["target"] != "DROP"]
    df_spat = df_spat[df_spat["target"] != "DROP"]
    df_final = df_final[df_final["target"] != "DROP"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    # (a) Temporal Validation MAE Skill
    sns.barplot(data=df_temp, y="target", x="MAE_skill", hue="experiment", ax=axes[0])
    axes[0].set_title("(a) 2019 Temporal Validation MAE Skill", loc='left')
    axes[0].set_ylabel("")
    axes[0].set_xlabel("MAE Skill")
    
    # (b) Spatial Block CV MAE Skill
    sns.barplot(data=df_spat, y="target", x="MAE_skill", hue="experiment", ax=axes[1], errorbar='sd')
    axes[1].set_title("(b) Five-Fold Spatial CV MAE Skill", loc='left')
    axes[1].set_ylabel("")
    axes[1].set_xlabel("MAE Skill")
    
    # (c) Final 2020 MAE Skill
    sns.barplot(data=df_final, y="target", x="MAE_skill", hue="experiment", ax=axes[2])
    axes[2].set_title("(c) Final 2020 Holdout MAE Skill", loc='left')
    axes[2].set_ylabel("")
    axes[2].set_xlabel("MAE Skill")
    
    # (d) Final 2020 R2
    sns.barplot(data=df_final, y="target", x="R2", hue="experiment", ax=axes[3])
    axes[3].set_title("(d) Final 2020 Holdout R²", loc='left')
    axes[3].set_ylabel("")
    axes[3].set_xlabel("R²")
    
    save_fig(fig, str(MAIN_DIR / "Figure_4_RF_performance"))

def generate_figure_5():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    df_pred = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_predictor_summary.csv")
    
    if df_grp is None or df_pred is None:
        print("FIGURE 5 INCOMPLETE: Missing canonical summary data.")
        return
        
    df_grp = df_grp[(df_grp["model_key"].str.contains("SOURCE")) & (df_grp["model_key"].str.contains("matched"))].copy()
    df_pred = df_pred[(df_pred["model_key"].str.contains("SOURCE")) & (df_pred["model_key"].str.contains("matched"))].copy()
    
    df_grp["Model"] = df_grp["model_key"].apply(clean_label)
    df_grp["Group"] = df_grp["group"].map(GROUP_MAP).fillna(df_grp["group"])
    df_grp["Importance (%)"] = df_grp["normalized_group_importance"] * 100
    
    df_pred["Model"] = df_pred["model_key"].apply(clean_label)
    
    # Only keep top 10
    top_preds = df_pred.groupby("Model").head(10)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # (a) Grouped SHAP
    sns.barplot(data=df_grp, y="Group", x="Importance (%)", hue="Model", ax=axes[0,0])
    axes[0,0].set_title("(a) Grouped Mean |SHAP| (Matched Support)", loc='left')
    axes[0,0].set_ylabel("")
    
    # (b) Top 10
    sns.barplot(data=top_preds, y="feature", x="mean_abs_shap", hue="Model", ax=axes[0,1])
    axes[0,1].set_title("(b) Top-10 Predictors", loc='left')
    axes[0,1].set_ylabel("")
    
    # (c) and (d) dependence plots require SHAP cohorts
    cdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_cdf_daily_absolute_increment_matched_support_cohort.parquet", is_parquet=True)
    nocdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_nocdf_daily_absolute_increment_matched_support_cohort.parquet", is_parquet=True)
    
    if cdf_shap is not None and nocdf_shap is not None:
        # Sample for plotting
        s_cdf = cdf_shap.sample(n=min(5000, len(cdf_shap)), random_state=42)
        s_nocdf = nocdf_shap.sample(n=min(5000, len(nocdf_shap)), random_state=42)
        
        if "shap__ssm_lag1" in s_cdf.columns and "value__ssm_lag1" in s_cdf.columns:
            axes[1,0].scatter(s_cdf["value__ssm_lag1"], s_cdf["shap__ssm_lag1"], label="CDF", alpha=0.3, s=10)
            axes[1,0].scatter(s_nocdf["value__ssm_lag1"], s_nocdf["shap__ssm_lag1"], label="NoCDF", alpha=0.3, s=10)
            axes[1,0].set_title("(c) ssm_lag1 Dependence", loc='left')
            axes[1,0].set_xlabel("ssm_lag1")
            axes[1,0].set_ylabel("SHAP Value")
            axes[1,0].legend()
            
        if "shap__precip_lag1" in s_cdf.columns and "value__precip_lag1" in s_cdf.columns:
            axes[1,1].scatter(s_cdf["value__precip_lag1"], s_cdf["shap__precip_lag1"], label="CDF", alpha=0.3, s=10)
            axes[1,1].scatter(s_nocdf["value__precip_lag1"], s_nocdf["shap__precip_lag1"], label="NoCDF", alpha=0.3, s=10)
            axes[1,1].set_title("(d) precip_lag1 Dependence", loc='left')
            axes[1,1].set_xlabel("precip_lag1")
            axes[1,1].set_ylabel("SHAP Value")
            axes[1,1].legend()
            
    save_fig(fig, str(MAIN_DIR / "Figure_5_SOURCE_XAI"))

def generate_figure_6():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    if df_grp is None:
        return
        
    df_tr = df_grp[df_grp["model_key"].str.contains("TRANSFER")].copy()
    df_tr["Model"] = df_tr["model_key"].apply(clean_label)
    df_tr["Group"] = df_tr["group"].map(GROUP_MAP).fillna(df_tr["group"])
    df_tr["Importance (%)"] = df_tr["normalized_group_importance"] * 100
    
    pivot = df_tr.pivot_table(index="Model", columns="Group", values="Importance (%)")
    
    # Target row order
    row_order = [
        "RZSM — CDF", "RZSM — NoCDF",
        "ET — CDF", "ET — NoCDF",
        "Surface runoff — CDF", "Surface runoff — NoCDF",
        "Baseflow — CDF", "Baseflow — NoCDF"
    ]
    # Filter to existing rows to avoid KeyError
    row_order = [r for r in row_order if r in pivot.index]
    pivot = pivot.loc[row_order]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax, cbar_kws={'label': 'Normalized mean |SHAP| (%)'})
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title("TRANSFER Grouped SHAP Heatmap", loc='left')
    save_fig(fig, str(MAIN_DIR / "Figure_6_TRANSFER_XAI"))

def generate_figure_7():
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    cdf_cohort = get_real_data("data/processed/modeling/xai/final_2020/cohorts/VALUE_da_cdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    nocdf_cohort = get_real_data("data/processed/modeling/xai/final_2020/cohorts/VALUE_da_nocdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    
    if cdf_cohort is not None and nocdf_cohort is not None:
        sns.kdeplot(cdf_cohort["value_ae"], label="CDF", ax=axes[0])
        sns.kdeplot(nocdf_cohort["value_ae"], label="NoCDF", ax=axes[0])
        axes[0].axvline(0, color='red', linestyle='--')
        
        # Annotate
        cdf_pos = (cdf_cohort["value_ae"] > 0).mean() * 100
        nocdf_pos = (nocdf_cohort["value_ae"] > 0).mean() * 100
        axes[0].text(0.05, 0.95, f"CDF > 0: {cdf_pos:.2f}%\nNoCDF > 0: {nocdf_pos:.2f}%", 
                     transform=axes[0].transAxes, verticalalignment='top')
        axes[0].set_title("(a) VALUE Distribution\n(>0 = lower ET disagreement)", loc='left')
        axes[0].set_xlabel("VALUE")
        axes[0].legend()
    else:
        axes[0].text(0.5, 0.5, "Missing Cohort Data", ha='center')
        
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    df_pred = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_predictor_summary.csv")
    
    if df_grp is not None and df_pred is not None:
        df_v = df_grp[df_grp["model_key"].str.contains("VALUE")].copy()
        df_v["Model"] = df_v["model_key"].apply(clean_label)
        df_v["Group"] = df_v["group"].map(GROUP_MAP).fillna(df_v["group"])
        df_v["Importance (%)"] = df_v["normalized_group_importance"] * 100
        sns.barplot(data=df_v, y="Group", x="Importance (%)", hue="Model", ax=axes[1])
        axes[1].set_title("(b) Grouped Normalized SHAP", loc='left')
        axes[1].set_ylabel("")
        
        df_p = df_pred[df_pred["model_key"].str.contains("VALUE")].copy()
        df_p["Model"] = df_p["model_key"].apply(clean_label)
        top_preds = df_p.groupby("Model").head(10)
        sns.barplot(data=top_preds, y="feature", x="mean_abs_shap", hue="Model", ax=axes[2])
        axes[2].set_title("(c) Top Predictors", loc='left')
        axes[2].set_ylabel("")
        
    # Dependencies
    cdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_cdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    nocdf_shap = get_real_data("data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_nocdf_value_ae_native_support_cohort.parquet", is_parquet=True)
    
    if cdf_shap is not None and nocdf_shap is not None:
        s_cdf = cdf_shap.sample(n=min(5000, len(cdf_shap)), random_state=42)
        s_nocdf = nocdf_shap.sample(n=min(5000, len(nocdf_shap)), random_state=42)
        
        for i, pred in enumerate(["et_opl_lag1", "tair_t", "land_cover_fraction_16"]):
            if f"value__{pred}" in s_cdf.columns and f"shap__{pred}" in s_cdf.columns:
                axes[3+i].scatter(s_cdf[f"value__{pred}"], s_cdf[f"shap__{pred}"], label="CDF", alpha=0.3, s=10)
                axes[3+i].scatter(s_nocdf[f"value__{pred}"], s_nocdf[f"shap__{pred}"], label="NoCDF", alpha=0.3, s=10)
                axes[3+i].set_title(f"({chr(100+i)}) {pred} Dependence", loc='left')
                axes[3+i].set_xlabel(pred)
                axes[3+i].set_ylabel("SHAP Value")
                axes[3+i].legend()

    save_fig(fig, str(MAIN_DIR / "Figure_7_VALUE_XAI"))

def generate_figure_8():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    if df_grp is None:
        return
        
    # Remove native SOURCE rows
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
    
    # Add horizontal separators
    ax.axhline(2, color='black', lw=2)
    for i in range(4, 11, 2):
        ax.axhline(i, color='gray', lw=1, linestyle='--')
    ax.axhline(10, color='black', lw=2)
    
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title("SOURCE -> TRANSFER -> VALUE Synthesis", loc='left')
    save_fig(fig, str(MAIN_DIR / "Figure_8_pathway_synthesis"))

if __name__ == "__main__":
    generate_figure_3()
    generate_figure_4()
    generate_figure_5()
    generate_figure_6()
    generate_figure_7()
    generate_figure_8()
