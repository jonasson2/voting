#!/bin/bash
pwd=$(pwd)
dir=${pwd#$HOME/}
rootdir=$HOME/${dir%%/*}

echo
echo IN JS FILES:
(cd $rootdir/vue-frontend/src && grep -s "$@" ./*.js)

echo
echo IN VUE FILES:
(cd $rootdir/vue-frontend/src && grep -s "$@" {.,components}/*.vue)

echo
echo IN PYTHON FILES:
(cd $rootdir/backend && grep -s "$@" {.,methods,distributions,newtest}/*.py)
(cd $rootdir/sensitivity && grep -s "$@" *.py)

echo
echo IN APP.CSS:
(cd $rootdir/vue-frontend/static/css && grep -s "$@" app.css)
