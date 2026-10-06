#!/bin/bash
#SBATCH --job-name=rf06_eval
#SBATCH --output=logs/slurm/rf06_eval_%j.out
#SBATCH --error=logs/slurm/rf06_eval_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=128G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute

source ~/.bashrc
conda activate smap-xai-audit

echo "Starting 2020 evaluation..."
python scripts/modeling/06_evaluate_final_2020.py
echo "Done"
