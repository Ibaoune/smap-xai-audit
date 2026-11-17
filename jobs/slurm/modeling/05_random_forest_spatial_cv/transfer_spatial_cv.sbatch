#!/bin/bash
#SBATCH --job-name=rf_tr_sp
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=39
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --array=0-4
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/transfer_spatial_cv_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/transfer_spatial_cv_%A_%a.err

folds=("spatial_0" "spatial_1" "spatial_2" "spatial_3" "spatial_4")
SPATIAL_FOLD=${folds[$SLURM_ARRAY_TASK_ID]}
CANDIDATE="RF_A"

cd ../../../../

echo "--- ENVIRONMENT PROVENANCE ---"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Candidate: $CANDIDATE | Spatial Fold: $SPATIAL_FOLD"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block TRANSFER \
    --experiment da_cdf \
    --target delta_rzsm \
    --feature-set source_context_feature_set \
    --candidate $CANDIDATE \
    --spatial-fold $SPATIAL_FOLD \
    --workspace-root .
