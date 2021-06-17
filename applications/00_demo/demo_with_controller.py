#!/usr/bin/env python3


import os, sys, time
import logging
from queue import Queue
from datetime import datetime
import argparse

# Workaround to import files from parent dir
sys.path.append("../../monitoring/")
import controller_client

from bluepy.btle import Scanner, DefaultDelegate


# ----------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# ----------------------------------------------------------------------------------------

# DEFINITIONS
LOG_LEVEL = logging.DEBUG

ROUTER_HOSTNAME = "tcp://193.2.205.19:5562"
SUBSCR_HOSTNAME = "tcp://193.2.205.19:5561"

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


try:
	APP_DURATION = int(os.environ['APP_DURATION_MIN'])
	APP_DURATION = APP_DURATION * 60
except:
	print("No app duration was defined...going with default 1min")
	APP_DURATION = 60


# ----------------------------------------------------------------------------------------
# FUNCTIONS to communicate with client script
# ----------------------------------------------------------------------------------------
def LGTC_send_sys_resp(self, state):
	A_C_QUEUE.put(["-1", state])

def LGTC_send_info_resp(self, state):
	A_C_QUEUE.put(["0", state])

def LGTC_send_cmd_resp(self, nbr, resp):
	A_C_QUEUE.put([nbr, resp])

def LGTC_rec_cmd(self):
	return C_A_QUEUE.get()


# ----------------------------------------------------------------------------------------
# EXPERIMENT APPLICATION
# ----------------------------------------------------------------------------------------
class ScanDelegate(DefaultDelegate):
	def __init__(self):
		DefaultDelegate.__init__(self)

	def handleDiscovery(self, dev, isNewDev, isNewData):

		if isNewDev:
			LGTC_send_info_resp("Discovered new device - %s" % dev.addr)
			file.write("[" + str(datetime.now().time())+"]: ")
			file.write("N " + str(dev.addr) + " RSSI" + str(dev.rssi) + "\n")
		elif isNewData:
			#print(dev.addr, dev.rssi, dev.updateCount, dev.getValueText(10), "Received new data")
			file.write("[" + str(datetime.now().time())+"]: ")
			file.write("D " + str(dev.addr) + " RSSI" + str(dev.rssi) + " CNT" + str(dev.updateCount) + "\n")
		else:
			#print(dev.addr, dev.rssi, dev.updateCount, dev.getValueText(10), "Update rssi")
			file.write("[" + str(datetime.now().time())+"]: ")
			file.write("R " + str(dev.addr) + " (" + str(dev.updateCount) + ") RSSI" + str(dev.rssi) + "\n")

		# this is how you get other info (advertising name, TX power... but LGTC isn't advertising much 
		#for i in range(255):
		#  if(dev.getValueText(i) != None):
		#   print("  ", i, dev.getValueText(i))



# ----------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------
# Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
#logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

logging.info("Testing demo application for " + str(APP_DURATION) + " minutes on device " + LGTC_NAME + "!")

# Create 2 queue for communication between threads
# ZMQ CLIENT -> APPLICATION
C_A_QUEUE = Queue()
# APPLICATION -> ZMQ CLIENT
A_C_QUEUE = Queue()

# Start client thread (communication with controller)
client_thread = controller_client.zmq_client_thread(A_C_QUEUE, C_A_QUEUE, LGTC_NAME, SUBSCR_HOSTNAME, ROUTER_HOSTNAME)
client_thread.start()

# Online
LGTC_send_sys_resp("SYNCED_WITH_VESNA")

# Prepare output file
file = open(RESULTS_FILENAME, mode="w", encoding = "ASCII")
file.write(str(datetime.now())+"\n")
file.write("BLE measurements \n")
file.write("N --> New device discovered \n D --> data received \n R --> rssi update \n")
file.write("------------------------- \n")
file.close()
file = open(RESULTS_FILENAME, "a")

# initialize scanner
scr = Scanner().withDelegate(ScanDelegate())

while(1):
	if(not C_A_QUEUE.epmty()):
		cmd = LGTC_rec_cmd()

		if cmd[0] == "-1":

			if cmd[1] == "EXIT":
				break
		else:

			if cmd[1] == "START":
				# start scanning for 30 seconds
				LGTC_send_sys_resp("START")
				scr.scan(timeout=APP_DURATION, passive=True)
				LGTC_send_sys_resp("END")


LGTC_send_sys_resp("EXIT")
logging.info("Main thread stopped, trying to stop client thread.")

# Wait for a second so client can finish its transmission
time.sleep(1)

# Notify zmq client thread to exit its operation and join until quit
client_thread.stop()
client_thread.join()

logging.info("Exit!")
# ---------------------------------------------------------------------------



