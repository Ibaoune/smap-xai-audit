#!/usr/bin/env python
import json
import pandas as pd
from pathlib import Path
import glob

def main():
    print("Auditing SOURCE XAI...")
    in_dir = Path("data/processed/modeling/xai/outputs/source")

    models = [
        ("da_cdf", "native"),
        ("da_nocdf", "native"),
        ("da_cdf", "matched"),
        ("da_nocdf", "matched")
    ]

    # Check execution
    for exp, sup in models:
        shap_file = in_dir / f"shap_{exp}_{sup}.parquet"
        assert shap_file.exists(), f"Missing {shap_file}"

        qc_file = in_dir / f"qc_{exp}_{sup}.json"
        assert qc_file.exists(), f"Missing {qc_file}"
        with open(qc_file, "r") as f:
            qc = json.load(f)

        assert qc["n_shap"] == 10000, f"Expected 10k SHAP rows, got {qc['n_shap']}"
        assert qc["max_abs_reconstruction_error"] < 1e-4, f"Additivity failed {qc['max_abs_reconstruction_error']}"

        perm_file = in_dir / f"permutation_{exp}_{sup}.json"
        assert perm_file.exists()
        with open(perm_file, "r") as f:
            perm = json.load(f)

        assert perm["cohort_size"] == 5000, "Expected 5k permutation rows"
        assert len(perm["features"]) > 0, "Empty feature list in permutation output"

    print("Execution outputs check: PASSED")

    # Matched keys check
    cdf = pd.read_parquet(in_dir / "shap_da_cdf_matched.parquet", columns=["date", "y_index", "x_index"])
    nocdf = pd.read_parquet(in_dir / "shap_da_nocdf_matched.parquet", columns=["date", "y_index", "x_index"])

    assert cdf.equals(nocdf), "Matched keys are not identical between CDF and NoCDF!"
    print("Matched support identical keys check: PASSED")

    # Summaries check
    assert (in_dir / "tidy_predictor_summary.csv").exists()
    assert (in_dir / "tidy_group_summary.csv").exists()
    assert (in_dir / "dependence_features.json").exists()
    with open(in_dir / "dependence_features.json") as f:
        dep_json = json.load(f)

    top4 = dep_json["top_4_dependence_features"]
    assert len(top4) == 4, "Expected top 4 predictors"

    # 2019 check
    assert pd.to_datetime(cdf["date"]).dt.year.eq(2019).all(), "Non-2019 data found"
    print("2019 isolation check: PASSED")

    print("\nSOURCE XAI Audit PASSED")

if __name__ == "__main__":
    main()
