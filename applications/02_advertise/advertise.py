#!/usr/bin/python3

import queue
import threading
from queue import Queue

from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate, Peripheral
import argparse
import os
import subprocess
import sys
import time
class BLE_experiment(threading.Thread):

    def __init__(self, input_q, output_q, results_filename, lgtc_name, experiment_name):
        threading.Thread.__init__(self)
        self._is_thread_running = True

        self.in_q = input_q
        self.out_q = output_q

    def run(self):
        print("Starting experiment thread...")
        self.queuePutState("RUNNING")
        # Start advertising

        while self._is_thread_running:
            print("Running...")
            # Stop scanning BLE
            print("Disabling scanning...")
            subprocess.call(["hciconfig", "hci0", "noscan"])
            subprocess.call(["hcitool", "cmd", "0x03", "0x0003"]) #reset command

            #Advertising parameters
            #reset cmd hcitool cmd 0x03 0x0003
            #interval = 200ms -> time = n * 0.625ms -> n = 320 = 0x0140
            #hcitool -i hci0 cmd 0x08 0x0006 40 01 40 01 00 00 00 00 00 00 00 00 00 07 00 
            print("Setting parameters...")
            subprocess.call(["hcitool", "-i", "hci0", "cmd", "0x08", "0x0006", "40", "01", "40", "01", "00", "00", "00", "00", "00", "00", "00", "00", "00", "07", "00"])

            #Start advertising 
            print("Starting advertising...")
            subprocess.call(["hcitool", "-i", "hci0", "cmd", "0x08", "0x00a", "0x01"])
            print("Advertising")
            time.sleep(60)
            print("Stopping advertising...")
            subprocess.call(["hcitool", "-i", "hci0", "cmd", "0x08", "0x00a", "0x00"])

            # -------------------------------------------------------------------------------
            # CONTROLLER CLIENT - GET COMMANDS
            # Check for incoming commands for queue - only when there is time 
            if (not self.in_q.empty()):

                sqn, cmd = self.queueGet()

                if cmd == "LINES":
                    resp = "Število vrstic je xy"
                    self.queuePutResp(sqn, resp)
            self.stop()

    def stop(self):
        self._is_thread_running = False
        print("Stopping BLE experiment thread")


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
