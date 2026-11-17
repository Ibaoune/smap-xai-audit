#!/bin/bash
#SBATCH --job-name=rf03b_val
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --array=0-1
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/rf03b_value_%A_%a.out
#SBATCH --error=../../../../logs/slurm/modeling/random_forest/rf03b_value_%A_%a.err

exps=("da_cdf" "da_nocdf")
EXP=${exps[$SLURM_ARRAY_TASK_ID]}
CANDIDATE="RF_B"

cd ../../../../

echo "--- ENVIRONMENT PROVENANCE ---"
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Candidate: $CANDIDATE | Experiment: $EXP | Native Support"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block VALUE \
    --experiment $EXP \
    --target value_ae \
    --feature-set value_context_feature_set \
    --candidate $CANDIDATE \
    --fold fold_3 \
    --support-mode native_support \
    --workspace-root .
