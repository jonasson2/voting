#!/bin/bash
pwd=$(pwd)
dir=${pwd#$HOME/}
rootdir=$HOME/${dir%%/*}
echo Running in $rootdir
(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
