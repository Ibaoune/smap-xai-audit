"""
Plotting Script for Supplementary Figure S2
===========================================
Seasonal Variation of Matched-Sample Increment Differences

Panels:
  (a) DJF (NoCDF − CDF)
  (b) MAM (NoCDF − CDF)
  (c) JJA (NoCDF − CDF)
  (d) SON (NoCDF − CDF)

Outputs:
  - figures/manuscript/section_3_1/FigS2_seasonal_matched_differences.png (500 DPI)
  - figures/manuscript/section_3_1/FigS2_seasonal_matched_differences.pdf
"""

import os
from pathlib import Path
import copy
import xarray as xr
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
        ax.set_xticklabels(LON_LABELS, fontsize=8.6)
    else:
        ax.set_xticklabels([])
        
    if show_yticklabels:
        ax.set_yticklabels(LAT_LABELS, fontsize=8.6)
        ax.tick_params(axis='y', left=True)
    else:
        ax.set_yticklabels([])
        ax.tick_params(axis='y', left=False)
        
    ax.set_title(title, pad=6.0, fontsize=10.5, weight='normal')
    ax.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)

def main():
    root = get_project_root()
    data_dir = Path(os.environ.get('SEC31_OUT_DIR', root / 'figures' / 'manuscript' / 'section_3_1'))
    
    nc_path = data_dir / 'FigS2_source_data.nc'
    if not nc_path.is_file():
        raise FileNotFoundError(f"Missing {nc_path}. Run process_supplementary_data.py first.")
        
    ds = xr.open_dataset(nc_path)
    
    # Static elevation for background domain context
    elev_path = root / 'data' / 'processed' / 'static' / 'elevation' / 'elevation.nc'
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull()
    
    # Setup colormap: discrete RdBu_r centered on 0, with 12 classes (step 0.01 from -0.06 to +0.06)
    bounds = np.linspace(-0.06, 0.06, 13)
    cmap_base = plt.cm.get_cmap('RdBu_r', 12)
    cmap_disc = copy.copy(cmap_base)
    cmap_disc.set_bad(color='#dcdcdc')
    norm = BoundaryNorm(bounds, cmap_disc.N)
    
    # Create compact 1x4 layout
    fig = plt.figure(figsize=(13.2, 3.9))
    gs = GridSpec(1, 4, figure=fig, left=0.045, right=0.985, bottom=0.22, top=0.88, wspace=0.09)
    
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    ax_d = fig.add_subplot(gs[0, 3])
    
    panels = [
        (ax_a, ds['diff_djf'], r"$\bf{(a)}$ DJF (NoCDF − CDF)", True),
        (ax_b, ds['diff_mam'], r"$\bf{(b)}$ MAM (NoCDF − CDF)", False),
        (ax_c, ds['diff_jja'], r"$\bf{(c)}$ JJA (NoCDF − CDF)", False),
        (ax_d, ds['diff_son'], r"$\bf{(d)}$ SON (NoCDF − CDF)", False),
    ]
    
    mesh_list = []
    for ax, data_var, title, show_y in panels:
        # Background unassimilated / neutral mask
        ax.pcolormesh(elev.lon, elev.lat, valid_land.where(valid_land),
                      cmap=mpl.colors.ListedColormap(['#dcdcdc']),
                      shading='auto', zorder=1)
        # Seasonal matched difference
        mesh = ax.pcolormesh(data_var.lon, data_var.lat, data_var,
                             cmap=cmap_disc, norm=norm,
                             shading='auto', zorder=2)
        mesh_list.append(mesh)
        setup_map_ax(ax, title, show_yticklabels=show_y, show_xticklabels=True)
        
    # Shared horizontal colorbar at the bottom
    fig.canvas.draw()
    pos_a = ax_a.get_position()
    pos_d = ax_d.get_position()
    
    cbar_w = 0.58 * (pos_d.x1 - pos_a.x0)
    cbar_x = (pos_a.x0 + pos_d.x1) / 2.0 - cbar_w / 2.0
    cbar_y = pos_a.y0 - 0.145
    cbar_h = 0.040
    
    cbar_ax = fig.add_axes([cbar_x, cbar_y, cbar_w, cbar_h])
    cbar = fig.colorbar(mesh_list[0], cax=cbar_ax, orientation='horizontal',
                        ticks=[-0.06, -0.04, -0.02, 0.00, 0.02, 0.04, 0.06])
    cbar.set_label('Seasonal mean signed increment difference [m³ m⁻³]', fontsize=9.4, labelpad=3.5)
    cbar.ax.tick_params(labelsize=8.8, length=2.8, width=0.7)
    
    # Title
    fig.suptitle("Seasonal variation of matched-sample increment differences", 
                 fontsize=11.6, weight='bold', y=0.970)
    
    png_path = data_dir / 'FigS2_seasonal_matched_differences.png'
    pdf_path = data_dir / 'FigS2_seasonal_matched_differences.pdf'
    
    fig.savefig(png_path, dpi=500, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated Figure S2: {png_path} (500 DPI) and {pdf_path}")

if __name__ == '__main__':
    main()
