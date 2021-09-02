#!/bin/bash
rootdir=$(dirname "$0")/..
echo
echo In vue files:
(cd $rootdir/vue-frontend/src && grep -s "$@" {.,components}/*.vue)

echo
echo In Python files
(cd $rootdir/backend && grep -s "$@" {.,methods,distributions}/*.py)

echo
echo In app.css
(cd $rootdir/vue-frontend/static/css && grep -s "$@" app.css)
