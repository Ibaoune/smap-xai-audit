import os
import hashlib
from pathlib import Path

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    print("Running RF-07D SUPPLEMENTARY FIGURE AUDIT...")
    
    main_figs = [f"Figure_{i}" for i in range(3, 9)]
    supp_figs = [f"Figure_S{i}" for i in range(1, 8)]
    
    for base in main_figs:
        matches = list(Path("figures/main").glob(f"{base}_*.pdf")) + list(Path("figures/main").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing main figure {base}"
        
    for base in supp_figs:
        matches = list(Path("figures/supplement").glob(f"{base}_*.pdf")) + list(Path("figures/supplement").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing supplement figure {base}"
        
    for script_file in ["scripts/figures/generate_final_figures.py", "scripts/figures/generate_supplements.py"]:
        with open(script_file, "r") as f:
            code = f.read()
            
        assert "Placeholder" not in code, f"Placeholder found in {script_file}"
        assert "Dummy" not in code, f"Dummy found in {script_file}"
        assert 'palette=PALETTE' in code, f"Inconsistent colors in {script_file}"
        assert "spatial cross-validation" not in code.lower(), f"S6 is called spatial CV in {script_file}"
        assert "Supplementary Figure S1" not in code, f"Empty axis printed in {script_file}"
        
    # Check config checksums
    assert get_md5("configs/modeling/models.yaml") == "6ad55edc495c89328e368546b317fd74"
    assert get_md5("configs/xai/rf_xai.yaml") == "703b2b28fc892f6648b3202b5aa376ef"
    assert get_md5("configs/xai/feature_groups.yaml") == "7816dfed4aecc15a177c6e09fb7e7b2c"
    assert get_md5("configs/modeling/splits.yaml") == "feb391f1cfe306ec36fa7c462b40b5f0"
    
    print("RF-07D SUPPLEMENTARY FIGURE AUDIT PASSED")

if __name__ == "__main__":
    main()
