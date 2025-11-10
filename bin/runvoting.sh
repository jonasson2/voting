#!/bin/bash
rootdir=${HOME}/drive/voting
echo Running in $rootdir
(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
