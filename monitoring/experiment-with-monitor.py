#!/usr/bin/python3

# First argument: last 3 digits of device IP address
# Second argument: application folder name 


import sys
import os
import logging
import time
from subprocess import Popen, PIPE

from lib import serial_monitor
from lib import file_logger
from lib import zmq_client



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

    # 1) Sync with broker (tell him we are online) with timeout of 10 seconds
    logging.info("Sync with broker ... ")
    client.transmit(["-1", "SYNC"])

    if client.wait_ack("-1", 10) is False:
        logging.error("Couldn't synchronize with broker..exiting now.")
        force_exit()
    

    # 2) Compile the application
    logging.info("Compile the application ... ")

    client.transmit(["-1", "COMPILING"])
    if client.wait_ack("-1", 2) is False:
        logging.error("No ack from broker...exiting now.")
        force_exit()

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


    # 4) Connect to VESNA serial port
    logging.info("Connect to VESNA serial port ....")
    if not monitor.connect_to("ttyS2"):
        logging.error("Couldn't connect to VESNA...exiting now.")
        soft_exit("VesnaERR")

    # 5) Sync with VESNA - start the serial_monitor but not the app #TODO add while(1) to VESNA main loop
    logging.info("Sync with VESNA ...")
    if not monitor.sync_with_vesna():
        logging.error("Couldn't sync with VESNA...exiting now.")
        soft_exit("VesnaERR")

    # Inform VESNA about application time duration
    monitor.send_command("&" + str(APP_DURATION * 60))

    # 6) Inform broker that LGTC is ready to start the app, timeout of 2 seconds
    client.transmit(["-1", "ONLINE"])

    if client.wait_ack("-1", 2) is False:
        logging.error("No ack from broker...exiting now.")
        force_exit()

    

    # ----------------------------------------------------------------------------------------
    # Wait for START command from frontend
    # ----------------------------------------------------------------------------------------
    try:
        while True:
            # Check input queue
            inp = client.check_input(10000)

            # If we received any message from the broker
            if inp:
                msg_nbr, msg = client.receive(inp)

                if msg == "ACK":
                    # Ignore acks with in loop..we don't use async methods
                    pass

                # If the message is SYSTEM 
                elif msg_nbr == "-1":
                    if msg == "END":
                        force_exit()
                    
                    elif msg == "STATE":
                        # Send the sate to broker
                        client.transmit(["-1", "ONLINE"])


                #If the message is CMD
                else:
                    if msg == "START_APP":
                        print("Got start command --> starting the app")
                        break
                    else:
                        # If we got some different cmd than start, inform user that we are waiting
                        client.transmit([msg_nbr,"WAITING_FOR_START"])

            else:
                print("Waiting...")
    
    except KeyboardInterrupt:
        print("\n Keyboard interrupt!.. Stop the app")

    # 7) Inform broker that LGTC has started the app
    client.transmit_async(["-1", "RUNNING"])
    # Here we are not waiting for ACK bc we will receive that ACK later in while loop below

    # 8) Send start command to vesna
    monitor.send_command("&" + str(APP_DURATION * 60))


    # ----------------------------------------------------------------------------------------
    # Start the application
    # ----------------------------------------------------------------------------------------
    print(" ")
    logging.info("Start loging serial input and wait for incoming commands ..")
    print(" ")

    try:
        while True:
            # --------------------------------------------------------------------------------
            # Wait for incoming line from VESNA serial port and read it

            if monitor.input_waiting():
                data = monitor.read_line()  
                
                # Store the line into file
                log.store_line(data)
                serialLinesStored += 1

            # --------------------------------------------------------------------------------
            # If we received some command from the broker, send it to VESNA and get response
            elif commandForVesna:
                # Get requested info from VESNA
                data = monitor.send_command(commandForVesna[1])

                # Form a reply
                response = commandForVesna
                response[1] = data

                # Send reply to the broker
                client.transmit_async(response)

                # Log it to file as well
                log.store_lgtc_line("Got command: " + commandForVesna[2])
                log.store_lgtc_line(" Got response: " + data)

                # Empty VESNA command queue
                commandForVesna = []


            # --------------------------------------------------------------------------------
            # If there is no data from VESNA to read and store, do other stuff
            else:

                # ----------------------------------------------------------------------------
                # Check if there is some incoming commad from the broker
                inp = client.check_input(0)

                # If we received any message from the broker
                if inp:
                    msg_nbr, msg = client.receive_async(inp)

                    # If the message is command (else (if we received ack) we got back None)
                    if msg_nbr:
                        
                        # If the message is SYSTEM
                        if msg_nbr == "-1":
                            if msg == "END":
                                force_exit()

                            elif msg == "STATE":
                                # Get LGTC state
                                reply = ["-1", "RUNNING"]

                                client.transmit_async(reply)

                        #If the message is CMD
                        else:
                            # Store the cmd and forward it to VESNA later
                            reply = [msg_nbr, msg]
                            commandForVesna = reply

                            
                # ----------------------------------------------------------------------------
                # If there is still some message that didn't receive ACK back, re send it
                elif (len(client.waitingForAck) != 0):
                    client.send_retry()    

            # TODO: Update status line in terminal.
            #print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
            #str(int(APP_DURATION)) + " min)", end="\r")

    except KeyboardInterrupt:
        print("\n Keyboard interrupt!.. Stop the app")


# ----------------------------------------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------------------------------------

def force_exit():
    monitor.close()
    #client.close() #TODO
    log.close()
    sys.exit(1)

# Soft exit also informs the broker about this
def soft_exit(reason):

    info = ["-1", "SOFT_EXIT"]  

    client.transmit(info)

    # Force wait ACK for 3 seconds
    if client.wait_ack("-1", 3):
        # Server acknowledged
        force_exit()
    else:
        print("No ack from broker...exiting now.")
        force_exit()




# ----------------------------------------------------------------------------------------
# GLOBAL VARIABLES 
# ----------------------------------------------------------------------------------------
# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://192.168.88.252:5562"
SUBSCR_HOSTNAME = "tcp://192.168.88.252:5561"

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


