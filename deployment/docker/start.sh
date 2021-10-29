#!/bin/bash

if [ "$APP" = ""]; then
  echo "No application given!"
else
  if [ "$OPTION" = ""]; then
    echo "No option given!"
    OPTION = "node"
  fi

  cd deployment/tasks/
  pwd
  make "experiment_$OPTION"
fi