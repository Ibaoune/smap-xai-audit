#!/usr/bin/env python
"""
RF-04B-VALUE: Generate all development figures (matplotlib only).

VALUE-A: value_ae target distribution, CDF vs NoCDF
VALUE-B: scientific-group importance, CDF vs NoCDF
VALUE-C: top predictor mean|SHAP| comparison, CDF vs NoCDF
VALUE-D: SHAP value distributions (top-8 predictors)
VALUE-E: dependence plots for frozen top-4 predictors
VALUE-F: DJF vs JJA group attribution
VALUE-G: spatial-fold group stability

GLEAM is an external evaluation reference — not ground truth.
2020 SEALED. No seaborn.
"""
import json
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

IN_DIR  = Path("data/processed/modeling/xai/outputs/value")
OUT_DIR = Path("figures/development/value")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET      = "value_ae"
EXPS        = ["da_cdf", "da_nocdf"]
CDF_COLOR   = "#2E86AB"
NOCDF_COLOR = "#E84855"
DJF_COLOR   = "#5B5EA6"
JJA_COLOR   = "#F4A261"

GROUP_ORDER = [
    "antecedent_soil_moisture_state",
    "meteorological_forcing",
    "temporal_context",
    "land_cover_or_vegetation",
    "soil_properties",
    "topography",
    "assimilation_diagnostics_or_history",
    "antecedent_land_surface_fluxes",
    "forcing_perturbation_controls",
]
GROUP_SHORT = {
    "antecedent_soil_moisture_state":      "Antec. SM state",
    "meteorological_forcing":              "Meteo. forcing",
    "temporal_context":                    "Temporal context",
    "land_cover_or_vegetation":            "Land cover/veg.",
    "soil_properties":                     "Soil properties",
    "topography":                          "Topography",
    "assimilation_diagnostics_or_history": "Assim. diagnostics",
    "antecedent_land_surface_fluxes":      "Antec. LSM fluxes",
    "forcing_perturbation_controls":       "Forcing ctrl.",
}


def savefig(fig, name, dpi=150):
    p = OUT_DIR / name
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {p}")


def fig_a_distribution():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        "VALUE-A  |  value_ae distribution · 2019 development cohort\n"
        "value_ae = |ET_OPL − ET_GLEAM| − |ET_DA − ET_GLEAM|   "
        "(GLEAM is an external evaluation reference, not ground truth)",
        fontsize=9,
    )
    colors = {"da_cdf": CDF_COLOR, "da_nocdf": NOCDF_COLOR}
    labels = {"da_cdf": "CDF", "da_nocdf": "NoCDF"}
    for ax, exp in zip(axes, EXPS):
        df   = pd.read_parquet(IN_DIR / f"shap_{exp}_{TARGET}.parquet")
        vals = df["target"].values
        ax.hist(vals, bins=80, color=colors[exp], alpha=0.85, edgecolor="none")
        ax.axvline(0, color="k", linewidth=1.2, linestyle="--", alpha=0.7)
        ax.axvline(float(np.mean(vals)), color=colors[exp], linewidth=1.5,
                   linestyle=":", label=f"mean={np.mean(vals):.3f}")
        ax.set_title(
            f"{labels[exp]}  (n={len(vals):,})\n"
            f"mean={np.mean(vals):.3f}  frac>0={np.mean(vals>0):.2%}",
            fontsize=9,
        )
        ax.set_xlabel("value_ae", fontsize=9)
        ax.set_ylabel("Count", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_a_distribution.png")


def fig_b_group_importance():
    gs      = pd.read_csv(IN_DIR / "tidy_group_summary.csv")
    grp_lbl = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    fig, ax = plt.subplots(figsize=(11, 5))
    fig.suptitle(
        "VALUE-B  |  Scientific-group predictive attribution · value_ae · 2019 dev cohort",
        fontsize=10,
    )
    y = np.arange(len(GROUP_ORDER))
    h = 0.38
    for exp, color, dy, label in [
        ("da_cdf",   CDF_COLOR,   h/2,  "CDF"),
        ("da_nocdf", NOCDF_COLOR, -h/2, "NoCDF"),
    ]:
        sub  = gs[gs["experiment"] == exp].set_index("group")
        vals = [float(sub["normalized_group_importance"].get(g, 0)) * 100 for g in GROUP_ORDER]
        ax.barh(y + dy, vals, h, color=color, label=label, alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(grp_lbl, fontsize=9)
    ax.set_xlabel("Normalized group importance (%)", fontsize=9)
    ax.invert_yaxis()
    ax.legend(fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_b_group_importance.png")


def fig_c_top_predictors():
    ps    = pd.read_csv(IN_DIR / "tidy_predictor_summary.csv")
    cdf_t = ps[ps["experiment"] == "da_cdf"].sort_values("mean_abs_shap", ascending=False).head(12)
    nocdf = ps[ps["experiment"] == "da_nocdf"]
    mm    = pd.merge(
        cdf_t[["feature","mean_abs_shap"]],
        nocdf[["feature","mean_abs_shap"]],
        on="feature", suffixes=("_cdf","_nocdf"),
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        "VALUE-C  |  Top-12 predictor mean|SHAP| · value_ae · 2019 dev cohort",
        fontsize=10,
    )
    y = np.arange(len(mm)); h = 0.38
    ax.barh(y + h/2, mm["mean_abs_shap_cdf"],   h, color=CDF_COLOR,   label="CDF",   alpha=0.85)
    ax.barh(y - h/2, mm["mean_abs_shap_nocdf"], h, color=NOCDF_COLOR, label="NoCDF", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(mm["feature"], fontsize=8)
    ax.set_xlabel("Mean |SHAP|", fontsize=9)
    ax.invert_yaxis()
    ax.legend(fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_c_top_predictors.png")


def fig_d_shap_distributions():
    ps   = pd.read_csv(IN_DIR / "tidy_predictor_summary.csv")
    top8 = (ps[ps["experiment"] == "da_cdf"]
              .sort_values("mean_abs_shap", ascending=False)
              .head(8)["feature"].tolist())
    df   = pd.read_parquet(IN_DIR / f"shap_da_cdf_{TARGET}.parquet")
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    fig.suptitle(
        "VALUE-D  |  SHAP value distributions — top-8 predictors (CDF · 2019 dev cohort)\n"
        "SHAP > 0: pushes predicted value_ae upward "
        "(associated with lower abs. ET disagreement relative to OPL)",
        fontsize=9,
    )
    for ax, feat in zip(axes.flat, top8):
        vals = df[f"shap__{feat}"].values
        ax.hist(vals, bins=50, color=CDF_COLOR, alpha=0.8, edgecolor="none")
        ax.axvline(0, color="k", linewidth=0.8, linestyle="--", alpha=0.6)
        ax.set_title(f"{feat}\nmean|SHAP|={np.mean(np.abs(vals)):.5f}", fontsize=7)
        ax.set_xlabel("SHAP (value_ae)", fontsize=7)
        ax.tick_params(labelsize=6)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_d_shap_distributions.png")


def fig_e_dependence():
    with open(IN_DIR / "dependence_features.json") as f:
        top4 = json.load(f)["top_4_dependence_features"]
    fig, axes = plt.subplots(2, 4, figsize=(14, 8))
    fig.suptitle(
        "VALUE-E  |  SHAP dependence plots — frozen top-4 predictors\n"
        "CDF (upper row) / NoCDF (lower row) · "
        "SHAP > 0: pushes predicted value_ae upward",
        fontsize=9,
    )
    rng = np.random.default_rng(42)
    for row_idx, exp in enumerate(EXPS):
        df    = pd.read_parquet(IN_DIR / f"shap_{exp}_{TARGET}.parquet")
        color = CDF_COLOR if exp == "da_cdf" else NOCDF_COLOR
        label = "CDF" if exp == "da_cdf" else "NoCDF"
        for col_idx, feat in enumerate(top4):
            ax     = axes[row_idx, col_idx]
            x_vals = df[f"value__{feat}"].values
            s_vals = df[f"shap__{feat}"].values
            idx    = rng.choice(len(x_vals), size=min(2000, len(x_vals)), replace=False)
            ax.scatter(x_vals[idx], s_vals[idx], s=4, alpha=0.35,
                       color=color, rasterized=True)
            ax.axhline(0, color="k", linewidth=0.6, linestyle="--", alpha=0.5)
            ax.set_title(f"{label} | {feat}", fontsize=7)
            ax.set_xlabel(feat, fontsize=7)
            ax.set_ylabel("SHAP (value_ae)" if col_idx == 0 else "", fontsize=7)
            ax.tick_params(labelsize=6)
    fig.tight_layout()
    savefig(fig, "fig_value_e_dependence.png")


def fig_f_seasonal():
    grp_lbl = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    fig.suptitle(
        "VALUE-F  |  DJF vs JJA group attribution · value_ae · 2019 dev cohort",
        fontsize=10,
    )
    for ax, exp in zip(axes, EXPS):
        label = "CDF" if exp == "da_cdf" else "NoCDF"
        djf = pd.read_csv(IN_DIR / f"seasonal_djf_group_{exp}.csv").set_index("group").reindex(GROUP_ORDER)
        jja = pd.read_csv(IN_DIR / f"seasonal_jja_group_{exp}.csv").set_index("group").reindex(GROUP_ORDER)
        djf_v = (djf["normalized_group_importance"].fillna(0) * 100).values
        jja_v = (jja["normalized_group_importance"].fillna(0) * 100).values
        y = np.arange(len(GROUP_ORDER)); h = 0.38
        ax.barh(y + h/2, djf_v, h, color=DJF_COLOR, label="DJF", alpha=0.85)
        ax.barh(y - h/2, jja_v, h, color=JJA_COLOR, label="JJA", alpha=0.85)
        ax.set_yticks(y)
        ax.set_yticklabels(grp_lbl, fontsize=8)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("%", fontsize=9)
        ax.legend(fontsize=8)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_f_seasonal.png")


def fig_g_spatial():
    grp_lbl = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    fig.suptitle(
        "VALUE-G  |  Spatial-fold group stability · value_ae · median ± IQR across 5 folds",
        fontsize=10,
    )
    for ax, exp in zip(axes, EXPS):
        label = "CDF" if exp == "da_cdf" else "NoCDF"
        color = CDF_COLOR if exp == "da_cdf" else NOCDF_COLOR
        spat  = pd.read_csv(IN_DIR / f"spatial_fold_group_{exp}.csv")
        agg   = (spat.groupby("group")["normalized_group_importance"]
                     .agg(["median",
                           lambda x: x.quantile(0.25),
                           lambda x: x.quantile(0.75)])
                     .rename(columns={"median": "med",
                                      "<lambda_0>": "q25",
                                      "<lambda_1>": "q75"})
                     .reindex(GROUP_ORDER))
        y = np.arange(len(GROUP_ORDER))
        for i, (_, row) in enumerate(agg.iterrows()):
            ax.plot([row["q25"]*100, row["q75"]*100], [i, i],
                    color="#aaa", linewidth=4, solid_capstyle="round", alpha=0.6)
            ax.scatter(row["med"]*100, i, color=color, s=50, zorder=5)
        ax.set_yticks(y)
        ax.set_yticklabels(grp_lbl, fontsize=8)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Normalized group importance (%)", fontsize=9)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_value_g_spatial.png")


def main():
    print("Generating VALUE XAI development figures (matplotlib only)...", flush=True)
    fig_a_distribution()
    fig_b_group_importance()
    fig_c_top_predictors()
    fig_d_shap_distributions()
    fig_e_dependence()
    fig_f_seasonal()
    fig_g_spatial()
    print("All VALUE figures complete.", flush=True)


if __name__ == "__main__":
    main()
