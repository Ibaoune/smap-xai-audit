#!/bin/bash
#SBATCH --job-name=rf03b_tr_cdf
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=39
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --array=0-3
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/rf03b_transfer_cdf_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/rf03b_transfer_cdf_%A_%a.err

targets=("delta_rzsm" "delta_et" "delta_surface_runoff" "delta_baseflow")
TARGET=${targets[$SLURM_ARRAY_TASK_ID]}
CANDIDATE="RF_A"

cd ../../../../

echo "--- ENVIRONMENT PROVENANCE ---"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Candidate: $CANDIDATE | Experiment: da_cdf | Target: $TARGET"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block TRANSFER \
    --experiment da_cdf \
    --target $TARGET \
    --feature-set source_context_feature_set \
    --candidate $CANDIDATE \
    --fold fold_3 \
    --support-mode native_support \
    --workspace-root .
