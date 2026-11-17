#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR/../../../..

echo "Submitting SMAP-XAI Baseline Jobs..."

# 1. Source array
SRC_JOB=$(sbatch --parsable $DIR/02_source.sbatch)
echo "Submitted SOURCE array: $SRC_JOB"

# 2. Transfer array
TRF_JOB=$(sbatch --parsable $DIR/02_transfer.sbatch)
echo "Submitted TRANSFER array: $TRF_JOB"

# 3. Value array
VAL_JOB=$(sbatch --parsable $DIR/02_value.sbatch)
echo "Submitted VALUE array: $VAL_JOB"

# 4. Source Matched array
MAT_JOB=$(sbatch --parsable $DIR/02_source_matched_support.sbatch)
echo "Submitted MATCHED SUPPORT: $MAT_JOB"

# 5. Merge (depends on all above)
MERGE_JOB=$(sbatch --parsable --dependency=afterok:$SRC_JOB:$TRF_JOB:$VAL_JOB:$MAT_JOB $DIR/02_merge.sbatch)
echo "Submitted MERGE job: $MERGE_JOB"

# 6. Audit (depends on merge)
AUDIT_JOB=$(sbatch --parsable --dependency=afterok:$MERGE_JOB $DIR/02_audit.sbatch)
echo "Submitted AUDIT job: $AUDIT_JOB"

echo "All jobs submitted successfully!"
