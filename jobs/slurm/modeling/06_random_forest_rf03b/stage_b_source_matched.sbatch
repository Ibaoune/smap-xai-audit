#!/bin/bash
#SBATCH --job-name=rf03b_src_mat
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --array=0-1
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/rf03b_source_matched_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/rf03b_source_matched_%A_%a.err

exps=("da_cdf" "da_nocdf")
EXP=${exps[$SLURM_ARRAY_TASK_ID]}
CANDIDATE="RF_A"

cd ../../../../

echo "--- ENVIRONMENT PROVENANCE ---"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Candidate: $CANDIDATE | Experiment: $EXP | Matched Support"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block SOURCE \
    --experiment $EXP \
    --target daily_absolute_increment \
    --feature-set context_only_feature_set \
    --candidate $CANDIDATE \
    --fold fold_3 \
    --support-mode matched_support \
    --workspace-root .
