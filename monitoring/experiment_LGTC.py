# TODO:
# Put zmq_client.py in this file as well?
# V clienta bi lahko dal ukaz UPTIME - da odgovori kolko časa je že on

#!/usr/bin/python3
import threading
from queue import Queue

import sys
import os
import logging
import time

from lib import zmq_client

LOG_LEVEL = logging.DEBUG

class zmq_client_thread(threading.Thread):

    # ----------------------------------------------------------------------------------------
    # INIT
    # ----------------------------------------------------------------------------------------
    def __init__(self, input_q, output_q, lgtc_id, subscriber, router):

        threading.Thread.__init__(self)
        self._is_thread_running = True
        self._controller_died = False
        self._is_app_running = False

        self.in_q = input_q
        self.out_q = output_q

        self.client = zmq_client.zmq_client(subscriber, router, lgtc_id)
        self.__LGTC_STATE = "OFFLINE"

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)


    # ----------------------------------------------------------------------------------------
    # MAIN
    # ----------------------------------------------------------------------------------------
    def run(self):

        # Sync with broker with timeout of 10 seconds
        self.log.info("Sync with broker ... ")
        self.client.transmit(["SYNC", "SYNC"])
        if self.client.wait_ack("SYNC", 10) is False:
            self.log.error("Couldn't synchronize with broker...")
            self.queuePut("0", "CONTROLLER_DIED")

        # ------------------------------------------------------------------------------------
        while self._is_thread_running:

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
                    self.sendCmdResp(sequence, response)
            
            # --------------------------------------------------------------------------------
            # If there is some incoming commad from the controller broker
            inp = self.client.check_input(0)
            if inp:
                sqn, msg = self.client.receive_async(inp)

                # if not ACK
                if sqn:

                    self.log.debug("Received command from broker: [" + sqn + "] " + msg)

                    # STATE COMMAND
                    # Return the state of the node
                    if sqn == "STATE":
                        self.updateState(self.getState())

                    # EXPERIMENT COMMAND
                    else:
                        # Forward it to the experiment
                        self.queuePut(sqn, msg)

                        # EXIT - close the client thread
                        if msg == "EXIT":
                            self.updateState("OFFLINE")
                            self.log.info("Closing client thread.")
                            break

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
    def stop(self):
        self._is_thread_running = False


    # Use in case of fatal errors in experiment app
    def exit(self, reason):
        self.client.transmit(["STATE", reason])
        if self.client.wait_ack("-1", 3):
            return True
        else:
            self.log.warning("No ACK from server while exiting...force exit.")
            return False

    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------

    def queuePut(self, sqn, cmd):
        self.out_q.put([sqn, cmd])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]

    # Send info to the server (WARNING: async method used...)
    def sendInfoResp(self, info):
        self.client.transmit_async(["INFO", info])

    # Send respond to the server (WARNING: async method used...)
    def sendCmdResp(self, sqn, resp):
        self.client.transmit_async([sqn, resp])

    # Set global variable and
    # Send new state to the server (WARNING: async method used...)
    def updateState(self, state):
        self.__LGTC_STATE = state
        # TODO check if state is possible, else set state LGTC_WARNING
        self.client.transmit_async(["STATE", state])

    # Get global variable
    def getState(self):
        return self.__LGTC_STATE




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


