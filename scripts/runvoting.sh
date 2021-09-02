#!/bin/bash
rootdir=$(dirname "$0")/..
echo Running in $rootdir
(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
