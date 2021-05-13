# TODO:
# Put zmq_client.py in this file as well?


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
        self.client.transmit(["-1", "SYNC"])
        if self.client.wait_ack("-1", 10) is False:
            self.log.error("Couldn't synchronize with broker...")
            self.out_q.put(["-1", "BROKER_DIED"])

        # ------------------------------------------------------------------------------------
        while self._is_thread_running:

            # If there is a message from VESNA
            # --------------------------------------------------------------------------------
            if not self.in_q.empty():
                response = self.in_q.get()
                
                # If the message is SYSTEM - new state
                if response[0] == "-1":
                    self.log.debug("New state: " + response[1])

                    if response[1] == "START":
                        self.LGTC_set_state("RUNNING")

                    elif response[1] == "STOP":
                        self.LGTC_set_state("STOPPED")

                    elif response[1] == "END":
                        self.LGTC_set_state("FINISHED")
                    
                    elif response[1] == "COMPILING":
                        self.LGTC_set_state("COMPILING")

                    elif response[1] == "FLASHED":
                        self.LGTC_set_state("ONLINE")
                    
                    elif response[1] == "SYNCED_WITH_VESNA":
                        self.LGTC_set_state("ONLINE")

                    elif response[1] == "JOINED":
                        self.LGTC_set_state("JOINED_NETWORK")

                    elif response[1] == "ROOT":
                        self.LGTC_set_state("RPL_ROOT")

                    elif response[1] == "VESNA_TIMEOUT":
                        self.LGTC_set_state("TIMEOUT")

                    elif response[1] == "COMPILE_ERR":
                        self.LGTC_exit("COMPILE_ERR")
                        break

                    elif response[1] == "VESNA_ERR":
                        self.LGTC_exit("VESNA_ERR")
                        break
                    
                    else:
                        self.LGTC_set_state("LGTC_WARNING")
                        self.log.warning("+--> Unsupported state!")                    
                
                # If the message is CMD - experiment response
                else:
                    self.log.debug("Forwarding cmd response to broker...")
                    self.client.transmit_async(response)
            
            # --------------------------------------------------------------------------------
            # If there is some incoming commad from the controller broker
            inp = self.client.check_input(0)
            if inp:
                msg_nbr, msg = self.client.receive_async(inp)

                # If the message is not ACK
                if msg_nbr:

                    self.log.debug("Received command from broker: [" + msg_nbr + "] " + msg)
                    # SYSTEM COMMANDS - application controll
                    if msg_nbr == "-1":

                        if msg == "STATE":
                            self.client.transmit_async(["-1", self.LGTC_get_state()])

                        elif msg == "EXIT":
                            self.LGTC_set_state("OFFLINE")
                            self.out_q.put([msg_nbr, msg])
                            self.log.info("Closing client thread.")
                            break
                            
                        else:
                            self.out_q.put([msg_nbr, msg])

                    # EXPERIMENT COMMANDS - experiment command
                    else:
                        self.out_q.put([msg_nbr, msg])


            # --------------------------------------------------------------------------------
            # If there is still some message that didn't receive ACK back from server, re send it
            elif (len(self.client.waitingForAck) != 0):
                self.client.send_retry()
                #TODO self.out_q.put(["-1", "BROKER_DIED"])

        # ------------------------------------------------------------------------------------
        self.log.debug("Exiting client thread")
        #self.client.close()


    # ----------------------------------------------------------------------------------------
    # END
    # ----------------------------------------------------------------------------------------
    def stop(self):
        self._is_thread_running = False

    


    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------

    # Use in case of fatal errors in experiment app
    def LGTC_exit(self, reason):
        self.client.transmit(["-1", reason])
        if self.client.wait_ack("-1", 3):
            return True
        else:
            self.log.warning("No ACK from server while exiting...force exit.")
            return False

    # Get global variable
    def LGTC_get_state(self):
        return self.__LGTC_STATE

    # Set global variable
    def LGTC_set_state(self, state):
        self.__LGTC_STATE = state
        # Send new state to the server (WARNING: async method used...)
        self.client.transmit_async(["-1", state])



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

