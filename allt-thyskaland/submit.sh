#!/usr/bin/env bash
# submit.sh <cluster> simulations <param>...
# fx:
#   'submit.sh elja 1000' for 1000 simulations (takes approx 30 sec.)
# or
#   'submit.sh elja 4x1000' for 1000 simulation on each of 4 nodes
# use 'ssh <cluster> squeue' to see queue information
cluster=$1
shift
nsim=$1
shift
copy.sh $cluster
dir="~/voting/allt-thyskaland"
subdir="."
array=""
if test -z $nsim; then
  param=64
elif [[ $nsim =~ x ]]; then
  subdir=$(date "+%b%d-%H%M")
  subdir=${subdir,,} # lowercase
  echo "Running in folder $subdir"
  ssh $cluster mkdir -p voting/allt-thyskaland/$subdir
  nnodes=${nsim%x*}
  nsim=${nsim#*x}
  array="--array 1-$nnodes"
  param="$nsim -a $subdir $*"
else
  param="$nsim $*"
fi
echo param="$param"
remote_command="sbatch --export=ALL,param=\"$param\" $array $dir/$cluster-batch.sh"
echo remote_command="$remote_command"
jobid=$(ssh $cluster "cd $dir/$subdir; $remote_command" | sed 's/.* //')
echo $jobid
