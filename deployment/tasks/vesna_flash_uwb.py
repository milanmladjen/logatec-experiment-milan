# @author: Aleš Simončič
# @modified: Klemen Bregar, Grega Morano
#
# Changes:
# Binaries are given as an argument
# Shortened time to enter bootloader (tested) 
# Added logging file for remote debugging


import subprocess
import Adafruit_BBIO.GPIO as GPIO
import time
import sys
import os
import logging

MAX_RETRY = 3

logging.basicConfig(format="%(asctime)s [%(levelname)7s] - %(message)s", level=logging.INFO, filename="flash_report.log")
log = logging.getLogger("Flash")

try:
    BIN = sys.argv[1]
except:
    sys.exit()

BIN_FILE = BIN

# Verify if binaries exists
# bin_files = os.listdir(BIN_LOC)
# if len(bin_files) == 0:
#    log.error("Folder with binary files is empty.")
#    sys.exit()
# BIN_FILE = bin_files[0]

#if not BIN_FILE.endswith('.bin'):
#    log.error('Selected file is not valid binary file')
#    sys.exit()

# TODO: Verify if bin file exists

# Put the device into boot loader
def put_into_bootloader():
    log.debug("Entering in bootloader ...")
    GPIO.output("GPIO1_25", GPIO.LOW)
    time.sleep(2)
    GPIO.output("GPIO1_25", GPIO.HIGH)
    time.sleep(10)
    GPIO.output("GPIO1_25", GPIO.LOW)
    time.sleep(2)
    

# Setup RST pin
GPIO.setup("GPIO1_25", GPIO.OUT)
GPIO.output("GPIO1_25", GPIO.LOW)
    

# Preform the flashing sequence
log.info("Disable flash read protection ...")
command = "stm32flash -k -b 115200 -R /dev/ttyS2"
put_into_bootloader()
for i in range(1, MAX_RETRY+1):
    try:
        return_sub = subprocess.call(command.split(" "))
        if return_sub != 0:
           log.warning("Command returned error code which is not 0") 
           put_into_bootloader()
        else:
            log.info("Read protect disable successful!")
            break
    except:
        log.error("Command invalid!")


log.info("Disable flash write protection ...")
command = "stm32flash -u -b 115200 -R /dev/ttyS2"
put_into_bootloader()
for i in range(1, MAX_RETRY+1):
    try:
        return_sub = subprocess.call(command.split(" "))
        if return_sub != 0:
           log.warning("Command returned error code which is not 0") 
           put_into_bootloader()
        else:
            log.info("Write protect disable successful!")
            break
    except:
        log.error("Command invalid!")


log.info("File to be flashed is: " + BIN_FILE)
command = "stm32flash -v -b 115200 -R /dev/ttyS2 -w " + BIN_FILE
put_into_bootloader()
for i in range(1, MAX_RETRY+1):
    log.debug("Trying to flash the device for the "+str(i)+" time" )
    try:
        return_sub = subprocess.call(command.split(" "))
        if return_sub != 0:
           log.warning("Flashing command returned error code which is not 0") 
           put_into_bootloader()
        else:
            log.info("Flashing succeed!")
            break
    except:
        log.error("Command invalid!")


log.info("Enable flash read protection ...")
command = "stm32flash -j -b 115200 -R /dev/ttyS2"
put_into_bootloader()
for i in range(1, MAX_RETRY+1):
    try:
        return_sub = subprocess.call(command.split(" "))
        if return_sub != 0:
           log.warning("Command returned error code which is not 0") 
           put_into_bootloader()
        else:
            log.info("Read protect enabled successful!")
            break
    except:
        log.error("Command invalid!")