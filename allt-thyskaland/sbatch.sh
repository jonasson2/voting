#!/bin/bash
#SBATCH --tasks-per-node=128
cd ~/voting/allt-thyskaland
time python run.py $param
