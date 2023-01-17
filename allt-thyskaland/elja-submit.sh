#!/bin/bash
# e.g. 'elja.sh 1000' for 1000 simulations (takes approx 30 sec.)
# use 'ssh elja squeue' to see queue information
elja-copy.sh
if test -z "$1"; then param="512 -n0"; else param="$*"; fi
jobid=$(ssh elja "sbatch --export=ALL,param=\"$param\" sbatch.sh" | sed 's/.* //')
echo $jobid
