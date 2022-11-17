#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
cd ~/voting/allt-thyskaland
time python run.py $param
