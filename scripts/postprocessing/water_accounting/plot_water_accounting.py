import argparse
import os
from pathlib import Path
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

# Repository root resolved from script location
REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description=(
            "Historical EnKF increment water accounting aggregation and plotting (2016-2020).\n"
            "WARNING: The historical DA-CDF simulation is scientifically invalidated\n"
            "due to spatial misalignment of CDF tables (see docs/invalidated_legacy_cdf_results.md).\n"
            "By default, this script is disabled to prevent accidental execution."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--include-legacy-cdf",
        action="store_true",
        help="Explicit authorization to process historical intermediates from the invalidated legacy DA-CDF run.",
    )
    parser.add_argument(
        "--run-dir",
        type=str,
        default=None,
        help="Path to an existing run directory under 'data/processed/water_accounting/runs/<run_id>/'.",
    )
    return parser.parse_args(args)


def validate_run_dir(run_dir_arg, repo_root):
    if not run_dir_arg:
        sys.exit("ERROR: --run-dir is mandatory when --include-legacy-cdf is specified.")

    raw_path = Path(run_dir_arg)
    if not raw_path.is_absolute():
        raw_path = repo_root / raw_path
    run_path = raw_path.resolve()

    runs_base = (repo_root / "data" / "processed" / "water_accounting" / "runs").resolve()
    legacy_dir = (repo_root / "data" / "processed" / "water_accounting" / "legacy_cdf_2016_2020").resolve()

    # 1. Refuse repo root, source directories, or legacy archive explicitly
    if run_path == repo_root:
        sys.exit(f"ERROR: --run-dir cannot point to the repository root ({repo_root}).")

    if run_path == legacy_dir:
        sys.exit(f"ERROR: Operating on the preserved legacy archive is strictly prohibited: {legacy_dir}.")

    # 2. Check that run_path is strictly within runs_base
    try:
        rel = run_path.relative_to(runs_base)
    except ValueError:
        sys.exit(f"ERROR: --run-dir must be strictly located within {runs_base} (got {run_path}).")

    if run_path == runs_base or str(rel) in (".", ""):
        sys.exit(
            f"ERROR: --run-dir cannot be the runs root directory itself ({runs_base}). "
            "Please provide a specific run sub-directory."
        )

    # 3. Refuse non-existent or non-directory run_path
    if not run_path.exists():
        sys.exit(f"ERROR: Specified run directory does not exist: {run_path}")
    if not run_path.is_dir():
        sys.exit(f"ERROR: Specified run path is not a directory: {run_path}")

    # 4. Check required inputs
    cdf_temp = run_path / "cdf_matched_temp.nc"
    nocdf_temp = run_path / "nocdf_matched_temp.nc"
    elev_path = repo_root / "data" / "processed" / "static" / "elevation" / "elevation.nc"

    missing_inputs = []
    if not cdf_temp.is_file():
        missing_inputs.append(str(cdf_temp))
    if not nocdf_temp.is_file():
        missing_inputs.append(str(nocdf_temp))
    if not elev_path.is_file():
        missing_inputs.append(str(elev_path))

    if missing_inputs:
        sys.exit(
            "ERROR: Required input file(s) missing:\n"
            + "\n".join(f"  - {f}" for f in missing_inputs)
        )

    # 5. Check that none of the 8 target outputs already exist (prevent overwrite)
    fig_dir = run_path / "figures"
    target_outputs = [
        run_path / "analysis_water_accounting_monthly.csv",
        run_path / "analysis_water_accounting_seasonal.csv",
        run_path / "analysis_water_accounting_summary.csv",
        run_path / "analysis_water_accounting_pixel_cumulative_cdf.nc",
        run_path / "analysis_water_accounting_pixel_cumulative_nocdf.nc",
        fig_dir / "Figure_S8.png",
        fig_dir / "Figure_S8.pdf",
        fig_dir / "QC_maps.png",
    ]

    existing_outputs = [p for p in target_outputs if p.exists()]
    if existing_outputs:
        sys.exit(
            "ERROR: Output file(s) already exist in the target run directory:\n"
            + "\n".join(f"  - {p}" for p in existing_outputs)
            + "\nAccidental overwriting is prohibited."
        )

    return run_path


def get_area_weights(ds):
    # Fallback: latitude-based cos(latitude) weighting
    weights = np.cos(np.deg2rad(ds.lat))
    weights.name = "weights"
    return weights


def spatial_agg(ds, repo_root=REPO_ROOT):
    # Weighted mean over space
    weights = get_area_weights(ds)
    # Broadcast weights to ds spatial shape
    weights, _ = xr.broadcast(weights, ds.lon)
    # Only average over valid pixels (where ds is not null)
    elev_path = repo_root / "data" / "processed" / "static" / "elevation" / "elevation.nc"
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull()

    masked_ds = ds.where(valid_land)

    # Calculate weighted mean
    weighted = masked_ds.weighted(weights.where(valid_land).fillna(0))
    return weighted.mean(dim=["lat", "lon"])


def compute_percentiles(da):
    valid_data = da.values[~np.isnan(da.values)]
    if len(valid_data) == 0:
        return np.nan, np.nan, np.nan, np.nan
    return np.percentile(valid_data, [25, 50, 75, 50])


def main(args=None):
    parsed = parse_args(args)

    if not parsed.include_legacy_cdf:
        if parsed.run_dir:
            sys.exit(
                "ERROR: Processing historical DA-CDF water accounting requires explicit authorization via --include-legacy-cdf."
            )
        print("=" * 80)
        print("AVERTISSEMENT : Visualisation historique de comptabilité hydrique désactivée.")
        print("La simulation historique DA-CDF 2016-2020 est scientifiquement invalidée")
        print("en raison du décalage spatial des tables CDF (cf. docs/invalidated_legacy_cdf_results.md).")
        print("Par défaut, aucun calcul ni rendu graphique n'est exécuté afin d'éviter toute")
        print("confusion entre l'ancienne simulation et les futurs résultats corrigés.")
        print()
        print("Pour exécuter ce traitement à des fins de reproduction technique :")
        print("  python scripts/postprocessing/water_accounting/plot_water_accounting.py \\")
        print("    --include-legacy-cdf \\")
        print("    --run-dir data/processed/water_accounting/runs/historical_repro_20261102/")
        print()
        print("Note : Cette reproduction technique ne constitue pas une validation scientifique.")
        print("=" * 80)
        return 0

    run_path = validate_run_dir(parsed.run_dir, REPO_ROOT)
    fig_dir = run_path / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    cdf = xr.open_dataset(run_path / "cdf_matched_temp.nc")
    nocdf = xr.open_dataset(run_path / "nocdf_matched_temp.nc")

    elev_path = REPO_ROOT / "data" / "processed" / "static" / "elevation" / "elevation.nc"
    elev = xr.open_dataset(elev_path)['elevation']
    valid_land = elev.notnull().assign_coords(lat=cdf.lat, lon=cdf.lon)

    cdf = cdf.where(valid_land)
    nocdf = nocdf.where(valid_land)

    # STEP 4: Temporal Aggregations
    # A. Monthly time series (2016-2020)
    cdf_monthly = cdf.resample(time='1MS').sum(dim='time')
    nocdf_monthly = nocdf.resample(time='1MS').sum(dim='time')

    cdf_monthly_spatial = spatial_agg(cdf_monthly, repo_root=REPO_ROOT)
    nocdf_monthly_spatial = spatial_agg(nocdf_monthly, repo_root=REPO_ROOT)

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
    df_monthly.to_csv(run_path / "analysis_water_accounting_monthly.csv", index=False)

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
    df_seasonal.to_csv(run_path / "analysis_water_accounting_seasonal.csv", index=False)

    # D. Full-period 2016-2020 cumulative
    cdf_cum = cdf.sum(dim='time')
    nocdf_cum = nocdf.sum(dim='time')

    cdf_cum.to_netcdf(run_path / "analysis_water_accounting_pixel_cumulative_cdf.nc")
    nocdf_cum.to_netcdf(run_path / "analysis_water_accounting_pixel_cumulative_nocdf.nc")

    cdf_cum_spatial = spatial_agg(cdf_cum, repo_root=REPO_ROOT)
    nocdf_cum_spatial = spatial_agg(nocdf_cum, repo_root=REPO_ROOT)

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
    df_sum.to_csv(run_path / "analysis_water_accounting_summary.csv", index=False)

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

    plt.tight_layout()
    plt.savefig(fig_dir / 'Figure_S8.png', dpi=300, bbox_inches='tight')
    plt.savefig(fig_dir / 'Figure_S8.pdf', bbox_inches='tight')

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
    plt.savefig(fig_dir / 'QC_maps.png')
    print(f"Aggregation and plotting completed successfully. Outputs written to {run_path}")
    return 0


if __name__ == "__main__":
    main()
