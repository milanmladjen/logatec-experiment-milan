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

PHONE_NAME = "Grega20"
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
                    print("a")
                    self.log.info("A")
                    resp = self.scr._waitResp(['scan', 'stat'], timeout)
                    if resp is None:
                        self.log.info("No response from BLE, exiting...")
                        #break
                    print("b")
                    self.log.info("B")
                    respType = resp['rsp'][0]
                    if respType == 'stat':
                        self.log.info("Scan ended, restarting it...")
                        if resp['state'][0] == 'disc':
                            self.scr._mgmtCmd(self.scr._cmd())
                            print("c")
                            self.log.info("C")

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
                        print("d")
                        self.log.info("D")
                        
                    else:
                        self.log.warning("Unexpected response: " + respType)
                except:
                    print("e")
                    self.log.info("E")
                    pass


            #### ECMS #####################################
            if (not self.in_q.empty()):
                sqn, cmd = self.queueGet()

                if sqn:
                    self.file.write(cmd + "\n")

                print("f")
                self.log.info("F")


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
            if(dev.getValueText(9) == PHONE_NAME):
                self.queuePutInfo("Found phone")
        else:

            unixTime = int(time.time())
            # 9 = ime naprave
            if(dev.getValueText(9) == PHONE_NAME):
                self.file.write("RSSI " + "[" + str(unixTime) + "]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") {" + str(dev.rssi) + "}\n")
                #self.file.write("Ttt")
                #self.log.info("Phone RSSI " + "[" + str(unixTime) +"s]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI {" + str(dev.rssi) + "}\n")
                #self.queuePutInfo("Target RSSI " + "[" + str(unixTime) +"s]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI {" + str(dev.rssi) + "}\n")
                #self.queuePutLoc(str(dev.rssi))
            
            #if(dev.getValueText(9) == "Galaxy S10e"):
            #    self.file.write("Aaa")
            #    self.queuePutLoc(str(dev.rssi))



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