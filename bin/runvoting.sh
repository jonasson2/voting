#!/bin/bash
pwd=$(pwd)
dir=${pwd#$HOME/}
rootdir=$HOME/${dir%%/*}
echo Running in $rootdir
echo "(pwd=$pwd, dir=$dir)"
(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
