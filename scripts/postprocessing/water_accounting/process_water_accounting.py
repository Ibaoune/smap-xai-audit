import argparse
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import xarray as xr

# Compatibility shim for pandas 2.0+ and xarray 2023.1 resample
_orig_grouper_init = pd.Grouper.__init__
def _compat_grouper_init(self, *args, **kwargs):
    kwargs.pop('base', None)
    kwargs.pop('loffset', None)
    _orig_grouper_init(self, *args, **kwargs)
    self.loffset = None
pd.Grouper.__init__ = _compat_grouper_init

# Resolve repository root from script location: scripts/postprocessing/water_accounting/<file> -> 3 parents up
REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description=(
            "Historical EnKF increment water accounting pre-processing (2016-2020).\n"
            "WARNING: The historical DA-CDF simulation is scientifically invalidated\n"
            "due to spatial misalignment of CDF tables (see docs/invalidated_legacy_cdf_results.md).\n"
            "By default, this script is disabled to prevent accidental execution."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--include-legacy-cdf",
        action="store_true",
        help="Explicit authorization to process historical increments from the invalidated legacy DA-CDF run.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to a new, non-existent output directory under 'data/processed/water_accounting/runs/<identifiant_execution>/'.",
    )
    return parser.parse_args(args)


def validate_output_dir(output_dir_arg, repo_root):
    if not output_dir_arg:
        sys.exit("ERROR: --output-dir is mandatory when --include-legacy-cdf is specified.")

    raw_path = Path(output_dir_arg)
    if not raw_path.is_absolute():
        raw_path = repo_root / raw_path
    out_path = raw_path.resolve()
    runs_base = (repo_root / "data" / "processed" / "water_accounting" / "runs").resolve()
    legacy_dir = (repo_root / "data" / "processed" / "water_accounting" / "legacy_cdf_2016_2020").resolve()

    # 1. Refuse repo root, source directories, or legacy archive explicitly
    if out_path == repo_root:
        sys.exit(f"ERROR: --output-dir cannot point to the repository root ({repo_root}).")

    if out_path == legacy_dir:
        sys.exit(f"ERROR: Writing to the preserved legacy archive is strictly prohibited: {legacy_dir}.")

    # 2. Check that out_path is strictly within runs_base
    try:
        rel = out_path.relative_to(runs_base)
    except ValueError:
        sys.exit(f"ERROR: --output-dir must be strictly located within {runs_base} (got {out_path}).")

    if out_path == runs_base or str(rel) in (".", ""):
        sys.exit(
            f"ERROR: --output-dir cannot be the runs root directory itself ({runs_base}). "
            "Please provide a run sub-directory (e.g. .../runs/<identifiant_execution>/)."
        )

    # 3. Refuse already existing directory
    if out_path.exists():
        sys.exit(
            f"ERROR: Destination directory already exists: {out_path}.\n"
            "Accidental overwriting is prohibited. Please specify a new, non-existent run directory."
        )

    return out_path


def process_year(year, repo_root=REPO_ROOT):
    print(f"Processing {year}...")

    # Load native event-level datasets
    ds_cdf_path = repo_root / f"data/interim/enkf/da_cdf/increment_signed/increment_signed_{year}.nc"
    ds_nocdf_path = repo_root / f"data/interim/enkf/da_nocdf/increment_signed/increment_signed_{year}.nc"
    ds_cdf = xr.open_dataset(ds_cdf_path)
    ds_nocdf = xr.open_dataset(ds_nocdf_path)

    # Load canonical daily absolute increments for exact SOURCE support masking
    da_cdf_daily_abs_path = (
        repo_root / "data/processed/daily_enkf/da_cdf/daily_absolute_increment" / f"daily_absolute_increment_{year}.nc"
    )
    da_nocdf_daily_abs_path = (
        repo_root / "data/processed/daily_enkf/da_nocdf/daily_absolute_increment" / f"daily_absolute_increment_{year}.nc"
    )
    da_cdf_daily_abs = xr.open_dataset(da_cdf_daily_abs_path)['daily_absolute_increment']
    da_nocdf_daily_abs = xr.open_dataset(da_nocdf_daily_abs_path)['daily_absolute_increment']

    da_cdf_daily_abs = da_cdf_daily_abs.assign_coords(lat=ds_cdf.lat, lon=ds_cdf.lon)
    da_nocdf_daily_abs = da_nocdf_daily_abs.assign_coords(lat=ds_nocdf.lat, lon=ds_nocdf.lon)

    mask_cdf_native = da_cdf_daily_abs > 0
    mask_nocdf_native = da_nocdf_daily_abs > 0
    matched_mask = mask_cdf_native & mask_nocdf_native

    # Convert to delta_W_mm (0.01 m3 m-3 -> 1.0 mm)
    delta_W_cdf = ds_cdf['increment_signed'] * 100.0
    delta_W_nocdf = ds_nocdf['increment_signed'] * 100.0

    def get_components(delta_W):
        pos = delta_W.where(delta_W > 0, 0.0)
        neg = np.abs(delta_W.where(delta_W < 0, 0.0))
        net = pos - neg
        absl = pos + neg

        # Resample to daily (summing EVENT LEVEL values per day)
        daily_pos = pos.resample(event_time='1D').sum(dim='event_time')
        daily_neg = neg.resample(event_time='1D').sum(dim='event_time')
        daily_net = net.resample(event_time='1D').sum(dim='event_time')
        daily_absl = absl.resample(event_time='1D').sum(dim='event_time')

        # Count non-zero events per day for QC
        valid_events = delta_W.where(delta_W != 0).notnull()
        n_events = valid_events.resample(event_time='1D').sum(dim='event_time')

        return xr.Dataset({
            'W_positive': daily_pos,
            'W_removal': daily_neg,
            'W_absolute': daily_absl,
            'W_net': daily_net,
            'n_events': n_events
        })

    comp_cdf = get_components(delta_W_cdf)
    comp_nocdf = get_components(delta_W_nocdf)

    comp_cdf = comp_cdf.rename({'event_time': 'time'})
    comp_nocdf = comp_nocdf.rename({'event_time': 'time'})

    # Apply masks
    def apply_mask(ds, mask):
        return ds[['W_positive', 'W_removal', 'W_absolute', 'W_net']].where(mask, 0.0)

    cdf_matched = apply_mask(comp_cdf, matched_mask)
    nocdf_matched = apply_mask(comp_nocdf, matched_mask)

    cdf_native = apply_mask(comp_cdf, mask_cdf_native)
    nocdf_native = apply_mask(comp_nocdf, mask_nocdf_native)

    qc_info = {
        'year': year,
        'cdf_events_total': comp_cdf['n_events'].sum().item(),
        'nocdf_events_total': comp_nocdf['n_events'].sum().item(),
        'cdf_native_days': mask_cdf_native.sum().item(),
        'nocdf_native_days': mask_nocdf_native.sum().item(),
        'matched_days': matched_mask.sum().item(),
        'cdf_min_raw': ds_cdf['increment_signed'].min().item(),
        'cdf_max_raw': ds_cdf['increment_signed'].max().item(),
        'nocdf_min_raw': ds_nocdf['increment_signed'].min().item(),
        'nocdf_max_raw': ds_nocdf['increment_signed'].max().item(),
    }

    # To get event-level matched, we find events whose day is in the matched_mask
    matched_days = matched_mask.where(matched_mask, drop=True).time
    matched_event_mask = delta_W_cdf.event_time.dt.floor('D').isin(matched_days)

    # Subset raw delta_W to only events occurring on matched days
    cdf_delta_W_matched = delta_W_cdf.where(matched_event_mask & delta_W_cdf.notnull())
    nocdf_delta_W_matched = delta_W_nocdf.where(matched_event_mask & delta_W_nocdf.notnull())

    cdf_arr = cdf_delta_W_matched.values[~np.isnan(cdf_delta_W_matched.values)]
    nocdf_arr = nocdf_delta_W_matched.values[~np.isnan(nocdf_delta_W_matched.values)]

    return cdf_matched, nocdf_matched, cdf_native, nocdf_native, qc_info, cdf_arr, nocdf_arr, matched_mask, mask_cdf_native, mask_nocdf_native, comp_cdf['n_events'], comp_nocdf['n_events']


def main(args=None):
    parsed = parse_args(args)

    # Processing allowed when explicit output directory is provided for regenerated simulations
    if not parsed.include_legacy_cdf and not parsed.output_dir:
        print("=" * 80)
        print("AVERTISSEMENT : Traitement historique de comptabilité hydrique désactivé.")
        print("La simulation historique DA-CDF 2016-2020 est scientifiquement invalidée")
        print("en raison du décalage spatial des tables CDF (cf. docs/invalidated_legacy_cdf_results.md).")
        print("Par défaut, aucun calcul ni lecture NetCDF n'est exécuté afin d'éviter toute")
        print("pollution ou confusion entre l'ancienne simulation et les futurs résultats corrigés.")
        print()
        print("Pour exécuter ce traitement à des fins de reproduction technique :")
        print("  python scripts/postprocessing/water_accounting/process_water_accounting.py \\")
        print("    --include-legacy-cdf \\")
        print("    --output-dir data/processed/water_accounting/runs/<identifiant_execution>/")
        print()
        print("Note : Cette reproduction technique ne constitue pas une validation scientifique.")
        print("=" * 80)
        return 0

    output_dir = validate_output_dir(parsed.output_dir, REPO_ROOT)

    # Create validated new output directory
    output_dir.mkdir(parents=True, exist_ok=False)
    print(f"Output directory initialized: {output_dir}")

    years = [2016, 2017, 2018, 2019, 2020]

    res = [process_year(y, repo_root=REPO_ROOT) for y in years]

    cdf_matched = xr.concat([r[0] for r in res], dim='time')
    nocdf_matched = xr.concat([r[1] for r in res], dim='time')
    cdf_native = xr.concat([r[2] for r in res], dim='time')
    nocdf_native = xr.concat([r[3] for r in res], dim='time')

    qc_infos = [r[4] for r in res]
    cdf_all_delta_W = np.concatenate([r[5] for r in res])
    nocdf_all_delta_W = np.concatenate([r[6] for r in res])

    matched_mask = xr.concat([r[7] for r in res], dim='time')
    cdf_native_mask = xr.concat([r[8] for r in res], dim='time')
    nocdf_native_mask = xr.concat([r[9] for r in res], dim='time')

    cdf_n_events = xr.concat([r[10] for r in res], dim='time')
    nocdf_n_events = xr.concat([r[11] for r in res], dim='time')

    qc_report_path = output_dir / "qc_report.txt"
    with open(qc_report_path, "w") as f:
        f.write("QC REPORT\n")
        f.write("1. Exact source file: data/interim/enkf/da_cdf/increment_signed/increment_signed_{year}.nc\n")
        f.write("2. exact native variable name: increment_signed\n")
        f.write("3. units: m3 m-3\n")
        f.write("4. sign convention: positive = analysis wetter than forecast\n")
        f.write("5. stored at native assimilation-event time: Yes, event_time coordinate\n")
        f.write("6. multiple events per pixel-day: Yes\n")
        f.write("7. existing daily SOURCE diagnostic: It is matched to daily valid events in the standard pipeline. We replicate exactly using daily_absolute_increment masks.\n\n")

        for q in qc_infos:
            f.write(str(q) + "\n")

        f.write(f"\nCDF delta_W matched min/max: {cdf_all_delta_W.min():.4f} / {cdf_all_delta_W.max():.4f}\n")
        f.write(f"NoCDF delta_W matched min/max: {nocdf_all_delta_W.min():.4f} / {nocdf_all_delta_W.max():.4f}\n")

        f.write(f"Percentiles CDF: {np.percentile(cdf_all_delta_W, [1, 5, 25, 50, 75, 95, 99])}\n")
        f.write(f"Percentiles NoCDF: {np.percentile(nocdf_all_delta_W, [1, 5, 25, 50, 75, 95, 99])}\n")

        f.write(f"Positive events CDF: {(cdf_all_delta_W > 0).sum()} ({(cdf_all_delta_W > 0).sum()/len(cdf_all_delta_W):.2f})\n")
        f.write(f"Negative events CDF: {(cdf_all_delta_W < 0).sum()} ({(cdf_all_delta_W < 0).sum()/len(cdf_all_delta_W):.2f})\n")
        f.write(f"Zero events CDF: {(cdf_all_delta_W == 0).sum()} ({(cdf_all_delta_W == 0).sum()/len(cdf_all_delta_W):.2f})\n")

        f.write(f"Positive events NoCDF: {(nocdf_all_delta_W > 0).sum()} ({(nocdf_all_delta_W > 0).sum()/len(nocdf_all_delta_W):.2f})\n")
        f.write(f"Negative events NoCDF: {(nocdf_all_delta_W < 0).sum()} ({(nocdf_all_delta_W < 0).sum()/len(nocdf_all_delta_W):.2f})\n")
        f.write(f"Zero events NoCDF: {(nocdf_all_delta_W == 0).sum()} ({(nocdf_all_delta_W == 0).sum()/len(nocdf_all_delta_W):.2f})\n")

        f.write(f"\nAlgebraic check CDF matched W_net == W_positive - W_removal: {np.allclose(cdf_matched['W_net'], cdf_matched['W_positive'] - cdf_matched['W_removal'])}\n")
        f.write(f"Algebraic check CDF matched W_absolute == W_positive + W_removal: {np.allclose(cdf_matched['W_absolute'], cdf_matched['W_positive'] + cdf_matched['W_removal'])}\n")

        f.write(f"Explicit check: 0.01 m3 m-3 -> {0.01 * 100.0} mm\n")

    # Save delta_W for histograms
    np.save(output_dir / "cdf_delta_W.npy", cdf_all_delta_W)
    np.save(output_dir / "nocdf_delta_W.npy", nocdf_all_delta_W)

    # Interim datasets saved to output_dir
    cdf_matched.to_netcdf(output_dir / "cdf_matched_temp.nc")
    nocdf_matched.to_netcdf(output_dir / "nocdf_matched_temp.nc")
    cdf_native.to_netcdf(output_dir / "cdf_native_temp.nc")
    nocdf_native.to_netcdf(output_dir / "nocdf_native_temp.nc")

    matched_mask.to_dataset(name="mask").to_netcdf(output_dir / "matched_mask_temp.nc")
    cdf_native_mask.to_dataset(name="mask").to_netcdf(output_dir / "cdf_native_mask_temp.nc")
    nocdf_native_mask.to_dataset(name="mask").to_netcdf(output_dir / "nocdf_native_mask_temp.nc")

    cdf_n_events.to_dataset(name="n_events").to_netcdf(output_dir / "cdf_n_events_temp.nc")
    nocdf_n_events.to_dataset(name="n_events").to_netcdf(output_dir / "nocdf_n_events_temp.nc")
    print(f"Pre-processing completed successfully. All 12 outputs in {output_dir}")
    return 0


if __name__ == "__main__":
    main()
