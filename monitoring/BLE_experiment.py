#!/usr/bin/python3

import queue
import threading
from queue import Queue

from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate, Peripheral
import argparse
import os
import sys
import time
class BLE_experiment(threading.Thread):

    def __init__(self, input_q, output_q, results_name, lgtc_name):
        threading.Thread.__init__(self)
        self._is_thread_running = True

        self.in_q = input_q
        self.out_q = output_q

        self.scr = Scanner().withDelegate(ScanDelegate())

    def run(self):
        print("Starting experiment thread...")
        self.queuePutState("RUNNING")
        # Start advertising

        while self._is_thread_running:
            print("Running...")
            # Scan BLE interface
            self.scr.scan(timeout=120, passive=True) 

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

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.file = open("neki.txt", mode="w", encoding = "ASCII")


    def handleDiscovery(self, dev, isNewDev, isNewData):

        if isNewDev:
            print("Discovered device", dev.addr, dev.rssi)
            #file.write("[" + str(datetime.now().time())+"]: ")
            #file.write("N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
        #elif isNewData:
            #print(dev.addr, dev.rssi, dev.updateCount, dev.getValueText(10), "Received new data")
            #file.write("[" + str(datetime.now().time())+"]: ")
            #file.write("D " + str(dev.addr) + " RSSI" + str(dev.rssi) + " CNT" + str(dev.updateCount) + "\n")
        else:
            #print(dev.addr, dev.rssi, dev.updateCount, dev.getValueText(10), "Update rssi")
            #file.write("[" + str(time.time())+"]: ")
            #file.write("R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI" + str(dev.rssi) + "\n")
        #per = Peripheral(dev.addr)
        #print(per.getServices())
        # this is how you get other info (advertising name, TX power... but LGTC isn't advertising much 
            if(dev.getValueText(9) == "OnePlus Nordic"):
                self.file.write("[" + str(int(time.time()))+"]: ")
                self.file.write("R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI " + str(dev.rssi) + "\n")
                print("RSSI of phone: ", dev.rssi)
                #for i in range(255):
                #	
                #	if(dev.getValueText(i)):
                #		print("  ", i, dev.getValueText(i))
