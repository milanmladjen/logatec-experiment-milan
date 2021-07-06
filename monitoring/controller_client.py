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
        self.client.transmit(["SYS", "SYNC"])
        if self.client.wait_ack("SYS", 10) is False:
            self.log.error("Couldn't synchronize with broker...")
            self._controller_died = True

        # ------------------------------------------------------------------------------------
        while self._is_thread_running:

            # --------------------------------------------------------------------------------
            # If there is a message from experiment thread
            # Filter out the information and act accordingly
            if not self.in_q.empty():

                self.log.debug("Received response from apk thread [" + response[0] + "]: " + response[1])

                sequence, response = self.in_q.get()

                if response == "START":
                    self.updateState("RUNNING")
                    self._is_app_running = True
                    self.log.debug("Application started!")

                elif response == "STOP":
                    self.updateState("STOPPED")
                    self._is_app_running = False
                    self.log.debug("Application stopped!")

                elif response == "END":
                    self.updateState("FINISHED")
                    self._is_app_running = False
                    self.log.info("End of application!")

                    if self._controller_died:
                        self.stop()
                        self.queuePut("SYS", "EXIT")
                        break
                
                elif response == "COMPILING":
                    self.updateState("COMPILING")

                elif response == "FLASHED":
                    self.updateState("ONLINE")
                
                elif response == "SYNCED_WITH_VESNA":
                    self.updateState("ONLINE")

                elif response == "JOIN_DAG":
                    self.updateState("JOINED_NETWORK")

                elif response == "EXIT_DAG":
                    self.updateState("EXITED_NETWORK")
                    
                elif response == "ROOT":
                    self.updateState("DAG_ROOT")
                    self.sendCmdResp(sequence, "Device is now RPL DAG root!")

                elif response == "VESNA_TIMEOUT":
                    self.updateState("TIMEOUT")

                elif response == "COMPILE_ERR":
                    self.exit("COMPILE_ERR")
                    break

                elif response == "VESNA_ERR":
                    self.exit("VESNA_ERR")
                    break              
                
                else:
                    self.log.debug("Forwarding it to the controller...")
                    self.sendCmdResp(sequence, response)
            
            # --------------------------------------------------------------------------------
            # If there is some incoming commad from the controller broker
            inp = self.client.check_input(0)
            if inp:
                msg_nbr, msg = self.client.receive_async(inp)

                # If the message is not ACK
                if msg_nbr:

                    self.log.debug("Received command from broker: [" + msg_nbr + "] " + msg)

                    # STATE COMMAND
                    # Return the state of the node
                    if msg_nbr == "STATE":
                        self.updateState(self.getState())
                    
                    # SYSTEM COMMANDS
                    # Forward them to the experiment app
                    elif msg_nbr == "SYS":

                        self.queuePut(msg_nbr, msg)

                        # EXIT - close the client thread
                        if msg == "EXIT":
                            self.updateState("OFFLINE")
                            self.log.info("Closing client thread.")
                            break

                    # EXPERIMENT COMMAND
                    # Forward them to the experiment app
                    else:
                        forward_cmd = True

                        if msg == "START":
                            if self._is_app_running == True:
                                self.sendCmdResp(msg_nbr, "App is allready running...")
                                forward_cmd = False
                        
                        if msg == "STOP":
                            if self._is_app_running == False:
                                self.sendCmdResp(msg_nbr, "No application running...")
                                forward_cmd = False

                        if msg == "RESTART":
                            self.queuePut("SYS", "RESET")
                            self.queuePut([msg_nbr, "START"])
                            forward_cmd = False

                        if forward_cmd:
                            self.log.debug("Forwarding it to the experiment thread")
                            self.queuePut(msg_nbr, msg)

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

    # Get global variable
    def getState(self):
        return self.__LGTC_STATE

    # Set global variable and
    # Send new state to the server (WARNING: async method used...)
    def updateState(self, state):
        self.__LGTC_STATE = state
        self.client.transmit_async(["STATE", state])

    # Send info to the server (WARNING: async method used...)
    def sendInfoResp(self, info):
        self.client.transmit_async(["INFO", info])

    # Send system message to the server (WARNING: async method used...)
    def sendSysResp(self, sys):
        self.client.transmit_async(["SYS", sys])

    # Send respond to the server (WARNING: async method used...)
    def sendCmdResp(self, sqn, resp):
        self.client.transmit_async([sqn, resp])




# This thread is designed for communication with controller_broker script - forwarding commands
# and responses & updating LGTC states.

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
# --> COMPILE_ERROR - Experiment application could not be compiled
# --> VESNA_ERROR   - Problems with UART communication
#
#
# ----------------------------------------------------------------------------------------
# SUPPORTED COMMANDS
# ----------------------------------------------------------------------------------------
# Incoming commands must be formated as a list with 2 string arguments: message number 
# and command itself (example: ["66", "SEC"]). Message number is used as a sequence
# number, but if it is set to "-1", command represents SYSTEM COMMAND:
#
# --> SYSTEM COMMANDS - used for controll over the LGTC monitoring application
#
#       * STATE           - return the current state of monitoring application
#       * EXIT            - exit monitoring application
#       * ACK             - acknowledge packet sent as a response on every message
#       * FLASH           - flash VESNA with experiment application
#       * RESET           - reset VESNA device
#       * BROKER_DIED     - if broker is not responding, inform serial monitor about it
#       * SYNC            - used to synchronize LGTC with broker/server
#
# System commands are also used to update device state!
#
# --> EXPERIMENT COMMANDS - used for controll over the VESNA experiment application
#
#       * START           - start the experiment application
#       * STOP            -
#       * RESTART         - 
#       * END             - when VESNA stops the experiment, this cmd is sent to broker
#       * DURRATION       - return predefined duration of the application
#       * LINES           - return the number of lines stored in measurement file
#       * SEC             - return the number of elapsed seconds since the beginning of exp.
#       TODO:
#       Depend on Contiki-NG application

