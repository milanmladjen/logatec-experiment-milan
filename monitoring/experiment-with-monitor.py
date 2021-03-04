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
                logging.debug("Got message from VESNA")
                response = vl_queue.get()
                
                # If the message is SYSTEM - application controll
                if response[0] == "-1":
                    if response[1] == "START_APP":
                        LGTC_set_state("RUNNING")

                    elif response[1] == "STOP_APP":
                        LGTC_set_state("STOPPED")
                    
                    elif response[1] == "SYNCED_WITH_VESNA":
                        LGTC_set_state("ONLINE")

                    elif response[1] == "END_OF_APP":
                        LGTC_set_state("FINISHED")

                    elif response[1] == "VESNA_ERR":
                        LGTC_exit("VESNA_ERROR")
                        break
                    
                    else:
                        LGTC_set_state("LGTC_WARNING")
                        logging.debug("Unsupported state")

                    # Send new state to the server
                    client.transmit_async(["-1", LGTC_get_state()])
                
                # If the message is CMD - experiment response
                else:
                    client.transmit_async(response)

            # ----------------------------------------------------------------------------
            # If there is some incoming commad from the broker
            inp = client.check_input(0)
            if inp:
                msg_nbr, msg = client.receive_async(inp)

                # If the message is not ACK
                if msg_nbr:

                    # If the message is SYSTEM - application controll
                    if msg_nbr == "-1":
                        if msg == "EXIT":
                            logging.info("Received EXIT command from server - closing the app.")
                            break

                        elif msg == "STATE":
                            client.transmit_async(["-1", LGTC_get_state()])
                            
                        elif msg == "FLASH":
                            client.transmit_async(["-1", "COMPILING"])
                            if not LGTC_flash_vesna():
                                LGTC_exit("COMPILE_ERROR")
                                break
                            client.transmit_async(["-1", "ONLINE"])
                            LGTC_set_state("ONLINE")
                            # Sync with VESNA right after compiling
                            # TODO: maybe you can do it before, so you can start logging before flashing to capture first few lines?
                            lv_queue.put(["-1", "SYNC_WITH_VESNA"])

                        elif msg == "RESTART_APP":
                            lv_queue.put(["-1", "STOP_APP"])
                            client.transmit_async(["-1", "COMPILING"])
                            LGTC_flash_vesna()
                            client.transmit_async(["-1", "ONLINE"])
                            lv_queue.put(["-1", "START_APP"])
                            logging.info("Restarting the application!")

                        elif msg == "START_APP":
                            lv_queue.put([msg_nbr, msg])
                            logging.info("Starting application!")

                        elif msg == "STOP_APP":
                            lv_queue.put([msg_nbr, msg])
                            logging.info("Application stopped!")
                        
                        else:
                            client.transmit_async(["-1", "LGTC_WARNING"])
                            logging.warning("Unsupported command!")


                    #If the message is CMD - experiment command
                    else:
                        lv_queue.put([msg_nbr, msg])

            # ----------------------------------------------------------------------------
            # If there is still some message that didn't receive ACK back from server, re send it
            elif (len(client.waitingForAck) != 0):
                client.send_retry()


    except KeyboardInterrupt:
        print("\n Keyboard interrupt!.. Stop the app")
        return

    finally:
        return


# ----------------------------------------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------------------------------------

# Use in case of fatal errors in experiment app
def LGTC_exit(reason):
    client.transmit(["-1", reason])
    if client.wait_ack("-1", 3):
        return True
    else:
        logging.warning("No ACK from server while exiting...force exit.")
        return False

# Get global variable
def LGTC_get_state():
    global LGTC_STATE
    return LGTC_STATE

# Set global variable
def LGTC_set_state(state):
    global LGTC_STATE
    LGTC_STATE = state

# Compile the C app and VESNA with its binary
def LGTC_flash_vesna():
    # Compile the application
    logging.info("Compile the application ... ")
    LGTC_set_state("COMPILING")
    procCompile = Popen(["make", APP_NAME, "-j2"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procCompile.communicate()
    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)
        #return False

    # Flash the VESNA with app binary
    logging.info("Flash the app to VESNA .. ")
    procFlash = Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
    stdout, stderr = procFlash.communicate()
    logging.debug(stdout)
    if(stderr):
        logging.debug(stderr)
        #return False

    return True

# Make a hardware reset on VESNA
def LGTC_reset_vesna():
    try:
        os.system('echo 66 > /sys/class/gpio/export')
    except Exception:
        pass
    os.system('echo out > /sys/class/gpio/gpio66/direction')

    os.system('echo 0 > /sys/class/gpio/gpio66/value')
    os.system('echo 1 > /sys/class/gpio/gpio66/value')




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
    #TODO client.close()

    logging.info("Main thread stopped, trying to stop monitor thread.")

    # Notify serial monitor thread to exit its operation and join until quit
    sm_thread.stop()
    sm_thread.join()

    logging.info("Exit!")
