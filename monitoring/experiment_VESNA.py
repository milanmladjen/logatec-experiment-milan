#!/usr/bin/python3

# ----------------------------------------------------------------------------------------
# Example of experiment with VESNA device. Application is made out of 2 threads:
#   * main for experiment controll and communication with VESNA device,
#   * client thread for communication with the controller server.
#
# Modules used:
#   * controller_client.py communicates with controller server.
#   * serial_monitor.py serves communication with VESNA via UART connection.
#   * file_logger.py stores all the measurements of the experiment.
# ----------------------------------------------------------------------------------------
# TODO: what to do with commands that have arguments? (example at sending DURAT)

from queue import Queue
import sys
import os
import logging
import time
from timeit import default_timer as timer
from subprocess import Popen, PIPE

from lib import serial_monitor
from lib import file_logger

import controller_client



# ----------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# ----------------------------------------------------------------------------------------

# DEFINITIONS
LOG_LEVEL = logging.DEBUG

#ROUTER_HOSTNAME = "tcp://192.168.2.191:5562"
#SUBSCR_HOSTNAME = "tcp://192.168.2.191:5561"
ROUTER_HOSTNAME = "tcp://193.2.205.19:5562"
SUBSCR_HOSTNAME = "tcp://193.2.205.19:5561"

SERIAL_TIMEOUT = 2  # In seconds

RESULTS_FILENAME = "node_results"
LOGGING_FILENAME = "logger"

# ENVIRONMENTAL VARIABLES
# Device id should be given as argument at start of the script
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





# ----------------------------------------------------------------------------------------
# EXPERIMENT APPLICATION
# ----------------------------------------------------------------------------------------
class experiment():

    def __init__(self, input_q, output_q, filename, lgtcname):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        # Init lib
        self.monitor = serial_monitor.serial_monitor(2)
        self.f = file_logger.file_logger()

        # controller_client.py - link multithread input output queue
        self.in_q = input_q
        self.out_q = output_q
        self._controller_died = False

        # file_logger.py - prepare measurements file
        self.f.prepare_file(filename, lgtcname)
        self.f.open_file()  

        # Experiment vars
        self._is_app_running = False
        self._command_waiting = None
        self._command_timeout = False
        self._lines_stored = 0
        self._elapsed_sec = 0



    def runApp(self):

        self.log.info("Starting experiment main thread!")

        # Connect to VESNA serial port
        if not self.VESNA_connect():
            return

        # Flash VESNA with application
        if not self.VESNA_flash():
            return        

        # Sync with experiment application
        if not self.VESNA_sync():
            return

        # Send app duration to VESNA
        # TODO: Controll this value with monitor??
        # Each time application starts, send duration to VESNA...if user wants to change it, he can do it with new command...
        self.monitor.send_command_with_arg("DURAT", str(APP_DURATION * 60))

        timeout_cnt = 0
        loop_time = timer()

        while(True):

            # -------------------------------------------------------------------------------
            # SERAIL_MONITOR - FAILSAFE
            # Enabled only while some application is running 
            #   * Check if serial was available in last 10 seconds
            #   * Check if we got respond on a command in last 3 sec
            if self._is_app_running:

                # Count seconds
                if ((timer() - loop_time) > 1):
                    self._elapsed_sec += (timer() - loop_time)
                    loop_time = timer()
                    #self.log.debug("Elapsed seconds: " + str(self._elapsed_sec))

                    # Every 10 seconds
                    if self._elapsed_sec % 10 == 0:
                        
                        # Check if serial_monitor received something
                        if not self.monitor.serial_avaliable:
                            self.f.store_lgtc_line("Timeout detected.")
                            timeout_cnt += 1
                            self.log.warning("No lines read for more than 10 seconds..")

                        if timeout_cnt > 5:
                            self.f.warning("VESNA did not respond for more than a minute")
                            self.queuePutState("TIMEOUT")
                            self.log.error("VESNA did not respond for more than a minute")
                            timeout_cnt = 0
                            self._is_app_running = False
                            # We don't do anything here - let the user interfeer

                        # Set to False, so when monitor reads something, it goes back to True
                        self.monitor.serial_avaliable = False

                    # Every 3 seconds
                    if self._elapsed_sec % 3 == 0:
                        if self._command_waiting != None:
                            self.log.debug("Waiting for response...")
                            # If _command_timeout allready occurred - response on command was
                            # not captured for more than 3 seconds. Something went wrong, 
                            # so stop waiting for it
                            if self._command_timeout:
                                self.f.warning("Command timeout occurred!")
                                self.queuePutResp(self._command_waiting, "Failed to get response ...")
                                self.queuePutState("TIMEOUT")
                                self.log.warning("No response on command for more than 3 seconds!")
                                self._command_timeout = False
                                self._command_waiting = None
                            
                            self._command_timeout = True

            # -------------------------------------------------------------------------------
            # SERIAL MONITOR - READ UART
            # Read and store everything that comes on Serial connection
            # If line is a response, forward it to zmq thread for processing
            if self.monitor.input_waiting():
                data = self.monitor.read_line()

                self.f.store_line(data)
                self._lines_stored += 1

                # If we got response on the command
                # TODO: check if it is a multiline response
                if data[0] == "$":

                    # Remove first 2 char '$ ' and last two char '\n'
                    resp = data[2:-1]

                    if resp == "START":
                        self._elapsed_sec = 0
                        loop_time = timer()
                        self._lines_stored = 0
                        self._is_app_running = True
                        self.queuePutState("RUNNING")
                        self.log.debug("Application started!")

                    elif resp == "STOP":
                        self._is_app_running = False
                        self.queuePutState("STOPPED")

                    elif resp == "END":
                        self._is_app_running = False
                        self.queuePutState("FINISHED")

                        if self._controller_died:
                            break

                    elif resp == "JOIN_DAG":
                        self.queuePutState("JOINED_NETWORK")
                        self.log.debug("Device joined RPL network!")

                    elif resp == "EXIT_DAG":
                        self.queuePutState("EXITED_NETWORK")
                        self.log.debug("Device exited RPL network!")

                    elif resp == "ROOT":
                        self.queuePutState("DAG_ROOT")
                        self.queuePutResp(self._command_waiting, "Device is now RPL DAG root!")
                        self.log.debug("Device is now RPL DAG root!")


                    # If there is no SQN waiting for response, we got INFO message from VESNA for monitor
                    elif(self._command_waiting):
                        self.queuePutResp(self._command_waiting, resp)
                        self.log.debug("Got response on cmd from VESNA: " + resp)
                    else:
                        self.queuePutInfo(resp)
                        self.log.debug("Got info from VESNA: " + resp)

                    self._command_waiting = None
                    self._command_timeout = False


            # -------------------------------------------------------------------------------
            # CONTROLLER CLIENT - GET COMMANDS
            # Check for incoming commands only when there is time - nothing to do on UART
            # If all comand responses were received (not waiting for one)
            # and there is new command in queue, forward it to VESNA
            elif (not self.in_q.empty() and self._command_waiting == None):

                sqn, cmd = self.queueGet()

                forward_cmd = True

                self.f.store_lgtc_line("Got command [" + sqn + "]: " + cmd)
                self.log.info("Got command [" + sqn + "]: " + cmd)

                if cmd == "FLASH":
                    forward_cmd = False
                    if not self.VESNA_flash():
                        break

                elif cmd == "RESET":
                    forward_cmd = False
                    if not self.VESNA_reset():
                        break

                elif cmd == "RESTART":
                    forward_cmd = False
                    if not self.VESNA_reset():
                        break

                elif cmd == "EXIT":
                    self.stop()
                    break

                elif cmd == "CONTROLLER_DIED":
                    forward_cmd = False
                    self._controller_died = True

                elif cmd == "START":
                    if self._is_app_running == True:
                        self.queuePutResp(sqn, "App is allready running...")
                        forward_cmd = False

                elif cmd == "STOP":
                    if self._is_app_running == False:
                        self.queuePutResp(sqn, "No application running ...")
                        forward_cmd = False

                # Return number of lines read
                elif cmd == "LINES":
                    forward_cmd = False
                    resp = "Lines stored: " + str(self._lines_stored)
                    self.queuePutResp(sqn, resp)
                    self.f.store_lgtc_line(resp)

                # Return number of seconds since the beginning of app
                elif cmd == "SEC":
                    forward_cmd = False
                    resp = "Seconds passed: " + str(round(self._elapsed_sec, 1)) + "s"
                    self.queuePutResp(sqn, resp)
                    self.f.store_lgtc_line(resp)

                # Return the predefined application duration
                elif cmd == "DURATION":
                    forward_cmd = False
                    resp = "Defined duration: " + str(APP_DURATION) + "min"
                    self.queuePutResp(sqn, resp)
                    self.f.store_lgtc_line(resp)

                # Forward command to VESNA
                if forward_cmd:
                    self.monitor.send_command(cmd)
                    self._command_waiting = sqn
    

    def clean(self):
        self.monitor.close()
        self.f.close()

    def stop(self):
        self.monitor.send_command("STOP")
        self.f.store_lgtc_line("Application exit!")
        self.log.info("Application exit!")

    def queuePutResp(self, sqn, resp):
        self.out_q.put([sqn, resp])

    def queuePutState(self, state):
        self.out_q.put(["STATE", state])

    def queuePutInfo(self, info):
        self.out_q.put(["INFO", info])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]





    # ----------------------------------------------------------------------------------------
    # VESNA CONTROLL
    # -------------------------------------------------------------------------------------
        # Connect to VESNA serial port
    def VESNA_connect(self):
        if not self.monitor.connect_to("ttyS2"):
            self.f.error("Couldn't connect to VESNA.")
            self.queuePutState("VESNA_ERR")
            self.log.error("Couldn't connect to VESNA.")
            return False
        
        self.log.info("Successfully connected to VESNA serial port!")
        return True

    # Sync with application 
    def VESNA_sync(self):
        if not self.monitor.sync_with_vesna():
            self.f.error("Couldn't sync with VESNA.")
            self.queuePutState("VESNA_ERR")
            self.log.error("Couldn't sync with VESNA.")
            return False

        self.queuePutState("ONLINE")
        self.log.info("Synced with VESNA over serial ...")
        return True

    # Compile the C app and VESNA with its binary
    def VESNA_flash(self):
        # Compile the application
        self.queuePutState("COMPILING")
        self.log.info("Complie the application.")
        #procDistclean = Popen(["make", "distclean"])
        with Popen(["make", APP_NAME, "-j2"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as p:
            for line in p.stdout:
                self.log.debug(line)    #TODO maybe use print(line, end="")
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.queuePutState("COMPILE_ERR")
            return False

        # Flash the VESNA with app binary
        self.log.info("Flash the app to VESNA .. ")
        with Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as p:
            for line in p.stdout:
                self.log.debug(line)
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.queuePutState("COMPILE_ERR")
            return False

        self.log.info("Successfully flashed VESNA ...")
        self.queuePutState("ONLINE")
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

        self.queuePutInfo("Device reset complete!")
        return True



# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":

    # Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

    logging.info("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_NAME + "!")

    # Create 2 queue for communication between threads
    # Client -> VESNA
    C_V_QUEUE = Queue()
    # VESNA -> Clinet
    V_C_QUEUE = Queue()

    # Start client thread (communication with controller)
    client_thread = controller_client.zmq_client_thread(V_C_QUEUE, C_V_QUEUE, LGTC_NAME, SUBSCR_HOSTNAME, ROUTER_HOSTNAME)
    client_thread.start()

    # Start main thread (experiment with serial monitor)
    main_thread = experiment(C_V_QUEUE, V_C_QUEUE, RESULTS_FILENAME, LGTC_NAME)
    main_thread.runApp()
    main_thread.clean()

    logging.info("Main thread stopped, trying to stop client thread.")

    # Wait for a second so client can finish its transmission
    time.sleep(1)

    # Notify zmq client thread to exit its operation and join until quit
    client_thread.stop()
    client_thread.join()

    logging.info("Exit!")




# This script acts as a main thread while zmq_client is another thread to communicate with
# controller entity. Threads communicate with Queue (FIFO buffer).
# This script controls the VESNA platform and communicates with it. It is responsible to
# execute commands | forward commands .

# ----------------------------------------------------------------------------------------
# SUPPORTED COMMANDS
# ----------------------------------------------------------------------------------------
# Messages in the monitoring systems (between controller and node!) are formed as a list 
# with 2 arguments: message_type and command itself (example: ["11", "START"]). First 
# argument is important for other scripts...for incoming commands in this script it 
# represents command sequence number (SQN), so experiment will know, which response from 
# VESNA will corespond on which given command. 
#
# List of (currently) supported commands is given below:
#
#       * EXIT      - exit experiment application
#       * RESET     - reset the device (if possible)
#       * FLASH     - flash the device (if possible)#
#       * START     - start the application loop
#       * STOP      - stop the application loop
#       * RESTART
#       * LINES     - return the number of done measurements
#       * SEC       - return the number of elapsed seconds
#       * DURATION  - return the duration of the app
#       * CONTROLLER_DIED - indicates that client thread lost communication
#
#       Other supported commands differ on Contiki-NG application
#
# List of currently supported responses is given below:
#       * END
#       * JOIN_DAG
#       * EXIT_DAG
#       * ROOT
#
#
# Script may response in 3 ways - they are distinguished with message_type argument.
#
# INFO - means an update in the experiment (without any given command) - displayed in output window
# STATE - application / node changed its state - change displayed in monitor window
# SQN - a number which represents response sequence number

