#!/bin/bash
#SBATCH --job-name=rf_src_sp
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --array=0-4
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/source_spatial_cv_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/source_spatial_cv_%A_%a.err

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
    --block SOURCE \
    --experiment da_cdf \
    --target daily_absolute_increment \
    --feature-set context_only_feature_set \
    --candidate $CANDIDATE \
    --spatial-fold $SPATIAL_FOLD \
    --workspace-root .
