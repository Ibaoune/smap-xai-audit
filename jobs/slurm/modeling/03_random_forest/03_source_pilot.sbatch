#!/bin/bash
#SBATCH --job-name=rf_source
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --partition=compute
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=../../../../logs/slurm/modeling/random_forest/source_%j.out

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
    --block SOURCE \
    --experiment da_cdf \
    --target daily_absolute_increment \
    --feature-set context_only_feature_set \
    --workspace-root .
