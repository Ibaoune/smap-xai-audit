#!/bin/bash
mkdir -p ../../../../logs/slurm/modeling/random_forest

echo "Submitting SOURCE pilot..."
sbatch 03_source_pilot.sbatch

echo "Submitting VALUE pilot..."
sbatch 03_value_pilot.sbatch

echo "--------------------------------------------------------"
echo "Wait for SOURCE and VALUE to complete successfully."
echo "Check completion/resource usage before submitting TRANSFER."
echo "To submit TRANSFER manually:"
echo "sbatch 03_transfer_pilot.sbatch"
