# Scripts de Lancement Batch SLURM (`scripts/job_scripts/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Scripts batch pour l'ordonnancement et l'exécution sur grappe de calcul haute performance (HPC) sous SLURM.

---

## 1. Objectif technique

Ce répertoire contient les scripts de soumission batch (`.sbatch`) permettant d'exécuter les phases intensives en calcul du pipeline sur les nœuds de calcul dédiés du cluster HPC :
- Réentraînement final des forêts aléatoires sur 2016–2019 (`rf05_refit_*.sbatch`).
- Évaluation sur l'année de test scellée 2020 (`rf06_evaluate_2020.sbatch`).
- Calculs intensifs de TreeSHAP et permutations sur GPU/CPU multicœur (`run_shap_bench.sbatch`, `run_value_xai.sbatch`, `rf06_xai_2020.sbatch`).

---

## 2. Configuration d'exécution SLURM

Chaque script spécifie les directives de ressources requises :
- **Partition cible :** `compute` (nœuds de calcul standard H-CEL).
- **Ressources CPU :** 8 à 10 cœurs alloués (`--cpus-per-task=10`).
- **Mémoire RAM :** 64 Go à 128 Go selon la taille du bloc (TRANSFER requiert le volume mémoire le plus élevé en raison de ses 23 millions de lignes).
- **Gestion des logs :** Redirection systématique de la sortie standard et d'erreur vers `logs/slurm/` sous le format `%x_%j.out` et `%x_%j.err`.

---

## 3. Guide de soumission type

```bash
# Exemple : Lancer le réentraînement final de SOURCE
sbatch scripts/job_scripts/rf05_refit_source.sbatch

# Exemple : Lancer l'évaluation finale scellée 2020
sbatch scripts/job_scripts/rf06_evaluate_2020.sbatch

# Suivre l'exécution d'un job
squeue -u $USER
sacct -j <JobID> --format=JobID,JobName,Partition,AllocCPUS,State,Elapsed
```

---

## 4. Précautions de sécurité et statut

- **Environnement Conda :** Les scripts activent automatiquement l'environnement `smap-xai-audit` ou `smap-xai`.
- **Règle de gel :** Aucun entraînement de modèle ni calcul SHAP pour la DA-CDF corrigée ne doit être soumis tant que la nouvelle logique scientifique n'a pas été formellement validée.
