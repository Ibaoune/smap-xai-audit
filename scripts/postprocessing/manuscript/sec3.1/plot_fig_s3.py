"""
Plotting Script for Supplementary Figure S3
===========================================
Water-Equivalent Surface-Layer Analysis Adjustment

Panels:
  (a) Absolute adjustment activity (monthly climatology of absolute adjustment [mm])
  (b) Net adjustment balance (monthly climatology of net adjustment [mm])
  (c) Cumulative absolute-adjustment difference (map: NoCDF − CDF [mm] over 2016–2020)
  (d) Cumulative matched-sample accounting (bar chart: Positive, Removal, Absolute, Net [mm])
      * Corrected visual sign convention: Wetting > 0, Drying / Removal < 0

Outputs:
  - figures/manuscript/section_3_1/FigS3_water_accounting.png (500 DPI)
  - figures/manuscript/section_3_1/FigS3_water_accounting.pdf
"""

import os
from pathlib import Path
import copy
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm
from matplotlib.gridspec import GridSpec

def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'data').is_dir() and (parent / 'figures').is_dir():
            return parent
    return Path.cwd()

# Typography and styling (matching Figure 3)
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 9.5,
    'axes.titlesize': 10.8,
    'axes.labelsize': 9.8,
    'xtick.labelsize': 8.8,
    'ytick.labelsize': 8.8,
    'legend.fontsize': 8.8,
    'figure.titlesize': 11.5,
    'lines.linewidth': 1.6,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'pdf.fonttype': 42,
    'ps.fonttype': 42
})

COLOR_CDF = '#1f77b4'       # manuscript blue
COLOR_NOCDF = '#ff7f0e'     # manuscript orange

LON_TICKS = [-10, -8, -6, -4, -2]
LON_LABELS = ['10°W', '8°W', '6°W', '4°W', '2°W']
LAT_TICKS = [30, 32, 34, 36]
LAT_LABELS = ['30°N', '32°N', '34°N', '36°N']

def setup_map_ax(ax, title: str):
    """Format geographical map axes consistently."""
    ax.set_aspect('equal', 'box')
    ax.set_xlim([-10.2, -1.0])
    ax.set_ylim([29.8, 36.2])
    ax.set_xticks(LON_TICKS)
    ax.set_xticklabels(LON_LABELS, fontsize=8.6)
    ax.set_yticks(LAT_TICKS)
    ax.set_yticklabels(LAT_LABELS, fontsize=8.6)
    ax.set_title(title, pad=6.5, fontsize=10.5, weight='normal')
    ax.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)

def main():
    root = get_project_root()
    data_dir = root / 'figures' / 'manuscript' / 'section_3_1'
    
    # Load input datasets
    clim_path = data_dir / 'FigS3_monthly_climatology.csv'
    map_path = data_dir / 'FigS3_cumulative_map.nc'
    summary_path = data_dir / 'FigS3_water_accounting_summary.csv'
    
    if not (clim_path.is_file() and map_path.is_file() and summary_path.is_file()):
        raise FileNotFoundError("Missing inputs for Figure S3. Run process_supplementary_data.py first.")
        
    df_clim = pd.read_csv(clim_path)
    ds_map = xr.open_dataset(map_path)
    df_summary = pd.read_csv(summary_path)
    
    # Static elevation for background domain context
    elev_path = root / 'data' / 'processed' / 'static' / 'elevation' / 'elevation.nc'
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull()
    
    # 2x2 GridSpec Layout
    fig = plt.figure(figsize=(10.8, 8.4))
    gs = GridSpec(2, 2, figure=fig,
                  left=0.08, right=0.96, bottom=0.10, top=0.92,
                  wspace=0.24, hspace=0.36,
                  width_ratios=[1, 1], height_ratios=[1, 1])
    
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])
    
    months_x = np.arange(12)
    month_labels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    
    # -------------------------------------------------------------------------
    # Panel (a): Absolute Adjustment Activity
    # -------------------------------------------------------------------------
    ax_a.plot(months_x, df_clim['CDF_W_absolute'].values, color=COLOR_CDF, marker='o',
              markersize=4.5, lw=1.8, label='CDF', zorder=3)
    ax_a.plot(months_x, df_clim['NoCDF_W_absolute'].values, color=COLOR_NOCDF, marker='s',
              markersize=4.5, lw=1.8, label='NoCDF', zorder=3)
    
    ax_a.set_title(r"$\bf{(a)}$ Absolute adjustment activity", pad=6.5, fontsize=10.5)
    ax_a.set_xlabel('Month', fontsize=9.8, labelpad=4)
    ax_a.set_ylabel('Mean monthly adjustment [mm]', fontsize=9.8, labelpad=4)
    ax_a.set_xticks(months_x)
    ax_a.set_xticklabels(month_labels)
    ax_a.set_xlim([-0.5, 11.5])
    ax_a.set_ylim([0, 8.8])
    ax_a.set_yticks([0, 2, 4, 6, 8])
    ax_a.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_a.legend(loc='upper left', frameon=True, framealpha=0.90, edgecolor='#cccccc', fontsize=8.8)
    
    # -------------------------------------------------------------------------
    # Panel (b): Net Adjustment Balance
    # -------------------------------------------------------------------------
    ax_b.axhline(0, color='#444444', linestyle='--', lw=0.9, alpha=0.75, zorder=1)
    ax_b.plot(months_x, df_clim['CDF_W_net'].values, color=COLOR_CDF, marker='o',
              markersize=4.5, lw=1.8, label='CDF', zorder=3)
    ax_b.plot(months_x, df_clim['NoCDF_W_net'].values, color=COLOR_NOCDF, marker='s',
              markersize=4.5, lw=1.8, label='NoCDF', zorder=3)
    
    ax_b.set_title(r"$\bf{(b)}$ Net adjustment balance", pad=6.5, fontsize=10.5)
    ax_b.set_xlabel('Month', fontsize=9.8, labelpad=4)
    ax_b.set_ylabel('Mean monthly net adjustment [mm]', fontsize=9.8, labelpad=4)
    ax_b.set_xticks(months_x)
    ax_b.set_xticklabels(month_labels)
    ax_b.set_xlim([-0.5, 11.5])
    ax_b.set_ylim([-4.2, 2.2])
    ax_b.set_yticks([-4, -3, -2, -1, 0, 1, 2])
    ax_b.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_b.legend(loc='lower left', frameon=True, framealpha=0.90, edgecolor='#cccccc', fontsize=8.8)
    
    # -------------------------------------------------------------------------
    # Panel (c): Cumulative Absolute-Adjustment Difference Map
    # -------------------------------------------------------------------------
    bounds_c = np.linspace(-150, 150, 13)  # 12 classes of 25 mm
    cmap_base = plt.cm.get_cmap('RdBu_r', 12)
    cmap_disc = copy.copy(cmap_base)
    cmap_disc.set_bad(color='#dcdcdc')
    norm_c = BoundaryNorm(bounds_c, cmap_disc.N)
    
    # Neutral background
    ax_c.pcolormesh(elev.lon, elev.lat, valid_land.where(valid_land),
                    cmap=mpl.colors.ListedColormap(['#dcdcdc']),
                    shading='auto', zorder=1)
    # Difference mesh
    diff_abs = ds_map['diff_cum_absolute']
    mesh_c = ax_c.pcolormesh(diff_abs.lon, diff_abs.lat, diff_abs,
                             cmap=cmap_disc, norm=norm_c,
                             shading='auto', zorder=2)
    setup_map_ax(ax_c, r"$\bf{(c)}$ Cumulative absolute-adjustment difference")
    
    # -------------------------------------------------------------------------
    # Panel (d): Cumulative Matched-Sample Accounting (Bar Chart with Correct Signs)
    # -------------------------------------------------------------------------
    # Water accounting values:
    # Wetting (Positive) > 0, Removal (Drying) < 0, Absolute (Activity) > 0, Net (Balance) < 0
    cdf_pos = float(df_summary.loc[0, 'area_weighted_positive_mm'])
    cdf_rem = -float(df_summary.loc[0, 'area_weighted_removal_mm'])  # Plotted below 0
    cdf_abs = float(df_summary.loc[0, 'area_weighted_absolute_mm'])
    cdf_net = float(df_summary.loc[0, 'area_weighted_net_mm'])       # Negative
    
    nocdf_pos = float(df_summary.loc[1, 'area_weighted_positive_mm'])
    nocdf_rem = -float(df_summary.loc[1, 'area_weighted_removal_mm'])  # Plotted below 0
    nocdf_abs = float(df_summary.loc[1, 'area_weighted_absolute_mm'])
    nocdf_net = float(df_summary.loc[1, 'area_weighted_net_mm'])       # Negative
    
    cdf_bars = [cdf_pos, cdf_rem, cdf_abs, cdf_net]
    nocdf_bars = [nocdf_pos, nocdf_rem, nocdf_abs, nocdf_net]
    
    categories = ['Positive\n(Wetting)', 'Removal\n(Drying)', 'Absolute\n(Activity)', 'Net\n(Balance)']
    x_indices = np.arange(len(categories))
    bar_width = 0.35
    
    # Solid horizontal zero reference
    ax_d.axhline(0, color='#333333', linestyle='-', lw=0.9, zorder=2)
    
    rects_cdf = ax_d.bar(x_indices - bar_width/2, cdf_bars, bar_width,
                         color=COLOR_CDF, edgecolor='#333333', lw=0.75,
                         label='CDF', zorder=3)
    rects_nocdf = ax_d.bar(x_indices + bar_width/2, nocdf_bars, bar_width,
                           color=COLOR_NOCDF, edgecolor='#333333', lw=0.75,
                           label='NoCDF', zorder=3)
    
    # Annotate numeric values above or below each bar
    for idx, (rect, val) in enumerate(zip(rects_cdf, cdf_bars)):
        val_str = f"+{val:.1f}" if val >= 0 else f"−{abs(val):.1f}"
        x_pos = rect.get_x() + rect.get_width() / 2
        if idx == 2:  # Absolute activity CDF
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(-6, 3.5),
                          textcoords="offset points", ha='center', va='bottom',
                          fontsize=8.1, weight='normal')
        elif val >= 0:
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(0, 3.5),
                          textcoords="offset points", ha='center', va='bottom',
                          fontsize=8.2, weight='normal')
        else:
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(0, -4.0),
                          textcoords="offset points", ha='center', va='top',
                          fontsize=8.2, weight='normal')
            
    for idx, (rect, val) in enumerate(zip(rects_nocdf, nocdf_bars)):
        val_str = f"+{val:.1f}" if val >= 0 else f"−{abs(val):.1f}"
        x_pos = rect.get_x() + rect.get_width() / 2
        if idx == 2:  # Absolute activity NoCDF
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(6, 3.5),
                          textcoords="offset points", ha='center', va='bottom',
                          fontsize=8.1, weight='normal')
        elif val >= 0:
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(0, 3.5),
                          textcoords="offset points", ha='center', va='bottom',
                          fontsize=8.2, weight='normal')
        else:
            ax_d.annotate(val_str, xy=(x_pos, val), xytext=(0, -4.0),
                          textcoords="offset points", ha='center', va='top',
                          fontsize=8.2, weight='normal')
    
    ax_d.set_title(r"$\bf{(d)}$ Cumulative matched-sample accounting", pad=6.5, fontsize=10.5)
    ax_d.set_ylabel('Cumulative adjustment [mm]', fontsize=9.8, labelpad=4)
    ax_d.set_xticks(x_indices)
    ax_d.set_xticklabels(categories, fontsize=8.8)
    ax_d.set_xlim([-0.6, len(categories) - 0.4])
    ax_d.set_ylim([-195, 245])
    ax_d.set_yticks([-150, -100, -50, 0, 50, 100, 150, 200])
    ax_d.grid(axis='y', linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_d.legend(loc='upper right', frameon=True, framealpha=0.90, edgecolor='#cccccc', fontsize=8.8)
    
    # Format Cartesian spines & ticks
    for ax in [ax_a, ax_b, ax_d]:
        ax.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')
            spine.set_linewidth(0.75)
            
    # Add horizontal colorbar below panel (c)
    fig.canvas.draw()
    pos_c = ax_c.get_position(original=False)
    
    cbar_w_c = 0.88 * (pos_c.x1 - pos_c.x0)
    cbar_x_c = (pos_c.x0 + pos_c.x1) / 2.0 - cbar_w_c / 2.0
    cbar_y_c = pos_c.y0 - 0.052
    cbar_h = 0.024
    
    cbar_ax_c = fig.add_axes([cbar_x_c, cbar_y_c, cbar_w_c, cbar_h])
    cbar_c = fig.colorbar(mesh_c, cax=cbar_ax_c, orientation='horizontal',
                          ticks=[-150, -100, -50, 0, 50, 100, 150])
    cbar_c.set_label('Difference [mm] (NoCDF − CDF)', fontsize=9.2, labelpad=3.0)
    cbar_c.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Supertitle
    fig.suptitle("Water-equivalent surface-layer analysis adjustment", 
                 fontsize=11.6, weight='bold', y=0.972)
    
    png_path = data_dir / 'FigS3_water_accounting.png'
    pdf_path = data_dir / 'FigS3_water_accounting.pdf'
    
    fig.savefig(png_path, dpi=500, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated Figure S3: {png_path} (500 DPI) and {pdf_path}")

if __name__ == '__main__':
    main()
