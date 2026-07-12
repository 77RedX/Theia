#!/bin/bash
#PBS -N Theia_train
#PBS -q gpu
#PBS -l select=1:ncpus=8:ngpus=1:mem=64gb
#PBS -j oe

# Go to the directory from which the job was submitted
cd $PBS_O_WORKDIR

# Activate the college-provided conda environment
source /apps/anaconda3/bin/activate deeplearning

# Safety prints (very useful for debugging)
echo "Job started on:"
hostname
date
echo "Working directory:"
pwd

# Run training
python train.py

echo "Job finished at:"
date

