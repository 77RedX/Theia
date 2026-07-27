#!/bin/bash
#PBS -N Theia_debug
#PBS -q gpu
#PBS -l select=1:ncpus=8:ngpus=1:mem=64gb
#PBS -j oe

# Go to the submission directory
cd "$PBS_O_WORKDIR"

# Activate conda environment
source /apps/anaconda3/bin/activate deeplearning

# Disable Python buffering
export PYTHONUNBUFFERED=1

# Optional: make CUDA errors synchronous (uncomment only when debugging crashes)
# export CUDA_LAUNCH_BLOCKING=1

# Create a unique log file for this job
LOG="debug_${PBS_JOBID}.log"

echo "=========================================="
echo "Theia Debug Job"
echo "=========================================="
echo "Job ID            : $PBS_JOBID"
echo "Running on        : $(hostname)"
echo "Working Directory : $(pwd)"
echo "Started           : $(date)"
echo "Log File          : $LOG"
echo "=========================================="

# Run with unbuffered stdout/stderr and mirror output to log
stdbuf -oL -eL python -u profile_model.py 2>&1 | tee "$LOG"

STATUS=${PIPESTATUS[0]}

echo
echo "Finished : $(date)"
echo "Exit Code: $STATUS"

exit $STATUS