import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.gridspec import GridSpec
import copy
from pathlib import Path

root = Path('/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit')
out_dir = root / 'figures' / 'manuscript' / 'section_3_1'

ds_ad = xr.open_dataset(out_dir / 'Fig3_a_d_source_data.nc')
df_monthly = pd.read_csv(out_dir / 'Fig3_a_d_source_data.csv')

# Truncated RdBu_r for panel c
colors_rdbu = plt.cm.RdBu_r(np.linspace(0.06, 0.94, 10))
cmap_diff = ListedColormap(colors_rdbu)
cmap_diff.set_bad(color='#dfdfdf')
diff_bounds = np.arange(-50, 51, 10)
norm_diff = BoundaryNorm(diff_bounds, ncolors=cmap_diff.N, clip=True)

for cmap_name in ['YlGnBu', 'Blues']:
    fig = plt.figure(figsize=(10.5, 8.4))
    
    gs = GridSpec(2, 2, figure=fig, 
                  left=0.08, right=0.96, bottom=0.155, top=0.955,
                  wspace=0.14, hspace=0.35,
                  width_ratios=[1, 1], height_ratios=[1, 1])
    
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])
    
    ax_d.set_box_aspect(6.4 / 9.2)
    
    # Colormap for (a) and (b)
    support_bounds = np.linspace(0, 100, 11)
    cmap_sup_base = plt.cm.get_cmap(cmap_name, 10)
    cmap_sup = copy.copy(cmap_sup_base)
    cmap_sup.set_bad(color='#dfdfdf')
    norm_sup = BoundaryNorm(support_bounds, ncolors=cmap_sup.N, clip=True)
    
    LON_TICKS = [-10, -8, -6, -4, -2]
    LON_LABELS = ['10°W', '8°W', '6°W', '4°W', '2°W']
    LAT_TICKS = [30, 32, 34, 36]
    LAT_LABELS = ['30°N', '32°N', '34°N', '36°N']
    
    def setup_map(ax, title, show_yticklabels=True, show_xticklabels=True):
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

    mesh_a = ax_a.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_cdf'], 
                             cmap=cmap_sup, norm=norm_sup, shading='auto')
    setup_map(ax_a, r"$\bf{(a)}$ CDF assimilation frequency", 
              show_yticklabels=True, show_xticklabels=False)
    
    mesh_b = ax_b.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_nocdf'], 
                             cmap=cmap_sup, norm=norm_sup, shading='auto')
    setup_map(ax_b, r"$\bf{(b)}$ NoCDF assimilation frequency", 
              show_yticklabels=False, show_xticklabels=False)
              
    mesh_c = ax_c.pcolormesh(ds_ad.lon, ds_ad.lat, ds_ad['freq_diff'], 
                             cmap=cmap_diff, norm=norm_diff, shading='auto')
    setup_map(ax_c, r"$\bf{(c)}$ Assimilation frequency difference: NoCDF − CDF", 
              show_yticklabels=True, show_xticklabels=True)
              
    # Panel d
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax_d.plot(range(1, 13), df_monthly['cdf_native_percent'].values, 
              label='CDF', color='#1f77b4', ls='-', lw=1.8, zorder=3)
    ax_d.plot(range(1, 13), df_monthly['nocdf_native_percent'].values, 
              label='NoCDF', color='#ff7f0e', ls='-', lw=1.8, zorder=3)
    ax_d.plot(range(1, 13), df_monthly['matched_support_percent'].values, 
              label='Joint CDF–NoCDF', color='#222222', ls='--', lw=1.5, dashes=(3.5, 2.5), zorder=4)
              
    ax_d.set_title(r"$\bf{(d)}$ Monthly assimilation frequency", pad=6.5, fontsize=10.8, weight='normal')
    ax_d.set_xticks(range(1, 13))
    ax_d.set_xticklabels(months, rotation=0, fontsize=8.8)
    ax_d.set_xlabel('Month', fontsize=9.8, labelpad=3.5)
    ax_d.set_ylabel('Assimilation frequency [%]', fontsize=9.8, labelpad=4)
    ax_d.set_ylim([0, 35])
    ax_d.set_yticks([0, 5, 10, 15, 20, 25, 30, 35])
    ax_d.grid(True, linestyle='-', alpha=0.18, color='#888888', linewidth=0.5)
    
    # Legend below panel (d)
    ax_d.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20),
                ncol=3, frameon=False, fontsize=8.5, columnspacing=1.2, handlelength=1.8)
    ax_d.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
    for spine in ax_d.spines.values():
        spine.set_edgecolor('#333333')
        spine.set_linewidth(0.75)
        
    fig.canvas.draw()
    pos_a = ax_a.get_position()
    pos_b = ax_b.get_position()
    pos_c = ax_c.get_position()
    pos_d = ax_d.get_position()
    
    # Shared horizontal colorbar for (a) and (b)
    comb_w_ab = pos_b.x1 - pos_a.x0
    cbar_w_ab = 0.72 * comb_w_ab
    cbar_x_ab = (pos_a.x0 + pos_b.x1) / 2.0 - cbar_w_ab / 2.0
    cbar_h = 0.018
    cbar_y_ab = 0.548
    
    cbar_ax_ab = fig.add_axes([cbar_x_ab, cbar_y_ab, cbar_w_ab, cbar_h])
    cbar_ab = fig.colorbar(mesh_a, cax=cbar_ax_ab, orientation='horizontal',
                           ticks=[0, 20, 40, 60, 80, 100])
    cbar_ab.set_label('Assimilation frequency [%]', fontsize=9.2, labelpad=3.5)
    cbar_ab.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    # Horizontal colorbar directly below panel (c)
    cbar_w_c = 0.82 * (pos_c.x1 - pos_c.x0)
    cbar_x_c = (pos_c.x0 + pos_c.x1) / 2.0 - cbar_w_c / 2.0
    cbar_y_c = 0.052
    
    cbar_ax_c = fig.add_axes([cbar_x_c, cbar_y_c, cbar_w_c, cbar_h])
    cbar_c = fig.colorbar(mesh_c, cax=cbar_ax_c, orientation='horizontal',
                         ticks=[-50, -25, 0, 25, 50])
    cbar_c.set_label('Frequency difference [percentage points]', fontsize=9.2, labelpad=3.5)
    cbar_c.ax.tick_params(labelsize=8.6, length=2.5, width=0.7)
    
    fig.savefig(out_dir / f'test_fig3_{cmap_name}.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved test_fig3_{cmap_name}.png")
