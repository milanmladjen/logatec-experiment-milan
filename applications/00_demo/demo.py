#!/usr/bin/env python3

from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate
import argparse

# Filename must be named like this, so client.py will send it to servers
filename = "node_results.txt"

try:
    APP_DURATION = int(os.environ['APP_DURATION_MIN'])
except:
    print("No app duration was defined...going with default 1min")
    APP_DURATION = 1


class ScanDelegate(DefaultDelegate):
	def __init__(self):
		DefaultDelegate.__init__(self)
	def handleDiscovery(self, dev, isNewDev, isNewData):

		if isNewDev:
			print("Discovered device", dev.addr, dev.rssi)
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



#parser = argparse.ArgumentParser(
#    description="Store serial input into given file.",
#    formatter_class=argparse.MetavarTypeHelpFormatter
#)
#parser.add_argument("-o", 
#                    "--output", 
#                    help="select file to store serial input", 
#                    type=str,
#                    required=False)

#args = parser.parse_args()

#filename = "node_" + args.output + ".txt"


file = open(filename, mode="w", encoding = "ASCII")
file.write(str(datetime.now())+"\n")
file.write("BLE measurements \n")
file.write("N --> New device discovered \n D --> data received \n R --> rssi update \n")
file.write("------------------------- \n")
file.close()

# initialize scanner
scr = Scanner().withDelegate(ScanDelegate())


file = open(filename, "a")

# start scanning for 30 seconds
scr.scan(timeout=APP_DURATION, passive=True) 
