#!/usr/bin/env python
"""
RF-04B-SOURCE: Generate all development diagnostic figures.

Uses matplotlib + pandas only (no seaborn dependency).

Frozen dependence predictors:
    ssm_lag1, precip_lag1, rzsm_lag1, land_cover_fraction_16

2020 is SEALED. All figures use the 10k balanced 2019 SHAP compute subset.
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

IN_DIR  = Path("data/processed/modeling/xai/outputs/source")
OUT_DIR = Path("figures/development/source")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette (matplotlib only) ──────────────────────────────────────────
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
GROUP_LABELS = {
    "antecedent_soil_moisture_state":     "Antecedent SM state",
    "meteorological_forcing":             "Meteorological forcing",
    "temporal_context":                   "Temporal context",
    "land_cover_or_vegetation":           "Land cover / vegetation",
    "soil_properties":                    "Soil properties",
    "topography":                         "Topography",
    "assimilation_diagnostics_or_history":"Assimilation diagnostics",
    "antecedent_land_surface_fluxes":     "Antecedent LSM fluxes",
    "forcing_perturbation_controls":      "Forcing perturbation ctrl",
}


def load_group_comp():
    return pd.read_csv(IN_DIR / "matched_group_comparison.csv")


def load_predictor_summary():
    return pd.read_csv(IN_DIR / "tidy_predictor_summary.csv")


def savefig(fig, name, dpi=150):
    p = OUT_DIR / name
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {p}")


# ── FIG SOURCE-A: Matched group importance CDF vs NoCDF ───────────────────────
def fig_a_group_importance():
    gc = load_group_comp()
    gc = gc.set_index("group").reindex(GROUP_ORDER).reset_index()

    cdf_vals   = (gc["normalized_group_importance_cdf"] * 100).fillna(0)
    nocdf_vals = (gc["normalized_group_importance_nocdf"] * 100).fillna(0)
    labels     = [GROUP_LABELS.get(g, g) for g in gc["group"]]
    y          = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9, 5))
    h = 0.35
    ax.barh(y + h/2, cdf_vals,   h, color=CDF_COLOR,   label="CDF",   alpha=0.85)
    ax.barh(y - h/2, nocdf_vals, h, color=NOCDF_COLOR, label="NoCDF", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Normalized group importance (%)", fontsize=10)
    ax.set_title(
        "FIG SOURCE-A  |  Matched-support group attribution: CDF vs NoCDF\n"
        "(Identical pixel-days · context_only_feature_set · 2019 development)",
        fontsize=10,
    )
    ax.legend(fontsize=9)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_source_a_group_importance.png")


# ── FIG SOURCE-B: Top predictor mean|SHAP| comparison ────────────────────────
def fig_b_top_predictors():
    ps = load_predictor_summary()
    cdf   = ps[(ps.experiment == "da_cdf")   & (ps.support_mode == "matched")].copy()
    nocdf = ps[(ps.experiment == "da_nocdf") & (ps.support_mode == "matched")].copy()

    mm = pd.merge(cdf, nocdf, on="feature", suffixes=("_cdf", "_nocdf"))
    mm["global_imp"] = (mm["mean_abs_shap_cdf"] + mm["mean_abs_shap_nocdf"]) / 2
    top = mm.sort_values("global_imp", ascending=False).head(15)
    labels = list(top["feature"])
    y = np.arange(len(labels))
    h = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(y + h/2, top["mean_abs_shap_cdf"],   h, color=CDF_COLOR,   label="CDF",   alpha=0.85)
    ax.barh(y - h/2, top["mean_abs_shap_nocdf"], h, color=NOCDF_COLOR, label="NoCDF", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Mean |SHAP| value", fontsize=10)
    ax.set_title(
        "FIG SOURCE-B  |  Top-15 predictor mean |SHAP|: matched CDF vs NoCDF\n"
        "(context_only_feature_set · 35 predictors · 2019 development)",
        fontsize=10,
    )
    ax.legend(fontsize=9)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_source_b_top_predictors.png")


# ── FIG SOURCE-C: SHAP distribution (violin proxy) for top predictors ─────────
def fig_c_beeswarm():
    """
    Approximated SHAP distribution figure.
    For each of the top-8 predictors by matched CDF mean|SHAP|, plot a
    strip-violin (histogram rotated) showing the distribution of SHAP values
    for CDF and NoCDF side by side.
    Matplotlib-only implementation.
    """
    ps   = load_predictor_summary()
    cdf_s = ps[(ps.experiment == "da_cdf") & (ps.support_mode == "matched")]
    top8  = cdf_s.sort_values("mean_abs_shap", ascending=False).head(8)["feature"].tolist()

    cdf_df   = pd.read_parquet(IN_DIR / "shap_da_cdf_matched.parquet")
    nocdf_df = pd.read_parquet(IN_DIR / "shap_da_nocdf_matched.parquet")

    fig, axes = plt.subplots(2, 4, figsize=(14, 7), sharey=False)
    fig.suptitle(
        "FIG SOURCE-C  |  SHAP value distributions for top-8 predictors (matched support)\n"
        "(context_only_feature_set · 2019 development · CDF=blue / NoCDF=red)",
        fontsize=10,
    )
    for i, (feat, ax) in enumerate(zip(top8, axes.flat)):
        c_vals  = cdf_df[f"shap__{feat}"].values
        nc_vals = nocdf_df[f"shap__{feat}"].values
        nbins   = 30
        shared_range = (min(c_vals.min(), nc_vals.min()),
                        max(c_vals.max(), nc_vals.max()))
        bins = np.linspace(*shared_range, nbins + 1)

        c_counts, _  = np.histogram(c_vals,  bins=bins)
        nc_counts, _ = np.histogram(nc_vals, bins=bins)
        bin_centers  = (bins[:-1] + bins[1:]) / 2
        width        = (bins[1] - bins[0]) * 0.42

        ax.barh(bin_centers, -c_counts  / c_counts.max(),  width, color=CDF_COLOR,   alpha=0.7, label="CDF")
        ax.barh(bin_centers,  nc_counts / nc_counts.max(), width, color=NOCDF_COLOR, alpha=0.7, label="NoCDF")
        ax.axhline(0, color="k", linewidth=0.6, linestyle="--", alpha=0.5)
        ax.set_title(feat, fontsize=8)
        ax.set_xlabel("← CDF     NoCDF →" if i == 0 else "", fontsize=7)
        ax.set_ylabel("SHAP value" if i % 4 == 0 else "", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_xticks([])

    fig.tight_layout()
    savefig(fig, "fig_source_c_beeswarm.png")


# ── FIG SOURCE-D: Dependence plots for frozen top-4 ──────────────────────────
def fig_d_dependence():
    top4 = ["ssm_lag1", "precip_lag1", "rzsm_lag1", "land_cover_fraction_16"]

    cdf_df   = pd.read_parquet(IN_DIR / "shap_da_cdf_matched.parquet")
    nocdf_df = pd.read_parquet(IN_DIR / "shap_da_nocdf_matched.parquet")

    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    fig.suptitle(
        "FIG SOURCE-D  |  SHAP dependence plots — frozen top-4 predictors (matched support)\n"
        "(context_only_feature_set · 2019 development · row 1=CDF, row 2=NoCDF)",
        fontsize=10,
    )

    for col, feat in enumerate(top4):
        for row, (df, label, color) in enumerate([
            (cdf_df,   "CDF",   CDF_COLOR),
            (nocdf_df, "NoCDF", NOCDF_COLOR),
        ]):
            ax = axes[row, col]
            x_vals = df[f"value__{feat}"].values
            s_vals = df[f"shap__{feat}"].values
            # Sample 3000 points for visibility
            rng = np.random.default_rng(42)
            idx = rng.choice(len(x_vals), size=min(3000, len(x_vals)), replace=False)
            ax.scatter(x_vals[idx], s_vals[idx], s=4, alpha=0.4, color=color, rasterized=True)
            ax.axhline(0, color="k", linewidth=0.6, linestyle="--", alpha=0.5)
            if row == 0:
                ax.set_title(feat, fontsize=9)
            ax.set_xlabel(feat if row == 1 else "", fontsize=8)
            ax.set_ylabel(f"SHAP ({label})" if col == 0 else "", fontsize=8)
            ax.tick_params(labelsize=7)

    fig.tight_layout()
    savefig(fig, "fig_source_d_dependence.png")


# ── FIG SOURCE-E: DJF vs JJA group importance ────────────────────────────────
def fig_e_seasonal():
    djf = pd.read_csv(IN_DIR / "seasonal_djf_group_da_cdf.csv")
    jja = pd.read_csv(IN_DIR / "seasonal_jja_group_da_cdf.csv")

    djf = djf.set_index("group").reindex(GROUP_ORDER).reset_index()
    jja = jja.set_index("group").reindex(GROUP_ORDER).reset_index()

    djf_vals = (djf["normalized_group_importance"] * 100).fillna(0)
    jja_vals = (jja["normalized_group_importance"] * 100).fillna(0)
    labels   = [GROUP_LABELS.get(g, g) for g in djf["group"]]
    y = np.arange(len(labels))
    h = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(y + h/2, djf_vals, h, color=DJF_COLOR, label="DJF", alpha=0.85)
    ax.barh(y - h/2, jja_vals, h, color=JJA_COLOR, label="JJA", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Normalized group importance (%)", fontsize=10)
    ax.set_title(
        "FIG SOURCE-E  |  DJF vs JJA group attribution (CDF matched · 2019 development)",
        fontsize=10,
    )
    ax.legend(fontsize=9)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_source_e_seasonal.png")


# ── FIG SOURCE-F: Spatial-fold group-importance stability ─────────────────────
def fig_f_spatial():
    spat = pd.read_csv(IN_DIR / "spatial_fold_group_da_cdf.csv")

    # Median and IQR per group across folds
    agg = (spat.groupby("group")["normalized_group_importance"]
               .agg(["median", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
               .rename(columns={"median": "med", "<lambda_0>": "q25", "<lambda_1>": "q75"})
               .reindex(GROUP_ORDER))
    labels = [GROUP_LABELS.get(g, g) for g in agg.index]
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (idx, row) in enumerate(agg.iterrows()):
        ax.plot([row["q25"]*100, row["q75"]*100], [i, i],
                color="#555", linewidth=4, alpha=0.4, solid_capstyle="round")
        ax.scatter(row["med"]*100, i, color=CDF_COLOR, s=60, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Normalized group importance (%) — median ± IQR across 5 spatial folds", fontsize=9)
    ax.set_title(
        "FIG SOURCE-F  |  Spatial-fold group importance stability (CDF matched · 2019 development)",
        fontsize=10,
    )
    ax.grid(axis="x", alpha=0.3)
    ax.invert_yaxis()
    fig.tight_layout()
    savefig(fig, "fig_source_f_spatial.png")


def main():
    print("Generating SOURCE XAI development figures (matplotlib only)...")
    fig_a_group_importance()
    fig_b_top_predictors()
    fig_c_beeswarm()
    fig_d_dependence()
    fig_e_seasonal()
    fig_f_spatial()
    print("All figures complete.")


if __name__ == "__main__":
    main()
