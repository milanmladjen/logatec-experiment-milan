#!/usr/bin/python3

import queue
import threading
from queue import Queue

from datetime import datetime
from bluepy.btle import Scanner, Peripheral, ScanEntry
import argparse
import os
import sys
import time
import logging
import binascii
import requests
from requests.auth import HTTPBasicAuth
import json

PHONE_NAME = "Note20G"
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
        self.file.write("usaj neki more bit shranjeno v text fajlu, da obstaja")

        self.scr = Scanner()

    def run(self):
        self.queuePutState("ONLINE")
        self.log.info("Experiment started")

        try:
            self.scr.clear()
            self.scr.start()
        except:
            pass       

        while self._is_thread_running:

            ##### MAIN APP #####################################
            if self._is_app_running:

                if self.scr._helper is None:
                    try: 
                        self.log.info("Starting BLE helper.")
                        self.scr.start()
                    except:
                        self.log.error("Helper not started!")
                
                try:
                    timeout = None
                    resp = self.scr._waitResp(['scan', 'stat'], timeout)
                    if resp is None:
                        self.log.info("No response from BLE, exiting...")
                        break

                    respType = resp['rsp'][0]
                    if respType == 'stat':
                        self.log.info("Scan ended, restarting it...")
                        if resp['state'][0] == 'disc':
                            self.scr._mgmtCmd(self.scr._cmd())

                    elif respType == 'scan':
                        # device found
                        addr = binascii.b2a_hex(resp['addr'][0]).decode('utf-8')
                        addr = ':'.join([addr[i:i+2] for i in range(0,12,2)])
                        if addr in self.scr.scanned:
                            dev = self.scr.scanned[addr]
                        else:
                            dev = ScanEntry(addr, self.scr.iface)
                            self.scr.scanned[addr] = dev
                        isNewData = dev._update(resp)
                        self.handleDiscovery(dev, (dev.updateCount <= 1), isNewData)
                        
                    else:
                        self.log.warning("Unexpected response: " + respType)
                except:
                    pass


            #### ECMS #####################################
            if (not self.in_q.empty()):
                sqn, cmd = self.queueGet()

        # End of experiment
        self.log.debug("Scanner stopped")
        self.scr.stop()

    def stop(self):
        self._is_thread_running = False
        self.log.info("Stopping BLE experiment thread")

    def clean(self):
        self.file.close()
        


    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            self.log.info("New device ""[" + str(datetime.now().time())+"]: " + "N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
            self.file.write("New device ""[" + str(datetime.now().time())+"]: " + "N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
            #self.queuePutInfo("New device ""[" + str(datetime.now().time())+"]: " + "N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
  
        else:
            # 9 = ime naprave
            if(dev.getValueText(9) == PHONE_NAME):
                unixTime = int(time.time())
                self.queuePutInfo("Target RSSI " + "[" + str(unixTime) +"s]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI {" + str(dev.rssi) + "}\n")
                self.log.info("Target RSSI " + "[" + str(unixTime) +"s]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI {" + str(dev.rssi) + "}\n")
                self.file.write("Target RSSI " + "[" + str(unixTime) +"s]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI {" + str(dev.rssi) + "}\n")



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