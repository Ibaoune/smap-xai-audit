#!/bin/bash
#SBATCH --job-name=rf02_source
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-11
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/source_cv_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/source_cv_%A_%a.err

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
    --block SOURCE \
    --experiment da_cdf \
    --target daily_absolute_increment \
    --feature-set context_only_feature_set \
    --candidate $CANDIDATE \
    --fold $FOLD \
    --workspace-root .
