# Description

Experiment application are located in the corresponding folders. 

## Local test

To test them locally, run:
`make <app_name>.olimex -j9` \
`python3 serial_monitor.py -o results.txt -p ttyUSB0 -r`

## Testbed

To use CD service, please refer to `../deployment/README.md`. Note that:

* experiment application folder should have number indicator (XX_),
* the application script must have the same name as the folder name,
* if there is a separate script for a root node, add a suffix "-root" at the end of its name.


