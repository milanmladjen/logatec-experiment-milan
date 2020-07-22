#!/bin/bash

# Set test
if [ "$TEST" = "" ] || [ "$TARGET" = "" ]; then
  echo "Test missing!"
else
  if [[ "$TARGET": = *"agent"* ]]; then
    # Set serial device
    if [ -z "$VESNA_DEV" ]; then
      echo "Serial device missing!"
    fi
  fi
  cd "$TEST"
  pwd 
  make "$TARGET"
fi