# TODO:
# Put zmq_client.py in this file as well?
# V clienta bi lahko dal ukaz UPTIME - da odgovori kolko časa je že on
# Controller_died obcijo dodej pousod, kjer je to mogoce zaznat


#!/usr/bin/python3
import threading
from queue import Queue

import sys
import os
import logging
from timeit import default_timer as timer
from subprocess import Popen, PIPE

from lib import zmq_client
from lib import serial_monitor_thread


# DEFINITIONS
LOG_LEVEL = logging.DEBUG

#ROUTER_HOSTNAME = "tcp://192.168.2.191:5562"
#SUBSCR_HOSTNAME = "tcp://192.168.2.191:5561"
ROUTER_HOSTNAME = "tcp://193.2.205.202:5562"
SUBSCR_HOSTNAME = "tcp://193.2.205.202:5561"  

RESULTS_FILENAME = "node_results"
LOGGING_FILENAME = "logger"



class ECMS_client():

    # ----------------------------------------------------------------------------------------
    # INIT
    # ----------------------------------------------------------------------------------------
    def __init__(self, input_q, output_q, lgtc_id, subscriber, router):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)
        
        self.client = zmq_client.zmq_client(subscriber, router, lgtc_id)

        self._controller_died = False
        self._is_app_running = False

        self.in_q = input_q
        self.out_q = output_q

        self.__LGTC_STATE = "OFFLINE"
        self._UPTIME = 0


    # ----------------------------------------------------------------------------------------
    # MAIN
    # ----------------------------------------------------------------------------------------
    def run(self):

        # Sync with broker with timeout of 10 seconds
        self.log.info("Sync with broker ... ")
        self.client.transmit(["SYNC", "SYNC"])
        if self.client.wait_ack("SYNC", 10) is False:
            self.log.error("Couldn't synchronize with broker...")
            self._controller_died = True

        # ------------------------------------------------------------------------------------
        loop_time = timer()
        while True:

            # --------------------------------------------------------------------------------
            # Count seconds
            if ((timer() - loop_time) > 1):
                self._UPTIME += (timer() - loop_time)
                loop_time = timer()

            # --------------------------------------------------------------------------------
            # If there is a message from experiment thread
            if not self.in_q.empty():

                sequence, response = self.in_q.get()

                self.log.debug("Received response from apk thread [" + sequence + "]: " + response)

                if sequence == "STATE":
                    self.updateState(response)

                elif sequence == "INFO":
                    self.sendInfoResp(response)

                else:
                    if response == "START":
                        self._is_app_running = True
                        self.updateState("RUNNING")
                        self.log.debug("Application started!")
                    
                    elif response == "STOP":
                        self._is_app_running = False
                        self.updateState("STOPPED")
                    
                    elif response == "END":
                        self._is_app_running = False
                        self.updateState("FINISHED")

                        if self._controller_died:
                            break

                    elif response == "JOIN_DAG":
                        self.updateState("JOINED_NETWORK")
                        self.log.debug("Device joined RPL network!")

                    elif response == "EXIT_DAG":
                        self.updateState("EXITED_NETWORK")
                        self.log.debug("Device exited RPL network!")

                    elif response == "ROOT":
                        self.updateState("DAG_ROOT")
                        self.sendCmdResp(sequence, "Device is now RPL DAG root!")
                    
                    # Forward command to the controller
                    else:
                        self.sendCmdResp(sequence, response)
            
            # --------------------------------------------------------------------------------
            # If there is some incoming commad from the controller broker
            inp = self.client.check_input(0)
            if inp:
                sqn, cmd = self.client.receive_async(inp)

                # if not ACK
                if sqn:

                    self.log.debug("Received command from broker: [" + sqn + "] " + cmd)
                    
                    # Evaluation 
                    if sqn == "ROUNDTRIP":
                        self.sendCmdResp(sqn, "ROUNDTRIP")

                    # STATE COMMAND
                    # Return the state of the node
                    elif sqn == "STATE":
                        self.updateState(self.getState())

                    # EXPERIMENT COMMAND
                    else:

                        if cmd == "EXIT":
                            self.updateState("OFFLINE")
                            self.log.info("Closing client thread.")
                            break

                        elif cmd == "FLASH":
                            self.log.debug("Flash obsolete..delete me")

                        elif cmd == "RESET":
                            self.log.debug("Reset obsolete..delete me")
                        
                        elif cmd == "START":
                            if self._is_app_running == True:
                                self.sendCmdResp(sqn, "App is allready running...")
                            else:
                                self.queuePut(sqn, cmd)

                        elif cmd == "STOP":
                            if self._is_app_running == False:
                                self.sendCmdResp(sqn, "No application running ...")
                            else:
                                self.queuePut(sqn, cmd)

                        elif cmd == "RESTART":
                            self.log.info("Restart the application") #TODO

                        elif cmd == "DURATION":
                            resp = "Defined duration: " + str(APP_DURATION) + " minutes"
                            self.sendCmdResp(sqn, resp)

                        elif cmd == "UPTIME":
                            resp = "Node is online for: " + str(self._UPTIME) + " seconds"
                            self.sendCmdResp(sqn, resp)

                        # All other commands are forwarded to the VESNA device
                        else:
                            self.queuePut(sqn, cmd)

            # --------------------------------------------------------------------------------
            # If there is still some message that didn't receive ACK back from server, re send it
            elif (len(self.client.waitingForAck) != 0):
                self.client.send_retry()
                #TODO self.queuePut(["-1", "BROKER_DIED"])

        # ------------------------------------------------------------------------------------
        self.log.debug("Exiting client thread")
        #self.client.close()


    # ----------------------------------------------------------------------------------------
    # END
    # ----------------------------------------------------------------------------------------
    def clean(self):
        # TODO: clean zmw_client resources
        print("Clean")


    # Use in case of fatal errors in experiment app
    def exit(self, reason):
        self.client.transmit(["STATE", reason])
        if self.client.wait_ack("STATE", 3):
            return True
        else:
            self.log.warning("No ACK from server while exiting...force exit.")
            return False

    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------

    def queuePut(self, sequence, command):
        self.out_q.put([sequence, command])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]


    # Get global variable
    def getState(self):
        return self.__LGTC_STATE

    # Set global variable and
    # Send new state to the server (WARNING: async method used...)
    def updateState(self, state):
        self.__LGTC_STATE = state
        # TODO check if state is possible, else set state LGTC_WARNING
        self.client.transmit_async(["STATE", state])
        self.log.debug("Updating state: " + state)

    # Send info to the server (WARNING: async method used...)
    def sendInfoResp(self, info):
        self.client.transmit_async(["INFO", info])
        self.log.debug("Sending info to the controller" + info)

    # Send respond to the server (WARNING: async method used...)
    def sendCmdResp(self, sqn, resp):
        self.client.transmit_async([sqn, resp])
        self.log.debug("Sending response("+ sqn +") to the controller: " + resp)

    

    


    # ----------------------------------------------------------------------------------------
    # FUNCTIONS TO CONTROL VESNA DEVICE
    # ----------------------------------------------------------------------------------------
    # Compile the C app and VESNA with its binary
    def VESNA_flash(self):
        # Compile the application
        self.updateState("COMPILING")
        self.log.info("Complie the application.")
        #procDistclean = Popen(["make", "distclean"])
        with Popen(["make", APP_NAME, "-j2"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as p:
            for line in p.stdout:
                self.log.debug(line)    #TODO maybe use print(line, end="")
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.updateState("COMPILE_ERR")
            return False

        # Flash the VESNA with app binary
        self.log.info("Flash the app to VESNA .. ")
        with Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as p:
            for line in p.stdout:
                self.log.debug(line)
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.updateState("COMPILE_ERR")
            return False

        self.log.info("Successfully flashed VESNA ...")
        self.updateState("ONLINE")
        return True

    # Make a hardware reset on VESNA
    def VESNA_reset(self):
        self.log.info("VESNA hardware reset.")
        try:
            os.system('echo 66 > /sys/class/gpio/export')
        except Exception:
            pass
        os.system('echo out > /sys/class/gpio/gpio66/direction')

        os.system('echo 0 > /sys/class/gpio/gpio66/value')
        os.system('echo 1 > /sys/class/gpio/gpio66/value')

        self.sendInfoResp("Device reset complete!")
        return True













# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":

    # ------------------------------------------------------------------------------------
    # EXPERIMENT CONFIG
    # ------------------------------------------------------------------------------------
    # Device id should be given as argument at start of the scripT
    try:
        LGTC_ID = sys.argv[1]
        LGTC_ID = LGTC_ID.replace(" ", "")
    except:
        print("No device name was given...going with default")
        LGTC_ID = "xy"

    LGTC_NAME = "LGTC" + LGTC_ID
    RESULTS_FILENAME += ("_" + LGTC_ID + ".txt")
    LOGGING_FILENAME += ("_" + LGTC_ID + ".log")

    # Application name and duration should be defined as variable while running container
    try:
        APP_DURATION = int(os.environ['APP_DURATION_MIN'])
    except:
        print("No app duration was defined...going with default 60min")
        APP_DURATION = 10

    try:
        APP_DIR = os.environ['APP_DIR']
    except:
        print("No application was given...aborting!")
        #sys.exit(1) TODO
        APP_DIR = "02_acs"

    # TODO: change when in container
    APP_PATH = "/root/logatec-experiment/applications/" + APP_DIR
    #APP_PATH = "/home/logatec/magistrska/logatec-experiment/applications/" + APP_DIR

    APP_NAME = APP_DIR[3:]

    # ------------------------------------------------------------------------------------
    # LOGGING CONFIG
    # ------------------------------------------------------------------------------------

    # Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

    logging.info("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_NAME + "!")


    # ------------------------------------------------------------------------------------
    # QUEUE CONFIG
    # ------------------------------------------------------------------------------------

    # Create 2 queue for communication between threads
    # Client -> Monitor
    C_M_QUEUE = Queue()
    # Monitr -> Clinet
    M_C_QUEUE = Queue()


    # ------------------------------------------------------------------------------------
    # SERIAL MONITOR THREAD
    # ------------------------------------------------------------------------------------

    # Start serial monitor thread (communication with VESNA)
    monitor_thread = serial_monitor_thread.serial_monitor_thread(C_M_QUEUE, M_C_QUEUE, RESULTS_FILENAME, LGTC_NAME, APP_NAME, APP_PATH)
    monitor_thread.start()

    # ------------------------------------------------------------------------------------
    # MAIN THREAD (ZMQ CLINET)
    # ------------------------------------------------------------------------------------

    # Start main thread - zmq client (communication with controller)
    main_thread = ECMS_client(M_C_QUEUE, C_M_QUEUE, LGTC_NAME, SUBSCR_HOSTNAME, ROUTER_HOSTNAME)
    main_thread.run()


    # ------------------------------------------------------------------------------------
    # EXIT EXPERIMENT
    # ------------------------------------------------------------------------------------
    # If we came here, main thread stopped
    logging.info("Main thread (client) stopped, trying to serial monitor thread.")
    #main_thread.clean()

    # Notify zmq client thread to exit its operation and join until quit
    monitor_thread.stop()
    monitor_thread.join()

    # TODO: put VESNA in reset state, so it doesn't interfeer with other networks?

    logging.info("Exit!")















# This thread is designed for communication with controller_broker script - forwarding commands
# and responses & updating LGTC state.

# ----------------------------------------------------------------------------------------
# POSSIBLE LGTC STATES
# ----------------------------------------------------------------------------------------
# --> ONLINE        - LGTC is online and ready
# --> COMPILING     - LGTC is compiling the experiment application
# --> RUNNING       - Experiment application is running
# --> STOPPED       - User successfully stopped the experiment app
# --> FINISHED      - Experiment application came to the end
#
# --> TIMEOUT       - VESNA is not responding for more than a minute
# --> LGTC_WARNING  - Warning sign that something was not as expected
# --> COMPILE_ERR - Experiment application could not be compiled
# --> VESNA_ERR   - Problems with UART communication
#
#
# ----------------------------------------------------------------------------------------
# SUPPORTED COMMANDS
# ----------------------------------------------------------------------------------------
# Messages in the monitoring systems (between controller and node!) are formed as a list 
# with 2 arguments: message_type and command itself (example: ["11", "START"]). First 
# argument distinguish between 4 possible packet types:
#
# INFO
# STATE
# SQN
# ACK


