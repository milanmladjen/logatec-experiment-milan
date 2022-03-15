#!/usr/bin/python3


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
RESULTS_FILENAME = "node_results"
LOGGING_FILENAME = "logger"

class BLE_experiment():

    def __init__(self, results_filename):
        #threading.Thread.__init__(self)
        self._is_thread_running = True
        self._is_app_running = True

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        self.file = open("/root/logatec-experiment/results/" + results_filename, "a+")
        self.file.write("usaj neki more bit shranjeno v text fajlu, da obstaja")

        self.scr = Scanner()

    def run(self):
        self.log.info("Experiment started")

        self.scr.clear()
        self.scr.start()
      

        start = time.time()
        while self._is_thread_running:

            if (time.time() - start >= 100):
                self._is_thread_running = False
                self.log.info("Exit")


            ##### MAIN APP #####################################
            if self._is_app_running:

                if self.scr._helper is None:
                    try: 
                        self.log.info("Starting BLE helper.")
                        self.scr.start()
                    except:
                        self.log.error("Helper not started!")

                # Timeout in seconds
                timeout = None
                self.log.info("A")
                resp = self.scr._waitResp(['scan', 'stat'], timeout)
                if resp is None:
                    self.log.info("No response from BLE, exiting...")
                    self.scr.start()
                    #break

                self.log.info("B")
                # ZDEJ KU JE timeout maš lohku resp=None in tuki vrže error
                respType = resp['rsp'][0]
                if respType == 'stat':
                    self.log.info("Scan ended, restarting it...")
                    if resp['state'][0] == 'disc':
                        self.log.info("C")
                        self.scr._mgmtCmd(self.scr._cmd())

                elif respType == 'scan':
                    self.log.info("D")
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
            if(dev.getValueText(9) == PHONE_NAME):
                self.log.info("Phone found")
        else:

            unixTime = int(time.time())
            self.log.debug("RSSI " + "[" + str(unixTime) + "]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") {" + str(dev.rssi) + "}\n")
            # 9 = ime naprave
            if(dev.getValueText(9) == PHONE_NAME):
                self.file.write("RSSI " + "[" + str(unixTime) + "]: " + "R " + str(dev.addr) + " (" + str(dev.updateCount) + ") {" + str(dev.rssi) + "}\n")
 



if __name__ == "__main__":

    try:
        LGTC_ID = sys.argv[1]
        LGTC_ID = LGTC_ID.replace(" ", "")
    except:
        print("No device name was given...going with default")
        LGTC_ID = "xy"

    LGTC_NAME = "LGTC" + LGTC_ID

    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

    _log = logging.getLogger(__name__)
    _log.setLevel(LOG_LEVEL)


    ble = BLE_experiment("rezultat_"+LGTC_NAME)

    ble.run()
