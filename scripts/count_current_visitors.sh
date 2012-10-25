#!/bin/bash

DATE=$(date --utc +"%Y-%m")
STAT_DIR="/home/ok/offeneskoeln/statistik"
VENV_NAME="webapp-venv"

cd ~/offeneskoeln

if [! -d $STAT_DIR ]
  then
    mkdir $STAT_DIR
fi

~/$VENV_NAME/bin/python scripts/count_current_visitors.py >> $STAT_DIR/visitors_$DATE.txt
