#!/bin/bash
# Ná í úttaksskrár úr "array"-keyrslu
#   'elja-getx.sh mmmdd-HHMM nær í skrár úr keyrslu dags. dd.mmm kl. HH:MM
#   'elja-getx.sh
cluster=$1
shift
dir="~/voting/allt-thyskaland"
if test -z "$1"; then
  subdir=$(ssh $cluster "cd $dir && ls -d *[0-9][0-9]-[0-9][0-9]*"|tail -1)
else
  subdir=$1
fi
echo "Fetching results from directory $subdir"
mkdir -p $subdir
scp $cluster:$dir/$subdir/* $subdir
