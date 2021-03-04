#!/usr/bin/python3
from queue import Queue
import threading
import sys
import os
import logging
import time
from subprocess import Popen, PIPE
from timeit import default_timer as timer

from lib import serial_monitor_thread
from lib import zmq_client


# ----------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# ----------------------------------------------------------------------------------------
# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://localhost:5562"
SUBSCR_HOSTNAME = "tcp://localhost:5561"

SERIAL_TIMEOUT = 2  # In seconds

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
    APP_DIR = "00_test"

# TODO: change when in container
# APP_PATH = "/root/logatec-experiment/application" + APP_DIR
APP_PATH = "/home/logatec/magistrska/logatec-experiment/applications/" + APP_DIR
APP_NAME = APP_DIR[3:]


print("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_ID)



# ----------------------------------------------------------------------------------------
# MAIN THREAD - ZMQ CLIENT
# ----------------------------------------------------------------------------------------
def main():

    # Sync with broker (tell him we are online) with timeout of 10 seconds
    logging.info("Sync with broker ... ")
    client.transmit(["-1", "SYNC"])
    if client.wait_ack("-1", 10) is False:
        logging.error("Couldn't synchronize with broker...")
    
    LGTC_set_state("ONLINE")

    try:
        while True:

            # ----------------------------------------------------------------------------
            # If there is a message from VESNA
            if not vl_queue.empty():
                print("Got response from VESNA")
                response = vl_queue.get()
                
                # If the message is SYSTEM
                if response[0] == "-1":
                    LGTC_update_state(response[1])
                    client.transmit_async(["-1", LGTC_get_state()])
                else:
                    client.transmit_async(response)

            # ----------------------------------------------------------------------------
            # If there is some incoming commad from the broker
            inp = client.check_input(0)
            if inp:
                msg_nbr, msg = client.receive_async(inp)

                # If the message is not ACK
                if msg_nbr:

                    # If the message is SYSTEM (for LGTC)
                    if msg_nbr == "-1":
                        if msg == "END":
                            force_exit()
                            break

                        elif msg == "STATE":
                            state = LGTC_get_state()
                            reply = ["-1", state]
                            client.transmit_async(reply)
                            
                        elif msg == "FLASH":
                            client.transmit_async(["-1", "COMPILING"])
                            LGTC_flash_vesna()
                            client.transmit_async(["-1", "COMPILED"])
                            lv_queue.put(["-1", "SYNC_WITH_VESNA"])

                        elif msg == "START_APP":
                            command = [msg_nbr, msg]
                            lv_queue.put(command)

                        elif msg == "STOP_APP":
                            command = [msg_nbr, msg]
                            lv_queue.put(command)

                        elif msg == "RESTART_APP":
                            lv_queue.put(["-1", "STOP_APP"])
                            client.transmit_async(["-1", "COMPILING"])
                            LGTC_flash_vesna()
                            client.transmit_async(["-1", "COMPILED"])
                            lv_queue.put(["-1", "START_APP"])


                    #If the message is CMD
                    else:
                        # Store the command in LGTC->VESNA queue
                        command = [msg_nbr, msg]
                        lv_queue.put(command)

            # If there is still some message that didn't receive ACK back, re send it
            elif (len(client.waitingForAck) != 0):
                client.send_retry()


    except KeyboardInterrupt:
        print("\n Keyboard interrupt!.. Stop the app")
        return

    finally:
        return


def force_exit():
    #client.close() #TODO
    print("TODO")

def soft_exit(reason):
    # Soft exit also informs the broker about this
    info = ["-1", "SOFT_EXIT"]  
    client.transmit(info)
    # Force wait ACK for 3 seconds
    if client.wait_ack("-1", 3):
        # Server acknowledged
        force_exit()
    else:
        print("No ack from broker...exiting now.")
        force_exit()

def LGTC_get_state():
    global LGTC_STATE
    return LGTC_STATE

def LGTC_set_state(state):
    global LGTC_STATE
    LGTC_STATE = state

def LGTC_update_state(state):
    global LGTC_STATE
    if state == "START_APP":
        LGTC_STATE = "RUNNING"
    elif state == "STOP_APP":
        LGTC_STATE = "ONLINE"
    else:
        print("Unknown state")

def LGTC_flash_vesna():
    # Compile the application
    logging.info("Compile the application ... ")
    LGTC_set_state("COMPILING")
    procCompile = Popen(["make", APP_NAME, "-j2"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procCompile.communicate()
    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)

    # Flash the VESNA with app binary
    logging.info("Flash the app to VESNA .. ")
    procFlash = Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procFlash.communicate()
    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)

    LGTC_set_state("COMPILED")




# ----------------------------------------------------------------------------------------
# GLOBAL VARIABLES
# ----------------------------------------------------------------------------------------
LGTC_STATE = "OFFLINE"

#logging.basicConfig(format="[%(module)15s: %(funcName)16s()] %(message)s", level=LOG_LEVEL) # To long module names
logging.basicConfig(format="[%(levelname)5s:%(funcName)16s()] %(message)s", level=LOG_LEVEL)

client = zmq_client.zmq_client(SUBSCR_HOSTNAME, ROUTER_HOSTNAME, LGTC_ID)

lv_queue = Queue()
vl_queue = Queue()

# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------

if __name__ == "__main__":

    sm_thread = serial_monitor_thread.serial_monitor_thread(lv_queue, vl_queue, DEFAULT_FILENAME, LGTC_ID)
    sm_thread.start()
 
    main()

    print("Stoping main thread")

    # Notify serial monitor thread to exit its operation and join until quit
    sm_thread.stop()
    sm_thread.join()
