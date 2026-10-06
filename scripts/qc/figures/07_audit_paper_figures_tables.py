import os
import hashlib
from pathlib import Path

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    print("Running RF-07 PAPER FIGURE/TABLE AUDIT...")
    
    # Check figures
    main_figs = [f"Figure_{i}" for i in range(3, 9)]
    supp_figs = [f"Figure_S{i}" for i in range(1, 11)]
    
    for base in main_figs:
        # Check that png and pdf exist, but we used suffixes in the script
        # E.g., Figure_3_assimilation_diagnostics
        matches = list(Path("figures/main").glob(f"{base}_*.pdf")) + list(Path("figures/main").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing main figure {base}"
        
    for base in supp_figs:
        matches = list(Path("figures/supplement").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing supplement figure {base}"
        
    # Check tables
    assert Path("tables/main/Table_1.csv").exists(), "Missing Table 1"
    assert Path("tables/main/Table_2.csv").exists(), "Missing Table 2"
    for i in range(1, 9):
        assert Path(f"tables/supplement/Table_S{i}.csv").exists(), f"Missing Table S{i}"
        
    # Check config checksums
    assert get_md5("configs/modeling/models.yaml") == "6ad55edc495c89328e368546b317fd74"
    assert get_md5("configs/xai/rf_xai.yaml") == "703b2b28fc892f6648b3202b5aa376ef"
    assert get_md5("configs/xai/feature_groups.yaml") == "7816dfed4aecc15a177c6e09fb7e7b2c"
    assert get_md5("configs/modeling/splits.yaml") == "feb391f1cfe306ec36fa7c462b40b5f0"
    
    print("RF-07 PAPER FIGURE/TABLE AUDIT PASSED")

if __name__ == "__main__":
    main()
