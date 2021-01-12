#!/usr/bin/python3

# First argument: last 3 digits of device IP address
# Second argument: application folder name 


import sys
import os
import logging
import time
from subprocess import Popen, PIPE

import serial_monitor
import file_logger
import zmq_client


# ----------------------------------------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------------------------------------
def obtain_info(cmd):
    # Return the requested info 

    if cmd == "END":
        # Exit application
        logging.debug("Received END command...exiting now!")
        force_exit()

    elif cmd == "STATE":
        data = " Stored " + str(serialLinesStored) + " lines."
        tip = LGTC_COMMAND

    elif cmd == "START_APP":
        data = ">"
        tip = VESNA_COMMAND

    elif cmd == "STOP_APP":
        data = "="
        tip = VESNA_COMMAND

    else:
        logging.warning("Unknown command: %s" % cmd)
        return LGTC_COMMAND, "Unknown cmd"

    #logging.info("Received " + cmd + " command.")
    return tip, data


def force_exit():
    monitor.close()
    #client.close() #TODO
    log.close()
    sys.exit(1)

# Soft exit also informs the server about this
def soft_exit(reason):

    info = ["SYS", "-1", reason]  

    client.send(info)

    if client.check_input(1000):
        if client.receive("DEALER") is True:    
            force_exit()
        # TODO: we might receive ACK for some other msg, not for this one ... 
    else:
        print("No ack from server...exiting now.")
        force_exit()



def main():
    # VARIABLES
    global serialLinesStored
    serialLinesStored = 0
    
    commandForVesna = []

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
    logging.info("Synced with server!")

    # 2) Compile the application
    logging.info("Compile the application ... ")

    """
    procCompile = Popen(["make", APP_NAME, "-j2"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procCompile.communicate()

    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)

    # 3) Flash the VESNA with app binary
    logging.info("Flash the app to VESNA .. ")

    procFlash = Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procFlash.communicate()

    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)
    """

    # TESTING PURPOSE - COMPILING TIME DELAY
    try:
        print("Device is \"compiling\" the code for VESNA...")
        time.sleep(10)
    except KeyboardInterrupt:
        print(" ")
    finally:
        print("Compiled application!")



    """
    # 4) Connect to VESNA serial port
    logging.info("Connect to VESNA serial port.")
    if not monitor.connect_to("ttyS2"):
        logging.error("Couldn't connect to VESNA...exiting now.")
        soft_exit("VesnaERR")

    # Sync with VESNA - start the serial_monitor but not the app #TODO add while(1) to VESNA main loop
    logging.info("Sync with VESNA.")
    if not monitor.sync_with_vesna():
        logging.error("Couldn't sync with VESNA...exiting now.")
        soft_exit("VesnaERR")

    # Inform VESNA about application time duration
    monitor.send_command("&" + str(APP_DURATION * 60))
    """

    # Inform server that LGTC is ready to start the app
    compiled_msg = ["UNI_DAT", "1", "COMPILED"]
    client.transmit(compiled_msg)

    if client.wait_ack("1", 1) is False:
        logging.error("No ack from server...exiting now.")
        force_exit()


    # ----------------------------------------------------------------------------------------
    # 
    # ----------------------------------------------------------------------------------------
    print(" ")
    logging.info("Start loging serial input and wait for incoming commands ..")
    print(" ")

    try:
        while True:
            # --------------------------------------------------------------------------------
            # Wait for incoming line from VESNA serial port and read it
            """
            if monitor.input_waiting():
                data = monitor.read_line()  
                
                # Store the line into file
                log.store_line(data)
                serialLinesStored += 1
            """
            # --------------------------------------------------------------------------------
            # If we received some command from the server, send it to VESNA and get response
            if commandForVesna:
                # Get requested info from VESNA
                #data = monitor.send_command(commandForVesna[2])

                # Form a reply
                response = commandForVesna
                response[2] = "Vesna says HI"

                # Send reply to the server
                client.transmit_async(response)

                # Log it to file as well
                log.store_lgtc_line("Got command: " + commandForVesna[2])
                log.store_lgtc_line(" Got response: " + data)

                commandForVesna = []


            # --------------------------------------------------------------------------------
            # If there is no data from VESNA to read and store, do other stuff
            else:

                # ----------------------------------------------------------------------------
                # Check if there is some incoming commad from the server
                inp = client.check_input(0)

                # If we received any message from the server
                if inp:
                    msg_type, msg_nbr, msg = client.receive_async(inp)

                    # If the message is command (else (if we received ack) we got back None)
                    if msg:
                        tip, info = obtain_info(msg)
                        
                        reply = [msg_type, msg_nbr, info]

                        # Some commands can be replied right away
                        if tip == LGTC_COMMAND:
                            client.transmit_async(reply)

                        # Store others and forward them to VESNA
                        else:
                            commandForVesna = reply

                # If there is still some message that didn't receive ACK back, re send it
                if (len(client.waitingForAck) != 0):
                    client.send_retry()    

            # TODO: Update status line in terminal.
            #print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
            #str(int(APP_DURATION)) + " min)", end="\r")

    except KeyboardInterrupt:
        print("\n Keyboard interrupt!.. Stop the app")







# ----------------------------------------------------------------------------------------
# GLOBAL VARIABLES 
# ----------------------------------------------------------------------------------------
# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://0.0.0.0:5562"
SUBSCR_HOSTNAME = "tcp://0.0.0.0:5561"

SERIAL_TIMEOUT = 2  # In seconds

DEFAULT_FILENAME = "node_results.txt"


LGTC_COMMAND = "1"
VESNA_COMMAND = "2"


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
    APP_DIR = "00_test"

# TODO: change when in container
# APP_PATH = "/root/logatec-experiment/application" + APP_DIR
APP_PATH = "/home/logatec/magistrska/logatec-experiment/applications/" + APP_DIR
APP_NAME = APP_DIR[3:]


print("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_ID)

# ----------------------------------------------------------------------------------------
# MODULE INITIALIZATION 
# ----------------------------------------------------------------------------------------
#logging.basicConfig(format="[%(module)15s: %(funcName)16s()] %(message)s", level=LOG_LEVEL) # To long module names
logging.basicConfig(format="[%(levelname)5s:%(funcName)16s()] %(message)s", level=LOG_LEVEL)

monitor = serial_monitor.serial_monitor(SERIAL_TIMEOUT)

log = file_logger.file_loger()

client = zmq_client.zmq_client(SUBSCR_HOSTNAME, ROUTER_HOSTNAME, LGTC_ID)

if __name__ == "__main__":
    main()


