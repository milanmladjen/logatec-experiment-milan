# ----------------------------------------------------------------------
# 
# This script will just store everything that it gets on serial connection,
# without checking if Vesna is alive
#
# Make sure to enter the same time (APP_DURATION_S) here and in hello-world.c
# (APP_DURATION_IN_SEC)! 
# ----------------------------------------------------------------------
import sys
import argparse
import serial
import os
from datetime import datetime
from timeit import default_timer as timer

APP_DURATION_S  = (60 * 1)

DEFAULT_FILE_NAME = "node_results.txt"

BASEPORT = "/dev/ttyS"
BAUD = 460800
PARITY = serial.PARITY_NONE
STOPBIT = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS

# ----------------------------------------------------------------------
# Monitor class
# ----------------------------------------------------------------------
class serial_monitor():

    def __init__(self):
        self.gotResponse = False

    
    def connect_to(self, p):
        try:
            self.port = "/dev/" + p
            self.ser = serial.Serial(self.port, BAUD, BYTESIZE, PARITY, STOPBIT, timeout=10)
            print("Serial monitor opened on port: " + self.port)
        except:
            print("Serial port not connected or in use!..Exiting now")
            sys.exit(1)


    def auto_connect(self):
        for i in range(2, 5):
            try:
                self.port = BASEPORT + str(i)
                self.ser = serial.Serial(self.port, BAUD, BYTESIZE, PARITY, STOPBIT, timeout=10)
                print("Serial monitor opened on port: " + self.port)
                break
            except:
                print("No serial port connected or all in use!..Exiting now")
                sys.exit(1)

    
    def read_line(self):
        value = self.ser.read_until(b'\n', None)
        return value

# ----------------------------------------------------------------------

    def prepare_file(self, filename):
        self.filename = filename
        self.file = open(filename, mode="w", encoding="ASCII")
        self.file.write(str(datetime.now())+"\n")
        self.file.write("----------------------------------------------------------------------------------------------- \n")
        self.file.write("Serial input from port:" + monitor.port + "\n")
        self.file.write("----------------------------------------------------------------------------------------------- \n")
        self.file.close()

    
    def store_to_file(self, data):
        self.file.write("[" + str(datetime.now().time())+"]: ")
        data = data.decode("ASCII")
        self.file.write(str(data))


    def close(self):
        self.ser.close()
        self.file.close()

monitor = serial_monitor()

# ----------------------------------------------------------------------
# Argument parser for selection output text file, port, root option,...
# ----------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Store serial input into given file.",
    formatter_class=argparse.MetavarTypeHelpFormatter
)
parser.add_argument("-o", 
                    "--output", 
                    help="select file to store serial input", 
                    type=str,
                    required=False)
parser.add_argument("-p", 
                    "--port",   
                    help="""select serial port [ttyUSBx]...if no port 
                    given, program will find it automatically""",
                    type=str, 
                    required=False)

args = parser.parse_args()

# ----------------------------------------------------------------------
# Open serial monitor
# ----------------------------------------------------------------------
if(not args.port):
    # Find port automatically - search for ttyUSB
    monitor.auto_connect()
else:
    # Connect to given port
    monitor.connect_to(args.port)

# ----------------------------------------------------------------------
# Prepare output file
# ----------------------------------------------------------------------
if(not args.output):
    name = DEFAULT_FILE_NAME
    print("Storing into default file: " + name)
else:
    name = args.output
    print("Storing into: " + name)

# (optional) Write first lines into it
monitor.prepare_file(name)

# Open file to append serial input to it
monitor.file = open(monitor.filename, "a")

# ----------------------------------------------------------------------
# Start the app
# ----------------------------------------------------------------------
print("Start logging serial input:") 

# ----------------------------------------------------------------------
# Read input lines until the end of predefined time
# ----------------------------------------------------------------------
line = 1
startTime = timer()
elapsedMin = 0

try:
    while(True):
        
        # Measure approximate elapsed time - just for a feeling (+- 10s)
        if((timer() - startTime) > 59):
            elapsedMin += 1
            startTime = timer()

        # If application come to an end - timing is not precise at all!!!
        if elapsedMin > ((APP_DURATION_S/60)):
            print("End of application time")
            break
        
        # Read one line (until \n char)
        value = monitor.read_line()

        # Because of timeout setting, serial may return empty list
        if value:           

            # Store value into file
            monitor.store_to_file(value)
            line += 1

        else:
            print("Serial timeout occurred")

        # Update status line in terminal
        print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
        str(int(APP_DURATION_S/60)) + " min)", end="\r")
    
    print("")
    print("Done!..Exiting serial monitor")

except KeyboardInterrupt:
    print("\n Keyboard interrupt!.. Exiting serial monitor")

except serial.SerialException:
    print("Error opening port!.. Exiting serial monitor")

except IOError:
    print("\n Serial port disconnected!.. Exiting serial monitor")

# ----------------------------------------------------------------------
# Close the monitor
# ----------------------------------------------------------------------
finally:
    monitor.close()