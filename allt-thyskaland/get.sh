#!/bin/bash
# Bíða eftir að verki á Elju ljúki, og ná síðan í úttaksskrá
#   'elja-get.sh 23322 &' bíður eftir verki með gefið verknúmer (jobid)
#   'elja-get.sh' notar fyrsta verknúmerið sem squeue skipun skilar
cluster=$1
shift
if [ "$1" == "" ]; then
  jobid=`ssh $cluster squeue -hu$USER | { read id _; echo $id; }`
else
  jobid=$1
fi
dir=voting/allt-thyskaland
if [ -z "$jobid" ]; then
  echo "Engar keyrslur í gangi á þyrpingu $cluster, næ í nýjustu skrá"
  file=$(ssh $cluster "cd $dir;ls -rt *.out"|tail -1)
  scp $cluster:$dir/$file .
  echo tail:
  tail $file
  exit
fi
echo waiting for job $jobid
while [ "$(ssh $cluster squeue -h | grep -w $jobid)" ]; do
  sleep 0.3
done
sleep 0.3
titill='"Hermun á Elju"'
texti='"Verki '$jobid' lokið"'
hljod='"default"'
osascript -e "display notification $texti with title $titill sound name $hljod"
scp $cluster:$dir/slurm-$jobid.out .
echo tail:
tail slurm-$jobid.out
