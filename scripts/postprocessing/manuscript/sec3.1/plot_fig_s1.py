"""
Plotting Script for Supplementary Figure S1
===========================================
Sensitivity of Increment Distributions to Sample Matching

Panels:
  (a) CDF signed increment distribution (native vs matched sample)
  (b) NoCDF signed increment distribution (native vs matched sample)
  (c) Empirical cumulative distribution functions (ECDF) of absolute increments

Outputs:
  - figures/manuscript/section_3_1/FigS1_sample_matching_sensitivity.png (500 DPI)
  - figures/manuscript/section_3_1/FigS1_sample_matching_sensitivity.pdf
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
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
COLOR_NATIVE = '#333333'    # dark neutral for native dashed reference

def calc_ecdf(arr, max_val=0.07, num_points=1000):
    """Compute empirical CDF curve up to max_val."""
    sorted_arr = np.sort(arr)
    n = len(sorted_arr)
    y = np.arange(1, n + 1) / n
    # Downsample for smooth plotting and lightweight vector export
    idx = np.linspace(0, n - 1, num_points, dtype=int)
    return sorted_arr[idx], y[idx]

def main():
    root = get_project_root()
    data_dir = Path(os.environ.get('SEC31_OUT_DIR', root / 'figures' / 'manuscript' / 'section_3_1'))
    
    # Load 1D distributions
    npz_path = data_dir / 'FigS1_distributions.npz'
    if not npz_path.is_file():
        raise FileNotFoundError(f"Missing {npz_path}. Run process_supplementary_data.py first.")
        
    data = np.load(npz_path)
    cdf_nat = data['cdf_native']
    cdf_mat = data['cdf_matched']
    nocdf_nat = data['nocdf_native']
    nocdf_mat = data['nocdf_matched']
    
    # Compute stats for clean annotations
    m_abs_c_nat = float(np.mean(np.abs(cdf_nat)))
    m_abs_c_mat = float(np.mean(np.abs(cdf_mat)))
    m_abs_nc_nat = float(np.mean(np.abs(nocdf_nat)))
    m_abs_nc_mat = float(np.mean(np.abs(nocdf_mat)))
    
    fig = plt.figure(figsize=(12.0, 4.4))
    gs = GridSpec(1, 3, figure=fig, left=0.065, right=0.98, bottom=0.14, top=0.88, wspace=0.28)
    
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    
    # Common binning for signed distributions
    xlim_signed = [-0.060, 0.060]
    bins_signed = np.linspace(xlim_signed[0], xlim_signed[1], 121)
    
    # -------------------------------------------------------------------------
    # Panel (a): CDF Increment Distribution
    # -------------------------------------------------------------------------
    counts_c_nat, edges_c = np.histogram(cdf_nat, bins=bins_signed, density=True)
    counts_c_mat, _ = np.histogram(cdf_mat, bins=bins_signed, density=True)
    
    ax_a.step(edges_c[:-1], counts_c_nat, where='post', color=COLOR_NATIVE, 
              linestyle=':', lw=1.5, label='Native sample', zorder=2)
    ax_a.step(edges_c[:-1], counts_c_mat, where='post', color=COLOR_CDF, 
              linestyle='-', lw=1.7, label='Matched sample', zorder=3)
    ax_a.axvline(0, color='#444444', linestyle='-', lw=0.8, alpha=0.7, zorder=1)
    
    ax_a.set_title(r"$\bf{(a)}$ CDF increment distribution", pad=6.5, fontsize=10.5)
    ax_a.set_xlabel('Signed increment [m³ m⁻³]', fontsize=9.8, labelpad=4)
    ax_a.set_ylabel('Density', fontsize=9.8, labelpad=4)
    ax_a.set_xlim(xlim_signed)
    ax_a.set_ylim([0, 78])
    ax_a.set_xticks([-0.05, -0.025, 0, 0.025, 0.05])
    ax_a.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_a.legend(loc='center right', frameon=True, framealpha=0.92, edgecolor='#cccccc', fontsize=8.6)
    
    # Compact clean annotation
    annot_a = (f"Mean |increment|:\n"
               f"  Native:   {m_abs_c_nat:.5f}\n"
               f"  Matched: {m_abs_c_mat:.5f} m³ m⁻³")
    ax_a.text(0.04, 0.94, annot_a, transform=ax_a.transAxes, fontsize=8.4,
              verticalalignment='top',
              bbox=dict(facecolor='white', edgecolor='#d0d0d0', alpha=0.92, pad=3.0, boxstyle='round,pad=0.3'))
    
    # -------------------------------------------------------------------------
    # Panel (b): NoCDF Increment Distribution
    # -------------------------------------------------------------------------
    counts_nc_nat, edges_nc = np.histogram(nocdf_nat, bins=bins_signed, density=True)
    counts_nc_mat, _ = np.histogram(nocdf_mat, bins=bins_signed, density=True)
    
    ax_b.step(edges_nc[:-1], counts_nc_nat, where='post', color=COLOR_NATIVE, 
              linestyle=':', lw=1.5, label='Native sample', zorder=2)
    ax_b.step(edges_nc[:-1], counts_nc_mat, where='post', color=COLOR_NOCDF, 
              linestyle='-', lw=1.7, label='Matched sample', zorder=3)
    ax_b.axvline(0, color='#444444', linestyle='-', lw=0.8, alpha=0.7, zorder=1)
    
    ax_b.set_title(r"$\bf{(b)}$ NoCDF increment distribution", pad=6.5, fontsize=10.5)
    ax_b.set_xlabel('Signed increment [m³ m⁻³]', fontsize=9.8, labelpad=4)
    ax_b.set_ylabel('Density', fontsize=9.8, labelpad=4)
    ax_b.set_xlim(xlim_signed)
    ax_b.set_ylim([0, 68])
    ax_b.set_xticks([-0.05, -0.025, 0, 0.025, 0.05])
    ax_b.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_b.legend(loc='center right', frameon=True, framealpha=0.92, edgecolor='#cccccc', fontsize=8.6)
    
    # Compact clean annotation
    annot_b = (f"Mean |increment|:\n"
               f"  Native:   {m_abs_nc_nat:.5f}\n"
               f"  Matched: {m_abs_nc_mat:.5f} m³ m⁻³")
    ax_b.text(0.04, 0.94, annot_b, transform=ax_b.transAxes, fontsize=8.4,
              verticalalignment='top',
              bbox=dict(facecolor='white', edgecolor='#d0d0d0', alpha=0.92, pad=3.0, boxstyle='round,pad=0.3'))
    
    # -------------------------------------------------------------------------
    # Panel (c): ECDF of Absolute Increments
    # -------------------------------------------------------------------------
    x_c_nat, y_c_nat = calc_ecdf(np.abs(cdf_nat))
    x_c_mat, y_c_mat = calc_ecdf(np.abs(cdf_mat))
    x_nc_nat, y_nc_nat = calc_ecdf(np.abs(nocdf_nat))
    x_nc_mat, y_nc_mat = calc_ecdf(np.abs(nocdf_mat))
    
    ax_c.plot(x_c_nat, y_c_nat, color=COLOR_CDF, linestyle=':', lw=1.6, label='CDF Native')
    ax_c.plot(x_c_mat, y_c_mat, color=COLOR_CDF, linestyle='-', lw=1.7, label='CDF Matched')
    ax_c.plot(x_nc_nat, y_nc_nat, color=COLOR_NOCDF, linestyle=':', lw=1.6, label='NoCDF Native')
    ax_c.plot(x_nc_mat, y_nc_mat, color=COLOR_NOCDF, linestyle='-', lw=1.7, label='NoCDF Matched')
    
    ax_c.set_title(r"$\bf{(c)}$ ECDF of absolute increments", pad=6.5, fontsize=10.5)
    ax_c.set_xlabel('Absolute increment [m³ m⁻³]', fontsize=9.8, labelpad=4)
    ax_c.set_ylabel('Cumulative probability', fontsize=9.8, labelpad=4)
    ax_c.set_xlim([0.0, 0.070])
    ax_c.set_ylim([-0.02, 1.05])
    ax_c.set_xticks([0.00, 0.02, 0.04, 0.06])
    ax_c.grid(True, linestyle='-', alpha=0.20, color='#888888', linewidth=0.5)
    ax_c.legend(loc='lower right', frameon=True, framealpha=0.90, edgecolor='#cccccc', fontsize=8.6)
    
    # Standardize axes spines & tick markers across all panels
    for ax in [ax_a, ax_b, ax_c]:
        ax.tick_params(direction='out', length=3.0, width=0.75, color='#444444')
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')
            spine.set_linewidth(0.75)
            
    # Clean centered figure supertitle
    fig.suptitle("Sensitivity of increment distributions to sample matching", 
                 fontsize=11.6, weight='bold', y=0.975)
    
    png_path = data_dir / 'FigS1_sample_matching_sensitivity.png'
    pdf_path = data_dir / 'FigS1_sample_matching_sensitivity.pdf'
    
    fig.savefig(png_path, dpi=500, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated Figure S1: {png_path} (500 DPI) and {pdf_path}")

if __name__ == '__main__':
    main()
