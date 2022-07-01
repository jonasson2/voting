#!/bin/bash

rootdir=${BASH_SOURCE%/*}
rootdir=${rootdir%/*}
echo Running in $rootdir

(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
