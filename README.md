# SMAP-XAI Audit

**Author:** M. El Aabaribaoune

## Purpose
The SMAP-XAI Audit framework is a rigorous research-software pipeline designed to evaluate SMAP soil moisture assimilation impacts using Explainable AI (XAI).

## Project Organization
The workflow follows a logical progression:
- **Block 1 — SOURCE**: Analyzes SMAP/EnKF source diagnostics (primary target: `daily_absolute_increment`, secondary: `daily_signed_increment`).
- **Block 2 — TRANSFER**: Examines downstream land model responses (`delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`).
- **Block 3 — VALUE**: Evaluates actual ET improvement against independent reference data (`value_ae`).

## High-Level Repository Structure
- [`docs/`](docs/): Scientific methodology, data contracts, and audit reports.
- [`scripts/`](scripts/): Executable workflow drivers for preprocessing and QC.
- [`src/`](src/): Reusable scientific source code and core logic.
- [`data/`](data/): Generated data lifecycle (interim and processed).
- [`reports/`](reports/): Generated diagnostics and QC visualizations.

## Environment

Create the Conda environment:

```bash
conda env create -f environment.yml
```
