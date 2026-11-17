#!/bin/bash
#SBATCH --job-name=drydown_pt1
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/slurm/audits/drydown_pt1_%j.out
#SBATCH --error=logs/slurm/audits/drydown_pt1_%j.err

echo "=== Lancement du job Slurm Drydown Point 1 ==="
echo "Node: $(hostname)"
echo "Date: $(date)"
echo "CPUs: $SLURM_CPUS_PER_TASK"

cd /home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit

source /home/mohammad.elaabaribao/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit

python -u scripts/audits/drydown_point1.py

echo "=== Fin du job : $(date) ==="
