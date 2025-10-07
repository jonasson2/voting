#!/bin/bash
cluster=$1
shift
rsync -a --exclude='*.out' ~/voting/allt-thyskaland/ $cluster:voting/allt-thyskaland
rsync -ar --exclude='*.out' ~/voting/backend/ $cluster:voting/backend
