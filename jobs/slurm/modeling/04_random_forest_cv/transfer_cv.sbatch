#!/bin/bash
#SBATCH --job-name=rf02_transfer
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --array=0-11
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/transfer_cv_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/transfer_cv_%A_%a.err

candidates=("RF_A" "RF_B" "RF_C" "RF_D")
folds=("fold_1" "fold_2" "fold_3")

CANDIDATE=${candidates[$((SLURM_ARRAY_TASK_ID / 3))]}
FOLD=${folds[$((SLURM_ARRAY_TASK_ID % 3))]}

cd ../../../../

echo "--- ENVIRONMENT PROVENANCE ---"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Candidate: $CANDIDATE | Fold: $FOLD"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block TRANSFER \
    --experiment da_cdf \
    --target delta_rzsm \
    --feature-set source_context_feature_set \
    --candidate $CANDIDATE \
    --fold $FOLD \
    --workspace-root .
