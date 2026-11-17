#!/bin/bash
#SBATCH --job-name=rf_xai_value
#SBATCH --output=logs/slurm/xai_value_%A_%a.out
#SBATCH --error=logs/slurm/xai_value_%A_%a.err
#SBATCH --mem=96G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute
#SBATCH --array=0-1

source ~/.bashrc
conda activate smap-xai-audit

EXPS=(da_cdf da_nocdf)
e=${EXPS[$SLURM_ARRAY_TASK_ID]}

echo "Starting VALUE XAI: experiment=$e"
python scripts/xai/09_run_value_xai.py --experiment $e
echo "Done: experiment=$e"
