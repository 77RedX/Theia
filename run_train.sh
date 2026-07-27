#!/bin/bash
#PBS -N Theia_train
#PBS -q gpu
#PBS -l select=1:ncpus=8:ngpus=1:mem=64gb
#PBS -j oe

# Go to the directory from which the job was submitted
cd "$PBS_O_WORKDIR"

# Activate the college-provided conda environment
source /apps/anaconda3/bin/activate deeplearning

# Disable Python output buffering
export PYTHONUNBUFFERED=1

# Safety prints
echo "============================================================"
echo "THEIA TRAINING"
echo "============================================================"
echo "Job started on:"
hostname
date
echo "Working directory:"
pwd
echo "============================================================"

# Log file
LOG="train_${PBS_JOBID}.log"

# Run training with live logging
stdbuf -oL -eL python -u pro_train.py 2>&1 | tee "$LOG"

# Preserve Python's exit status instead of tee's
EXIT_CODE=${PIPESTATUS[0]}

echo "============================================================"
echo "Job finished at:"
date
echo "Exit code: $EXIT_CODE"
echo "============================================================"

exit $EXIT_CODE