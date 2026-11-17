#!/bin/bash
#SBATCH --job-name=smap_02_transfer
#SBATCH --array=0-7
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/slurm/modeling/baselines/transfer_%A_%a.out
#SBATCH --error=logs/slurm/modeling/baselines/transfer_%A_%a.err

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
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"
echo "Git SHA: $(git rev-parse HEAD 2>/dev/null || echo 'Unknown')"

source $(conda info --base)/etc/profile.d/conda.sh || true
conda activate smap-xai-audit
echo "Python version: $(python --version)"

EXPERIMENTS=("da_cdf" "da_nocdf")
TARGETS=("delta_rzsm" "delta_et" "delta_surface_runoff" "delta_baseflow")

EXP_IDX=$(($SLURM_ARRAY_TASK_ID / 4))
TARGET_IDX=$(($SLURM_ARRAY_TASK_ID % 4))

EXP=${EXPERIMENTS[$EXP_IDX]}
TARGET=${TARGETS[$TARGET_IDX]}

echo "Running TRANSFER block for experiment $EXP and target $TARGET"
CMD="python scripts/modeling/02_run_baselines.py --block transfer --experiment $EXP --target $TARGET --protocol all"
echo "Command: $CMD"

start_time=$(date +%s)
$CMD
end_time=$(date +%s)

echo "Finished in $((end_time - start_time)) seconds."
