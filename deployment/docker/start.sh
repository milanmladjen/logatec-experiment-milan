#!/bin/bash

if [ "$APP" = "" ]; then
  echo "No application given! Aborting!"
else
  if [ "$OPTION" = "" ]; then
    echo "Option param is missing ... going with default."
    OPTION="none"
  fi

  if [ "$INSTANCE" = "" ]; then
    echo "Instance is missing ... going with default."
    export INSTANCE="tag"
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