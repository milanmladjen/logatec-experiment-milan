#!/usr/bin/python3

import queue
import threading
from queue import Queue

from datetime import datetime
import argparse
import os
import sys
import time
import logging
import binascii
import requests
from requests.auth import HTTPBasicAuth
import json

from subprocess import Popen, PIPE

LOG_LEVEL = logging.DEBUG

class BLE_experiment(threading.Thread):

    def __init__(self, input_q, output_q, results_filename):
        threading.Thread.__init__(self)
        self._is_thread_running = True
        self._is_app_running = False

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        self.in_q = input_q
        self.out_q = output_q

        self.file = open("../results/" + results_filename, "a+")
        self.file.write("Measurements on date: " + str(time.asctime(time.localtime(time.time()))))
        self.file.write("Detected beacons:")

    def run(self):
        self.queuePutState("ONLINE")
        self.log.info("Experiment started")

        while self._is_thread_running:

            ##### MAIN APP #####################################
            if self._is_app_running:

                with Popen(["./scanner"], stdout = PIPE, bufsize=1, universal_newlines=True, cwd = "/root/logatec-experiment/applications/02_localization") as p:
                    for line in p.stdout:
                        self.file.write(line)

                        if (not self.in_q.empty()):
                            sqn, cmd = self.queueGet()
                            
                            if sqn:
                                unixTime = int(time.time())
                                self.file.write("CMD [" + str(unixTime) + "] " + cmd + "\n")


                if p.returncode:
                    self.log.error("Command " + str(p.args) + " returned non-zero exit status " + str(p.returncode))

                #### ECMS #####################################
                # Store in file whatever comes to the node
                if (not self.in_q.empty()):
                    sqn, cmd = self.queueGet()
                    
                    if sqn:
                        self.file.write("CMD [" + str(time.time()) + "] " + cmd + "\n")



        # End of experiment
        self.log.info("Scanner stopped")

    def stop(self):
        self._is_thread_running = False
        self.log.info("Stopping BLE experiment thread")

    def clean(self):
        self.file.close()
        


    # ----------------------------------------------------------------------------------------
    # OTHER FUNCTIONS
    # ----------------------------------------------------------------------------------------
    def queuePutResp(self, sqn, resp):
        self.out_q.put([sqn, resp])
    
    def queuePutLoc(self, rssi):
        self.out_q.put(["LOC", rssi])

    def queuePutState(self, state):
        self.out_q.put(["STATE", state])

    def queuePutInfo(self, info):
        self.out_q.put(["INFO", info])

    def queueGet(self):
        tmp = self.in_q.get()
        return tmp[0], tmp[1]