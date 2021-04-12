# ----------------------------------------------------------------------
# SERIAL MONITOR: Communication between VESNA and LGTC via UART
# ----------------------------------------------------------------------
import sys
import serial
import logging
from timeit import default_timer as timer


# ----------------------------------------------------------------------
class serial_monitor():

    BASEPORT = "/dev/ttyS"
    BAUD = 460800
    PARITY = serial.PARITY_NONE
    STOPBIT = serial.STOPBITS_ONE
    BYTESIZE = serial.EIGHTBITS
    
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.ser = None
        self.serial_avaliable = False
        

    # Basic serial commands    
    # ------------------------------------------------------------------
    def connect_to(self, p):
        try:
            port = "/dev/" + p
            self.ser = serial.Serial(port, self.BAUD, self.BYTESIZE, self.PARITY, self.STOPBIT, timeout=self.timeout)
            logging.debug("Serial monitor opened on port: " + port)
            return True

        except:
            logging.error("Serial port not connected or in use.")
            return False


    def auto_connect(self):
        for i in range(2, 5):
            try:
                port = self.BASEPORT + str(i)
                self.ser = serial.Serial(port, self.BAUD, self.BYTESIZE, self.PARITY, self.STOPBIT, timeout=self.timeout)
                logging.debug("Serial monitor opened on port: " + port)
                break
            except:
                logging.error("No serial port connected or all in use.")
                return False
        return True


    def read_line(self):
        #logging.debug("Serial read")
        #data = self.ser.readline()
        # TODO:AttributeError: 'NoneType' object has no attribute 'read_until'
        data = self.ser.read_until(b'\n', None)
        data = data.decode()
        self.serial_avaliable = True
        return data


    def write_line(self, data):
        # Convert data to string and add \n | send over serial
        #logging.debug("Serial write")
        try:
            self.ser.write((data + "\n").encode("ASCII"))
        except:
            logging.error("Error writing to device!")
        finally:
            return

    def input_waiting(self):
        if self.ser.inWaiting() > 0:
            return True
        else:
            return False

    def flush(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return

    def close(self):
        logging.debug("Serial close!")
        self.ser.close()


    # Serial commands made for communication with VESNA
    # ------------------------------------------------------------------

    def wait_response(self, max_time, char):
        startTime = timer()
        while((timer() - startTime) < max_time):
            try:
                value = self.read_line()
                if not value:
                    break     
                if(value[0] == char):
                    return True

            except KeyboardInterrupt:
                print("\n Keyboard interrupt!..Exiting now")
                sys.exit(1)
        return False


    def sync_with_vesna(self):
        logging.debug("Send sync command to VESNA")
        self.write_line("@")

        # Wait for response ('@' character) from Vesna for 3 seconds
        gotResponse = self.wait_response(3, "@")

        # If device is not responding, try again
        if(not gotResponse):
            logging.debug("No response -> send sync cmd again...")
            self.flush()
            self.write_line("=")    # Send stop command in case the app is running
            self.write_line("@")
            gotResponse = self.wait_response(3, "@")

        if(not gotResponse):
            logging.error("No response...please reset the device and try again")
            close()
            return False

        logging.debug("Got response...synced with VESNA")
        return True


    def start_app(self, app_duration):
        logging.debug("Starting application")
        self.write_line(">")

        if not self.wait_response(3, ">"):
            return False

        self.write_line("&"+app_duration)

        return True

    def stop_app(self, app_duration):
        logging.debug("Stoppin application")
        self.write_line("=")

        if not self.wait_response(3, "="):
            return False
    
        return True


    def send_command(self, command):
        logging.debug("Serial send %s command to VESNA" % command)

        self.write_line("*" + command)
        # TODO: Vesna can return something else than our data...what to do then?
        # TODO: response may also be formed in multiple lines...





# ----------------------------------------------------------------------
# Demo usage
if __name__ == "__main__":

    monitor = serial_monitor(timeout=10)

    # Open serial monitor
    if (sys.argv[1] == None):
        # Find port automatically - search for ttyUSB
        monitor.auto_connect()
    else:
        # Connect to given port
        monitor.connect_to(sys.argv[1])

    # Optional - send start command ">" to VESNA
    monitor.sync_with_vesna()

    try:
        while(True):
            
            # Wait for incoming line and read it
            data = monitor.read_line()

            if data:
                if(data[0] == "="):
                    print("Found stop command")
                    break

                print(data)
            else:
                print("Serial timeout")
            
        print("\n Done!")

    except KeyboardInterrupt:
        print("\n Keyboard interrupt!..send stop command")
        monitor.write_line("=")

    except serial.SerialException:
        print("Error opening port!..Exiting serial monitor")

    except IOError:
        print("\n Serial port disconnected!.. Exiting serial monitor")
    
    finally:
        monitor.close()