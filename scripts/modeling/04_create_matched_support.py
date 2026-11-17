#!/usr/bin/env python
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=str, default=".")
    args = parser.parse_args()

    out_dir = Path(args.workspace_root) / "data" / "processed" / "modeling" / "splits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "source_matched_support.parquet"

    print("Loading keys for SOURCE da_cdf...")
    cdf_dataset = ds.dataset(f"{args.workspace_root}/data/processed/modeling/source/da_cdf", format="parquet", ignore_prefixes=['.', '_', 'README.md'])
    cdf_keys = cdf_dataset.to_table(columns=["date", "y_index", "x_index"]).to_pandas()

    print("Loading keys for SOURCE da_nocdf...")
    nocdf_dataset = ds.dataset(f"{args.workspace_root}/data/processed/modeling/source/da_nocdf", format="parquet", ignore_prefixes=['.', '_', 'README.md'])
    nocdf_keys = nocdf_dataset.to_table(columns=["date", "y_index", "x_index"]).to_pandas()

    print(f"CDF rows: {len(cdf_keys)}")
    print(f"NoCDF rows: {len(nocdf_keys)}")

    print("Finding intersection...")
    matched = pd.merge(cdf_keys, nocdf_keys, on=["date", "y_index", "x_index"], how="inner")

    print(f"Matched rows: {len(matched)}")

    matched.to_parquet(out_file, index=False)
    print(f"Saved matched support keys to {out_file}")

if __name__ == "__main__":
    main()
