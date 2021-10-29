# ----------------------------------------------------------------------
# 
# This script first sends start command '>' to Vesna to start the app.
# Then it waits for response from Vesna - if no response, exit monitor
# Then it sends app duration and desired frequency on which Vesna will
# generate noise. It is obtained as environmental variable.  
# ----------------------------------------------------------------------
import sys
import argparse
import serial
import os
from datetime import datetime
from timeit import default_timer as timer


# Application duration should be defined as variable while running container
try:
    APP_DURATION = int(os.environ['APP_DURATION_MIN'])
except:
    print("No app duration was defined...going with default 60min")
    APP_DURATION = 60

# Frequency on which to jam should be defined as variable while running container
try:
    CC_NUM = int(os.environ['APP_DURATION_MIN'])
except:
    print("No app duration was defined...going with default 60min")
    CC_NUM = 110 # Default is 868 MHz


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


    def send_cmd(self, cmd):
        try:
            self.ser.write((cmd + "\n").encode("ASCII"))
        except:
            print("Error writing to device!")


    def wait_response(self, max_time):
        startTime = timer()
        while((timer() - startTime) < max_time):
            try:
                value = self.ser.readline()
                if not value:
                    break     
                if(chr(value[0]) == '>'):
                    self.gotResponse = True
                    break
            except KeyboardInterrupt:
                print("\n Keyboard interrupt!..Exiting now")
                sys.exit(1)


    def flush(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

# ----------------------------------------------------------------------

    def prepare_file(self, filename):
        self.filename = filename
        self.file = open(filename, mode="w", encoding="ASCII")
        self.file.write(str(datetime.now())+"\n")
        self.file.write("----------------------------------------------------------------------------------------------- \n")
        self.file.write("Serial input from port:" + monitor.port + "\n")
        self.file.close()
    
    def store_to_file(self, data):
        self.file.write("[" + str(datetime.now().time())+"]: ")
        data = data.decode("ASCII")
        self.file.write(str(data))

    def store_str_to_file(self,string):
        self.file.write("[" + str(datetime.now().time())+"]: ")
        self.file.write(string)

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
# Send desired duration of the application (Vesna needs it in seconds)
# ----------------------------------------------------------------------
monitor.send_cmd("&" + str(APP_DURATION * 60))
print("Application duration " + str(APP_DURATION) + "min")

# ----------------------------------------------------------------------
# Send desired frequency on which to preform CTTM 
# ----------------------------------------------------------------------
monitor.send_cmd("?" + str(CC_NUM))
print("CC_NUM set to " + str(CC_NUM))

# ----------------------------------------------------------------------
# Start the app
# ----------------------------------------------------------------------
print("Send start command")
monitor.send_cmd(">")

# Wait for response ('>' character) from Vesna for 3 seconds
monitor.wait_response(3)

# If device is not responding, try again
if(not monitor.gotResponse):
    print("No response -> send start cmd again...")
    monitor.flush()
    monitor.send_cmd("=")
    monitor.send_cmd(">")
    monitor.wait_response(3)

if(not monitor.gotResponse):
    print("No response...please reset the device and try again")
    monitor.store_str_to_file("No response from Vesna...")
    monitor.close()
    sys.exit(1)

print("Got response!")
   
# ----------------------------------------------------------------------
# Read input lines until app stops sending data
# ----------------------------------------------------------------------
line = 1
startTime = timer()
elapsedMin = 0

print("Start logging serial input...although there won't be any input from Vesna :)") 

try:
    while(True):
               
        # Read one line (until \n char)
        value = monitor.read_line()

        # Because of timeout setting, serial may return empty list
        if value:           
            # If stop command '=' found, exit monitor
            if(chr(value[0]) == '='):
                print("Found stop command (" + str(APP_DURATION) +
                " minutes has elapsed)..stored " + str(line) + " lines.")
                break

            # Store value into file
            monitor.store_to_file(value)

            line += 1

        # Update status line in terminal
        print("Line: " + str(line) + " (~ " + str(elapsedMin) + "|" + 
        str(int(APP_DURATION)) + " min)", end="\r")
    
    print("")
    print("Done!..Exiting serial monitor")

except KeyboardInterrupt:
    print("\n Keyboard interrupt!..send stop command")
    monitor.send_cmd("=")

    while(True):
        try:
            value = monitor.read_line()
            if(chr(value[0]) == '='):
                break
        except:
            print("Error closing monitor, no response")  
            break
    print("Exiting serial monitor")

except serial.SerialException:
    print("Error opening port!..Exiting serial monitor")

except IOError:
    print("\n Serial port disconnected!.. Exiting serial monitor")

# ----------------------------------------------------------------------
# Close the monitor
# ----------------------------------------------------------------------
finally:
    monitor.close()