# ----------------------------------------------------------------------
# 
# This script first sends start command '>' to Vesna to start the app.
# Then it waits for response from Vesna - if no response, exit monitor
# Then it sends app duration and root command if specified as argument 
# After it monitors serial input and store the lines into given file
#
# Serial monitor has included failsafe mechanism 
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
    port = ""
    
    def __init__(self, to):
        self.timeout = to
        self.ser = None
        

# ----------------------------------------------------------------------
# Basic serial commands    
    def connect_to(self, p):
        try:
            port = "/dev/" + p
            self.ser = serial.Serial(port, BAUD, BYTESIZE, PARITY, STOPBIT, timeout=self.timeout)
            print("Serial monitor opened on port: " + self.port)
        except:
            print("Serial port not connected or in use!..Exiting now")
            sys.exit(1)


    def auto_connect(self):
        for i in range(2, 5):
            try:
                port = BASEPORT + str(i)
                self.ser = serial.Serial(port, BAUD, BYTESIZE, PARITY, STOPBIT, timeout=self.timeout)
                print("Serial monitor opened on port: " + self.port)
                break
            except:
                print("No serial port connected or all in use!..Exiting now")
                sys.exit(1)


    def read_line(self):
        data = self.ser.read_until(b'\n', None)
        return data


    def write_line(self, data):
        try:
            self.ser.write((data + "\n").encode("ASCII"))
        except:
            print("Error writing to device!")

    def flush(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

# ----------------------------------------------------------------------
# Serial commands made for communication with VESNA
    def sync_with_vesna(self):
        print("Send start command")
        write_line(">")

        # Wait for response ('>' character) from Vesna for 3 seconds
        gotResponse = wait_start_response(3)

        # If device is not responding, try again
        if(not gotResponse):
            print("No response -> send start cmd again...")
            flush()
            write_line("=")
            write_line(">")
            gotResponse = wait_start_response(3)

        if(not gotResponse):
            print("No response...please reset the device and try again")
            # TODO: store_str_to_file("No response from Vesna...")
            close()
            # TODO: Return 0 to client file and it can do sys.exit(1) 
            # sys.exit(1)

        print("Got response!")
        return
    
    def wait_start_response(self, max_time):
        startTime = timer()
        while((timer() - startTime) < max_time):
            try:
                value = self.ser.readline()
                if not value:
                    break     
                if(chr(value[0]) == '>'):
                    return True

            except KeyboardInterrupt:
                print("\n Keyboard interrupt!..Exiting now")
                sys.exit(1)

    def send_command(self, command):
        print("Send %s command" % command)
        write_line(command)

        # Read the response
        value = self.ser.readline()

        # TODO: Vesna can return something else than our data...what to do then?
        # Ad some checking mechanism... if not our data, store it to file and wait for right response.
        # If no response for more than 3 seconds, send command again
        if not value:
            return "No response from VESNA"
        else:
            return value



    

# ----------------------------------------------------------------------





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
monitor.open_file()

# ----------------------------------------------------------------------
# Start the app
# ----------------------------------------------------------------------
monitor.sync_with_vesna()

# ----------------------------------------------------------------------
# Set device as root of the network via serial CLI
# ----------------------------------------------------------------------
if(args.root):
    print("Set device as DAG root")
    monitor.send_cmd("*")
    
# ----------------------------------------------------------------------
# Send desired duration of the application (Vesna needs it in seconds)
# ----------------------------------------------------------------------
monitor.send_cmd("&" + str(APP_DURATION * 60))
print("Application duration " + str(APP_DURATION) + "min")

# ----------------------------------------------------------------------
# Read input lines until app stops sending data
# ----------------------------------------------------------------------
line = 1
startTime = timer()
elapsedMin = 0

print("Start logging serial input:") 

try:
    while(True):
        
        # Measure approximate elapsed time - just for a feeling (+- 10s)
        if((timer() - startTime) > 59):
            elapsedMin += 1
            startTime = timer()

        # Failsafe mechanism - if Vesna for some reason stops responding 
        # So it didn't sent stop command 3min after APP_DURATION, stop the monitor
        if elapsedMin > ((APP_DURATION) + 2):
            print("\n \n Vesna must have crashed... :( \n \n")
            monitor.store_str_to_file(""" \n CRITICAL WARNING!
            Vesna has crashed durring application.""")
            break
        
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

        else:
            print("Serial timeout occurred!")

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