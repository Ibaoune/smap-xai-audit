#!/usr/bin/env python3
"""
Discussion figure for J. Ahmad: XAI framing (SOURCE -> TRANSFER -> VALUE) and
first CDF vs NoCDF diagnostic (grouped SHAP importance, SOURCE model).

Not a final paper figure. Values in panel (b) are read from the frozen
final-2020 XAI summaries and cross-checked against the raw SHAP cohorts.

Usage:
    python scripts/figures/make_xai_figure_for_ahmad.py
Outputs (figures/discussion/):
    xai_figure_for_Ahmad.{png,pdf,svg}, xai_figure_for_Ahmad_values.csv
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
import yaml
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
XAI = ROOT / "data/processed/modeling/xai/final_2020"
TIDY_CSV = XAI / "summaries/tidy_group_summary.csv"
STATS_JSON = XAI / "summaries/source_matched_comparison_stats.json"
SHAP_DIR = XAI / "shap"
GROUPS_YAML = ROOT / "configs/xai/feature_groups.yaml"
OUT_DIR = ROOT / "figures/discussion"
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM = "xai_figure_for_Ahmad"

MODEL_KEYS = {
    "CDF": "SOURCE_da_cdf_daily_absolute_increment_matched_support",
    "NoCDF": "SOURCE_da_nocdf_daily_absolute_increment_matched_support",
}

# Display order (top -> bottom) and labels; registry key -> label
FAMILIES = [
    ("antecedent_soil_moisture_state", "Antecedent soil moisture"),
    ("meteorological_forcing", "Meteorology"),
    ("antecedent_land_surface_fluxes", "Antecedent fluxes"),
    ("assimilation_diagnostics_or_history", "Assimilation history"),
    ("soil_properties", "Soil properties"),
    ("land_cover_or_vegetation", "Land cover / vegetation"),
    ("topography", "Topography"),
    ("temporal_context", "Temporal context"),
]

# --------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------
FONT = "Nimbus Sans"  # metric clone of Helvetica (Arial/Helvetica not installed)
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONT, "Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "custom",
    "mathtext.rm": FONT,
    "mathtext.it": f"{FONT}:italic",
    "mathtext.bf": f"{FONT}:bold",
    "font.size": 9,
    "axes.linewidth": 0.7,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})

C_CDF = "#2F5D8C"      # muted manuscript blue
C_NOCDF = "#D9893B"    # muted manuscript orange
C_TXT = "#1A1A1A"
C_GREY = "#666666"
C_LIGHT = "#A8A8A8"
C_HEAD = "#E7EDF3"
C_EDGE = "#5B6C7E"


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def load_grouped_importance():
    tidy = pd.read_csv(TIDY_CSV)
    out = {}
    for exp, key in MODEL_KEYS.items():
        sub = tidy[tidy["model_key"] == key].set_index("group")
        if sub.empty:
            raise RuntimeError(f"No rows for {key} in {TIDY_CSV}")
        out[exp] = sub["normalized_group_importance_pct"]
    return pd.DataFrame(out)


def recompute_from_shap():
    """Independent check: sum mean|SHAP| per group from raw SHAP cohorts."""
    groups = yaml.safe_load(GROUPS_YAML.read_text())
    f2g = {f: g for g, feats in groups.items() for f in feats}
    res = {}
    for exp, key in MODEL_KEYS.items():
        p = SHAP_DIR / f"shap_{key}_cohort.parquet"
        if not p.exists():
            return None
        df = pd.read_parquet(p)
        cols = [c for c in df.columns if c.startswith("shap__")]
        mabs = df[cols].abs().mean()
        mabs.index = [c[len("shap__"):] for c in mabs.index]
        g = mabs.groupby(mabs.index.map(lambda f: f2g.get(f, "UNMAPPED"))).sum()
        res[exp] = 100 * g / g.sum()
        res[f"n_{exp}"] = len(df)
        res[f"nfeat_{exp}"] = len(cols)
    return res


imp = load_grouped_importance()
check = recompute_from_shap()
n_rows = 10000
if check is not None:
    n_rows = check["n_CDF"]
    for exp in MODEL_KEYS:
        diff = (imp[exp] - check[exp].reindex(imp.index).fillna(0)).abs().max()
        print(f"[check] {exp}: max |CSV - recomputed| = {diff:.4f} pp "
              f"(n={check[f'n_{exp}']}, features={check[f'nfeat_{exp}']})")
group_rho = None
if STATS_JSON.exists():
    import json
    group_rho = json.loads(STATS_JSON.read_text()).get("group_rho")

keys = [k for k, _ in FAMILIES]
labels = [l for _, l in FAMILIES]
vals = imp.reindex(keys).fillna(0.0)
in_source = (vals[["CDF", "NoCDF"]].sum(axis=1) > 0).values

table = vals.copy()
table.insert(0, "family", labels)
table["CDF_minus_NoCDF_pp"] = table["CDF"] - table["NoCDF"]
table["in_SOURCE_predictor_set"] = in_source
table.to_csv(OUT_DIR / f"{STEM}_values.csv", float_format="%.2f")
print(table.round(2).to_string())

# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
FW, FH = 10.0, 8.6
fig = plt.figure(figsize=(FW, FH))


def fx(x):  # inches -> figure fraction
    return x / FW


def fy(y):
    return y / FH


fig.text(fx(0.15), fy(8.34),
         "XAI framing and first CDF\u2013NoCDF diagnostic for SMAP assimilation",
         fontsize=13, fontweight="bold", color=C_TXT, va="center")

# ============================ PANEL (a) ===================================
A_H = 3.60
ax = fig.add_axes([0, fy(4.55), 1, fy(A_H)])
ax.set_xlim(0, FW)
ax.set_ylim(0, A_H)
ax.axis("off")

ax.text(0.15, 3.42, "(a)", fontsize=11.5, fontweight="bold", va="center")
ax.text(0.52, 3.42, "XAI diagnostic framework for SMAP assimilation impacts",
        fontsize=11.5, fontweight="bold", va="center", color=C_TXT)

BY0, BY1 = 1.30, 3.10           # main boxes vertical extent
HEAD = 0.34
YC = (BY0 + BY1) / 2
BW = 2.45
BX = [1.70, 4.55, 7.40]

# SMAP assimilation (entry node)
sx0, sx1 = 0.15, 1.30
ax.add_patch(FancyBboxPatch((sx0, YC - 0.55), sx1 - sx0, 1.10,
                            boxstyle="round,pad=0,rounding_size=0.08",
                            fc="#F3F3F3", ec="#9A9A9A", lw=0.8))
ax.text((sx0 + sx1) / 2, YC + 0.17, "SMAP\nassimilation", ha="center",
        va="center", fontsize=9.5, fontweight="bold", linespacing=1.15)
ax.text((sx0 + sx1) / 2, YC - 0.30, "Noah-MP EnKF\nDA vs open loop", ha="center",
        va="center", fontsize=7.3, color=C_GREY, linespacing=1.2)


def arrow(x0, y0, x1, y1, color="#4A4A4A", lw=1.4, ms=11):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=ms, color=color, lw=lw,
                                 shrinkA=0, shrinkB=0))


arrow(sx1 + 0.05, YC, BX[0] - 0.05, YC)
for i in range(2):
    arrow(BX[i] + BW + 0.05, YC, BX[i + 1] - 0.05, YC)

BLOCKS = [
    dict(name="SOURCE",
         q="Which conditions control the\nSMAP analysis update?",
         t=[(r"Target:  $\delta x$  or  $|\delta x|$", 8.8, C_TXT)],
         g="\u03b4x: surface soil-moisture analysis increment"),
    dict(name="TRANSFER",
         q="When and where does the\nsurface update propagate?",
         t=[(r"Targets:  $\Delta$RZSM  \u00b7  $\Delta$ET  \u00b7  $\Delta$Q$_\mathrm{s}$  \u00b7  $\Delta$Q$_\mathrm{sb}$"
             .replace("\\u00b7", "\u00b7"), 8.8, C_TXT)],
         g="\u0394 = DA \u2212 open loop (OPL)"),
    dict(name="VALUE",
         q="When does the DA response improve\nagreement with an independent\nreference?",
         t=[("Target:  value_ae =", 8.6, C_TXT),
            (r"$|\mathrm{ET}_\mathrm{OPL}-\mathrm{ET}_\mathrm{GLEAM}|-|\mathrm{ET}_\mathrm{DA}-\mathrm{ET}_\mathrm{GLEAM}|$",
             8.4, C_TXT)],
         g="> 0: DA closer to GLEAM ET"),
]

for x0, b in zip(BX, BLOCKS):
    xc = x0 + BW / 2
    ax.add_patch(FancyBboxPatch((x0, BY0), BW, BY1 - BY0,
                                boxstyle="round,pad=0,rounding_size=0.07",
                                fc="white", ec=C_EDGE, lw=1.0, zorder=2))
    # header strip (clip to box via a plain rectangle under the rounded top)
    ax.add_patch(FancyBboxPatch((x0, BY1 - HEAD), BW, HEAD,
                                boxstyle="round,pad=0,rounding_size=0.07",
                                fc=C_HEAD, ec="none", zorder=2.5))
    ax.add_patch(Rectangle((x0 + 0.01, BY1 - HEAD), BW - 0.02, HEAD / 2,
                           fc=C_HEAD, ec="none", zorder=2.6))
    ax.plot([x0, x0 + BW], [BY1 - HEAD] * 2, color=C_EDGE, lw=0.6, zorder=3)
    ax.add_patch(FancyBboxPatch((x0, BY0), BW, BY1 - BY0,
                                boxstyle="round,pad=0,rounding_size=0.07",
                                fc="none", ec=C_EDGE, lw=1.0, zorder=4))
    ax.text(xc, BY1 - HEAD / 2, b["name"], ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#24384D", zorder=5)
    ax.text(xc, BY1 - HEAD - 0.10, b["q"], ha="center", va="top",
            fontsize=8.8, style="italic", color=C_TXT, linespacing=1.25, zorder=5)
    ax.plot([x0 + 0.25, x0 + BW - 0.25], [2.02] * 2, color="#C9C9C9", lw=0.6, zorder=5)
    y = 1.90
    for txt, fs, col in b["t"]:
        ax.text(xc, y, txt, ha="center", va="top", fontsize=fs, color=col, zorder=5)
        y -= 0.21
    ax.text(xc, BY0 + 0.07, b["g"], ha="center", va="bottom", fontsize=7.2,
            color=C_GREY, zorder=5)

# Predictor-family band
PY0, PY1 = 0.30, 1.02
ax.add_patch(FancyBboxPatch((0.15, PY0), 9.70, PY1 - PY0,
                            boxstyle="round,pad=0,rounding_size=0.06",
                            fc="#FAFAFA", ec="#BDBDBD", lw=0.8))
ax.text(0.78, (PY0 + PY1) / 2, "Predictor\nfamilies", ha="center", va="center",
        fontsize=9.2, fontweight="bold", color="#24384D", linespacing=1.15)
ax.plot([1.45, 1.45], [PY0 + 0.10, PY1 - 0.10], color="#CFCFCF", lw=0.8)
cols_x = [1.70, 3.75, 5.85, 7.85]
rows_y = [0.84, 0.48]
for i, lab in enumerate(labels):
    cx, cy = cols_x[i % 4], rows_y[i // 4]
    ax.add_patch(Rectangle((cx, cy - 0.045), 0.09, 0.09, fc="#7D8C9B", ec="none"))
    ax.text(cx + 0.17, cy, lab, va="center", fontsize=8.8, color=C_TXT)

for x0 in BX:  # families feed every block
    arrow(x0 + BW / 2, PY1 + 0.02, x0 + BW / 2, BY0 - 0.03,
          color="#9AA5B1", lw=0.9, ms=8)

ax.text(0.15, 0.10, "Random forest + TreeSHAP used as a diagnostic of the DA system, "
        "not as a surrogate for Noah-MP/EnKF.", fontsize=7.8, style="italic",
        color=C_GREY, va="center")
ax.text(9.85, 0.10, "CDF and NoCDF are modeled separately.", fontsize=7.8,
        style="italic", color=C_GREY, va="center", ha="right")

# panel separator
fig.add_artist(Line2D([fx(0.15), fx(9.85)], [fy(4.50)] * 2, color="#D9D9D9", lw=0.8))

# ============================ PANEL (b) ===================================
fig.text(fx(0.15), fy(4.25), "(b)", fontsize=11.5, fontweight="bold", va="center")
fig.text(fx(0.52), fy(4.25),
         "Grouped predictor importance for SOURCE under CDF and NoCDF",
         fontsize=11.5, fontweight="bold", va="center", color=C_TXT)
fig.text(fx(0.52), fy(4.03),
         f"Target |\u03b4x|  \u00b7  2020 hold-out  \u00b7  matched support "
         f"(identical pixel-days, n = {n_rows:,})",
         fontsize=8.2, color=C_GREY, va="center")

AXL, AXB, AXW, AXH = 2.55, 0.92, 3.85, 2.85
axb = fig.add_axes([fx(AXL), fy(AXB), fx(AXW), fy(AXH)])
n = len(keys)
yy = np.arange(n)[::-1].astype(float)
h = 0.36
axb.barh(yy + h / 2, vals["CDF"], height=h, color=C_CDF, label="CDF", zorder=3)
axb.barh(yy - h / 2, vals["NoCDF"], height=h, color=C_NOCDF, label="NoCDF", zorder=3)
for y, v1, v2, ok in zip(yy, vals["CDF"], vals["NoCDF"], in_source):
    if ok:
        axb.text(v1 + 0.8, y + h / 2, f"{v1:.1f}", va="center", fontsize=7.6, color=C_CDF)
        axb.text(v2 + 0.8, y - h / 2, f"{v2:.1f}", va="center", fontsize=7.6, color="#A8601F")
    else:
        axb.text(1.0, y, "not in SOURCE predictor set\u2020", va="center",
                 fontsize=7.6, style="italic", color=C_LIGHT)
axb.set_yticks(yy)
axb.set_yticklabels(labels, fontsize=8.8)
for tl, ok in zip(axb.get_yticklabels(), in_source):
    if not ok:
        tl.set_color(C_LIGHT)
axb.set_xlim(0, 68)
axb.set_ylim(-0.6, n - 0.4)
axb.set_xticks([0, 20, 40, 60])
axb.tick_params(axis="x", labelsize=8.2, length=3, width=0.6, color="#555555")
axb.tick_params(axis="y", length=0)
axb.set_xlabel("Share of grouped mean |SHAP| (%)", fontsize=8.6, color=C_TXT)
axb.grid(axis="x", color="#E3E3E3", lw=0.6, zorder=0)
for s in ("top", "right", "left"):
    axb.spines[s].set_visible(False)
axb.spines["bottom"].set_color("#555555")
axb.legend(loc="lower right", frameon=False, fontsize=8.6, handlelength=1.2,
           handleheight=0.9, borderaxespad=0.2)

# CDF - NoCDF column (percentage points)
DX = AXL + AXW + 0.35
fig.text(fx(DX), fy(AXB + AXH + 0.12), "CDF \u2212 NoCDF", ha="center",
         fontsize=8.0, fontweight="bold", color=C_TXT)
fig.text(fx(DX), fy(AXB + AXH - 0.02), "(pp)", ha="center", fontsize=7.4, color=C_GREY)
y2f = lambda y: AXB + AXH * (y - (-0.6)) / ((n - 0.4) - (-0.6))
for y, d, ok in zip(yy, table["CDF_minus_NoCDF_pp"], in_source):
    if abs(d) < 0.05:
        d = 0.0
    s = ("0.0" if d == 0 else f"{d:+.1f}".replace("-", "\u2212")) if ok else "\u2014"
    bold = ok and abs(d) >= 10
    fig.text(fx(DX), fy(y2f(y)), s, ha="center", va="center", fontsize=8.2,
             color=(C_TXT if ok else C_LIGHT), fontweight=("bold" if bold else "normal"))

# Key reading (right)
KX = 7.45
fig.text(fx(KX), fy(3.72), "Key reading", fontsize=9.2, fontweight="bold",
         color="#24384D", va="top")
asm = vals.loc["antecedent_soil_moisture_state"]
bullets = [
    f"CDF: attribution of |\u03b4x| dominated by\nantecedent soil moisture ({asm['CDF']:.0f}%).",
    f"NoCDF: antecedent soil moisture drops\nto {asm['NoCDF']:.0f}%; weight shifts toward\n"
    "meteorology, soil, land cover and\ntopography.",
]
if group_rho is not None:
    bullets.append(f"Group rankings remain broadly\nconcordant (Spearman \u03c1 = {group_rho:.2f}).")
METRICS = ROOT / "figures/manuscript/rf/rf_eval/Figure4_2020_holdout_metrics.csv"
r2 = {}
if METRICS.exists():
    m = pd.read_csv(METRICS)
    m = m[m["target"] == "SOURCE"].set_index("experiment")["r2"]
    r2 = {k: m.get(k) for k in ("CDF", "NoCDF")}
if r2.get("CDF") is not None and r2.get("NoCDF") is not None:
    bullets.append("Associations, not causal effects.\nNoCDF emulator is less skilful\n"
                   f"(2020 R\u00b2 = {r2['NoCDF']:.2f} vs {r2['CDF']:.2f} for CDF).")
else:
    bullets.append("Associations within the RF\nemulator, not causal effects.")
y = 3.42
for b in bullets:
    fig.text(fx(KX), fy(y), "\u2022", fontsize=8.6, va="top", color=C_TXT)
    t = fig.text(fx(KX + 0.14), fy(y), b, fontsize=8.3, va="top", color=C_TXT,
                 linespacing=1.25)
    y -= 0.152 * (b.count("\n") + 1) + 0.14

# footnotes
fig.text(fx(0.15), fy(0.34),
         "Grouped importance shown as normalized contributions within the SOURCE model "
         "(sum of group mean |SHAP| = 100% per configuration).",
         fontsize=7.6, style="italic", color=C_GREY, va="center")
fig.text(fx(0.15), fy(0.15),
         "\u2020 Not part of the SOURCE context-only predictor set (35 predictors); "
         "these families are used in the TRANSFER and VALUE models.",
         fontsize=7.6, style="italic", color=C_GREY, va="center")

# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
png = OUT_DIR / f"{STEM}.png"
pdf = OUT_DIR / f"{STEM}.pdf"
svg = OUT_DIR / f"{STEM}.svg"
fig.savefig(png, dpi=400)
fig.savefig(pdf)
fig.savefig(svg)
# Make SVG text fall back to Arial/Helvetica on the reader's machine
s = svg.read_text()
s = re.sub(r"font-family:\s*'?Nimbus Sans'?",
           "font-family:Arial, Helvetica, 'Nimbus Sans', sans-serif", s)
s = re.sub(r'font-family="Nimbus Sans"',
           'font-family="Arial, Helvetica, Nimbus Sans, sans-serif"', s)
svg.write_text(s)
print("Saved:", png, pdf, svg, sep="\n  ")
