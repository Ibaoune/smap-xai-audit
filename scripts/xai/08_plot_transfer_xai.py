#!/usr/bin/env python
"""
RF-04B-TRANSFER: Generate all development diagnostic figures (matplotlib only).

Figures:
  TRANSFER-A: Scientific-group importance matrix (targets × groups), CDF + NoCDF panels
  TRANSFER-B: Top predictor importance by target (CDF + NoCDF side-by-side)
  TRANSFER-C: Predictor-rank correlation across targets (heatmaps)
  TRANSFER-D: Representative SHAP distributions for top predictors per target
  TRANSFER-E: Dependence plots (frozen target-specific top-3)
  TRANSFER-F: DJF vs JJA group importance comparison
  TRANSFER-G: Spatial-fold group-importance stability

No seaborn. 2020 SEALED.
"""
import json
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

IN_DIR  = Path("data/processed/modeling/xai/outputs/transfer")
OUT_DIR = Path("figures/development/transfer")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["delta_rzsm", "delta_et", "delta_surface_runoff", "delta_baseflow"]
TARGET_LABELS = {
    "delta_rzsm":           "ΔRZSM",
    "delta_et":             "ΔET",
    "delta_surface_runoff": "ΔRunoff",
    "delta_baseflow":       "ΔBaseflow",
}
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
    "antecedent_soil_moisture_state":     "Antec. SM state",
    "meteorological_forcing":             "Meteo. forcing",
    "temporal_context":                   "Temporal context",
    "land_cover_or_vegetation":           "Land cover/veg.",
    "soil_properties":                    "Soil properties",
    "topography":                         "Topography",
    "assimilation_diagnostics_or_history":"Assim. diagnostics",
    "antecedent_land_surface_fluxes":     "Antec. LSM fluxes",
    "forcing_perturbation_controls":      "Forcing ctrl.",
}


def savefig(fig, name, dpi=150):
    p = OUT_DIR / name
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {p}")


def load_group_matrix(exp):
    label = exp.split("_")[1]
    return pd.read_csv(IN_DIR / f"group_matrix_{label}.csv", index_col="target")


# ── TRANSFER-A: Group importance matrix panels ─────────────────────────────────
def fig_a_group_matrix():
    fig, axes = plt.subplots(1, 3, figsize=(17, 6), sharey=True)
    fig.suptitle(
        "TRANSFER-A  |  Scientific-group attribution by target (matched support · 2019 dev)\n"
        "Left=CDF  Centre=NoCDF  Right=CDF−NoCDF difference",
        fontsize=10,
    )
    grps  = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    t_lbl = [TARGET_LABELS[t] for t in TARGETS]

    for ax_idx, (exp, label, cmap) in enumerate([
        ("da_cdf",   "CDF",        "Blues"),
        ("da_nocdf", "NoCDF",      "Reds"),
    ]):
        ax  = axes[ax_idx]
        mat = load_group_matrix(exp)
        mat = mat.reindex(TARGETS)[[g for g in GROUP_ORDER if g in mat.columns]]
        data = mat.values * 100   # percent
        im = ax.imshow(data, aspect="auto", cmap=cmap, vmin=0)
        ax.set_xticks(range(len(GROUP_ORDER)))
        ax.set_xticklabels(grps, rotation=40, ha="right", fontsize=7)
        ax.set_yticks(range(len(TARGETS)))
        ax.set_yticklabels(t_lbl, fontsize=9)
        ax.set_title(label, fontsize=10)
        for i in range(len(TARGETS)):
            for j in range(len(GROUP_ORDER)):
                v = data[i, j]
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6,
                        color="white" if v > 35 else "black")
        plt.colorbar(im, ax=ax, shrink=0.6, label="%")

    # Diff panel
    ax   = axes[2]
    mat_c = load_group_matrix("da_cdf").reindex(TARGETS)[[g for g in GROUP_ORDER if g in load_group_matrix("da_cdf").columns]]
    mat_n = load_group_matrix("da_nocdf").reindex(TARGETS)[[g for g in GROUP_ORDER if g in load_group_matrix("da_nocdf").columns]]
    diff  = (mat_c.values - mat_n.values) * 100
    vmax  = max(abs(diff).max(), 0.5)
    im2   = ax.imshow(diff, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(GROUP_ORDER)))
    ax.set_xticklabels(grps, rotation=40, ha="right", fontsize=7)
    ax.set_yticks(range(len(TARGETS)))
    ax.set_yticklabels(t_lbl, fontsize=9)
    ax.set_title("CDF − NoCDF", fontsize=10)
    for i in range(len(TARGETS)):
        for j in range(len(GROUP_ORDER)):
            ax.text(j, i, f"{diff[i,j]:+.1f}", ha="center", va="center", fontsize=6)
    plt.colorbar(im2, ax=ax, shrink=0.6, label="pp diff")

    fig.tight_layout()
    savefig(fig, "fig_transfer_a_group_matrix.png")


# ── TRANSFER-B: Top predictor importance by target ─────────────────────────────
def fig_b_top_predictors():
    ps = pd.read_csv(IN_DIR / "tidy_predictor_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "TRANSFER-B  |  Top-10 predictor mean|SHAP| by target (matched support · 2019 dev)",
        fontsize=10,
    )
    for ax, tgt in zip(axes.flat, TARGETS):
        cdf   = ps[(ps.experiment == "da_cdf")   & (ps.target == tgt)].sort_values("mean_abs_shap", ascending=False).head(10)
        nocdf = ps[(ps.experiment == "da_nocdf") & (ps.target == tgt)]
        mm    = pd.merge(cdf[["feature", "mean_abs_shap"]], nocdf[["feature", "mean_abs_shap"]], on="feature", suffixes=("_cdf", "_nocdf"))
        y = np.arange(len(mm))
        h = 0.38
        ax.barh(y + h/2, mm["mean_abs_shap_cdf"],   h, color=CDF_COLOR,   label="CDF",   alpha=0.85)
        ax.barh(y - h/2, mm["mean_abs_shap_nocdf"], h, color=NOCDF_COLOR, label="NoCDF", alpha=0.85)
        ax.set_yticks(y)
        ax.set_yticklabels(mm["feature"], fontsize=7)
        ax.set_title(TARGET_LABELS[tgt], fontsize=9)
        ax.set_xlabel("Mean |SHAP|", fontsize=8)
        ax.invert_yaxis()
        ax.legend(fontsize=7)
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_transfer_b_top_predictors.png")


# ── TRANSFER-C: Cross-target predictor-rank correlation heatmap ────────────────
def fig_c_cross_target():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        "TRANSFER-C  |  Predictor-rank Spearman ρ across targets (matched support · 2019 dev)",
        fontsize=10,
    )
    for ax, exp in zip(axes, ["da_cdf", "da_nocdf"]):
        label = exp.split("_")[1].upper()
        mat   = pd.read_csv(IN_DIR / f"cross_target_pred_corr_{label.lower()}.csv", index_col=0)
        mat   = mat.reindex(index=TARGETS, columns=TARGETS).astype(float)
        im    = ax.imshow(mat.values, vmin=-1, vmax=1, cmap="RdYlGn", aspect="auto")
        t_lbl = [TARGET_LABELS[t] for t in TARGETS]
        ax.set_xticks(range(4)); ax.set_xticklabels(t_lbl, rotation=30, ha="right", fontsize=8)
        ax.set_yticks(range(4)); ax.set_yticklabels(t_lbl, fontsize=8)
        ax.set_title(label, fontsize=10)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{mat.values[i,j]:.2f}", ha="center", va="center", fontsize=8)
        plt.colorbar(im, ax=ax, shrink=0.8, label="ρ")
    fig.tight_layout()
    savefig(fig, "fig_transfer_c_cross_target.png")


# ── TRANSFER-D: SHAP distributions for representative target (RZSM, CDF) ───────
def fig_d_beeswarm():
    """Histogram-violin for top-6 predictors for each target."""
    ps = pd.read_csv(IN_DIR / "tidy_predictor_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "TRANSFER-D  |  SHAP value distributions — top-6 predictors by target (CDF matched · 2019 dev)",
        fontsize=10,
    )
    for ax_main, tgt in zip(axes.flat, TARGETS):
        cdf_top6 = (ps[(ps.experiment == "da_cdf") & (ps.target == tgt)]
                    .sort_values("mean_abs_shap", ascending=False)
                    .head(6)["feature"].tolist())
        df = pd.read_parquet(IN_DIR / f"shap_da_cdf_{tgt}.parquet")

        # Create inset sub-axes manually via a mini sub-figure approach
        ax_main.axis("off")
        for i, feat in enumerate(cdf_top6):
            # Use a crude strip approach: text + bar
            vals = df[f"shap__{feat}"].values
            mas  = float(np.mean(np.abs(vals)))
            ax_main.barh(i, mas, color=CDF_COLOR, alpha=0.75)
            ax_main.text(mas * 1.02, i, feat, va="center", fontsize=7)
        ax_main.set_xlim(0, ax_main.get_xlim()[1] * 1.3 if ax_main.get_xlim()[1] > 0 else 1)
        ax_main.set_yticks([])
        ax_main.set_xlabel("Mean |SHAP|", fontsize=8)
        ax_main.set_title(f"{TARGET_LABELS[tgt]} — CDF top-6", fontsize=9)
        ax_main.axis("on")
        ax_main.invert_yaxis()

    fig.tight_layout()
    savefig(fig, "fig_transfer_d_distributions.png")


# ── TRANSFER-E: Dependence plots (frozen top-3 per target) ────────────────────
def fig_e_dependence():
    with open(IN_DIR / "dependence_features.json") as f:
        dep = json.load(f)["targets"]

    fig, axes = plt.subplots(len(TARGETS), 3, figsize=(13, 14))
    fig.suptitle(
        "TRANSFER-E  |  SHAP dependence plots — frozen top-3 per target (CDF matched · 2019 dev)",
        fontsize=10,
    )
    for row_idx, tgt in enumerate(TARGETS):
        df   = pd.read_parquet(IN_DIR / f"shap_da_cdf_{tgt}.parquet")
        top3 = dep[tgt]
        for col_idx, feat in enumerate(top3):
            ax = axes[row_idx, col_idx]
            x_vals = df[f"value__{feat}"].values
            s_vals = df[f"shap__{feat}"].values
            rng    = np.random.default_rng(42)
            idx    = rng.choice(len(x_vals), size=min(2000, len(x_vals)), replace=False)
            ax.scatter(x_vals[idx], s_vals[idx], s=4, alpha=0.4, color=CDF_COLOR, rasterized=True)
            ax.axhline(0, color="k", linewidth=0.6, linestyle="--", alpha=0.5)
            ax.set_title(f"{TARGET_LABELS[tgt]} | {feat}", fontsize=7)
            ax.set_xlabel(feat if row_idx == len(TARGETS)-1 else "", fontsize=7)
            ax.set_ylabel(f"SHAP" if col_idx == 0 else "", fontsize=7)
            ax.tick_params(labelsize=6)
    fig.tight_layout()
    savefig(fig, "fig_transfer_e_dependence.png")


# ── TRANSFER-F: DJF vs JJA group importance ────────────────────────────────────
def fig_f_seasonal():
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(
        "TRANSFER-F  |  DJF vs JJA group attribution by target (CDF matched · 2019 dev)",
        fontsize=10,
    )
    grp_lbl = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    for ax, tgt in zip(axes.flat, TARGETS):
        tag = f"da_cdf_{tgt}"
        djf = pd.read_csv(IN_DIR / f"seasonal_djf_group_{tag}.csv").set_index("group").reindex(GROUP_ORDER)
        jja = pd.read_csv(IN_DIR / f"seasonal_jja_group_{tag}.csv").set_index("group").reindex(GROUP_ORDER)
        djf_v = (djf["normalized_group_importance"].fillna(0) * 100).values
        jja_v = (jja["normalized_group_importance"].fillna(0) * 100).values
        y = np.arange(len(GROUP_ORDER))
        h = 0.38
        ax.barh(y + h/2, djf_v, h, color=DJF_COLOR, label="DJF", alpha=0.85)
        ax.barh(y - h/2, jja_v, h, color=JJA_COLOR, label="JJA", alpha=0.85)
        ax.set_yticks(y)
        ax.set_yticklabels(grp_lbl, fontsize=7)
        ax.set_title(TARGET_LABELS[tgt], fontsize=9)
        ax.set_xlabel("%", fontsize=8)
        ax.legend(fontsize=7)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_transfer_f_seasonal.png")


# ── TRANSFER-G: Spatial-fold stability ─────────────────────────────────────────
def fig_g_spatial():
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(
        "TRANSFER-G  |  Spatial-fold group importance stability (CDF matched · median ± IQR)",
        fontsize=10,
    )
    grp_lbl = [GROUP_SHORT.get(g, g) for g in GROUP_ORDER]
    for ax, tgt in zip(axes.flat, TARGETS):
        tag  = f"da_cdf_{tgt}"
        spat = pd.read_csv(IN_DIR / f"spatial_fold_group_{tag}.csv")
        agg  = (spat.groupby("group")["normalized_group_importance"]
                    .agg(["median",
                          lambda x: x.quantile(0.25),
                          lambda x: x.quantile(0.75)])
                    .rename(columns={"median":"med","<lambda_0>":"q25","<lambda_1>":"q75"})
                    .reindex(GROUP_ORDER))
        y = np.arange(len(GROUP_ORDER))
        for i, (_, row) in enumerate(agg.iterrows()):
            ax.plot([row["q25"]*100, row["q75"]*100], [i, i],
                    color="#777", linewidth=4, alpha=0.5, solid_capstyle="round")
            ax.scatter(row["med"]*100, i, color=CDF_COLOR, s=50, zorder=5)
        ax.set_yticks(y)
        ax.set_yticklabels(grp_lbl, fontsize=7)
        ax.set_title(TARGET_LABELS[tgt], fontsize=9)
        ax.set_xlabel("Normalized group importance (%)", fontsize=8)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    savefig(fig, "fig_transfer_g_spatial.png")


def main():
    print("Generating TRANSFER XAI development figures (matplotlib only)...", flush=True)
    fig_a_group_matrix()
    fig_b_top_predictors()
    fig_c_cross_target()
    fig_d_beeswarm()
    fig_e_dependence()
    fig_f_seasonal()
    fig_g_spatial()
    print("All TRANSFER figures complete.", flush=True)


if __name__ == "__main__":
    main()
