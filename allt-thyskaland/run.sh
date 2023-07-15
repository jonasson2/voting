#!/bin/bash
sbatch --export=ALL,param="$*" sbatch.sh
