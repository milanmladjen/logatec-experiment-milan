#!/usr/bin/python3

# LGTC EMULATOR - for testing without VESNA device connected to LGTC


from queue import Queue
import threading
import sys
import os
import logging
import time
from timeit import default_timer as timer


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

ROUTER_HOSTNAME = "tcp://192.168.88.239:5562"
SUBSCR_HOSTNAME = "tcp://192.168.88.239:5561"

#ROUTER_HOSTNAME = "tcp://192.168.89.250:5562"
#SUBSCR_HOSTNAME = "tcp://192.168.89.250:5561"

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

print("Testing application " + APP_NAME + " for " + str(APP_DURATION) + " minutes on device " + LGTC_NAME)



# ----------------------------------------------------------------------------------------
# EXPERIMENT APPLICATION
# ----------------------------------------------------------------------------------------
class experiment():

    def __init__(self, input_q, output_q, filename, lgtcname):

        self.log = logging.getLogger(__name__)

        # Init lib
        """self.monitor = serial_monitor.serial_monitor(2)"""
        self.txt = file_logger.file_logger()

        # controller_client.py - link multithread input output queue
        self.in_q = input_q
        self.out_q = output_q

        # file_logger.py - prepare measurements file
        self.txt.prepare_file(filename, lgtcname)
        self.txt.open_file()  

        # Experiment vars
        self._is_app_running = False
        self._command_waiting = None
        self._command_timeout = False
        self._lines_stored = 0



    def run(self):

        self.log.info("Starting experiment main thread!")
        """
        # Connect to VESNA serial port
        if not self.monitor.connect_to("ttyS2"):
            self.log.error("Couldn't connect to VESNA.")
            self.LGTC_sys_resp("VESNA_ERR")
            return
        """
        self.log.info("Successfully connected to VESNA serial port!")

        elapsed_sec = 0
        timeout_cnt = 0
        loop_time = timer()

        try:
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
                                self.txt.store_lgtc_line("Timeout detected.")
                                timeout_cnt += 1
                                self.log.warning("No lines read for more than 10 seconds..")

                            if timeout_cnt > 5:
                                self.txt.warning("VESNA did not respond for more than a minute")
                                self.LGTC_sys_resp("VESNA_TIMEOUT")
                                self.log.error("VESNA did not respond for more than a minute")
                                timeout_cnt = 0
                                self._is_app_running = False
                                # We don't do anything here - let the user interfeer

                            # Set to False, so when monitor reads something, it goes back to True
                            self.monitor.serial_avaliable = False

                        # Every 3 seconds
                        if elapsed_sec % 3 == 0:
                            if self._command_waiting != None:
                                # If _command_timeout allready occurred - response on command was
                                # not captured for more than 3 seconds. Something went wrong, 
                                # so stop waiting for it
                                if self._command_timeout:
                                    self.txt.warning("Command timeout occurred!")
                                    self.LGTC_cmd_resp([self._command_waiting, "Failed to get response ..."])
                                    self.log.warning("No response on command for more than 3 seconds!")
                                    self._command_timeout = False
                                    self._command_waiting = None
                                
                                self._command_timeout = True

                # -------------------------------------------------------------------------------
                # SERIAL MONITOR - READ UART
                # Read and store everything that comes on Serial connection
                # If line is a response, forward it to controller
                """
                if self.monitor.input_waiting():
                    data = self.monitor.read_line()

                    self.txt.store_line(data)
                    self._lines_stored += 1

                    # If we got response on the command
                    # TODO: check if it is a multiline response
                    if data[0] == "*":
                        self.LGTC_cmd_resp([self._command_waiting, data[1:]])
                        self._command_waiting = None
                        self._command_timeout = False
                        self.log.debug("Got response on cmd " + data[1:])
                    
                    # If we got stop command
                    elif data[0] == "=":
                        self.LGTC_sys_resp("END_OF_APP")
                        self._command_waiting = None
                        self._command_timeout = False
                        self._is_app_running = False
                        self.log.info("Got end-of-app response!")
                """
                # Fake response
                if self._command_waiting != None:
                    fake_data = "*Odgovor na CMD*"
                    self.LGTC_cmd_resp([self._command_waiting, fake_data[1:]])
                    self._command_waiting = None
                    self._command_timeout = False
                    self.log.debug("Got response " + fake_data[1:])
                else:
                    time.sleep(0.7)
                    fake_data = "Prebrana vrstica"

                # Store fake line into the file
                self.txt.store_line(fake_data)
                self._lines_stored += 1

                # -------------------------------------------------------------------------------
                # CONTROLLER CLIENT - GET COMMANDS
                # Check for incoming commands only when there is time - nothing to do on UART
                # If all comand responses were received (not waiting for one)
                # and there is new command in queue, forward it to VESNA
                if (not self.in_q.empty() and self._command_waiting == None):

                    cmd = self.LGTC_rec_cmd()

                    # SYSTEM COMMANDS
                    if cmd[0] == "-1":

                        # > Start the app (with app running time as an argument)
                        if cmd[1] == "START_APP":
                            if self._is_app_running == True:
                                self.LGTC_cmd_resp("0", "App is allready running...")
                            else:
                                if not self.LGTC_app_start(APP_DURATION):
                                    break
                                self._lines_stored = 0
                                self._is_app_running = True
                                elapsed_sec = 0

                        elif cmd[1] == "STOP_APP":
                            if not self.LGTC_app_stop():
                                break
                            self._is_app_running = False

                        elif cmd[1] == "RESTAR_APP":
                            #self.LGTC_app_stop()
                            self.LGTC_vesna_reset()
                            #time.sleep(1)
                            #self.LGTC_vesna_sync()
                            if not self.LGTC_app_start(APP_DURATION):
                                break
                            self._lines_stored = 0
                            self._is_app_running = True
                            elapsed_sec = 0

                        # @ Sync with VESNA - start the serial_monitor but not the app 
                        # #TODO add while(1) to VESNA main loop
                        if cmd[1] == "SYNC_WITH_VESNA":
                            if not self.LGTC_vesna_sync():
                                break

                        elif cmd[1] == "EXIT":
                            self.LGTC_app_exit()
                            break

                        elif cmd[1] == "FLASH":
                            if not self.LGTC_vesna_flash():
                                self.LGTC_sys_resp("COMPILE_ERR")
                            self.LGTC_sys_resp("FLASHED") 

                    # EXPERIMENT COMMANDS
                    else:
                        # Return number of lines read
                        if cmd[1] == "LINES":
                            self.LGTC_cmd_resp([cmd[0], ("LINES " + str(_lines_stored))])

                        # Return number of seconds since the beginning of app
                        elif cmd[1] == "SEC":
                            self.LGTC_cmd_resp([cmd[0], ("SEC " + str(elapsed_sec))])

                        # Forward command to VESNA
                        else:
                            """self.monitor.send_command(cmd[1])"""
                            self._command_waiting = cmd[0]

                        # Log it to file as well
                        self.txt.store_lgtc_line("Received command [" + cmd[0] + "]: " + cmd[1])
                        self.log.debug("Received command [" + cmd[0] + "]: " + cmd[1])

        # ------------------------------------------------------------------------------------
        except KeyboardInterrupt:
            self.log.info("\n Keyboard interrupt!.. Stopping the monitor")
            self.LGTC_app_exit()
            self.LGTC_sys_resp("END_OF_APP")

        except serial.SerialException:
            self.log.error("Serial error!.. Stopping the monitor")

        except IOError:
            self.log.error("Serial port disconnected!.. Stopping the monitor")
        
        finally:
            # Clear resources
            #self.monitor.close()
            self.txt.close()
            return         


    # ------------------------------------------------------------------------------------
    # CLASS FUNCTIONS
    # ------------------------------------------------------------------------------------
    def LGTC_sys_resp(self, state):
        self.out_q.put(["-1", state])

    def LGTC_cmd_resp(self, nbr, resp):
        self.out_q.put([nbr, resp])

    def LGTC_rec_cmd(self):
        return self.in_q.get()



    def LGTC_app_start(self, duration):
        """if not self.monitor.start_app(str(duration * 60)):
            self.txt.warning("Couldn't start the APP.")
            self.LGTC_sys_resp("VESNA_ERR")
            self.log.error("Couldn't start the APP.")
            return False
        """
        self.txt.store_lgtc_line("Application started!")
        self.LGTC_sys_resp("START_APP")
        self.log.info("Application started!")
        return True

    def LGTC_app_stop(self):
        """if not self.monitor.stop_app():
            self.txt.warning("Couldn't stop the APP.")
            self.LGTC_sys_resp("VESNA_ERR")
            self.log.error("Couldn't stop the APP.")
            return False
        """
        self.txt.store_lgtc_line("Application stopped!")
        self.LGTC_sys_resp("STOP_APP")
        self.log.info("Application stopped!")
        return True

    def LGTC_app_exit(self):
        """self.monitor.stop_app()"""
        self.txt.store_lgtc_line("Application exit!")
        self.log.info("Application exit!")


    # Sync with application 
    def LGTC_vesna_sync(self):
        """if not self.monitor.sync_with_vesna():
            self.txt.warning("Couldn't sync with VESNA.")
            self.LGTC_sys_resp("VESNA_ERR")
            self.log.error("Couldn't sync with VESNA.")
            return False
        """
        self.txt.store_lgtc_line("Synced with VESNA ...")
        self.LGTC_sys_resp("SYNCED_WITH_VESNA")
        self.log.info("Synced with VESNA over serial ...")
        return True

    # Compile the C app and VESNA with its binary
    def LGTC_vesna_flash(self):
        """# Compile the application
        self.log.info("Complie the application.")
        procCompile = Popen(["make", APP_NAME, "-j2"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
        stdout, stderr = procCompile.communicate()
        self.log.debug(stdout)
        if(stderr):
            self.log.debug(stderr)
            return False

        # Flash the VESNA with app binary
        self.log.info("Flash the app to VESNA .. ")
        procFlash = Popen(["make", APP_NAME + ".logatec3"], stdout = PIPE, stderr= PIPE, cwd = APP_PATH)
        stdout, stderr = procFlash.communicate()
        self.log.debug(stdout)
        if(stderr):
            self.log.debug(stderr)
            return False

        self.log.info("Successfully flashed VESNA")
        return True
        """
        try:
            print("Device is \"compiling\" the code for VESNA...")
            time.sleep(10)
        except KeyboardInterrupt:
            print(" ")
        finally:
            print("Compiled application!")

        return True


    # Make a hardware reset on VESNA
    def LGTC_vesna_reset(self):
        """
        self.log.info("VESNA hardware reset.")
        try:
            os.system('echo 66 > /sys/class/gpio/export')
        except Exception:
            pass
        os.system('echo out > /sys/class/gpio/gpio66/direction')

        os.system('echo 0 > /sys/class/gpio/gpio66/value')
        os.system('echo 1 > /sys/class/gpio/gpio66/value')
        """
        print("\"Reseting\" VESNA")


# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":

    # Use this logging setup for testbed usage
    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=logging.DEBUG, filename=LOGGING_FILENAME)
    # Use this logging setup for testing 
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s()] %(message)s", level=LOG_LEVEL)
    #logging.root.setLevel(logging.DEBUG)

    # Create 2 queue for communication between threads
    # LGTC -> VESNA
    L_V_QUEUE = Queue()
    # VESNA -> LGTC
    V_L_QUEUE = Queue()

    # Start client thread (communication with controller)
    client_thread = controller_client.zmq_client_thread(V_L_QUEUE, L_V_QUEUE, LGTC_NAME, SUBSCR_HOSTNAME, ROUTER_HOSTNAME)
    client_thread.start()

    # Start main thread (experiment with serial monitor)
    main_thread = experiment(L_V_QUEUE, V_L_QUEUE, RESULTS_FILENAME, LGTC_NAME)
    main_thread.run()

    logging.info("Main thread stopped, trying to stop client thread.")

    # Notify zmq client thread to exit its operation and join until quit
    client_thread.stop()
    client_thread.join()

    logging.info("Exit!")




# ----------------------------------------------------------------------------------------
# SUPPORTED COMMANDS
# ----------------------------------------------------------------------------------------
# Incoming commands must be formated as a list with 2 string arguments: message number 
# and command itself (example: ["66", "STATE"]). Message number is used as a sequence
# number, but if it is set to "-1", command represents SYSTEM COMMAND:
#
# --> SYSTEM COMMANDS - used for controll over the LGTC monitoring application
#
#       * START_APP       - start the experiment application
#       * STOP_APP        -
#       * RESTART_APP     - 
#       * FLASH           - flash VESNA with experiment application
#       * SYNC_WITH_VESNA - start the serial monitor
#       * EXIT            - exit monitoring application
#       
#       * STATE           - return the current state of monitoring application
#       * SYNC            - used to synchronize LGTC with broker/server
#       * ACK             - acknowledge packet sent as a response on every message
#       
# --> EXPERIMENT COMMANDS - used for controll over the VESNA experiment application
#
#       * LINES           - return the number of lines stored in measurement file
#       * SEC             - return the number of elapsed seconds since the beginning of exp.
#       TODO:
#       They should start with the char "*" so VESNA will know?
#       Depend on Contiki-NG application
#
