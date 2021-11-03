#!/bin/bash

if [ "$APP" = "" ]; then
  echo "No application given!"
else
  if [ "$OPTION" = "" ]; then
    echo "No option given!"
    OPTION="node"
  fi

  cd deployment/tasks/
  pwd
  make "experiment_$OPTION"
fi


# -------------- OLD VERSION -------------------
# Set test
#if [ "$TARGET" = "" ]; then
#  echo "Target missing!"
#else
#  if [[ "$TARGET": = *"agent"* ]]; then
#    # Set serial device
#    if [ -z "$VESNA_DEV" ]; then
#      echo "Serial device missing!"
#    fi
#  fi
#  cd deployment/tasks/
#  pwd 
#  make "$TARGET"
#fi