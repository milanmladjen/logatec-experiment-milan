#   TODO different var names
#   TODO make it multitherad? meh
#   TODO fix logging
#   TODO struktura


import zmq 
import time
import logging

from timeit import default_timer as timer

#from lib import mongodb_client
from lib import testbed_database

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



# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------
# Logging module
# Config logging module format for all scripts. Log level is defined in each submodule with var LOG_LEVEL.
#logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(module)26s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)

# Database library
db = testbed_database.testbed_database("test_database.db")

# ZMQ init
context = zmq.Context.instance()

# Socket for publishing commands
backend_pub = context.socket(zmq.PUB)
backend_pub.sndhwm = 1100000
backend_pub.bind('tcp://*:5561')

# Socket to get responses
backend = context.socket(zmq.ROUTER)
backend.bind('tcp://*:5562')

# Socket for intra-process communication with flask server
frontend = context.socket(zmq.ROUTER)
#frontend.bind("ipc:///tmp/zmq_ipc")
frontend.bind("tcp://*:5563")
controller_server_id = b"flask_process"      # As defined in controller_server.py

# Configure poller
poller = zmq.Poller()
poller.register(backend, zmq.POLLIN)
poller.register(frontend, zmq.POLLIN)

# Small delay for zmq init
time.sleep(1)


# -------------------------------------------------------------------------------
# Sync with frontend
# -------------------------------------------------------------------------------
logging.info("Inform frontend about beginning of an experiment.")
frontend.send_multipart([controller_server_id, b"Online", b"0", RADIO_TYPE.encode()])

logging.debug("Starting main loop...")
tx_msg_nbr = 0
subscribers = 0

hb_time = timer()
# -------------------------------------------------------------------------------
# Start the main loop
# -------------------------------------------------------------------------------

try:
    while True:

        sockets = dict(poller.poll(100))

        # -------------------------------------------------------------------------------
        # FRONTEND ---> BACKEND
        # -------------------------------------------------------------------------------
        # If there is a message in polling queue from the flask server, forward it to LGTC devices
        if sockets.get(frontend) == zmq.POLLIN:

            logging.debug("Received from frontend...")

            dummy_controller_server_id, device, count, data = frontend.recv_multipart()

            # [device, count, data] From bytes to string for loging output
            msg = [device.decode(), count.decode(), data.decode()]

            tx_msg_nbr += 1

            # UPDATE TESTBED STATE
            if msg[0] == "TestbedUpdate":

                # Send testbed state to the frontend
                testbed = db.get_tb_state_json()
                testbed = str(testbed)
                frontend.send_multipart([controller_server_id, b"TestbedUpdate", b"", testbed.encode()])
                logging.debug("Return testbed state: \n" + db.get_tb_state_str)


            # PUBLISH COMMAND - if message is for all devices
            elif msg[0] == "All":

                cmd ="%s %s" % (msg[1], msg[2])
                backend_pub.send(cmd.encode())
                logging.debug("Published message [%s]: %s" % (msg[1], msg[2]))
 
            # UNICAST COMMAND - if message is only for one device
            else:
                # Addres must be in database, otherwise it is not active
                if db.is_dev(msg[0]):
                    cmd = [device, count, data]
                    backend.send_multipart(cmd)
                    logging.debug("Router sent message [%s]: %s to device %s" % (msg[1], msg[2], msg[0]))
                else:
                    # Inform frontend that address is not in database
                    frontend.send_multipart([controller_server_id, device, "0", "Device is not active..."])
                    devstate = {"address":device, "state":"OFFLINE"}    #TODO some other state maybe? To delete device from tloris and dropdown
                    devstate = str(devstate)
                    frontend.send_multipart([controller_server_id, b"DeviceUpdate", b"-1", devstate.encode()])
                    logging.warning("Device address is not in DB")

        # -------------------------------------------------------------------------------
        # BACKEND ---> FRONTEND
        # -------------------------------------------------------------------------------
        # If there is any message in pollin queue from LGTC devices, forward it to flask_server
        elif sockets.get(backend) == zmq.POLLIN:

            logging.debug("Received from backend...")

            address, data_nbr, data = backend.recv_multipart()

            # Send ACK back
            backend.send_multipart([address, data_nbr, b"ACK"])

            # From bytes to string for loging output [address, count, data]
            msg = [address.decode(), data_nbr.decode(), data.decode()]

            # SYSTEM message (only to update the database)
            if msg[1] == "-1":

                # If device come to experiment add it do database
                if msg[2] == "SYNC":
                    if not db.is_dev(msg[0]):
                        db.insert_dev(msg[0], "ONLINE")

                        devstate = {"address":msg[0], "state":"ONLINE"}
                        devstate = str(devstate)
                        frontend.send_multipart([controller_server_id, b"DeviceUpdate", b"-1", devstate.encode()])
                        logging.debug("Device %s joined the experiment" % msg[0])

                        subscribers += 1
                        if subscribers == NUMBER_OF_DEVICES:
                            logging.info("All devices (" + str(NUMBER_OF_DEVICES) + ") active")
                            # TODO: inform frontend about this

                    else:
                        logging.warning("Device with the name %s allready in the experiment" % msg[0])
                        # TODO send END command to LGTC with stated reason

                # If device exited the experiment, remove it from the database
                elif msg[2] == "ERROR":  
                    db.remove_dev(msg[0])

                    devstate = {"address":msg[0], "state":"OFFLINE"}
                    devstate = str(devstate)
                    frontend.send_multipart([controller_server_id, b"DeviceUpdate", b"-1", devstate.encode()])
                    logging.warning("Device %s send ERROR message" % msg[0])

                # Else update device state in the database
                else:
                    db.update_dev_state(msg[0], msg[2])
                    logging.info("New state of device %s: %s" % (msg[0], db.get_dev_state(msg[0])))

                    devstate = {"address":msg[0], "state":msg[2]}
                    devstate = str(devstate)
                    frontend.send_multipart([controller_server_id, b"DeviceUpdate", b"-1", devstate.encode()])

            # EXPERIMENT COMMAND response
            else:
                # Forward response back to the server [device, count, data]
                frontend.send_multipart([controller_server_id, address, data_nbr, data])
                logging.debug("Received response [%s] from device %s: %s" % (msg[1], msg[0], msg[2]))


        # -------------------------------------------------------------------------------
        # HEARTBEAT - TODO
        # -------------------------------------------------------------------------------
        else:
            # Every 3 seconds send STATE command all of active devices in the experiment
            # Update database accordingly to
            if((timer() - hb_time) > 3):
                hb_time = timer()

                #device = TODO: get it from DB
                #cmd = [device, "-1", "STATE"]
                #backend.send_multipart(cmd)


except KeyboardInterrupt:
    logging.info("Keyboard interrupt...exiting now.")

tx_msg_nbr += 1
logging.info("Messages sent: %i" % tx_msg_nbr)

# Inform devices in backend that monitoring is over
msg =b"-1 EXIT"
backend_pub.send(msg)

# Inform the frontend that experiment has stopped
frontend.send_multipart([controller_server_id, b"End", b"0", b"0"])

