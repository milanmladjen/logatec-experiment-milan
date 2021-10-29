#!/usr/bin/python3

from queue import Queue
import sys
import logging
import importlib

from lib import zmq_client


# -------------------------------------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------------------------------------
LOG_LEVEL = logging.DEBUG

#ROUTER_HOSTNAME = "tcp://192.168.2.191:5562"
#SUBSCR_HOSTNAME = "tcp://192.168.2.191:5561"
ROUTER_HOSTNAME = "tcp://193.2.205.19:5562"
SUBSCR_HOSTNAME = "tcp://193.2.205.19:5561"  

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
            self.queuePut("0", "CONTROLLER_DIED")

        # ------------------------------------------------------------------------------------
        while True:

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
                        
                        # EXIT - close the client thread
                        if msg == "EXIT":
                            self.updateState("OFFLINE")
                            self.log.info("Closing client thread.")
                            break

                        elif msg == "START":
                            self.log.debug("Start experiment thread")
                            experiment_thread.start()

                        elif msg == "STOP":
                            self.log.debug("Stop experiment thread")
                            experiment_thread.stop()
                            experiment_thread.join()

                        #NAME - name experiment - use case: NAME$your_name
                        #elif "NAME$" in msg: 
                            #self.experiment_name = msg[5:]
                            #self.log.info("Naming experiment thread: {}".format(self.experiment_name))
                            #print("Naming experiment thread: {}".format(self.experiment_name))
                            #TODOB - nazalost obsolete funkcionalnost

                        else:
                            # Forward it to the experiment
                            self.queuePut(sqn, msg)

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
# MAIN
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":    
        
    # ------------------------------------------------------------------------------------
    # EXPERIMENT CONFIG
    # ------------------------------------------------------------------------------------
    try:
        LGTC_ID = sys.argv[1]
        LGTC_ID = LGTC_ID.replace(" ", "")
    except:
        print("No device name was given...going with default")
        LGTC_ID = "xy"

    LGTC_NAME = "LGTC" + LGTC_ID
    RESULTS_FILENAME += ("_" + LGTC_ID + ".txt")
    LOGGING_FILENAME += ("_" + LGTC_ID + ".log")

    # ------------------------------------------------------------------------------------
    # LOGGING CONFIG
    # ------------------------------------------------------------------------------------
    # Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

    _log = logging.getLogger(__name__)
    _log.setLevel(LOG_LEVEL)

    try:
        APP_DIR = sys.argv[2]
        APP_NAME = sys.argv[3]
    except:
        _log.error("No application given. Aborting execution!")
        sys.exit()

    _log.info("Testing application " + APP_NAME + " on device " + LGTC_NAME + "!")


    # ------------------------------------------------------------------------------------
    # QUEUE CONFIG
    # ------------------------------------------------------------------------------------
    # Create 2 queue for communication between threads
    # Client -> Experiment
    C_E_QUEUE = Queue()
    # Experiment -> Clinet
    E_C_QUEUE = Queue()

    # ------------------------------------------------------------------------------------
    # EXPERIMENT THREAD
    # ------------------------------------------------------------------------------------
    # TODOB: samo za info, kako se importa aplikacija, ki jo podaš kot spremenljivko pri zagonu apk
    # Class aplikacije mora biti vedno isto poimenovan - lahko je kar BLE_experiment

    # Import application thread during runtime and configure it (__init__)
    sys.path.append("../applications/" + APP_DIR)
    module = importlib.import_module(APP_NAME, __name__)
    experiment_thread = module.BLE_experiment(C_E_QUEUE, E_C_QUEUE, RESULTS_FILENAME, LGTC_NAME, APP_NAME)

    # ------------------------------------------------------------------------------------
    # MAIN THREAD (ZMQ CLINET)
    # ------------------------------------------------------------------------------------

    # Start main thread - zmq client (communication with controller)
    client_thread = ECMS_client(E_C_QUEUE, C_E_QUEUE, LGTC_NAME, SUBSCR_HOSTNAME, ROUTER_HOSTNAME)
    client_thread.run()

    # TODO clean stuff

    client_thread.clean()

    experiment_thread.stop()
    experiment_thread.join()

    _log.info("Exiting application!")


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

