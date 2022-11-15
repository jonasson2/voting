#!/bin/bash
# e.g. 'elja.sh 1000' for 1000 simulations (takes approx 30 sec.)
# use 'ssh elja squeue' to see queue information
rsync -a --exclude='*.out' ~/voting/allt-thyskaland/ elja:voting/allt-thyskaland
rsync -a --exclude='*.out' ~/voting/backend/ elja:voting/backend
rsync -a ./sbatch.sh elja:~/sbatch.sh
if test -z "$1"; then param="512 -n128"; else param="$1"; fi
jobid=$(ssh elja "sbatch --export=ALL,param=\"$param\" sbatch.sh" | sed 's/.* //')
echo $jobid
