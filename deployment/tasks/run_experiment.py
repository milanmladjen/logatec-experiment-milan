#!/usr/bin/python3

import subprocess
import sys

# Add path to import costum modules
sys.path.insert(0, "../../monitoring")
import serial_monitor
import file_logger
import zmq_client

"""
ser = serial_monitor.serial_monitor(10)
fileloger = file_logger.file_loger()
client = zmq_client.zmq_client("lgtc-3")"""


# Update Contiki-NG 
#subprocess.run(["git", "pull"], cwd = "/root/logatec-experiment/contiki-ng")

# Get the IP address of the device
# IPADDR = ...


# Get the app name from environment variable
# APP_LOC = "/root/logatec-experiment/application" + APP_DIR
# APP = ${APP_DIR:3}
# print("Testing " + APP + " on device " + IPADDR)

# Compile the application
#subprocess.run(["make", APP, "-j2"], cwd = APP_LOC)

# Flash the application to the VESNA device
#subprocess.run(["make", APP + ".logatec"], cwd = APP_LOC)

# Start the serial_monitor 

# Start the testbed_controller_client

# Wait for incoming commands and log the output from VESNA devices