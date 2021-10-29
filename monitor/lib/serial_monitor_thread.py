#!/usr/bin/python3


import threading
from queue import Queue
import sys
import os
import logging
import time
from timeit import default_timer as timer
from subprocess import Popen, PIPE

from lib import serial_monitor
from lib import file_logger


# DEFINITIONS
LOG_LEVEL = logging.DEBUG
SERIAL_TIMEOUT = 2  # In seconds


class serial_monitor_thread(threading.Thread):

    # ----------------------------------------------------------------------------------------
    # INIT
    # ----------------------------------------------------------------------------------------
    def __init__(self, input_q, output_q, filename, lgtcname, app_name, app_path):

        threading.Thread.__init__(self)
        self._is_thread_running = True
        self.app_name = app_name
        self.app_path = app_path

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        # Init lib
        self.monitor = serial_monitor.serial_monitor(SERIAL_TIMEOUT)
        self.f = file_logger.file_logger()

        # Link multithread input output queue
        self.in_q = input_q
        self.out_q = output_q

        # file_logger.py - prepare measurements file
        self.f.prepare_file(filename, lgtcname)
        self.f.open_file()  

        # Experiment vars
        self._command_waiting = None
        self._command_timeout = False

        # Class vars
        self.lines_stored = 0
        self.elapsed_sec = 0


    # ----------------------------------------------------------------------------------------  
    # MAIN
    # ----------------------------------------------------------------------------------------
    def run(self):

        self.log.info("Starting serial monitor thread!")

        # Connect to VESNA serial port
        if not self.VESNA_connect():
            return

        # Flash VESNA with application
        if not self.VESNA_flash():
            return     

        # Sync with experiment application
        if not self.VESNA_sync():
            return

        timeout_cnt = 0
        loop_time = timer()

        while self._is_thread_running:

            # -------------------------------------------------------------------------------
            # SERAIL_MONITOR - FAILSAFE
            # You can disable it by changing value to False (TODO different mechanism?)
            #   * Check if serial was available in last 10 seconds
            #   * Check if we got respond on a command in last 3 sec
            if True:

                # Count seconds
                if ((timer() - loop_time) > 1):
                    self.elapsed_sec += (timer() - loop_time)
                    loop_time = timer()
                    #self.log.debug("Elapsed seconds: " + str(self.elapsed_sec))

                    # Every 10 seconds
                    if self.elapsed_sec % 10 == 0:
                        
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
                    if self.elapsed_sec % 3 == 0:
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
                self.lines_stored += 1

                # If we got response on the command
                # TODO: check if it is a multiline response
                if data[0] == "$":

                    # Remove first 2 char '$ ' and last two char '\n'
                    resp = data[2:-1]

                    # If application just started, reset values
                    if resp == "START":
                        self.lines_stored = 0
                        self.elapsed_sec = 0

                    # If there is no SQN waiting for response, we got INFO message from VESNA for monitor
                    if(self._command_waiting):
                        self.queuePutResp(self._command_waiting, resp)
                        self.log.debug("Got response on cmd from VESNA: " + resp)
                    else:
                        # TODO: if there is command waiting but VESNA responds with info, SQN is lost - 
                        # Fix this with another character for info (@-sync, $-cmd, &-info for example)
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

                if cmd == "LINES":
                    resp = "Sotred lines: " + self.lines_stored
                    self.queuePutResp(sqn, resp)
                else:
                    self.monitor.send_command(cmd)
                    self._command_waiting = sqn


    # ----------------------------------------------------------------------------------------
    # END
    # ----------------------------------------------------------------------------------------
    def stop(self):
        self._is_thread_running = False
        self.monitor.send_command("STOP")
        self.f.store_lgtc_line("Application exit!")
        self.log.info("Stopping serial monitor thread")
        self.monitor.close()
        self.f.close()

    
    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------
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
        with Popen(["make", self.app_name, "-j2"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = self.app_path) as p:
            for line in p.stdout:
                self.log.debug(line)    #TODO maybe use print(line, end="")
        if p.returncode:
            self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))
            self.queuePutState("COMPILE_ERR")
            return False

        # Flash the VESNA with app binary
        self.log.info("Flash the app to VESNA .. ")
        with Popen(["make", self.app_name + ".logatec3"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = self.app_path) as p:
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

