
import zmq 
import time
import logging

from timeit import default_timer as timer

#from lib import mongodb_client
from lib import testbed_database


# --------------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# --------------------------------------------------------------------------------------------

LOG_LEVEL = logging.DEBUG
LOGGING_FILENAME = "controller.log"

try:
    NUMBER_OF_DEVICES = int(os.environ["DEV_NUMBER"])
except:
    print("No device number given...going with default: 21")
    NUMBER_OF_DEVICES = 21

try:
    RADIO_TYPE = os.environ(["RADIO_TYPE"])
except:
    print("No radio type given...going with default: TEST_TYPE")
    RADIO_TYPE = "TEST_TYPE"





# --------------------------------------------------------------------------------------------
# ZeroMQ class
# --------------------------------------------------------------------------------------------
class zmq_broker():

    # ----------------------------------------------------------------------------------------
    # Initialize sockets and poller
    # ----------------------------------------------------------------------------------------
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        context = zmq.Context.instance()

        # Socket for communication with Flask server
        self.frontend = context.socket(zmq.ROUTER)
        #frontend.bind("ipc:///tmp/zmq_ipc")
        self.frontend.bind("tcp://*:5563")
        self.controller_server_id = b"flask_process"      # As defined in controller_server.py

        # Socket for publishing LGTC commands
        self.backend_pub = context.socket(zmq.PUB)
        self.backend_pub.sndhwm = 1100000
        self.backend_pub.bind('tcp://*:5561')

        # Socket to get responses from LGTC
        self.backend = context.socket(zmq.ROUTER)
        self.backend.bind('tcp://*:5562')

        # Configure poller
        self.poller = zmq.Poller()
        self.poller.register(backend, zmq.POLLIN)
        self.poller.register(frontend, zmq.POLLIN)



    # ----------------------------------------------------------------------------------------
    # Check poller for any incoming message
    #
    #   @params:    timeout - number of ms to wait (0 = return immediately)
    #   @return:    name of the instance that received the message
    # ----------------------------------------------------------------------------------------
    def check_input(self, timeout):
        sockets = dict(self.poller.poll(timeout))

        if sockets.get(self.backend) == zmq.POLLIN:
            return "BACKEND"
        elif sockets.get(self.frontend) == zmq.POLLIN:
            return "FRONTEND"
        else:
            return None



    # ----------------------------------------------------------------------------------------
    # Read received message from backend socket. 
    #
    #   @return:    adr - name of the device that sent the message
    #               nbr - number of received message (-1 means SYSTEM message)
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def backend_receive(self):
        self.log.debug("Received from backend...")

        adr, nbr, data = self.backend.recv_multipart()

        return adr.decode(), nbr.decode(), data.decode()


    # ----------------------------------------------------------------------------------------
    # Send a message to a device in backend.
    #
    #   @params:    adr - name of targeted device
    #                     if adr is "All" send message to all devices (publish socket)
    #               nbr - number of sent message (-1 means SYSTEM message)
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def backend_send(self, adr, nbr, data):

        if adr == "All":
            self.log.debug("Publish message [%s]: %s" % (nbr, data))

            cmd ="%s %s" % (nbr, data)
            self.backend_pub.send(cmd.encode())

        else:
            self.log.debug("Router send message [%s]: %s to device %s" % (nbr, data, adr))

            self.backend.send_multipart([adr.encode(), nbr.encode(), data.encode()])




    # ----------------------------------------------------------------------------------------
    # Read received message from frontend socket. Used for forwarding commands from F -> B and
    # for sending user commands targeted for broker script (depends on the the adr var)
    #
    #   @return:    adr - (=tip) name of targeted device OR type of message for broker
    #               nbr - number of received message
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def frontend_receive(self):
        self.log.debug("Received from frontend...")

        # dummy is the frontend ID
        dummy, adr, nbr, data = self.frontend.recv_multipart()

        return adr.decode(), nbr.decode(), data.decode()

    # ----------------------------------------------------------------------------------------
    # Send message to the frontend socket. Used for forwarding responses B -> F and for 
    # sending some experiment commands for server script
    #
    #   @params:    tip - (=adr) name of device OR type (tip) of message for server
    #               nbr - number of received message
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def frontend_send(self, tip, nbr, data):
        self.log.debug("Send to frontend...")

        self.frontend.send_multipart(
            [self.controller_server_id, tip.encode(), nbr.encode(), data.encode()])

    # ----------------------------------------------------------------------------------------
    # Send device state to frontend socket - costum function to inform server about new state.
    #
    #  @params:     device - name of device
    #               state  - new state of device
    # ----------------------------------------------------------------------------------------
    def frontend_deviceUpdate(self, device, state):
        self.log.debug("Send new state of device to frontend...")

        data = str({"address":device, "state":state})
        self.frontend.send_multipart(
            [self.controller_server_id, b"DeviceUpdate", b"-1", data.encode()])

    # ----------------------------------------------------------------------------------------
    # Send some info string to frontend socket - costum function to inform user about smth.
    #
    #  @params:     info - string which will be displayed to the user console
    #               
    # ----------------------------------------------------------------------------------------
    def frontend_info(self, info):
        self.log.debug("Send info to frontend: " + info)

        self.frontend.send_multipart(
            [self.controller_server_id, b"Info", b"", info.encode()])





# --------------------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------------------
if __name__ == "__main__":

    # Config logging module format for all scripts. 
    # Log level is defined in each submodule with var LOG_LEVEL.
    #logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

    # Init ZMQ 
    broker = zmq_broker()

    # Small delay for zmq init
    time.sleep(1)

    # Init database library
    db = testbed_database.testbed_database("test_database.db")

    # Inform frontend that experiment began
    broker.frontend_send("Online", "", RADIO_TYPE)
    broker.frontend_info("------ \n New active experiment in the testbed! \n")

    logging.debug("Starting main loop...")

    subscribers = 0
    hb_time = timer()

    # ----------------------------------------------------------------------------------------
    # MAIN LOOP
    while True:

        inp = broker.check_input(100)

        # ------------------------------------------------------------------------------------
        # FRONTEND --> BACKEND
        if inp == "FRONTEND":
            address, number, data = broker.frontend_receive()

            # UPDATE TESTBED STATE - return state of testbed to server
            if address == "TestbedUpdate":
                logging.debug("Return testbed state: \n" + db.get_tb_state_str)
                broker.frontend_send(address, "", str(db.get_tb_state_json()))

            # FORWARD COMMAND - to LGTC devices
            else:
                # Addres must be in database, otherwise it is not active
                if db.is_dev(address) or (address == "All"):
                    broker.backend_send(address, number, data)
                else:
                    logging.warning("Device address is not in DB")
                    broker.frontend_info("Device " + address + " is not active!")
                    broker.frontend_deviceUpdate(address,"OFFLINE")

        # ------------------------------------------------------------------------------------
        # BACKEND --> FRONTEND 
        elif inp == "BACKEND":
            address, number, data = broker.backend_receive()

            # Send ACK back
            broker.backend_send(address, number, "ACK")

            # SYSTEM MESSAGE (only to update the database)
            if number == "-1":

                # If device come to experiment add it do database
                if data == "SYNC":
                    if not db.is_dev(address):
                        db.insert_dev(address, "ONLINE")
                        broker.frontend_deviceUpdate(address, "ONLINE")

                        subscribers += 1
                        if subscribers == NUMBER_OF_DEVICES:
                            logging.info("All devices ("+ str(NUMBER_OF_DEVICES) +") active")
                            # TODO: inform frontend about this

                    else:
                        logging.warning("Device %s allready in the experiment" % address)
                        # TODO send END command to LGTC with stated reason

                # If device exited the experiment, remove it from the database
                elif data == "ERROR":  
                    db.remove_dev(address)
                    broker.frontend_deviceUpdate(address, "OFFLINE")
                    logging.warning("Device %s send ERROR message..." % address)

                # Else update device state in the database
                else:
                    db.update_dev_state(address, data)
                    broker.frontend_deviceUpdate(address, data)
                    logging.info("New state of device %s: %s" % (address, data))

            # EXPERIMENT COMMAND (response)
            else:
                # Forward response back to the server
                broker.frontend_send(address, number, data)
                logging.debug("Received response [%s] from device %s: %s" % (number, address, data))

        # -------------------------------------------------------------------------------
        # HEARTBEAT - TODO
        else:
            # Every 3 seconds send STATE command all of active devices in the experiment
            # Update database accordingly to
            if((timer() - hb_time) > 3):
                hb_time = timer()

                #device = TODO: get it from DB
                #cmd = [device, "-1", "STATE"]




    # -------------------------------------------------------------------------------
    # END

    # Inform devices in backend that monitoring is over
    broker.backend_send("All", "-1", "EXIT")

    # Inform the frontend that experiment has stopped
    broker.frontend_send("End", "", "")
    broker.frontend_info("\n ----------------- \n Experiment ended! \n -----------------")

    logging.info("End of controller main loop...")
