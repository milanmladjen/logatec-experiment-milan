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

from queue import Queue
import sys
import os
import logging
import time
from timeit import default_timer as timer
from subprocess import Popen, PIPE

# Workaround to import files from parent dir
cdir = os.path.dirname(os.path.realpath(__file__))
pdir = os.path.dirname(cdir)
sys.path.append(pdir)

from lib import serial_monitor
from lib import file_logger

import controller_client



# ----------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# ----------------------------------------------------------------------------------------

# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://192.168.2.148:5562"
SUBSCR_HOSTNAME = "tcp://192.168.2.148:5561"

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
    APP_DIR = int(os.environ['APP_DIR'])
except:
    APP_DIR = "00_test"

APP_PATH = "/home/grega/Workspace/magistrska/logatec-experiment/applications/" + APP_DIR
APP_NAME = APP_DIR[3:]

#print("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_NAME)





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

        # file_logger.py - prepare measurements file
        self.f.prepare_file(filename, lgtcname)
        self.f.open_file()  

        # Experiment vars
        self._is_app_running = False
        self._command_waiting = None
        self._command_timeout = False
        self._lines_stored = 0



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

        elapsed_sec = 0
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
                    elapsed_sec += (timer() - loop_time)
                    loop_time = timer()
                    #self.log.debug("Elapsed seconds: " + str(elapsed_sec))

                    # Every 10 seconds
                    if elapsed_sec % 10 == 0:
                        
                        # Check if serial_monitor received something
                        if not self.monitor.serial_avaliable:
                            self.f.store_lgtc_line("Timeout detected.")
                            timeout_cnt += 1
                            self.log.warning("No lines read for more than 10 seconds..")

                        if timeout_cnt > 5:
                            self.f.warning("VESNA did not respond for more than a minute")
                            self.queuePut("STATE","VESNA_TIMEOUT")
                            self.log.error("VESNA did not respond for more than a minute")
                            timeout_cnt = 0
                            self._is_app_running = False
                            # We don't do anything here - let the user interfeer

                        # Set to False, so when monitor reads something, it goes back to True
                        self.monitor.serial_avaliable = False

                    # Every 3 seconds
                    if elapsed_sec % 3 == 0:
                        if self._command_waiting != None:
                            self.log.debug("Waiting for response...")
                            # If _command_timeout allready occurred - response on command was
                            # not captured for more than 3 seconds. Something went wrong, 
                            # so stop waiting for it
                            if self._command_timeout:
                                self.f.warning("Command timeout occurred!")
                                self.queuePut(self._command_waiting, "Failed to get response ...")
                                self.queuePut("STATE", "VESNA_TIMEOUT")
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

                    # If there is no SQN waiting for response, we got INFO message from VESNA for monitor
                    if(self._command_waiting):
                        self.queuePut(self._command_waiting, resp)
                        self.log.debug("Got response on cmd from VESNA: " + resp)
                    else:
                        self.queuePut("INFO", resp)
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

                # SYSTEM COMMANDS
                # Act upon system command
                if sqn == "SYS":

                    if cmd == "FLASH":
                        if not self.VESNA_flash():
                            break

                    elif cmd == "RESET":
                        self.VESNA_reset()
                        break

                    elif cmd == "EXIT":
                        self.stop()
                        break

                    # We need var state "_is_app_running" for timeout detection
                    elif cmd == "APP_STARTED":
                        elapsed_sec = 0
                        self._lines_stored = 0
                        self._is_app_running = True

                    elif cmd == "APP_STOPPED":
                        self._is_app_running = False

                    else:
                        self.log.warning("Unsupported SYS command " + cmd)


                # EXPERIMENT COMMANDS
                # Check if there is a command on which we can respond here,
                # otherwise forward it to VESNA 
                else:

                    self.f.store_lgtc_line("Got command [" + sqn + "]: " + cmd)
                    self.log.info("Got command [" + sqn + "]: " + cmd)

                    # Return number of lines read
                    if cmd == "LINES":
                        resp = "Lines stored: " + str(self._lines_stored)
                        self.queuePut(sqn, resp)
                        self.f.store_lgtc_line(resp)

                    # Return number of seconds since the beginning of app
                    elif cmd == "SEC":
                        resp = "Seconds passed: " + str(round(elapsed_sec, 1)) + "s"
                        self.queuePut(sqn, resp)
                        self.f.store_lgtc_line(resp)

                    # Return the predefined application duration
                    elif cmd == "DURATION":
                        resp = "Defined duration: " + str(APP_DURATION) + "min"
                        self.queuePut(sqn, resp)
                        self.f.store_lgtc_line(resp)

                    # Forward command to VESNA
                    else:
                        self.monitor.send_command(cmd)
                        self._command_waiting = sqn
    

    def clean(self):
        self.monitor.close()
        self.f.close()

    def stop(self):
        self.monitor.send_command("STOP")
        self.f.store_lgtc_line("Application exit!")
        self.log.info("Application exit!")

    def queuePut(self, sqn, resp):
        self.out_q.put([sqn, resp])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]





    # ----------------------------------------------------------------------------------------
    # VESNA CONTROLL
    # -------------------------------------------------------------------------------------
    # Connect to VESNA serial port
    def VESNA_connect(self):
        if not self.monitor.connect_to("ttyUSB0"):
            self.f.error("Couldn't connect to VESNA.")
            self.LGTC_state_change("VESNA_ERR")
            self.log.error("Couldn't connect to VESNA.")
            return
        
        self.log.info("Successfully connected to VESNA serial port!")
        return True

    # Sync with application 
    def VESNA_sync(self):
        if not self.monitor.sync_with_vesna():
            self.f.error("Couldn't sync with VESNA.")
            self.LGTC_state_change("VESNA_ERR")
            self.log.error("Couldn't sync with VESNA.")
            return False

        self.LGTC_send_sys_resp("SYNCED_WITH_VESNA")
        self.log.info("Synced with VESNA over serial ...")
        return True

    # Compile the C app and VESNA with its binary
    def VESNA_flash(self):
        # Compile the application
        self.LGTC_state_change("COMPILING")
        self.log.info("Complie the application.")
        #procDistclean = Popen(["make", "distclean"])
        with Popen(["make", APP_NAME, "-j9"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as pr:
            for line in pr.stdout:
                self.log.debug(line)    #TODO maybe use print(line, end="")
        if pr.returncode:
            self.log.error("Command " + str(pr.args) + " returned non-zero exit status " + str(pr.returncode))
            self.LGTC_state_change("COMPILE_ERR")
            return False

        # Flash the VESNA with app binary
        self.log.info("Flash the app to VESNA .. ")
        with Popen(["make", APP_NAME + ".olimex"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = APP_PATH) as p:
            for line in p.stdout:
                self.log.debug(line)
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.LGTC_state_change("COMPILE_ERR")
            return False

        self.log.info("Successfully flashed VESNA ...")
        self.LGTC_state_change("FLASHED")
        return True

    # Make a hardware reset on VESNA
    def VESNA_reset(self):
        self.log.info("VESNA hardware reset.")
        print("\n\n Preform reset please! \n")
        time.sleep(1)

        self.LGTC_send_info_resp("Device reset complete!")
        """
        try:
            os.system('echo 66 > /sys/class/gpio/export')
        except Exception:
            pass
        os.system('echo out > /sys/class/gpio/gpio66/direction')

        os.system('echo 0 > /sys/class/gpio/gpio66/value')
        os.system('echo 1 > /sys/class/gpio/gpio66/value')
        """



# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":

    # Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
    #logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

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

