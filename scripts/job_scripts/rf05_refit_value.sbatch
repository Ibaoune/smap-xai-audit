#!/bin/bash
#SBATCH --job-name=rf05_value
#SBATCH --output=logs/slurm/rf05_value_%A_%a.out
#SBATCH --error=logs/slurm/rf05_value_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --mem=96G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute
#SBATCH --array=0-1

source ~/.bashrc
conda activate smap-xai-audit

EXP=(da_cdf da_nocdf)
e=${EXP[$SLURM_ARRAY_TASK_ID]}

echo "Starting VALUE final refit: exp=$e"
python scripts/modeling/05_refit_final_rf_2016_2019.py --block VALUE --experiment $e --target value_ae --support-mode native_support
echo "Done"
