#!/bin/bash
#PBS -N Theia_preprocess
#PBS -q workq
#PBS -l select=1:ncpus=8:mem=32gb
#PBS -j oe

cd $PBS_O_WORKDIR

source /apps/anaconda3/bin/activate deeplearning

echo "Preprocessing started on:"
hostname
date
pwd

python preprocess.py

echo "Finished at:"
date
