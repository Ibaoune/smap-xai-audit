# Preprocessing Directory

**Author:** M. El Aabaribaoune

## Purpose
Executable drivers for preparing the XAI data requirements.

## Workflow Progression
The preprocessing scripts follow a numbered conceptual progression:
1. Noah-MP variable preparation
2. EnKF diagnostics extraction
3. Static field harmonization
4. Transfer targets derivation
5. GLEAM harmonization (Step 30)
6. Canonical `value_ae` computation (Step 31)
7. Assimilation-support projection (Step 31b)

## Role in Workflow
These orchestrate the transformation of raw/native products into the standardized formats defined by the data contract. Reusable scientific logic is abstracted into `src/`.
