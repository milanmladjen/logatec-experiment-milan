#!/usr/bin/python3

# First argument: last 3 digits of device IP address
# Second argument: application folder name 

import subprocess
import sys
import os
import logging
import time

import serial_monitor
import file_logger
import zmq_client

# ----------------------------------------------------------------------------------------
# GLOBAL VARIABLES 
# ----------------------------------------------------------------------------------------
# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://192.168.88.253:5562"
SUBSCR_HOSTNAME = "tcp://192.168.88.253:5561"

SERIAL_TIMEOUT = 1  # In seconds

DEFAULT_FILENAME = "node_results.txt"


# ENVIRONMENTAL VARIABLES
# Device id should be given as argument at start of the script
try:
    LGTC_ID = sys.argv[1]
    LGTC_ID = LGTC_ID.replace(" ", "")
    LGTC_ID = "LGTC" + LGTC_ID
except:
    print("No device name was given...going with default")
    LGTC_ID = "LGTCxy"

# Application name and duration should be defined as variable while running container
try:
    APP_DURATION = int(os.environ['APP_DURATION_MIN'])
except:
    print("No app duration was defined...going with default 60min")
    APP_DURATION = 60

try:
    APP_DIR = int(os.environ['APP_DIR'])
except:
    print("No application was given...aborting!")
    #sys.exit(1) TODO
    APP_DIR = "00_demo"

APP_PATH = "/root/logatec-experiment/application" + APP_DIR
APP_NAME = APP_DIR[3:]



print("Testing application " + APP_NAME + "for " + str(APP_DURATION) + " minutes on device " + LGTC_ID)

# ----------------------------------------------------------------------------------------
# MODULE INITIALIZATION 
# ----------------------------------------------------------------------------------------
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

ser = serial_monitor.serial_monitor(SERIAL_TIMEOUT)

log = file_logger.file_loger()

client = zmq_client.zmq_client(SUBSCR_HOSTNAME, ROUTER_HOSTNAME, LGTC_ID)


# ----------------------------------------------------------------------------------------
# PREPARE THE APP
# ----------------------------------------------------------------------------------------

# 0) Prepare log file   #TODO put in in __init__?
log.prepare_file(DEFAULT_FILENAME, LGTC_ID)
log.open_file()

# 1) Sync with server (tell him we are online) - start the client
if not client.sync_with_server():
    print("Couldn't synchronize with server..exiting now.")
    force_exit()

# 2) Compile the application
#subprocess.run(["make", APP, "-j2"], cwd = APP_LOC)

# 3) Flash the VESNA with app binary
#subprocess.run(["make", APP + ".logatec"], cwd = APP_LOC)

# 4) Connect to VESNA serial port
if not ser.connect_to("ttyS2"):
    print("Couldn't connect to VESNA...exiting now.")
    soft_exit("VesnaERR")

# Sync with VESNA - start the serial_monitor but not the app #TODO add while(1) to VESNA main loop
if not ser.sync_with_vesna():
    print("Couldn't sync with VESNA...exiting now.")
    soft_exit("VesnaERR")

# 5) Inform server that LGTC is ready to start the app
msg = ["UNI_DAT", 0, "COMPILED"]
client.send(msg)
if client.check_input(1000):
    if client.receive("DEALER") is not True:    
        print("No ack from server...exiting now.")
        force_exit()
    # TODO Problem might occur if we receive something else rather than ACK packet


# ----------------------------------------------------------------------------------------
# Wait for incoming start command
# ----------------------------------------------------------------------------------------
try:
    while True:
        poller = dict(client.poller.poll(0))

        if poller.get(client.subscriber) == 1:

            msg, nbr = client.receive("SUBSCRIBER")
            if msg == "START_APP"

                # Inform server that app has started
                client.send(["PUB_DAT", nbr, msg])

                break
except:
    print("Didn't want to wait for START command any more :(")

ser.send_command("START")
# ----------------------------------------------------------------------------------------
# Log the output from VESNA devices and wait for incoming commands
# ----------------------------------------------------------------------------------------

try:
    while True:
        # --------------------------------------------------------------------------------
        # Wait for incoming line from VESNA serial port and read it
        data = monitor.read_line()

        if data:
            log.store_line(data)
        else:
            print("Serial timeout")

        # --------------------------------------------------------------------------------
        # Check if any incoming command
        

        print(".")

except KeyboardInterrupt:
    print("\n Keyboard interrupt!.. Stop the app")



# ----------------------------------------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------------------------------------
def obtain_info(cmd):
    # Return the requested info 

    data = "42!"

    if cmd == "END":
        # Exit application
        logging.debug("Got END command...exiting now!")
        soft_exit("OK")

    elif cmd == "STATE":
        # Return the current state of the LGTC deivce
        logging.debug("Return the STATE of the device")

    elif cmd == "START_APP":
        # Send start command through serial_monitor.py
        logging.debug("Start the application!")

    elif cmd == "STOP_APP":
        # Send stop command through serial_monitor.py
        logging.debug("Stop the application!")

    else:
        logging.warning("Unknown command: %s" % cmd)

    return data


def force_exit():
    ser.close()
    client.close()
    log.close()
    sys.exit(1)

# Soft exit also informs the server about this
def soft_exit(reason):

    info = ["SYS", b"-1", reason]  

    client.send(info)

    if client.check_input(1000):
        if client.receive("DEALER") is True:    
            force_exit()
        # TODO: we might receive ACK for some other msg, not for this one ... 
    else:
        print("No ack from server...exiting now.")
        force_exit()

