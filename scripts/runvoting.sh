#!/bin/bash
rootdir=$(dirname "$0")/..
(cd $rootdir/vue-frontend; npm run build) && (cd $rootdir/backend; python web.py)
