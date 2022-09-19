#!/bin/bash
# Bíða eftir að verki á Elju ljúki, og ná síðan í úttaksskrá
#   'elja-get.sh 23322 &' bíður eftir verki með gefið verknúmer (jobid)
#   'elja-get.sh' notar fyrsta verknúmerið sem squeue skipun skilar

if [ "$1" == "" ]; then
  jobid=`ssh elja squeue -hujonasson | { read id _; echo $id; }`
else
  jobid=$1
fi
if [ -z "$jobid" ]; then
  echo "Engar keyrslur í gangi á Elju"
  exit
fi
echo waiting for job $jobid
while [ "$(ssh elja squeue -hj$jobid)" ]; do
  sleep 0.5
done
sleep 1.0
titill='"Hermun á Elju"'
texti='"Verki '$jobid' lokið"'
hljod='"default"'
osascript -e "display notification $texti with title $titill sound name $hljod"
scp elja:slurm-$jobid.out .