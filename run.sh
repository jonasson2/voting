#!/bin/bash
(cd vue-frontend; npm run build) && (cd backend; python web.py)
