import os
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# Repository root and output directory for figures
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT_FIG_DIR = os.path.join(REPO_ROOT, 'figures', 'water_balance')

def get_area_weights(ds):
    # Fallback: latitude-based cos(latitude) weighting
    weights = np.cos(np.deg2rad(ds.lat))
    weights.name = "weights"
    return weights

def spatial_agg(ds):
    # Weighted mean over space
    weights = get_area_weights(ds)
    # Broadcast weights to ds spatial shape
    weights, _ = xr.broadcast(weights, ds.lon)
    # Only average over valid pixels (where ds is not null)
    # Note: the input datasets have 0.0 for masked values instead of NaN
    # We should average over the canonical valid land mask.
    # The valid land mask can be determined from elevation or just where daily_signed_increment != NaN natively.
    # Let's load static elevation to get valid land mask.
    elev = xr.open_dataset('data/processed/static/elevation/elevation.nc')['elevation']
    valid_land = elev.notnull()
    
    masked_ds = ds.where(valid_land)
    
    # Calculate weighted mean
    weighted = masked_ds.weighted(weights.where(valid_land).fillna(0))
    return weighted.mean(dim=["lat", "lon"])

def compute_percentiles(da):
    valid_data = da.values[~np.isnan(da.values)]
    if len(valid_data) == 0:
        return np.nan, np.nan, np.nan, np.nan
    return np.percentile(valid_data, [25, 50, 75, 50]) # return Q25, Q50, Q75, and we'll compute median separately or use this

def main():
    cdf = xr.open_dataset("cdf_matched_temp.nc")
    nocdf = xr.open_dataset("nocdf_matched_temp.nc")
    
    elev = xr.open_dataset('data/processed/static/elevation/elevation.nc')['elevation']
    valid_land = elev.notnull().assign_coords(lat=cdf.lat, lon=cdf.lon)
    
    cdf = cdf.where(valid_land)
    nocdf = nocdf.where(valid_land)
    
    # STEP 4: Temporal Aggregations
    # A. Monthly time series (2016-2020)
    cdf_monthly = cdf.resample(time='1MS').sum(dim='time')
    nocdf_monthly = nocdf.resample(time='1MS').sum(dim='time')
    
    cdf_monthly_spatial = spatial_agg(cdf_monthly)
    nocdf_monthly_spatial = spatial_agg(nocdf_monthly)
    
    df_monthly = pd.DataFrame({
        'time': cdf_monthly_spatial.time.values,
        'CDF_W_positive': cdf_monthly_spatial['W_positive'].values,
        'CDF_W_removal': cdf_monthly_spatial['W_removal'].values,
        'CDF_W_absolute': cdf_monthly_spatial['W_absolute'].values,
        'CDF_W_net': cdf_monthly_spatial['W_net'].values,
        'NoCDF_W_positive': nocdf_monthly_spatial['W_positive'].values,
        'NoCDF_W_removal': nocdf_monthly_spatial['W_removal'].values,
        'NoCDF_W_absolute': nocdf_monthly_spatial['W_absolute'].values,
        'NoCDF_W_net': nocdf_monthly_spatial['W_net'].values,
    })
    df_monthly.to_csv("analysis_water_accounting_monthly.csv", index=False)
    
    # B. Jan-Dec monthly climatology (mean of monthly sums)
    # We first group by month on the spatial aggregates
    cdf_clim = cdf_monthly_spatial.groupby('time.month').mean('time')
    nocdf_clim = nocdf_monthly_spatial.groupby('time.month').mean('time')
    
    # C. Seasonal
    cdf_seas = cdf_monthly_spatial.groupby('time.season').mean('time')
    nocdf_seas = nocdf_monthly_spatial.groupby('time.season').mean('time')
    
    df_seasonal = pd.DataFrame({
        'season': cdf_seas.season.values,
        'CDF_W_positive': cdf_seas['W_positive'].values,
        'CDF_W_absolute': cdf_seas['W_absolute'].values,
        'NoCDF_W_positive': nocdf_seas['W_positive'].values,
        'NoCDF_W_absolute': nocdf_seas['W_absolute'].values,
    })
    df_seasonal.to_csv("analysis_water_accounting_seasonal.csv", index=False)
    
    # D. Full-period 2016-2020 cumulative
    cdf_cum = cdf.sum(dim='time')
    nocdf_cum = nocdf.sum(dim='time')
    
    cdf_cum.to_netcdf("analysis_water_accounting_pixel_cumulative_cdf.nc")
    nocdf_cum.to_netcdf("analysis_water_accounting_pixel_cumulative_nocdf.nc")
    
    cdf_cum_spatial = spatial_agg(cdf_cum)
    nocdf_cum_spatial = spatial_agg(nocdf_cum)
    
    # Compute spatial percentiles for cumulative
    cdf_abs_vals = cdf_cum['W_absolute'].values[valid_land.values]
    nocdf_abs_vals = nocdf_cum['W_absolute'].values[valid_land.values]
    
    # Build summary table
    summary = []
    
    def get_row(exp, cum, cum_spatial, abs_vals):
        q25, q50, q75 = np.percentile(abs_vals, [25, 50, 75])
        return {
            'support': 'matched_support',
            'experiment': exp,
            'n_events': 'N/A', # can add later if needed
            'n_pixel_days': 'N/A',
            'area_weighted_positive_mm': cum_spatial['W_positive'].item(),
            'area_weighted_removal_mm': cum_spatial['W_removal'].item(),
            'area_weighted_absolute_mm': cum_spatial['W_absolute'].item(),
            'area_weighted_net_mm': cum_spatial['W_net'].item(),
            'spatial_median_absolute_mm': q50,
            'spatial_q25_absolute_mm': q25,
            'spatial_q75_absolute_mm': q75
        }
        
    summary.append(get_row('DA_CDF', cdf_cum, cdf_cum_spatial, cdf_abs_vals))
    summary.append(get_row('DA_NoCDF', nocdf_cum, nocdf_cum_spatial, nocdf_abs_vals))
    
    df_sum = pd.DataFrame(summary)
    df_sum.to_csv("analysis_water_accounting_summary.csv", index=False)
    
    # PLOTTING FIGURE S8
    mpl.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 12,
        'legend.fontsize': 9,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'font.family': 'sans-serif'
    })
    
    fig = plt.figure(figsize=(12, 10))
    
    # Panel (a) Jan-Dec monthly climatology of W_absolute
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(cdf_clim.month, cdf_clim['W_absolute'], label='CDF', color='#1f77b4', marker='o', lw=2)
    ax1.plot(nocdf_clim.month, nocdf_clim['W_absolute'], label='NoCDF', color='#ff7f0e', marker='o', lw=2)
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
    ax1.set_ylabel('Absolute adjustment [mm month$^{-1}$]')
    ax1.set_title('(a) Monthly Climatology (Absolute)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel (b) Jan-Dec monthly climatology of W_net
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.plot(cdf_clim.month, cdf_clim['W_net'], label='CDF', color='#1f77b4', marker='o', lw=2)
    ax2.plot(nocdf_clim.month, nocdf_clim['W_net'], label='NoCDF', color='#ff7f0e', marker='o', lw=2)
    ax2.axhline(0, color='k', linestyle='--', alpha=0.5)
    ax2.set_xticks(range(1, 13))
    ax2.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
    ax2.set_ylabel('Net adjustment [mm month$^{-1}$]')
    ax2.set_title('(b) Monthly Climatology (Net)')
    ax2.grid(True, alpha=0.3)
    
    # Panel (c) Map of cumulative difference
    ax3 = fig.add_subplot(2, 2, 3)
    diff = nocdf_cum['W_absolute'] - cdf_cum['W_absolute']
    diff_vals = diff.values[valid_land.values]
    p1 = np.percentile(diff_vals, 1)
    p99 = np.percentile(diff_vals, 99)
    vmax = max(abs(p1), abs(p99))
    
    print(f"Clipping map at +/- {vmax:.1f} mm (1st/99th percentiles)")
    
    c = ax3.pcolormesh(diff.lon, diff.lat, diff.where(valid_land), cmap='RdBu_r', 
                       vmin=-vmax, vmax=vmax)
    plt.colorbar(c, ax=ax3, orientation='horizontal', pad=0.08, label='Difference [mm] (NoCDF - CDF)')
    ax3.set_title('(c) Cumulative Absolute Difference (2016-2020)')
    
    # Panel (d) Grouped bars
    ax4 = fig.add_subplot(2, 2, 4)
    labels = ['W_positive', 'W_removal', 'W_absolute', 'W_net']
    cdf_bars = [cdf_cum_spatial[v].item() for v in labels]
    nocdf_bars = [nocdf_cum_spatial[v].item() for v in labels]
    
    x = np.arange(len(labels))
    width = 0.35
    
    ax4.bar(x - width/2, cdf_bars, width, label='CDF', color='#1f77b4')
    ax4.bar(x + width/2, nocdf_bars, width, label='NoCDF', color='#ff7f0e')
    
    ax4.axhline(0, color='k', linestyle='--', alpha=0.5)
    ax4.set_xticks(x)
    ax4.set_xticklabels(['Positive\n(Added)', 'Removal\n(Magnitude)', 'Absolute\n(Total Activity)', 'Net\n(Balance)'])
    ax4.set_ylabel('Cumulative adjustment [mm]')
    ax4.set_title('(d) Domain Cumulative (2016-2020)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    os.makedirs(OUT_FIG_DIR, exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_FIG_DIR, 'Figure_S8.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUT_FIG_DIR, 'Figure_S8.pdf'), bbox_inches='tight')
    
    # QC Plots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    def plot_map(ax, da, title, cmap, vmin=None, vmax=None):
        if vmin is None:
            vmax = np.percentile(np.abs(da.values[valid_land.values]), 98)
            vmin = 0 if 'absolute' in title.lower() else -vmax
            
        c = ax.pcolormesh(da.lon, da.lat, da.where(valid_land), cmap=cmap, vmin=vmin, vmax=vmax)
        plt.colorbar(c, ax=ax, orientation='horizontal', pad=0.08)
        ax.set_title(title)
        
    plot_map(axes[0,0], cdf_cum['W_absolute'], 'CDF Cum. W_absolute', 'viridis', vmin=0)
    plot_map(axes[0,1], nocdf_cum['W_absolute'], 'NoCDF Cum. W_absolute', 'viridis', vmin=0)
    
    vmax_net = np.percentile(np.abs(nocdf_cum['W_net'].values[valid_land.values]), 98)
    plot_map(axes[1,0], cdf_cum['W_net'], 'CDF Cum. W_net', 'RdBu_r', vmin=-vmax_net, vmax=vmax_net)
    plot_map(axes[1,1], nocdf_cum['W_net'], 'NoCDF Cum. W_net', 'RdBu_r', vmin=-vmax_net, vmax=vmax_net)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_FIG_DIR, 'QC_maps.png'))
    
if __name__ == "__main__":
    main()
