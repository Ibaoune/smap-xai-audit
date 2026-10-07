import os
import json
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

SUPP_DIR = Path("figures/supplement")
SUPP_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {"CDF": "blue", "NoCDF": "orange"}

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
    "soil_texture_fraction_1": "Soil-texture fraction 1",
    "rzsm_opl_lag1": "Antecedent OPL RZSM (t-1)",
    "baseflow_opl_lag1": "Antecedent OPL Baseflow (t-1)",
    "et_opl_lag1": "Antecedent OPL ET (t-1)",
    "ssm_opl_lag1": "Antecedent OPL SSM (t-1)",
    "source_signed_increment_pre7d_sum": "Signed DA increment, previous 7 d",
    "precip_t": "Precipitation (t)",
    "soil_texture_fraction_6": "Soil-texture fraction 6",
    "tair_t": "Air temperature (t)"
}

TARG_MAP = {
    "daily_absolute_increment": "SOURCE",
    "delta_rzsm": "RZSM",
    "delta_et": "ET",
    "delta_surface_runoff": "Surface runoff",
    "delta_baseflow": "Baseflow",
    "value_ae": "VALUE"
}

def save_fig(fig, path_without_ext):
    fig.tight_layout()
    fig.savefig(f"{path_without_ext}.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.png", dpi=300, bbox_inches='tight')
    plt.close(fig)

def get_real_data(path, is_parquet=False):
    if not os.path.exists(path): return None
    return pd.read_parquet(path) if is_parquet else pd.read_csv(path)

# S1
def generate_s1():
    df_grp = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv")
    df_pred = get_real_data("data/processed/modeling/xai/final_2020/summaries/tidy_predictor_summary.csv")
    if df_grp is None or df_pred is None: return

    src_grp = df_grp[df_grp["model_key"].str.contains("SOURCE")].copy()
    src_grp["Experiment"] = src_grp["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    src_grp["Support"] = src_grp["model_key"].apply(lambda x: "Matched" if "matched" in x else "Native")
    src_grp["Group"] = src_grp["group"].map(GROUP_MAP).fillna(src_grp["group"])
    src_grp["Importance (%)"] = src_grp["normalized_group_importance"] * 100

    src_pred = df_pred[df_pred["model_key"].str.contains("SOURCE")].copy()
    src_pred["Experiment"] = src_pred["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    src_pred["Support"] = src_pred["model_key"].apply(lambda x: "Matched" if "matched" in x else "Native")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    sns.barplot(data=src_grp[src_grp["Experiment"]=="CDF"], y="Group", x="Importance (%)", hue="Support", ax=axes[0,0], palette=["#2ca02c", "#d62728"])
    axes[0,0].set_title("(a) CDF: Grouped |SHAP| (Native vs Matched)", loc='left')
    axes[0,0].set_ylabel("")

    sns.barplot(data=src_grp[src_grp["Experiment"]=="NoCDF"], y="Group", x="Importance (%)", hue="Support", ax=axes[0,1], palette=["#2ca02c", "#d62728"])
    axes[0,1].set_title("(b) NoCDF: Grouped |SHAP| (Native vs Matched)", loc='left')
    axes[0,1].set_ylabel("")

    for i, exp in enumerate(["CDF", "NoCDF"]):
        nat = src_pred[(src_pred["Experiment"]==exp) & (src_pred["Support"]=="Native")].set_index("feature")["mean_abs_shap"]
        mat = src_pred[(src_pred["Experiment"]==exp) & (src_pred["Support"]=="Matched")].set_index("feature")["mean_abs_shap"]
        df_merged = pd.DataFrame({"Native": nat, "Matched": mat}).dropna()
        axes[1,i].scatter(df_merged["Native"], df_merged["Matched"], alpha=0.7)
        axes[1,i].plot([0, df_merged.max().max()], [0, df_merged.max().max()], 'k--')
        
        # Load the stats json if available
        stats_path = "data/processed/modeling/xai/final_2020/summaries/source_matched_comparison_stats.json"
        if os.path.exists(stats_path):
            with open(stats_path) as f:
                stats = json.load(f)
            axes[1,i].text(0.05, 0.95, f"Rank rho: {stats['predictor_rho']:.3f}\nTop-10 overlap: {stats['top10_overlap']}/10", 
                           transform=axes[1,i].transAxes, verticalalignment='top')
        
        axes[1,i].set_title(f"({chr(99+i)}) {exp}: Predictor Mean |SHAP| Agreement", loc='left')
        axes[1,i].set_xlabel("Native Support Mean |SHAP|")
        axes[1,i].set_ylabel("Matched Support Mean |SHAP|")

    save_fig(fig, str(SUPP_DIR / "Figure_S1_SOURCE_support_sensitivity"))

# S2
def generate_s2():
    summary_dir = Path("data/processed/modeling/xai/final_2020/summaries")
    files = list(summary_dir.glob("robustness_*.json"))
    if not files: return
    
    data = []
    for f in files:
        key = f.stem.replace("robustness_", "")
        parts = key.split("_")
        block = parts[0]
        exp = "CDF" if "da_cdf" in key else "NoCDF"
        targ = "_".join(parts[3:-2])
        if targ in TARG_MAP: targ = TARG_MAP[targ]
        model_name = f"{block} {targ} {exp}" if targ != "SOURCE" else f"{block} {exp}"
        
        with open(f) as jf:
            d = json.load(jf)
            data.append({"Model": model_name, "Rho": d["spearman_rho"], "Top-5": d["top5_overlap"], "Top-10": d["top10_overlap"]})
            
    df = pd.DataFrame(data).sort_values("Model")
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    
    sns.barplot(data=df, y="Model", x="Rho", ax=axes[0], color="gray")
    axes[0].set_title("(a) Spearman Rho (SHAP vs Permutation)", loc='left')
    axes[0].set_ylabel("")
    axes[0].set_xlabel("Spearman Rho")
    
    sns.barplot(data=df, y="Model", x="Top-10", ax=axes[1], color="gray")
    axes[1].set_title("(b) Top-10 Predictor Overlap", loc='left')
    axes[1].set_ylabel("")
    axes[1].set_xlabel("Overlap Count (out of 10)")
    
    sns.barplot(data=df, y="Model", x="Top-5", ax=axes[2], color="gray")
    axes[2].set_title("(c) Top-5 Predictor Overlap", loc='left')
    axes[2].set_ylabel("")
    axes[2].set_xlabel("Overlap Count (out of 5)")
    
    save_fig(fig, str(SUPP_DIR / "Figure_S2_SHAP_permutation_robustness"))

# S3
def generate_s3():
    df = get_real_data("data/processed/modeling/xai/final_2020/summaries/seasonal_group_summary_2020.csv")
    if df is None: return
    
    df = df[df["model_key"].str.contains("SOURCE") & df["model_key"].str.contains("matched")].copy()
    df["Experiment"] = df["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    df["Group"] = df["group"].map(GROUP_MAP).fillna(df["group"])
    
    # Melt it back for barplots
    df_melt = df.melt(id_vars=["Experiment", "Group"], value_vars=["DJF_normalized_importance", "JJA_normalized_importance"], var_name="season", value_name="Importance (%)")
    df_melt["Importance (%)"] = df_melt["Importance (%)"] * 100
    df_melt["season"] = df_melt["season"].apply(lambda x: "DJF" if "DJF" in x else "JJA")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    sns.barplot(data=df_melt[df_melt["Experiment"]=="CDF"], y="Group", x="Importance (%)", hue="season", ax=axes[0], palette=["#1f77b4", "#ff7f0e"])
    axes[0].set_title("(a) CDF: Seasonal Grouped Attribution", loc='left')
    axes[0].set_ylabel("")
    
    sns.barplot(data=df_melt[df_melt["Experiment"]=="NoCDF"], y="Group", x="Importance (%)", hue="season", ax=axes[1], palette=["#1f77b4", "#ff7f0e"])
    axes[1].set_title("(b) NoCDF: Seasonal Grouped Attribution", loc='left')
    axes[1].set_ylabel("")
    
    df["Difference (%)"] = df["DJF_minus_JJA"] * 100
    sns.barplot(data=df, y="Group", x="Difference (%)", hue="Experiment", ax=axes[2], palette=PALETTE)
    axes[2].set_title("(c) Difference (DJF minus JJA)", loc='left')
    axes[2].set_ylabel("")
    
    save_fig(fig, str(SUPP_DIR / "Figure_S3_SOURCE_seasonal_robustness"))

# S4
def generate_s4():
    df = get_real_data("data/processed/modeling/xai/final_2020/summaries/seasonal_group_summary_2020.csv")
    if df is None: return
    
    df = df[df["model_key"].str.contains("TRANSFER")].copy()
    df["Group"] = df["group"].map(GROUP_MAP).fillna(df["group"])
    
    def get_targ(k):
        exp = "CDF" if "da_cdf" in k else "NoCDF"
        t = "_".join(k.split("_")[3:-2])
        if t in TARG_MAP: t = TARG_MAP[t]
        return f"{t} — {exp}"
    df["Model"] = df["model_key"].apply(get_targ)
    
    djf = df.pivot_table(index="Model", columns="Group", values="DJF_normalized_importance") * 100
    jja = df.pivot_table(index="Model", columns="Group", values="JJA_normalized_importance") * 100
    diff = df.pivot_table(index="Model", columns="Group", values="DJF_minus_JJA") * 100
    
    # Sort models nicely
    row_order = [
        "RZSM — CDF", "RZSM — NoCDF",
        "ET — CDF", "ET — NoCDF",
        "Surface runoff — CDF", "Surface runoff — NoCDF",
        "Baseflow — CDF", "Baseflow — NoCDF"
    ]
    row_order = [r for r in row_order if r in djf.index]
    djf = djf.loc[row_order]
    jja = jja.loc[row_order]
    diff = diff.loc[row_order]
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    sns.heatmap(djf, annot=True, fmt=".1f", cmap="YlGnBu", ax=axes[0], cbar=False)
    axes[0].set_title("(a) DJF Attribution (%)", loc='left')
    axes[0].set_ylabel("")
    
    sns.heatmap(jja, annot=True, fmt=".1f", cmap="YlGnBu", ax=axes[1], cbar=False)
    axes[1].set_title("(b) JJA Attribution (%)", loc='left')
    axes[1].set_ylabel("")
    
    sns.heatmap(diff, annot=True, fmt=".1f", cmap="vlag", center=0, ax=axes[2], cbar_kws={'label': 'DJF - JJA Difference (%)'})
    axes[2].set_title("(c) Difference (DJF minus JJA)", loc='left')
    axes[2].set_ylabel("")
    
    save_fig(fig, str(SUPP_DIR / "Figure_S4_TRANSFER_seasonal_robustness"))

# S5
def generate_s5():
    df = get_real_data("data/processed/modeling/xai/final_2020/summaries/seasonal_group_summary_2020.csv")
    if df is None: return
    
    df = df[df["model_key"].str.contains("VALUE")].copy()
    df["Experiment"] = df["model_key"].apply(lambda x: "CDF" if "da_cdf" in x else "NoCDF")
    df["Group"] = df["group"].map(GROUP_MAP).fillna(df["group"])
    
    df_melt = df.melt(id_vars=["Experiment", "Group"], value_vars=["DJF_normalized_importance", "JJA_normalized_importance"], var_name="season", value_name="Importance (%)")
    df_melt["Importance (%)"] = df_melt["Importance (%)"] * 100
    df_melt["season"] = df_melt["season"].apply(lambda x: "DJF" if "DJF" in x else "JJA")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    sns.barplot(data=df_melt[df_melt["Experiment"]=="CDF"], y="Group", x="Importance (%)", hue="season", ax=axes[0], palette=["#1f77b4", "#ff7f0e"])
    axes[0].set_title("(a) CDF: Seasonal VALUE Attribution", loc='left')
    axes[0].set_ylabel("")
    
    sns.barplot(data=df_melt[df_melt["Experiment"]=="NoCDF"], y="Group", x="Importance (%)", hue="season", ax=axes[1], palette=["#1f77b4", "#ff7f0e"])
    axes[1].set_title("(b) NoCDF: Seasonal VALUE Attribution", loc='left')
    axes[1].set_ylabel("")
    
    save_fig(fig, str(SUPP_DIR / "Figure_S5_VALUE_seasonal_robustness"))

# S6
def generate_s6():
    df = get_real_data("data/processed/modeling/xai/final_2020/summaries/spatial_group_stability_2020.csv")
    if df is None: return
    
    df["Group"] = df["group"].map(GROUP_MAP).fillna(df["group"])
    def get_model(k):
        parts = k.split("_")
        block = parts[0]
        exp = "CDF" if "da_cdf" in k else "NoCDF"
        if block == "SOURCE": return f"SOURCE {exp}"
        if block == "VALUE": return f"VALUE {exp}"
        t = "_".join(parts[3:-2])
        if t in TARG_MAP: t = TARG_MAP[t]
        return f"{t} {exp}"
        
    df["Model"] = df["model_key"].apply(get_model)
    df["SD (%)"] = df["std"] * 100
    
    pivot = df.pivot_table(index="Model", columns="Group", values="SD (%)")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="Reds", ax=ax, cbar_kws={'label': 'SD across 2020 spatial strata (%)'})
    ax.set_title("2020 spatial-stratum attribution stability", loc='left')
    ax.set_ylabel("")
    ax.set_xlabel("")
    
    save_fig(fig, str(SUPP_DIR / "Figure_S6_spatial_stratum_stability"))

# S7
def generate_s7():
    fig, axes = plt.subplots(4, 2, figsize=(14, 18))
    
    def plot_dep(ax, cohort_path, pred, title, cdf_flag):
        if not os.path.exists(cohort_path): return
        df = pd.read_parquet(cohort_path)
        df = df.sample(n=min(5000, len(df)), random_state=42)
        if f"value__{pred}" in df.columns and f"shap__{pred}" in df.columns:
            lbl, col = ("CDF", PALETTE["CDF"]) if cdf_flag else ("NoCDF", PALETTE["NoCDF"])
            ax.scatter(df[f"value__{pred}"], df[f"shap__{pred}"], label=lbl, alpha=0.3, s=10, color=col)
            ax.set_title(title, loc='left')
            ax.set_xlabel(PRED_MAP.get(pred, pred))
            ax.set_ylabel("SHAP value")
            ax.legend()
            
    # SOURCE (rzsm_lag1, land_cover_fraction_16)
    src_c = "data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_cdf_daily_absolute_increment_matched_support_cohort.parquet"
    src_n = "data/processed/modeling/xai/final_2020/shap/shap_SOURCE_da_nocdf_daily_absolute_increment_matched_support_cohort.parquet"
    plot_dep(axes[0,0], src_c, "rzsm_lag1", "(a) SOURCE (CDF): rzsm_lag1", True)
    plot_dep(axes[0,0], src_n, "rzsm_lag1", "(a) SOURCE (CDF/NoCDF): rzsm_lag1", False)
    plot_dep(axes[0,1], src_c, "land_cover_fraction_16", "(b) SOURCE (CDF): LC16", True)
    plot_dep(axes[0,1], src_n, "land_cover_fraction_16", "(b) SOURCE (CDF/NoCDF): LC16", False)

    # RZSM
    r_c = "data/processed/modeling/xai/final_2020/shap/shap_TRANSFER_da_cdf_delta_rzsm_native_support_cohort.parquet"
    r_n = "data/processed/modeling/xai/final_2020/shap/shap_TRANSFER_da_nocdf_delta_rzsm_native_support_cohort.parquet"
    plot_dep(axes[1,0], r_c, "rzsm_opl_lag1", "(c) RZSM (CDF/NoCDF)", True)
    plot_dep(axes[1,0], r_n, "rzsm_opl_lag1", "(c) RZSM (CDF/NoCDF)", False)
    plot_dep(axes[1,1], r_c, "baseflow_opl_lag1", "(d) RZSM (CDF/NoCDF)", True)
    plot_dep(axes[1,1], r_n, "baseflow_opl_lag1", "(d) RZSM (CDF/NoCDF)", False)

    # ET
    e_c = "data/processed/modeling/xai/final_2020/shap/shap_TRANSFER_da_cdf_delta_et_native_support_cohort.parquet"
    e_n = "data/processed/modeling/xai/final_2020/shap/shap_TRANSFER_da_nocdf_delta_et_native_support_cohort.parquet"
    plot_dep(axes[2,0], e_c, "ssm_opl_lag1", "(e) ET (CDF/NoCDF)", True)
    plot_dep(axes[2,0], e_n, "ssm_opl_lag1", "(e) ET (CDF/NoCDF)", False)
    plot_dep(axes[2,1], e_c, "source_signed_increment_pre7d_sum", "(f) ET (CDF/NoCDF)", True)
    plot_dep(axes[2,1], e_n, "source_signed_increment_pre7d_sum", "(f) ET (CDF/NoCDF)", False)

    # VALUE
    v_c = "data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_cdf_value_ae_native_support_cohort.parquet"
    v_n = "data/processed/modeling/xai/final_2020/shap/shap_VALUE_da_nocdf_value_ae_native_support_cohort.parquet"
    plot_dep(axes[3,0], v_c, "ssm_opl_lag1", "(g) VALUE (CDF/NoCDF)", True)
    plot_dep(axes[3,0], v_n, "ssm_opl_lag1", "(g) VALUE (CDF/NoCDF)", False)
    plot_dep(axes[3,1], v_c, "et_opl_lag1", "(h) VALUE (CDF/NoCDF)", True)
    plot_dep(axes[3,1], v_n, "et_opl_lag1", "(h) VALUE (CDF/NoCDF)", False)

    save_fig(fig, str(SUPP_DIR / "Figure_S7_additional_dependence_relationships"))

if __name__ == "__main__":
    generate_s1()
    generate_s2()
    generate_s3()
    generate_s4()
    generate_s5()
    generate_s6()
    generate_s7()
