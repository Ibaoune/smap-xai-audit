#!/usr/bin/env python
import sys
from smap_xai.modeling.evaluation import load_baseline_metrics

def main():
    try:
        # Test 1: Native support should resolve to temporal metrics
        native_cdf = load_baseline_metrics("SOURCE", "da_cdf", "daily_absolute_increment", "monthly_train_median", support_mode="native_support")
        native_nocdf = load_baseline_metrics("SOURCE", "da_nocdf", "daily_absolute_increment", "monthly_train_median", support_mode="native_support")
        
        # Test 2: Matched support should resolve to matched metrics
        matched_cdf = load_baseline_metrics("SOURCE", "da_cdf", "daily_absolute_increment", "monthly_train_median", support_mode="matched_support")
        matched_nocdf = load_baseline_metrics("SOURCE", "da_nocdf", "daily_absolute_increment", "monthly_train_median", support_mode="matched_support")
        
        # Test 3: Assert they are different (native != matched)
        assert native_cdf["baseline_MAE"] != matched_cdf["baseline_MAE"], "Silent reuse of native CDF baseline for matched!"
        assert native_nocdf["baseline_MAE"] != matched_nocdf["baseline_MAE"], "Silent reuse of native NoCDF baseline for matched!"
        
        # Test 4: Assert matched resolves to exact known values from source_matched_support_metrics.csv
        # Known da_cdf: 0.009457439
        # Known da_nocdf: 0.009304297
        assert abs(matched_cdf["baseline_MAE"] - 0.009457439) < 1e-7, "Matched CDF baseline MAE mismatch"
        assert abs(matched_nocdf["baseline_MAE"] - 0.009304297) < 1e-7, "Matched NoCDF baseline MAE mismatch"
        
        # Test 5: Missing file or experiment raises error
        try:
            load_baseline_metrics("SOURCE", "unknown_exp", "daily_absolute_increment", "monthly_train_median", support_mode="matched_support")
            assert False, "Should have raised ValueError for missing experiment"
        except ValueError:
            pass

        print("Matched baseline resolver test PASSED.")
        sys.exit(0)
    except AssertionError as e:
        print(f"FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAILED with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
