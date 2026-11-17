# Baseline Job Submission

This directory contains the SLURM submission scripts for the Baseline step of the modeling phase.

## Architecture

1. `02_source.sbatch`: Array size 2. Computes temporal and spatial baselines for DA-CDF and DA-NoCDF on `daily_absolute_increment`.
2. `02_transfer.sbatch`: Array size 8. Computes temporal and spatial baselines across 2 experiments and 4 targets (`delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`).
3. `02_value.sbatch`: Array size 2. Computes temporal and spatial baselines for DA-CDF and DA-NoCDF on `value_ae`.
4. `02_source_matched_support.sbatch`: Re-computes source baselines strictly on matched support (the spatial/temporal intersection of CDF and NoCDF).
5. `02_merge.sbatch`: Collects all `.csv` outputs from `reports/modeling/baselines/raw/`, deduplicates them, and generates the canonical `reports/modeling/baselines/temporal_baseline_metrics.csv` and `spatial_baseline_metrics.csv`.
6. `02_audit.sbatch`: Runs final sanity checks on the merged outputs to ensure 2020 isolation, valid schemas, and valid metrics.

## Production Execution
**Confirmed SLURM Parameters:**
- Account: `empowermed-ahl6xm8o7mg-default-cpu`
- Partition: `compute`
- QOS: `default-cpu`

**Pilot Job:**
- Job ID: 7974942
- Status: COMPLETED

**Production Submission:**
The full deterministic matrix is submitted using:
```bash
bash jobs/slurm/modeling/02_baselines/submit_all.sh
```

## Submission
To submit all jobs with proper dependencies:
```bash
bash jobs/slurm/modeling/02_baselines/submit_all.sh
```
