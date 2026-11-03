#!/usr/bin/env python3
"""
Revised discussion figure for Jawairia Ahmad (XAI framework + preliminary SOURCE evidence).

Revision of make_xai_figure_for_ahmad.py (original script and outputs are left untouched):
  - diagnostic / associative wording in panel (a); stage-specific predictor families;
    irrigation-OFF baseline + open question highlighted;
  - panel (b) restricted to the six families of the SOURCE context-only predictor set;
  - bar labels rounded half-up to 1 decimal; CDF - NoCDF computed from the displayed values
    so that bars, labels and differences are arithmetically consistent;
  - Spearman rho removed (0.93 was obtained with 9 groups incl. 3 structurally-zero ties;
    on the 6 SOURCE families rho = 0.77, n = 6, p = 0.07 -> not informative);
  - sober academic style.

Usage:
    python3 scripts/figures/make_xai_figure_for_ahmad_revised.py
Outputs (figures/discussion/):
    xai_figure_for_Ahmad_revised.{png,pdf,svg}
    xai_figure_for_Ahmad_revised_values.csv
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json
import re
import textwrap

import numpy as np
import pandas as pd
import yaml
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from scipy.stats import spearmanr

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
XAI = ROOT / "data/processed/modeling/xai/final_2020"
TIDY_CSV = XAI / "summaries/tidy_group_summary.csv"
STATS_JSON = XAI / "summaries/source_matched_comparison_stats.json"
SHAP_DIR = XAI / "shap"
GROUPS_YAML = ROOT / "configs/xai/feature_groups.yaml"
METRICS = ROOT / "figures/manuscript/rf/rf_eval/Figure4_2020_holdout_metrics.csv"
OUT_DIR = ROOT / "figures/discussion"
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM = "xai_figure_for_Ahmad_revised"

MODEL_KEYS = {
    "CDF": "SOURCE_da_cdf_daily_absolute_increment_matched_support",
    "NoCDF": "SOURCE_da_nocdf_daily_absolute_increment_matched_support",
}

# Families of the SOURCE context-only predictor set (display order, top -> bottom)
SOURCE_FAMILIES = [
    ("antecedent_soil_moisture_state", "Antecedent soil moisture"),
    ("meteorological_forcing", "Meteorology"),
    ("soil_properties", "Soil properties"),
    ("land_cover_or_vegetation", "Land cover / vegetation"),
    ("topography", "Topography"),
    ("temporal_context", "Temporal context"),
]
# Families used only in TRANSFER and VALUE (absent from the SOURCE context-only set)
TV_ONLY_FAMILIES = [
    ("antecedent_land_surface_fluxes", "Antecedent fluxes"),
    ("assimilation_diagnostics_or_history", "Assimilation history"),
]

# --------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------
FONT = "Nimbus Sans"  # URW metric clone of Helvetica (Arial/Helvetica/Calibri not installed)
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

C_CDF = "#3E6A97"        # sober blue
C_CDF_TXT = "#2E5277"
C_NOCDF = "#C8904F"      # sober ochre
C_NOCDF_TXT = "#8E5E28"
C_TXT = "#1F1F1F"
C_SUB = "#5E5E5E"        # secondary text (not too dark, not too light)
C_HEAD_TXT = "#2A3D52"
C_BOX_EDGE = "#8C9CAD"
C_BOX_HEAD = "#EDF1F5"
C_LINE = "#D3D9E0"
C_ARROW = "#66717E"
C_MARK = "#9AA7B5"

FS_TITLE, FS_PANEL, FS_BOXHEAD = 13.0, 11.0, 10.0
FS_BODY, FS_SMALL, FS_FOOT = 8.8, 8.0, 7.9


# --------------------------------------------------------------------------
# Data + numerical checks
# --------------------------------------------------------------------------
def r1(v):
    """Round half-up to 1 decimal (avoids banker's/binary-float surprises)."""
    return float(Decimal(repr(float(v))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


tidy = pd.read_csv(TIDY_CSV)
imp = pd.DataFrame({exp: tidy[tidy["model_key"] == key].set_index("group")
                    ["normalized_group_importance_pct"] for exp, key in MODEL_KEYS.items()}).fillna(0.0)
assert not imp.empty, "No SOURCE matched rows in tidy_group_summary.csv"

# (1) independent recomputation from raw SHAP cohorts + matched-support check
groups = yaml.safe_load(GROUPS_YAML.read_text())
f2g = {f: g for g, feats in groups.items() for f in feats}
keysets, n_rows = {}, None
for exp, key in MODEL_KEYS.items():
    df = pd.read_parquet(SHAP_DIR / f"shap_{key}_cohort.parquet")
    cols = [c for c in df.columns if c.startswith("shap__")]
    mabs = df[cols].abs().mean()
    mabs.index = [c[len("shap__"):] for c in mabs.index]
    unmapped = [f for f in mabs.index if f not in f2g]
    assert not unmapped, f"Unmapped SHAP features: {unmapped}"
    g = mabs.groupby(mabs.index.map(f2g)).sum()
    rec = (100 * g / g.sum()).reindex(imp.index).fillna(0.0)
    print(f"[check] {exp}: max |CSV - recomputed| = {(imp[exp] - rec).abs().max():.2e} pp "
          f"(n = {len(df)}, {len(cols)} predictors)")
    keysets[exp] = set(map(tuple, df[["date", "y_index", "x_index"]].astype(str).values))
    n_rows = len(df)
print(f"[check] identical pixel-days CDF vs NoCDF: {keysets['CDF'] == keysets['NoCDF']}")

# (2) families with non-zero importance must be exactly the six SOURCE families
src_keys = [k for k, _ in SOURCE_FAMILIES]
nonzero = set(imp.index[(imp > 0).any(axis=1)])
assert nonzero == set(src_keys), f"Unexpected SOURCE families: {nonzero ^ set(src_keys)}"

vals = imp.reindex(src_keys)
table = pd.DataFrame({
    "family": [l for _, l in SOURCE_FAMILIES],
    "CDF_exact_pct": vals["CDF"].values,
    "NoCDF_exact_pct": vals["NoCDF"].values,
}, index=src_keys)
table["CDF_minus_NoCDF_exact_pp"] = table["CDF_exact_pct"] - table["NoCDF_exact_pct"]
table["CDF_displayed"] = table["CDF_exact_pct"].map(r1)
table["NoCDF_displayed"] = table["NoCDF_exact_pct"].map(r1)
table["CDF_minus_NoCDF_displayed_pp"] = (table["CDF_displayed"] - table["NoCDF_displayed"]).map(r1)
table["exact_diff_rounded_pp"] = table["CDF_minus_NoCDF_exact_pp"].map(r1)

for exp in MODEL_KEYS:
    s_exact, s_disp = table[f"{exp}_exact_pct"].sum(), table[f"{exp}_displayed"].sum()
    print(f"[check] {exp}: sum exact = {s_exact:.4f} %, sum displayed = {r1(s_disp):.1f} %")
mism = table[table["CDF_minus_NoCDF_displayed_pp"] != table["exact_diff_rounded_pp"]]
print("[check] families where diff(displayed) != round(diff exact):",
      ", ".join(f"{r.family} ({r.CDF_minus_NoCDF_displayed_pp:+.1f} vs {r.exact_diff_rounded_pp:+.1f})"
                for r in mism.itertuples()) or "none")

# (3) Spearman: stored value vs. recomputation on the six SOURCE families (not displayed)
stored_rho = json.loads(STATS_JSON.read_text()).get("group_rho") if STATS_JSON.exists() else None
rho9 = spearmanr(imp["CDF"], imp["NoCDF"])
rho6 = spearmanr(vals["CDF"], vals["NoCDF"])
print(f"[check] Spearman stored = {stored_rho}; all {len(imp)} groups (incl. zero ties) = "
      f"{rho9.correlation:.3f}; 6 SOURCE families = {rho6.correlation:.3f} (p = {rho6.pvalue:.3f})"
      " -> not displayed")

# (4) SOURCE predictive skill (2020 hold-out, all rows)
m = pd.read_csv(METRICS)
m = m[m["target"] == "SOURCE"].set_index("experiment")
r2 = {k: float(m.loc[k, "r2"]) for k in ("CDF", "NoCDF")}
print(f"[check] SOURCE 2020 hold-out R2: CDF = {r2['CDF']:.3f}, NoCDF = {r2['NoCDF']:.3f} "
      f"(n = {int(m.loc['CDF', 'n']):,})")

table.to_csv(OUT_DIR / f"{STEM}_values.csv", float_format="%.4f", index_label="group")
print(table.drop(columns=["exact_diff_rounded_pp"]).round(2).to_string())

# --------------------------------------------------------------------------
# Figure (single overlay axis in inches + one axis for the bar chart)
# --------------------------------------------------------------------------
FW, FH = 10.0, 8.62
fig = plt.figure(figsize=(FW, FH))
ov = fig.add_axes([0, 0, 1, 1])
ov.set_xlim(0, FW)
ov.set_ylim(0, FH)
ov.axis("off")
renderer = fig.canvas.get_renderer()


def text_runs(x, y, runs, fs, **kw):
    """Draw consecutive text runs [(txt, weight, color), ...] on one line; return end x."""
    inv = ov.transData.inverted()
    for txt, weight, color in runs:
        t = ov.text(x, y, txt, fontsize=fs, fontweight=weight, color=color, va="center", **kw)
        bb = t.get_window_extent(renderer=renderer)
        x = inv.transform((bb.x1, bb.y0))[0]
    return x


def arrow(x0, y0, x1, y1, color=C_ARROW, lw=1.2, ms=10):
    ov.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms,
                                 color=color, lw=lw, shrinkA=0, shrinkB=0))


def rbox(x, y, w, h, fc, ec, lw=0.8, r=0.06, z=2):
    ov.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z))


XL, XR = 0.15, 9.85

# Title
ov.text(XL, 8.36, "Explaining SMAP assimilation responses: framework and preliminary "
        "CDF\u2013NoCDF evidence", fontsize=FS_TITLE, fontweight="bold", color=C_TXT, va="center")

# ============================ PANEL (a) ===================================
ov.text(XL, 7.90, "(a)", fontsize=FS_PANEL, fontweight="bold", va="center")
ov.text(0.50, 7.90, "XAI diagnostic framework for SMAP assimilation impacts",
        fontsize=FS_PANEL, fontweight="bold", va="center", color=C_TXT)

BY0, BY1, HEAD = 5.72, 7.62, 0.34
YC = (BY0 + BY1) / 2
BW = 2.45
BX = [1.70, 4.55, 7.40]

# entry node
sx0, sx1 = XL, 1.30
rbox(sx0, YC - 0.52, sx1 - sx0, 1.04, fc="#F6F7F8", ec="#B3BAC2")
ov.text((sx0 + sx1) / 2, YC + 0.16, "SMAP\nassimilation", ha="center", va="center",
        fontsize=9.4, fontweight="bold", color=C_HEAD_TXT, linespacing=1.15)
ov.text((sx0 + sx1) / 2, YC - 0.28, "Noah-MP EnKF\nDA vs open loop", ha="center",
        va="center", fontsize=7.8, color=C_SUB, linespacing=1.2)

arrow(sx1 + 0.06, YC, BX[0] - 0.06, YC)
for i in range(2):
    arrow(BX[i] + BW + 0.07, YC, BX[i + 1] - 0.07, YC)

BLOCKS = [
    dict(name="SOURCE",
         q="Which conditions are associated\nwith SMAP analysis updates?",
         t=[(r"Target:  $\delta x$  or  $|\delta x|$", FS_BODY)],
         g="\u03b4x: surface soil-moisture analysis increment"),
    dict(name="TRANSFER",
         q="Under which conditions do\nDA-induced responses\nappear downstream?",
         t=[("Targets:  $\\Delta$RZSM  \u00b7  $\\Delta$ET  \u00b7  $\\Delta$Q$_\\mathrm{s}$"
             "  \u00b7  $\\Delta$Q$_\\mathrm{sb}$", FS_BODY)],
         g="\u0394 = DA \u2212 open loop (OPL)"),
    dict(name="VALUE",
         q="When does the DA response\nimprove agreement with an\nindependent reference?",
         t=[("Target:  value_ae =", FS_BODY),
            (r"$|\mathrm{ET}_\mathrm{OPL}-\mathrm{ET}_\mathrm{GLEAM}|-"
             r"|\mathrm{ET}_\mathrm{DA}-\mathrm{ET}_\mathrm{GLEAM}|$", 8.4)],
         g="> 0: DA closer to GLEAM ET"),
]
DIV_Y = 6.53
for x0, b in zip(BX, BLOCKS):
    xc = x0 + BW / 2
    rbox(x0, BY0, BW, BY1 - BY0, fc="white", ec="none", z=2)
    rbox(x0, BY1 - HEAD, BW, HEAD, fc=C_BOX_HEAD, ec="none", z=2.5, r=0.06)
    ov.add_patch(Rectangle((x0 + 0.005, BY1 - HEAD), BW - 0.01, HEAD / 2,
                           fc=C_BOX_HEAD, ec="none", zorder=2.6))
    ov.plot([x0, x0 + BW], [BY1 - HEAD] * 2, color=C_BOX_EDGE, lw=0.5, zorder=3)
    rbox(x0, BY0, BW, BY1 - BY0, fc="none", ec=C_BOX_EDGE, lw=0.9, z=4)
    ov.text(xc, BY1 - HEAD / 2, b["name"], ha="center", va="center", fontsize=FS_BOXHEAD,
            fontweight="bold", color=C_HEAD_TXT, zorder=5)
    ov.text(xc, BY1 - HEAD - 0.11, b["q"], ha="center", va="top", fontsize=FS_BODY,
            style="italic", color=C_TXT, linespacing=1.25, zorder=5)
    ov.plot([x0 + 0.30, x0 + BW - 0.30], [DIV_Y] * 2, color=C_LINE, lw=0.6, zorder=5)
    y = DIV_Y - 0.13
    for txt, fs in b["t"]:
        ov.text(xc, y, txt, ha="center", va="top", fontsize=fs, color=C_TXT, zorder=5)
        y -= 0.23
    ov.text(xc, BY0 + 0.09, b["g"], ha="center", va="bottom", fontsize=FS_SMALL - 0.2,
            color=C_SUB, zorder=5)

# Predictor-family band (light): all-stage families | TRANSFER & VALUE only
PY0, PY1 = 4.60, 5.48
rbox(XL, PY0, XR - XL, PY1 - PY0, fc="white", ec=C_LINE, lw=0.8)
ov.text(0.80, (PY0 + PY1) / 2, "Predictor\nfamilies", ha="center", va="center",
        fontsize=9.2, fontweight="bold", color=C_HEAD_TXT, linespacing=1.15)
ov.plot([1.45, 1.45], [PY0 + 0.12, PY1 - 0.12], color=C_LINE, lw=0.8)
SPLIT = 7.25
ov.plot([SPLIT, SPLIT], [PY0 + 0.12, PY1 - 0.12], color=C_LINE, lw=0.8)

HY, ROWS = PY1 - 0.17, [PY1 - 0.43, PY1 - 0.68]
ov.text(1.65, HY, "SOURCE \u00b7 TRANSFER \u00b7 VALUE", fontsize=FS_SMALL, color=C_SUB,
        fontweight="bold", va="center")
cols = [1.65, 3.65, 5.35]
for i, (_, lab) in enumerate(SOURCE_FAMILIES):
    cx, cy = cols[i % 3], ROWS[i // 3]
    ov.add_patch(Rectangle((cx, cy - 0.04), 0.08, 0.08, fc=C_MARK, ec="none", zorder=3))
    ov.text(cx + 0.16, cy, lab, va="center", fontsize=FS_BODY, color=C_TXT)
ov.text(SPLIT + 0.20, HY, "TRANSFER \u00b7 VALUE only", fontsize=FS_SMALL, color=C_SUB,
        fontweight="bold", va="center")
for j, (_, lab) in enumerate(TV_ONLY_FAMILIES):
    cx, cy = SPLIT + 0.20, ROWS[j]
    ov.add_patch(Rectangle((cx, cy - 0.04), 0.08, 0.08, fc="white", ec=C_MARK, lw=0.9,
                           zorder=3))
    ov.text(cx + 0.16, cy, lab, va="center", fontsize=FS_BODY, color=C_TXT)

ov.text(XL, 4.40, "Predictor selection is stage-specific to avoid target leakage and "
        "circular interpretation.", fontsize=FS_SMALL, style="italic", color=C_SUB, va="center")

# Irrigation note (discreet but visible: thin warm-grey frame)
IY0, IY1 = 3.94, 4.22
rbox(XL, IY0, XR - XL, IY1 - IY0, fc="#FAF7F1", ec="#D9CBB0", lw=0.8, r=0.05)
text_runs(XL + 0.14, (IY0 + IY1) / 2, [
    ("Current baseline experiments: ", "bold", C_TXT),
    ("irrigation OFF.", "normal", C_TXT),
    ("      Open question: ", "bold", C_HEAD_TXT),
    ("should irrigation-on sensitivity experiments be added?", "normal", C_TXT),
], fs=8.7)

# panel separator
ov.plot([XL, XR], [3.74, 3.74], color="#E1E1E1", lw=0.8)

# ============================ PANEL (b) ===================================
ov.text(XL, 3.50, "(b)", fontsize=FS_PANEL, fontweight="bold", va="center")
ov.text(0.50, 3.50, "Preliminary SOURCE attribution under CDF and NoCDF",
        fontsize=FS_PANEL, fontweight="bold", va="center", color=C_TXT)
ov.text(0.50, 3.27, f"Target |\u03b4x|  \u00b7  2020 hold-out  \u00b7  matched support "
        f"(identical pixel-days, n = {n_rows:,})", fontsize=FS_SMALL, color=C_SUB, va="center")

AXL, AXB, AXW, AXH = 2.30, 1.08, 3.55, 1.95
axb = fig.add_axes([AXL / FW, AXB / FH, AXW / FW, AXH / FH])
n = len(table)
yy = np.arange(n)[::-1].astype(float)
h = 0.37
YLIM = (-0.6, n - 0.4)
axb.barh(yy + h / 2, table["CDF_exact_pct"], height=h, color=C_CDF, label="CDF", zorder=3)
axb.barh(yy - h / 2, table["NoCDF_exact_pct"], height=h, color=C_NOCDF, label="NoCDF", zorder=3)
for y, (a, b) in zip(yy, table[["CDF_displayed", "NoCDF_displayed"]].values):
    axb.text(a + 0.8, y + h / 2, f"{a:.1f}",
             va="center", fontsize=7.9, color=C_CDF_TXT)
    axb.text(b + 0.8, y - h / 2, f"{b:.1f}", va="center", fontsize=7.9, color=C_NOCDF_TXT)
axb.set_yticks(yy)
axb.set_yticklabels(table["family"], fontsize=9.0, color=C_TXT)
axb.set_xlim(0, 67)
axb.set_ylim(*YLIM)
axb.set_xticks([0, 20, 40, 60])
axb.tick_params(axis="x", labelsize=8.2, length=3, width=0.6, color="#777777", labelcolor=C_TXT)
axb.tick_params(axis="y", length=0, pad=5)
axb.set_xlabel("Share of grouped mean |SHAP| (%)", fontsize=8.6, color=C_TXT, labelpad=4)
axb.grid(axis="x", color="#ECECEC", lw=0.6, zorder=0)
for s in ("top", "right", "left"):
    axb.spines[s].set_visible(False)
axb.spines["bottom"].set_color("#777777")
axb.legend(loc="lower right", frameon=False, fontsize=8.6, handlelength=1.1,
           handleheight=0.9, borderaxespad=0.1)

# CDF - NoCDF column (pp), computed from displayed values
DX = AXL + AXW + 0.42
ov.text(DX, AXB + AXH + 0.22, "CDF \u2212 NoCDF", ha="center", va="center",
        fontsize=FS_SMALL, fontweight="bold", color=C_TXT)
ov.text(DX, AXB + AXH + 0.07, "(pp)", ha="center", va="center", fontsize=7.6, color=C_SUB)
y2in = lambda y: AXB + AXH * (y - YLIM[0]) / (YLIM[1] - YLIM[0])
for y, d in zip(yy, table["CDF_minus_NoCDF_displayed_pp"]):
    s = "0.0" if d == 0 else f"{d:+.1f}".replace("-", "\u2212")
    ov.text(DX, y2in(y), s, ha="center", va="center", fontsize=8.4, color=C_TXT,
            fontweight=("bold" if abs(d) >= 10 else "normal"))

# Key-reading box
KX0, KX1, KY0, KY1 = 6.75, XR, 0.98, 3.12
rbox(KX0, KY0, KX1 - KX0, KY1 - KY0, fc="#FAFBFC", ec=C_LINE, lw=0.8, r=0.05)
ov.text(KX0 + 0.16, KY1 - 0.20, "Key reading", fontsize=9.0, fontweight="bold",
        color=C_HEAD_TXT, va="center")
bullets = [
    "Antecedent soil moisture dominates SOURCE attribution, particularly under CDF.",
    "Under NoCDF, attribution is relatively more distributed across meteorology and "
    "land-surface properties.",
    "Interpretation remains diagnostic rather than causal.",
    f"Lower NoCDF predictive skill should be kept in mind (2020 hold-out "
    f"R\u00b2 = {r2['NoCDF']:.2f} vs {r2['CDF']:.2f} for CDF).",
]
FS_K, LH = 8.2, 0.146
y = KY1 - 0.42
for b in bullets:
    wrapped = textwrap.fill(b, width=48, break_on_hyphens=False)
    ov.text(KX0 + 0.18, y, "\u2022", fontsize=FS_K, va="top", color=C_SUB)
    ov.text(KX0 + 0.32, y, wrapped, fontsize=FS_K, va="top", color=C_TXT, linespacing=1.25)
    y -= LH * (wrapped.count("\n") + 1) + 0.10

# Footnotes
FOOT = [
    "Bars: share of grouped mean |SHAP| within each configuration (the six SOURCE families sum to "
    "100%); CDF \u2212 NoCDF in percentage points, from the displayed values.",
    "Antecedent fluxes and assimilation history are excluded from the SOURCE predictor set and are "
    "used only in the TRANSFER and VALUE models.",
    "Random forest + TreeSHAP used as a diagnostic of the DA system, not as a surrogate for "
    "Noah-MP/EnKF; CDF and NoCDF are modeled separately.",
]
for i, t in enumerate(FOOT):
    ov.text(XL, 0.46 - 0.165 * i, t, fontsize=FS_FOOT, style="italic", color=C_SUB, va="center")

# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
png, pdf, svg = (OUT_DIR / f"{STEM}.{ext}" for ext in ("png", "pdf", "svg"))
fig.savefig(png, dpi=400)
fig.savefig(pdf)
fig.savefig(svg)
s = svg.read_text()
s = re.sub(r"font-family:\s*'?Nimbus Sans'?", "font-family:Arial, Helvetica, 'Nimbus Sans', sans-serif", s)
s = re.sub(r'font-family="Nimbus Sans"', 'font-family="Arial, Helvetica, Nimbus Sans, sans-serif"', s)
svg.write_text(s)
print("Saved:", png, pdf, svg, sep="\n  ")
