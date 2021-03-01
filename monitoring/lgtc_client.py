#!/usr/bin/python3

import threading
from queue import Queue

import sys
import os
import logging
import time
from subprocess import Popen, PIPE

from lib import serial_monitor
from lib import file_logger
from lib import zmq_client


# ----------------------------------------------------------------------------------------
# APP DEFINITIONS AND CONFIGURATION
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

    # 1) Sync with broker (tell him we are online) with timeout of 10 seconds
    logging.info("Sync with broker ... ")
    client.transmit(["-1", "SYNC"])
    if client.wait_ack("-1", 10) is False:
        logging.error("Couldn't synchronize with broker..exiting now.")
        force_exit()
        return

    try:
        while True:

            # ----------------------------------------------------------------------------
            # If there is a message from VESNA
            if not vl_queue.empty():
                print("Got response from VESNA")
                response = vl_queue.get()

                # TODO
                if response[0] == "-1":
                    if response[1] == "START_APP":
                        app_is_running = True

                client.transmit_async(response)

            # ----------------------------------------------------------------------------
            # Check if there is some incoming commad from the broker
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
                            state = LGTC_flash_vesna()
                            reply = ["-1", state]
                            client.transmit_async(reply)

                        elif msg == "START_APP":
                            command = [msg_nbr, msg]
                            lv_queue.put(command)

                        elif msg == "STOP_APP":
                            command = [msg_nbr, msg]
                            lv_queue.put(command)

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


# FUNCTIONS

def force_exit():
    #client.close() #TODO
    print("TODO")

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

def LGTC_get_state():
    if app_is_running:
        return "RUNNING"
    else:
        return "ONLINE"

# ----------------------------------------------------------------------------------------
# THREAD - SERIAL MONITOR 
# ----------------------------------------------------------------------------------------

class serial_monitor_thread(threading.Thread):

    def __init__(self, input_q, output_q):
        threading.Thread.__init__(self)
        self.in_q = input_q
        self.out_q = output_q

        #self.serialLinesStored = 0
        #self.monitor = serial_monitor.serial_monitor(SERIAL_TIMEOUT)

        #self.log = file_logger.file_logger()
        #self.log.prepare_file(DEFAULT_FILENAME, LGTC_ID)
        #self.log.open_file()

    def run(self):
        print("Starting serial monitor thread")      

        while not exitFlag:
            
            # Read line from UART
            #if self.monitor.input_waiting():
                #data = self.monitor.read_line()  
                
                # Store the line into file
                #self.log.store_line(data)
                #self.serialLinesStored += 1
            time.sleep(0.7)

            # If there is any command in queue, forward it to VESNA
            if not self.in_q.empty():
                cmd = self.in_q.get()

                print(cmd)
                data = ["1", "solata"]

                #data = self.monitor.send_command(cmd)

                self.out_q.put(data)

                # Log it to file as well
                #self.log.store_lgtc_line("Got command: " + commandForVesna[2])
                #self.log.store_lgtc_line(" Got response: " + data)

            else:
                print(".")
                # TODO: Update status line in terminal.
                #print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
                #str(int(APP_DURATION)) + " min)", end="\r")
        
        #self.monitor.close()
        #self.log.close()





# ----------------------------------------------------------------------------------------
# THREAD - SERIAL MONITOR 
# ----------------------------------------------------------------------------------------

app_is_running = False

#logging.basicConfig(format="[%(module)15s: %(funcName)16s()] %(message)s", level=LOG_LEVEL) # To long module names
logging.basicConfig(format="[%(levelname)5s:%(funcName)16s()] %(message)s", level=LOG_LEVEL)

client = zmq_client.zmq_client(SUBSCR_HOSTNAME, ROUTER_HOSTNAME, LGTC_ID)

lv_queue = Queue()
vl_queue = Queue()

exitFlag = 0

if __name__ == "__main__":

    sm_thread = serial_monitor_thread(lv_queue, vl_queue)
    sm_thread.start()
 
    main()

    print("Stoping main thread")

    # Notify serial monitor thread to exit its operation and join until quit
    exitFlag = 1
    sm_thread.join()
