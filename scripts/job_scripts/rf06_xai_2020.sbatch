#!/bin/bash
#SBATCH --job-name=rf06_xai
#SBATCH --output=logs/slurm/rf06_xai_%j.out
#SBATCH --error=logs/slurm/rf06_xai_%j.err
#SBATCH --time=24:00:00
#SBATCH --mem=128G
#SBATCH --cpus-per-task=16
#SBATCH --partition=compute

source ~/.bashrc
conda activate smap-xai-audit

echo "Starting 2020 XAI generation..."
python scripts/xai/12_run_final_2020_xai.py
echo "Done"
