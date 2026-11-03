#!/bin/bash
# ==============================================================================
# Script Name   : aud05_reproduction.sbatch
# Author        : M. El Aabaribaoune (@um6p)
# Description   : Exécution de la reproduction numérique du bilan hydrique AUD-05
#                 (Open Loop, Contrôle DA-NoCDF, DA-Nowilt) sur nœud CPU.
#                 Intègre 62 jours de flux, les incréments EnKF et les restarts.
# Usage         : sbatch scripts/jobs/aud05_reproduction.sbatch
# ==============================================================================
#SBATCH --job-name=aud05_reproduction
#SBATCH --output=reports/aud05_reproduction/aud05_reproduction_%j.out
#SBATCH --error=reports/aud05_reproduction/aud05_reproduction_%j.err
#SBATCH --partition=compute
#SBATCH --account=empowermed-ahl6xm8o7mg-default-cpu
#SBATCH --qos=default-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00

set -eo pipefail

# 1. Positionnement strict à la racine du dépôt d'audit XAI
REPO_DIR="/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit"
cd "${REPO_DIR}"

# 2. Préparation du répertoire de sortie (couvert par .gitignore)
mkdir -p reports/aud05_reproduction

# 3. Activation de l'environnement Conda dédié
source ~/.bashrc
conda activate smap-xai-audit

# 4. Traces et métadonnées d'exécution
echo "================================================================================"
echo "Validation numérique AUD-05 : Reproduction du bilan hydrique Noah-MP / EnKF"
echo "Job SLURM ID : ${SLURM_JOB_ID:-standalone}"
echo "Nœud d'exéc. : $(hostname)"
echo "Date début   : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Interpréteur : $(which python3)"
echo "Dépôt XAI    : ${REPO_DIR}"
echo "================================================================================"

# 5. Exécution du calcul complet (lecture seule sur NoahMP_Morocco)
python3 -u scripts/audits/reproduce_aud05_water_balance.py \
    --output_csv reports/aud05_reproduction/aud05_water_balance.csv

EXIT_CODE=$?

echo "================================================================================"
echo "Date fin     : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Code retour  : ${EXIT_CODE}"
echo "================================================================================"

# 6. Duplication du journal d'exécution vers un nom standard stable
if [ -n "${SLURM_JOB_ID}" ] && [ -f "reports/aud05_reproduction/aud05_reproduction_${SLURM_JOB_ID}.out" ]; then
    cp "reports/aud05_reproduction/aud05_reproduction_${SLURM_JOB_ID}.out" "reports/aud05_reproduction/aud05_reproduction.log"
fi

exit ${EXIT_CODE}
