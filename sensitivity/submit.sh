#!/bin/sh
while read n; do
    echo $n
    ssh compute-0-$n "cd voting/sensitivity && python sim.py simres-$n" &
done < nodelist
