#!/bin/bash
emacs -geometry 150x48 `ls -rt slurm*.out|tail -1`
