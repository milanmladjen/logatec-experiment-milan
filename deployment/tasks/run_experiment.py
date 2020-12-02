#!/usr/bin/python3

import subprocess

# Update Contiki-NG 
subprocess.run(["git", "pull"], cwd = "/root/logatec-experiment/contiki-ng")

# Get the IP address of the device
# IPADDR = ...


# Get the app name from environment variable
# APP_LOC = "/root/logatec-experiment/application" + APP_DIR
# APP = ${APP_DIR:3}
# print("Testing " + APP + " on device " + IPADDR)

# Compile the application
subprocess.run(["make", APP, "-j2"], cwd = APP_LOC)

# Flash the application to the VESNA device
subprocess.run(["make", APP + ".logatec"], cwd = APP_LOC)

# Start the serial_monitor 

# Start the testbed_controller_client

# Wait for incoming commands and log the output from VESNA devices