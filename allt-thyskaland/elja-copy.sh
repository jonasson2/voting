#!/bin/bash
rsync -a --exclude='*.out' ~/voting/allt-thyskaland/ elja:voting/allt-thyskaland
rsync -ar --exclude='*.out' ~/voting/backend/ elja:voting/backend
