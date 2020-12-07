# ----------------------------------------------------------------------
# SERIAL MONITOR
# ----------------------------------------------------------------------
import sys
import serial

# ----------------------------------------------------------------------
BASEPORT = "/dev/ttyS"
BAUD = 460800
PARITY = serial.PARITY_NONE
STOPBIT = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS


# ----------------------------------------------------------------------
class serial_monitor():
    port = ""
    
    def __init__(self, to):
        self.timeout = to
        self.ser = None
        

    # Basic serial commands    
    # ------------------------------------------------------------------
    def connect_to(self, p):
        try:
            port = "/dev/" + p
            self.ser = serial.Serial(port, BAUD, BYTESIZE, PARITY, STOPBIT, timeout=self.timeout)
            print("Serial monitor opened on port: " + self.port)
            return

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
        return


    def read_line(self):
        data = self.ser.read_until(b'\n', None)
        return data


    def write_line(self, data):
        try:
            self.ser.write((data + "\n").encode("ASCII"))
        except:
            print("Error writing to device!")
        finally:
            return

    def flush(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return

    def close(self):
        self.ser.close()


    # Serial commands made for communication with VESNA
    # ------------------------------------------------------------------

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
        return False

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
