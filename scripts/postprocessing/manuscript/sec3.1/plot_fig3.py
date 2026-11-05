"""
Plotting Pipeline for Manuscript Section 3.1 (Figure 3)
======================================================

Generates the two coordinated publication figure blocks for Section 3.1:

  Block 1: Fig3_a_d_support.png / .pdf
    - (a) CDF assimilation frequency [%]
    - (b) NoCDF assimilation frequency [%]
    - (c) Assimilation frequency difference: NoCDF - CDF [percentage points]
    - (d) Monthly assimilation frequency [%]

  Block 2: Fig3_e_h_matched_updates.png / .pdf
    - (e) Matched signed-increment distributions [m3 m-3]
    - (f) CDF mean signed increment on matched support [m3 m-3]
    - (g) NoCDF mean signed increment on matched support [m3 m-3]
    - (h) Matched increment difference: NoCDF - CDF [m3 m-3]

Aesthetics:
  - Strict GridSpec layout architecture
  - Discrete BoundaryNorm colormaps (10-class YlGnBu/RdBu_r, 14-class BrBG/RdBu_r)
  - Unified sans-serif typography (DejaVu Sans / Arial)
  - Aligned horizontal colorbars with clean padding
  - High-resolution (500 DPI) raster and vector PDF exports
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
    """Resolve the repository root directory robustly."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'data').is_dir() and (parent / 'figures').is_dir():
            return parent
    return Path.cwd()

# Typography and publication style
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
COLOR_MATCHED = '#222222'   # dark gray / black

LON_TICKS = [-10, -8, -6, -4, -2]
LON_LABELS = ['10°W', '8°W', '6°W', '4°W', '2°W']
LAT_TICKS = [30, 32, 34, 36]
LAT_LABELS = ['30°N', '32°N', '34°N', '36°N']

def setup_map_ax(ax, title: str, show_yticklabels: bool = True, show_xticklabels: bool = True):
    """Format geographical map axes consistently."""
    ax.set_aspect('equal', 'box')
    ax.set_xlim([-10.2, -1.0])
    ax.set_ylim([29.8, 36.2])
    ax.set_xticks(LON_TICKS)
    ax.set_yticks(LAT_TICKS)
    
    if show_xticklabels:
        ax.set_xticklabels(LON_LABELS, fontsize=8.8)
    else:
        ax.set_xticklabels([])
        
    if show_yticklabels:
        ax.set_yticklabels(LAT_LABELS, fontsize=8.8)
    else:
        ax.set_yticklabels([])
        
    ax.set_title(title, pad=6.5, fontsize=10.8, weight='normal')
    ax.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)

# ==============================================================================
# FIGURE 3a–d: ASSIMILATION FREQUENCY
# ==============================================================================
def make_fig3_a_d(out_dir: Path):
    print("Generating Figure 3a-d (Assimilation Frequency)...")
    ds_ad = xr.open_dataset(out_dir / 'Fig3_a_d_source_data.nc')
    df_monthly = pd.read_csv(out_dir / 'Fig3_a_d_source_data.csv')
    
    fig = plt.figure(figsize=(10.5, 8.5))
    
    # 2x2 GridSpec with standardized spacing and generous vertical gap
    gs = GridSpec(2, 2, figure=fig, 
                  left=0.08, right=0.96, bottom=0.155, top=0.960,
                  wspace=0.14, hspace=0.42,
                  width_ratios=[1, 1], height_ratios=[1, 1])
    
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])
    
    # Enforce exact box aspect ratio on line plot (d) to match map panels (6.4 / 9.2)
    box_aspect = 6.4 / 9.2
    ax_d.set_box_aspect(box_aspect)
    
    # --------------------------------------------------------------------------
    # Panels (a) & (b): Discrete Assimilation Frequency Maps (0-100%, 10 classes)
    # Colormap: Sequential YlGnBu (pale cream -> green-cyan -> dark blue)
    # --------------------------------------------------------------------------
    support_bounds = np.linspace(0, 100, 11)
    cmap_sup_base = plt.cm.get_cmap('YlGnBu', 10)
    cmap_sup = copy.copy(cmap_sup_base)
    cmap_sup.set_bad(color='#dfdfdf')  # Neutral light gray clearly distinct from pale yellow
    norm_sup = BoundaryNorm(support_bounds, ncolors=cmap_sup.N, clip=True)
    
    mesh_a = ax_a.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_cdf'], 
                             cmap=cmap_sup, norm=norm_sup, shading='auto')
    setup_map_ax(ax_a, r"$\bf{(a)}$ CDF assimilation frequency", 
                 show_yticklabels=True, show_xticklabels=False)
    
    mesh_b = ax_b.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_nocdf'], 
                             cmap=cmap_sup, norm=norm_sup, shading='auto')
    setup_map_ax(ax_b, r"$\bf{(b)}$ NoCDF assimilation frequency", 
                 show_yticklabels=False, show_xticklabels=False)
    
    # --------------------------------------------------------------------------
    # Panel (c): Discrete Difference Map (NoCDF - CDF, [-50, +50] pp)
    # Colormap: Truncated RdBu_r centered at zero (avoid oversaturation)
    # --------------------------------------------------------------------------
    diff_bounds = np.arange(-50, 51, 10)
    colors_rdbu = plt.cm.RdBu_r(np.linspace(0.06, 0.94, 10))
    from matplotlib.colors import ListedColormap
    cmap_diff = ListedColormap(colors_rdbu)
    cmap_diff.set_bad(color='#dfdfdf')
    norm_diff = BoundaryNorm(diff_bounds, ncolors=cmap_diff.N, clip=True)
    
    mesh_c = ax_c.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_diff'], 
                             cmap=cmap_diff, norm=norm_diff, shading='auto')
    setup_map_ax(ax_c, r"$\bf{(c)}$ Assimilation frequency difference: NoCDF − CDF", 
                 show_yticklabels=True, show_xticklabels=True)
    
    # --------------------------------------------------------------------------
    # Panel (d): Monthly Assimilation Frequency
    # --------------------------------------------------------------------------
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax_d.plot(range(1, 13), df_monthly['cdf_native_percent'].values, 
              label='CDF', color=COLOR_CDF, ls='-', lw=1.8, zorder=3)
    ax_d.plot(range(1, 13), df_monthly['nocdf_native_percent'].values, 
              label='NoCDF', color=COLOR_NOCDF, ls='-', lw=1.8, zorder=3)
    ax_d.plot(range(1, 13), df_monthly['matched_support_percent'].values, 
              label='Joint CDF–NoCDF', color=COLOR_MATCHED, ls='--', lw=1.5, dashes=(3.5, 2.5), zorder=4)
    
    ax_d.set_title(r"$\bf{(d)}$ Monthly assimilation frequency", pad=6.5, fontsize=10.8, weight='normal')
    ax_d.set_xticks(range(1, 13))
    ax_d.set_xticklabels(months, rotation=0, fontsize=8.8)
    ax_d.set_xlabel('Month', fontsize=9.8, labelpad=3.5)
    ax_d.set_ylabel('Assimilation frequency [%]', fontsize=9.8, labelpad=4)
    ax_d.set_ylim([0, 35])
    ax_d.set_yticks([0, 5, 10, 15, 20, 25, 30, 35])
    ax_d.grid(True, linestyle='-', alpha=0.18, color='#888888', linewidth=0.5)
    
    # Horizontal legend placed BELOW panel (d)
    ax_d.legend(loc='upper center', bbox_to_anchor=(0.5, -0.22),
                ncol=3, frameon=False, fontsize=8.5, columnspacing=1.2, handlelength=1.8)
    ax_d.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax_d.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)
        
    # Get accurate axes geometry for colorbar placement
    fig.canvas.draw()
    pos_a = ax_a.get_position()
    pos_b = ax_b.get_position()
    pos_c = ax_c.get_position()
    
    # Shared horizontal colorbar for panels (a) and (b) placed comfortably between rows
    comb_w_ab = pos_b.x1 - pos_a.x0
    cbar_w_ab = 0.72 * comb_w_ab
    cbar_x_ab = (pos_a.x0 + pos_b.x1) / 2.0 - cbar_w_ab / 2.0
    cbar_h = 0.017
    cbar_y_ab = pos_a.y0 - 0.038
    
    cbar_ax_ab = fig.add_axes([cbar_x_ab, cbar_y_ab, cbar_w_ab, cbar_h])
    cbar_ab = fig.colorbar(mesh_a, cax=cbar_ax_ab, orientation='horizontal',
                           ticks=[0, 20, 40, 60, 80, 100])
    cbar_ab.set_label('Assimilation frequency [%]', fontsize=9.2, labelpad=3.0)
    cbar_ab.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Horizontal colorbar directly below panel (c)
    cbar_w_c = 0.82 * (pos_c.x1 - pos_c.x0)
    cbar_x_c = (pos_c.x0 + pos_c.x1) / 2.0 - cbar_w_c / 2.0
    cbar_y_c = pos_c.y0 - 0.075
    
    cbar_ax_c = fig.add_axes([cbar_x_c, cbar_y_c, cbar_w_c, cbar_h])
    cbar_c = fig.colorbar(mesh_c, cax=cbar_ax_c, orientation='horizontal',
                         ticks=[-50, -25, 0, 25, 50])
    cbar_c.set_label('Frequency difference [percentage points]', fontsize=9.2, labelpad=3.0)
    cbar_c.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Save standard publication figures (high-resolution PNG + vector PDF)
    png_path = out_dir / 'Fig3_a_d_support.png'
    pdf_path = out_dir / 'Fig3_a_d_support.pdf'
    
    fig.savefig(png_path, dpi=500, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {png_path} (500 DPI) and {pdf_path}")

# ==============================================================================
# FIGURE 3e–h: MATCHED ANALYSIS UPDATES
# ==============================================================================
def make_fig3_e_h(out_dir: Path):
    print("Generating Figure 3e-h (Matched Analysis Updates)...")
    ds_eh = xr.open_dataset(out_dir / 'Fig3_e_h_source_data.nc')
    dist = np.load(out_dir / 'matched_increments_1d.npz')
    cdf_mat = dist['cdf_mat']
    nocdf_mat = dist['nocdf_mat']
    
    fig = plt.figure(figsize=(11.0, 7.2))
    
    # 2 rows x 3 columns GridSpec
    gs = GridSpec(2, 3, figure=fig,
                  left=0.065, right=0.975, bottom=0.140, top=0.950,
                  height_ratios=[0.90, 1.0], wspace=0.12, hspace=0.28)
    
    ax_e = fig.add_subplot(gs[0, :])
    ax_f = fig.add_subplot(gs[1, 0])
    ax_g = fig.add_subplot(gs[1, 1])
    ax_h = fig.add_subplot(gs[1, 2])
    
    # --------------------------------------------------------------------------
    # Panel (e): Matched Signed-Increment Distributions
    # --------------------------------------------------------------------------
    xlim_range = [-0.065, 0.065]
    bins = np.linspace(xlim_range[0], xlim_range[1], 131)
    
    counts_cdf, bin_edges = np.histogram(cdf_mat, bins=bins, density=True)
    counts_nocdf, _ = np.histogram(nocdf_mat, bins=bins, density=True)
    
    mean_cdf = float(np.mean(cdf_mat))
    mean_nocdf = float(np.mean(nocdf_mat))
    
    # Step histograms
    ax_e.step(bin_edges[:-1], counts_cdf, where='post', color=COLOR_CDF, 
              label='CDF matched', lw=1.8, zorder=3)
    ax_e.step(bin_edges[:-1], counts_nocdf, where='post', color=COLOR_NOCDF, 
              label='NoCDF matched', lw=1.8, zorder=3)
    
    # Vertical zero reference
    ax_e.axvline(0, color='#333333', linestyle='-', lw=0.9, alpha=0.70, zorder=2)
    
    # Vertical mean reference dashed lines
    ax_e.axvline(mean_cdf, color=COLOR_CDF, linestyle='--', lw=1.2, alpha=0.85, zorder=2)
    ax_e.axvline(mean_nocdf, color=COLOR_NOCDF, linestyle='--', lw=1.2, alpha=0.85, zorder=2)
    
    ax_e.set_title(r"$\bf{(e)}$ Matched signed-increment distributions", pad=6.5, fontsize=10.8, weight='normal')
    ax_e.set_xlabel('Signed analysis increment [m³ m⁻³]', fontsize=9.8, labelpad=4)
    ax_e.set_ylabel('Density', fontsize=9.8, labelpad=4)
    ax_e.set_xlim(xlim_range)
    ax_e.set_xticks([-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06])
    ax_e.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    
    # Legend in upper right
    ax_e.legend(loc='upper right', frameon=True, framealpha=0.90, edgecolor='#cccccc', fontsize=8.8)
    
    # Compact in-panel statistical annotation (clean typography with Unicode minus)
    mean_cdf_str = f"−{abs(mean_cdf):.4f}" if mean_cdf < 0 else f"+{mean_cdf:.4f}"
    mean_nocdf_str = f"−{abs(mean_nocdf):.4f}" if mean_nocdf < 0 else f"+{mean_nocdf:.4f}"
    stats_text = f"mean(CDF) = {mean_cdf_str}\nmean(NoCDF) = {mean_nocdf_str} m³ m⁻³"
    ax_e.text(0.025, 0.90, stats_text, transform=ax_e.transAxes, fontsize=8.6,
              verticalalignment='top',
              bbox=dict(facecolor='white', edgecolor='#cccccc', alpha=0.85, pad=2.0))
    
    ax_e.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax_e.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)
        
    # --------------------------------------------------------------------------
    # Panels (f) & (g): Discrete Mean Signed Increments (BrBG, 14 classes)
    # --------------------------------------------------------------------------
    incr_bounds = np.arange(-0.035, 0.0351, 0.005)
    cmap_incr_base = plt.cm.get_cmap('BrBG', 14)
    cmap_incr = copy.copy(cmap_incr_base)
    cmap_incr.set_bad(color='#f2f2f2')
    norm_incr = BoundaryNorm(incr_bounds, ncolors=cmap_incr.N, clip=True)
    
    mesh_f = ax_f.pcolormesh(ds_eh.lon, ds_eh.lat, ds_eh['mean_cdf_matched'], 
                             cmap=cmap_incr, norm=norm_incr, shading='auto')
    setup_map_ax(ax_f, r"$\bf{(f)}$ CDF mean signed increment", 
                 show_yticklabels=True, show_xticklabels=True)
    
    mesh_g = ax_g.pcolormesh(ds_eh.lon, ds_eh.lat, ds_eh['mean_nocdf_matched'], 
                             cmap=cmap_incr, norm=norm_incr, shading='auto')
    setup_map_ax(ax_g, r"$\bf{(g)}$ NoCDF mean signed increment", 
                 show_yticklabels=False, show_xticklabels=True)
    
    # --------------------------------------------------------------------------
    # Panel (h): Discrete Difference Map (RdBu_r, 14 classes)
    # --------------------------------------------------------------------------
    cmap_h_base = plt.cm.get_cmap('RdBu_r', 14)
    cmap_h = copy.copy(cmap_h_base)
    cmap_h.set_bad(color='#f2f2f2')
    norm_h = BoundaryNorm(incr_bounds, ncolors=cmap_h.N, clip=True)
    
    mesh_h = ax_h.pcolormesh(ds_eh.lon, ds_eh.lat, ds_eh['mean_diff_matched'], 
                             cmap=cmap_h, norm=norm_h, shading='auto')
    setup_map_ax(ax_h, r"$\bf{(h)}$ Increment difference: NoCDF − CDF", 
                 show_yticklabels=False, show_xticklabels=True)
    
    # In-map statistical annotations
    bbox_props = dict(facecolor='white', edgecolor='0.75', alpha=0.82, pad=1.5)
    ax_f.text(0.04, 0.06, 'Drying: 96.7%', transform=ax_f.transAxes, fontsize=8.2, bbox=bbox_props)
    ax_g.text(0.04, 0.06, 'Wetting: 36.2%', transform=ax_g.transAxes, fontsize=8.2, bbox=bbox_props)
    ax_h.text(0.04, 0.06, 'NoCDF > CDF: 98.2%', transform=ax_h.transAxes, fontsize=8.2, bbox=bbox_props)
    
    # Colorbars geometry
    fig.canvas.draw()
    pos_f = ax_f.get_position()
    pos_g = ax_g.get_position()
    pos_h = ax_h.get_position()
    
    cbar_h_dim = 0.018
    cbar_y_maps = 0.065
    
    # Shared horizontal colorbar for (f) and (g)
    comb_w_fg = pos_g.x1 - pos_f.x0
    cbar_w_fg = 0.78 * comb_w_fg
    cbar_x_fg = (pos_f.x0 + pos_g.x1) / 2.0 - cbar_w_fg / 2.0
    
    cbar_ax_fg = fig.add_axes([cbar_x_fg, cbar_y_maps, cbar_w_fg, cbar_h_dim])
    cbar_fg = fig.colorbar(mesh_f, cax=cbar_ax_fg, orientation='horizontal',
                           ticks=[-0.03, -0.015, 0, 0.015, 0.03])
    cbar_fg.set_label('Mean signed increment [m³ m⁻³]', fontsize=9.2, labelpad=3.5)
    cbar_fg.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Separate horizontal colorbar for (h) below panel (h)
    cbar_w_h = 0.82 * (pos_h.x1 - pos_h.x0)
    cbar_x_h = (pos_h.x0 + pos_h.x1) / 2.0 - cbar_w_h / 2.0
    
    cbar_ax_h = fig.add_axes([cbar_x_h, cbar_y_maps, cbar_w_h, cbar_h_dim])
    cbar_h = fig.colorbar(mesh_h, cax=cbar_ax_h, orientation='horizontal',
                         ticks=[-0.03, -0.015, 0, 0.015, 0.03])
    cbar_h.set_label('NoCDF − CDF increment [m³ m⁻³]', fontsize=9.2, labelpad=3.5)
    cbar_h.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Save standard publication figures (high-resolution PNG + vector PDF)
    png_path = out_dir / 'Fig3_e_h_matched_updates.png'
    pdf_path = out_dir / 'Fig3_e_h_matched_updates.pdf'
    
    fig.savefig(png_path, dpi=500, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {png_path} (500 DPI) and {pdf_path}")

def main():
    root = get_project_root()
    out_dir = Path(os.environ.get('SEC31_OUT_DIR', root / 'figures' / 'manuscript' / 'section_3_1'))
    print(f"Project root: {root}")
    print(f"Output directory: {out_dir}")
    
    make_fig3_a_d(out_dir)
    make_fig3_e_h(out_dir)
    print("All Section 3.1 figures plotted successfully.")

if __name__ == "__main__":
    main()
