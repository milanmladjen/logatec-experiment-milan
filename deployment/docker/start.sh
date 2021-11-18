#!/bin/bash

if [ "$APP" = "" ]; then
  echo "No application given! Aborting!"
else

  if [ "$OPTION" = "" ]; then
    echo "Option param is missing ... going with default."
    OPTION="none"
  fi

  if [ "$APP_DUR" = "" ]; then
    echo "Application duration not defined ... going with default."
    export APP_DUR="10"
  fi

  cd /root/logatec-experiment/deployment/tasks/
  pwd
  make "experiment_$OPTION"
fi
