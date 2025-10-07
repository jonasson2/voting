#!/bin/bash
#SBATCH --partition=dp-cn
#SBATCH --tasks-per-node=24
#MODULES BEGIN pyproj
cd ~/voting/allt-thyskaland
time python run.py $param
#MODULES END
