#!/bin/bash
#SBATCH --job-name=rf_transfer
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=28
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/transfer_%j.out

# Go to workspace root
cd ../../../../

source /home/mohammad.elaabaribao/.bashrc
eval "$(conda shell.bash hook)"
conda activate smap-xai-audit

echo "--- ENVIRONMENT PROVENANCE ---"
which python
python --version
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
python -c "
import sys, sklearn, joblib
print('Executable:', sys.executable)
print('Python:', sys.version)
print('sklearn:', sklearn.__version__)
print('joblib:', joblib.__version__)
"
echo "------------------------------"

python scripts/modeling/03_train_model.py \
    --model random_forest \
    --block TRANSFER \
    --experiment da_cdf \
    --target delta_rzsm \
    --feature-set source_context_feature_set \
    --workspace-root .
