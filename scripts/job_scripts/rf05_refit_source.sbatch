#!/bin/bash
#SBATCH --job-name=rf05_source
#SBATCH --output=logs/slurm/rf05_source_%A_%a.out
#SBATCH --error=logs/slurm/rf05_source_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute
#SBATCH --array=0-3

source ~/.bashrc
conda activate smap-xai-audit

EXP=(da_cdf da_nocdf da_cdf da_nocdf)
SUP=(native_support native_support matched_support matched_support)

e=${EXP[$SLURM_ARRAY_TASK_ID]}
s=${SUP[$SLURM_ARRAY_TASK_ID]}

echo "Starting SOURCE final refit: exp=$e sup=$s"
python scripts/modeling/05_refit_final_rf_2016_2019.py --block SOURCE --experiment $e --target daily_absolute_increment --support-mode $s
echo "Done"
