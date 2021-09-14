#!/usr/bin/python3

from monitoring.experiment_LGTC import LOG_LEVEL
import queue
import threading
from queue import Queue

from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, ScanEntry, BTLEInternalError
import argparse
import os
import sys
import time
import logging
import binascii

LOG_LEVEL = logging.DEBUG
class BLE_experiment(threading.Thread):

    def __init__(self, input_q, output_q, results_name, lgtc_name):
        threading.Thread.__init__(self)
        self._is_thread_running = True

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        self.in_q = input_q
        self.out_q = output_q

        self.scr = Scanner()

    def run(self):
        self.log.info("Starting experiment thread...")
        self.queuePutState("RUNNING")

        self.scr.clear()
        self.scr.start()

        while self._is_thread_running:
            if self._helper is None:
                raise BTLEInternalError("Helper not started (did you call start()?)")
            remain = None
            resp = self._waitResp(['scan', 'stat'], remain)
            if resp is None:
                break

            respType = resp['rsp'][0]
            if respType == 'stat':
                # if scan ended, restart it
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
                isNewData = dev.scr._update(resp)
                self.handleDiscovery(dev, (dev.updateCount <= 1), isNewData)
                 
            else:
                raise BTLEInternalError("Unexpected response: " + respType, resp)
            
            if (not self.in_q.empty()):

                sqn, cmd = self.queueGet()

                if cmd == "LINES":
                    resp = "Število vrstic je xy"
                    self.queuePutResp(sqn, resp)
            self.scr.stop()

    def stop(self):
        self._is_thread_running = False
        self.log.info("Stopping BLE experiment thread")


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

    def handleDiscovery(self, dev, isNewDev, isNewData):

        if isNewDev:
            print("Discovered device", dev.addr, dev.rssi)
            self.log.info("[" + str(datetime.now().time())+"]: ")
            self.log.info("N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
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
                self.queuePutInfo("[" + str(int(time.time()))+"]: ")
                self.queuePutInfo("R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI " + str(dev.rssi) + "\n")
                print("RSSI of phone: ", dev.rssi)
                #for i in range(255):
                #	
                #	if(dev.getValueText(i)):
                #		print("  ", i, dev.getValueText(i)