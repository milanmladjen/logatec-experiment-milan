# ----------------------------------------------------------------------
# SERIAL MONITOR: Communication between VESNA and LGTC via UART
# Class for multithread application
# ----------------------------------------------------------------------
import threading
from queue import Queue
import logging
from timeit import default_timer as timer

from lib import serial_monitor
from lib import file_logger


class serial_monitor_thread(threading.Thread):

    def __init__(self, input_q, output_q, filename, lgtcname):
        # Thread
        threading.Thread.__init__(self)
        self._is_thread_running = True
        self._is_app_running = False
        self.in_q = input_q
        self.out_q = output_q

        # Serial monitor
        self.monitor = serial_monitor.serial_monitor(2)
        self._lines_stored = 0

        # File logger
        self.log = file_logger.file_logger()
        self.log.prepare_file(filename, lgtcname)
      

    def run(self):
        
        elapsed_sec = 0
        timeout_cnt = 0
        command_waiting = None
        command_timeout = False
        loop_time = timer()
        
        print("Starting serial monitor thread")   

        # Connect to VESNA serial port
        logging.info("Connect to VESNA serial port ....")
        if not self.monitor.connect_to("ttyS2"):
            logging.error("Couldn't connect to VESNA.")
            self.out_q.put(["-1", "VESNA_ERR"])
            self._is_thread_running = False

        # Open file to store measurements
        self.log.open_file()        
        
        # ------------------------------------------------------------------
        # Main while loop
        while self._is_thread_running:

            # ------------------------------------------------------------------
            # Failsafe - Check if serial was available in last 10 seconds
            # Failsafe - Check if we got respond on a command in last 3 sec
            if self._is_app_running:

                # Every second
                if ((timer() - loop_time) > 1):
                    elapsed_sec += (timer() - loop_time)
                    loop_time = timer()
                    logging.debug("Elapsed seconds: " + str(elapsed_sec))

                    # Every 10 seconds
                    if elapsed_sec % 10 == 0:

                        if not self.monitor.serial_avaliable:
                            self.log.store_lgtc_line("Timeout detected.")
                            timeout_cnt += 1
                            logging.debug("No lines read for more than a 10 seconds")

                        if timeout_cnt > 5:
                            self.log.warning("VESNA did not respond for more than a minute")
                            self.out_q.put(["-1", "VESNA_TIMEOUT"])
                            timeout_cnt = 0
                            logging.error("VESNA did not respond for more than a minute")
                            self._is_app_running = False
                            # We don't do anything here - let the user interfeer

                        # Force variable to False, so when monitor reads something, it goes back to True
                        self.monitor.serial_avaliable = False

                    # Every 3 seconds
                    if elapsed_sec % 3 == 0:
                        if command_waiting != None:
                            # If command_timeout allready occurred - response on command was not captured 
                            # for more than 3 seconds. Something went wrong, so stop waiting for it
                            if command_timeout:
                                self.log.warning("Command timeout occurred!")
                                self.out_q.put([command_waiting, "Failed to get response from VESNA"])
                                logging.warning("Command timeout occurred!")
                                command_timeout = False
                                command_waiting = None
                            
                            command_timeout = True

            # ------------------------------------------------------------------
            # Read line from VESNA
            if self.monitor.input_waiting():
                data = self.monitor.read_line()

                # Store the line into file
                self.log.store_line(data)
                self._lines_stored += 1

                # If we got response on the command
                if data[0] == "*":
                    self.out_q.put([command_waiting, data[1:]])
                    command_waiting = None
                    command_timeout = False
                    logging.debug("Got response " + data[1:])
                
                # If we got stop command
                elif data[0] == "=":
                    self.out_q.put(["-1","END_OF_APP"])
                    command_waiting = None
                    command_timeout = False
                    self._is_app_running = False
                    logging.debug("Got end-of-app response")
                
                

            # ------------------------------------------------------------------
            # If we are not witing for any response
            # and there is any command in queue, send it to VESNA
            elif (not self.in_q.empty() and command_waiting == None):
                cmd = self.in_q.get()

                # SYSTEM COMMANDS
                if cmd[0] == "-1":

                    # @ Sync with VESNA - start the serial_monitor but not the app #TODO add while(1) to VESNA main loop
                    if cmd[1] == "SYNC_WITH_VESNA":
                        if not self.monitor.sync_with_vesna():
                            self.out_q.put(["-1", "VESNA_ERR"])
                            self._is_thread_running = False
                            self.log.warning("Couldn't sync with VESNA.")
                            logging.error("Couldn't sync with VESNA.")
                        
                        self.out_q.put(["-1", "SYNCED_WITH_VESNA"])
                        self.log.store_lgtc_line("Synced with VESNA ...")
                        logging.info("Synced with VESNA ...")
                    
                    # > Start the app (with app running time as an argument)
                    elif cmd[1] == "START_APP":
                        if not self.monitor.start_app(str(APP_DURATION * 60)):
                            self.out_q.put(["-1", "VESNA_ERR"])
                            self._is_thread_running = False
                            self.log.warning("Couldn't start the APP.")
                            logging.error("Couldn't start the APP.")
                        
                        self._is_app_running = True
                        self.out_q.put(["-1", "START_APP"])
                        self.log.store_lgtc_line("Application started!")
                        logging.info("Application started!")

                    # = Stop the app
                    elif cmd[1] == "STOP_APP":
                        if not self.monitor.stop_app():
                            self.out_q.put(["-1", "VESNA_TIMEOUT"])
                            self.log.warning("Couldn't stop the APP.")
                            logging.error("Couldn't stop the APP.")
                        
                        self._is_app_running = False
                        self.out_q.put(["-1", "STOP_APP"])
                        self.log.store_lgtc_line("Application stopped!")
                        logging.info("Application stopped!")

                # EXPERIMENT COMMANDS
                else:
                    # Return number of lines read
                    if cmd[1] == "LINES":
                        self.out_q.put([cmd[0], ("LINES " + str(self._lines_stored))])

                    # Return number of seconds since the beginning of app
                    elif cmd[1] == "SEC":
                        self.out_q.put([cmd[0], ("SEC " + str(elapsed_sec))])

                    # Forward command to VESNA
                    else:
                        self.monitor.send_command(cmd[1])
                        command_waiting = cmd[0]

                    # Log it to file as well
                    self.log.store_lgtc_line("Received command [" + cmd[0] + "]: " + cmd[1])
                    logging.debug("Received command [" + cmd[0] + "]: " + cmd[1])

            # ------------------------------------------------------------------
            else:
                print(".")
                # TODO: Update status line in terminal.
                #print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
                #str(int(APP_DURATION)) + " min)", end="\r")
        
        # ------------------------------------------------------------------
        # Close everything on the end
        self.monitor.close()
        self.log.close()
        

    def stop(self):
        self._is_thread_running = False
