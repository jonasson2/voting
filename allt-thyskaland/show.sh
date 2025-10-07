#!/bin/bash
# Sýna stöðu hermunar á þyrpingu
#   t.d. show.sh elja
if [ "$1" == "" ]; then
  cluster=elja
else
  cluster=$1
  shift
fi
dir=~/voting/allt-thyskaland
#HOST=$(hostname:%%[.-]*}
echo HOST=$HOST
echo cluster=$cluster
if [[ "$(hostname)HOST"==$cluster ]]; then
  cd $dir
  subdir=$(ls -d [a-z][a-z][a-z][0-9][0-9]-[0-9][0-9]*|tail -1)
  echo subdir=$subdir
  cd $subdir
  pwd
  file=$(ls|head -1)
  head -7 $file; echo ...; tail -8 $file
else
  echo using ssh
  ssh $cluster "cd $dir && show.sh $cluster"
fi
