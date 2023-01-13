#!/bin/bash
rootdir=${BASH_SOURCE%/*}
rootdir=${rootdir%/*}

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
echo IN ALLT ÞÝSKALAND:
(cd $rootdir/allt-thyskaland && grep -s "$@" ./*.py ./matlab/*.m)

echo
echo IN APP.CSS:
(cd $rootdir/vue-frontend/static/css && grep -s "$@" app.css)
