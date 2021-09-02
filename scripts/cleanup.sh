#!/bin/bash
# The function of this script is similar to that of "make clean"
rm -rf vue-frontend/{node_modules,package-lock.json,static/js/bundle.js}
rm -f backend/logs/*.log
rm -rf backend/{,methods,distributions}/__pycache__
