#!/bin/bash
# e.g. 'elja.sh 1000' for 1000 simulations (takes approx 30 sec.)
# use 'ssh elja squeue' to see queue information
rsync -a ~/voting/allt-thyskaland/ elja:voting/allt-thyskaland
rsync -a ~/voting/backend/ elja:voting/backend
if test -z "$1"; then nsim=500; else nsim=$1; fi
jobid=$(ssh elja "sbatch --export=ALL,nsim=$nsim thyskaland.sh" | sed 's/.* //')
echo $jobid
