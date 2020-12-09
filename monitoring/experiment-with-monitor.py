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
# FUNCTIONS
# ----------------------------------------------------------------------------------------
def obtain_info(cmd):
    # Return the requested info 

    data = "xyz"

    if cmd == "END":
        # Exit application
        logging.debug("Got END command...exiting now!")
        force_exit()

    elif cmd == "STATE":
        # Return the current state of the LGTC deivce
        logging.debug("Return the STATE of the device")
        data = "42!"

    elif cmd == "START_APP":
        # Send start command through serial_monitor.py
        logging.info("Start the application!")
        data ="App started"

    elif cmd == "STOP_APP":
        # Send stop command through serial_monitor.py
        logging.info("Stop the application!")
        data = "App stopped"

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



print("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_ID)

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

# 1) Sync with server (tell him we are online) with timeout of 10 seconds
if client.sync_with_server(10000) is False:
    logging.error("Couldn't synchronize with server..exiting now.")
    force_exit()

# 2) Compile the application
#subprocess.run(["make", APP, "-j2"], cwd = APP_LOC)


# TESTING PURPOSE - COMPILING TIME DELAY
try:
    time.sleep(10)
except KeyboardInterrupt:
    print(" ")
finally:
    print("Compiled application!")


# 3) Flash the VESNA with app binary
#subprocess.run(["make", APP + ".logatec"], cwd = APP_LOC)

# 4) Connect to VESNA serial port
logging.info("Connect to VESNA serial port")
#if not ser.connect_to("ttyS2"):
    #logging.error("Couldn't connect to VESNA...exiting now.")
    #soft_exit("VesnaERR")

# Sync with VESNA - start the serial_monitor but not the app #TODO add while(1) to VESNA main loop
logging.info("Sync with VESNA")
#if not ser.sync_with_vesna():
    #logging.error("Couldn't sync with VESNA...exiting now.")
    #soft_exit("VesnaERR")



# ----------------------------------------------------------------------------------------
# Inform server that LGTC is ready to start the app
# ----------------------------------------------------------------------------------------
compiled_msg = [b"UNI_DAT", b"1", b"COMPILED"]
client.transmit(compiled_msg)

if client.wait_ack("1", 1) is False:
    logging.error("No ack from server...exiting now.")
    force_exit()

print("-------")
logging.info("Starting the application!")
# ----------------------------------------------------------------------------------------
# Wait for incoming start command. We might also receive some other cmd in the mean time.
# ----------------------------------------------------------------------------------------
try:
    while True:
        # --------------------------------------------------------------------------------
        # Wait for incoming line from VESNA serial port and read it
        #data = monitor.read_line()
        time.sleep(1)
        print(".")

        #if data:
            # ----------------------------------------------------------------------------
            # Store the line into file
        #    log.store_line(data)
        #else:
        #    print("Serial timeout")

        # --------------------------------------------------------------------------------
        # Check if there is some incoming commad 
        # TODO: We can check only when we have some extra time? Ex. when there is timeout
        # on serial connection, not every round.
        inp = client.check_input(0)

        # If we received any message
        if inp:
            msg_type, msg_nbr, msg = client.receive_async(inp)

            # If the message is command (else we got back None)
            if msg:
                info = obtain_info(msg)

                # Form reply
                reply = [msg_type, msg_nbr, info]

                # Send it back to server
                client.transmit_async(reply)

        if (len(client.waitingForAck) != 0):
            client.send_retry()    


except KeyboardInterrupt:
    print("\n Keyboard interrupt!.. Stop the app")



