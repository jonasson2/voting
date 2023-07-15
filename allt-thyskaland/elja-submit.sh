#!/opt/bin/bash
# fx:
#   'elja.sh 1000' for 1000 simulations (takes approx 30 sec.)
# or
#   'elja.sh 4x1000' for 1000 simulation on each of 4 nodes
# use 'ssh elja squeue' to see queue information
#elja-copy.sh
nsim=$1
shift
if [[ $nsim =~ x ]]; then
  subdir=$(date "+%b%d-%H%M")
  subdir=${subdir,,} # lowercase
  ssh elja mkdir -p voting/allt-thyskaland/$subdir
  nnodes=${nsim%x*}
  nsim=${nsim#*x}
  array="--array 1-$nnodes"
else
  if test -z "$1"; then
    param="64 -n0"
  else
    param="$nsim $*"
  fi  
  subdir="."
  array=""
fi
echo param="$param"
remote_command="sbatch --export=ALL,param=\"$param\" $array sbatch.sh"
echo remote_command="$remote_command"
jobid=$(ssh elja "cd voting/allt-thyskaland; $remote_command" | sed 's/.* //')
echo $jobid
