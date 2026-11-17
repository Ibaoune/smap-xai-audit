#!/bin/bash
#SBATCH --job-name=rf05_transfer
#SBATCH --output=logs/slurm/rf05_transfer_%A_%a.out
#SBATCH --error=logs/slurm/rf05_transfer_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --mem=96G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute
#SBATCH --array=0-7

source ~/.bashrc
conda activate smap-xai-audit

EXP=(da_cdf da_nocdf da_cdf da_nocdf da_cdf da_nocdf da_cdf da_nocdf)
TGT=(delta_rzsm delta_rzsm delta_et delta_et delta_surface_runoff delta_surface_runoff delta_baseflow delta_baseflow)

e=${EXP[$SLURM_ARRAY_TASK_ID]}
t=${TGT[$SLURM_ARRAY_TASK_ID]}

echo "Starting TRANSFER final refit: exp=$e tgt=$t"
python scripts/modeling/05_refit_final_rf_2016_2019.py --block TRANSFER --experiment $e --target $t --support-mode native_support
echo "Done"
