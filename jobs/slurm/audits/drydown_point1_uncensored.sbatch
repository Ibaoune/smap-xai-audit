#!/bin/bash
#SBATCH --job-name=drydown_uncens
#SBATCH --partition=himem
#SBATCH --qos=himem-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=reports/audits/drydown_point1_uncensored/drydown_uncensored_%j.out
#SBATCH --error=reports/audits/drydown_point1_uncensored/drydown_uncensored_%j.err

echo "Starting job on $(hostname) at $(date)"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit

cd /home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit
python3 scripts/audits/drydown_point1_uncensored.py

echo "Job finished at $(date)"
