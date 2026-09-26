#!/bin/bash
#SBATCH --job-name=smap_02_merge
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/slurm/modeling/baselines/merge_%j.out
#SBATCH --error=logs/slurm/modeling/baselines/merge_%j.err

#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu

set -eo pipefail

PROJ_DIR="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
if [ ! -d "$PROJ_DIR" ]; then
    exit 1
fi
cd "$PROJ_DIR"

export PYTHONUNBUFFERED=1

echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "SLURM_JOB_ID: $SLURM_JOB_ID"
echo "Git SHA: $(git rev-parse HEAD 2>/dev/null || echo 'Unknown')"

source $(conda info --base)/etc/profile.d/conda.sh || true
conda activate smap-xai-audit
echo "Python version: $(python --version)"

echo "Merging baseline metrics..."
CMD="python scripts/modeling/02_merge_baselines.py"
echo "Command: $CMD"

start_time=$(date +%s)
$CMD
end_time=$(date +%s)

echo "Finished in $((end_time - start_time)) seconds."
