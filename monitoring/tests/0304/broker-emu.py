#   TODO different var names
#   TODO make it multitherad?


import zmq 
import time
import logging

#from lib import mongodb_client
from lib import testbed_database

import select, sys # For user input

LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 3

# ------------------------------------------------------------------------------- #
# Configuration
# ------------------------------------------------------------------------------- #
# Logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

#if __name__ == '__main__':

db = testbed_database.testbed_database("test_database.db")

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
flask_script_id = b"flask_process"    # As defined in flask

# Configure poller
poller = zmq.Poller()
poller.register(backend, zmq.POLLIN)
poller.register(frontend, zmq.POLLIN)


# Small delay for zmq init
time.sleep(1)

"""
print("Sync with frontend")
# Inform the frontend that experiment has started
frontend.send_multipart([flask_script_id, b"Online", b"0", b"0"])
"""

print("Starting main loop...")
tx_msg_nbr = 0
subscribers = 0

# -------------------------------------------------------------------------------
# Start the main loop
# -------------------------------------------------------------------------------

print("-------------------------------------------------------------------------------")
print("Type in the command. For multicast use prefix m, for unicast use prefix u.")
print("Example: mSTATE, mSTART_APP, u81STATE, ...")
print(" ")
print("To check the database enter command d")
print(" ")

try:
    while True:

        # Wait one second for any user input message
        i, o, e = select.select( [sys.stdin], [], [], 1 )

        # If there is any user input in terminal, act upon it
        if (i):
        
            msg = sys.stdin.readline().strip()
            #print("User input:" + cmd)
            print (" ")

            # PUBLISH COMMAND (mSTART_APP)
            if msg[0] == "m":

                # Manually check if message number should be 0
                if msg[1:] == "STATE":
                    cmd ="-1 STATE"
                else:
                    cmd ="%i %s" % (tx_msg_nbr, msg[1:])
            
                backend_pub.send(cmd.encode())
                logging.debug("Published message: " + cmd)
            
            # UNICAST COMMAND (u66START_APP)
            elif msg[0] == "u":
                adr = "LGTC" + msg[1:3]

                # Addres must be in database, otherwise it is not active
                if mdb.isDeviceActive(adr):
                    
                    # Manually check if message number should be 0
                    if msg[3:] == "STATE":
                        cmd = [adr.encode(), b"0", b"STATE"]
                        logging.debug("Router sent message [0]: STATE to device %s" % adr)

                    else:
                        nbr = str(tx_msg_nbr)
                        dat = msg[3:]
                        cmd = [adr.encode(), nbr.encode(), dat.encode()]
                        logging.debug("Router sent message [%s]: %s to device %s" % (nbr, dat, adr))

                    backend.send_multipart(cmd)
                    
                else:
                    logging.warning("Device address is not in DB")
            
            elif msg[0] == "d":
                mdb.printTestbedState()
            
            print(" ")




        """
        # -------------------------------------------------------------------------------
        # FRONTEND ---> BACKEND
        # -------------------------------------------------------------------------------
        """

        sockets = dict(poller.poll(100))

        # -------------------------------------------------------------------------------
        # BACKEND ---> FRONTEND
        # -------------------------------------------------------------------------------
        # If there is any message in pollin queue from LGTC devices, forward it to flask_server
        if sockets.get(backend) == zmq.POLLIN:

            print("Received from backend...")

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
                        frontend.send_multipart([flask_script_id, b"DeviceUpdate", b"-1", devstate.encode()])
                        print("Device %s joined the experiment" % msg[0])

                        subscribers += 1
                        if subscribers == NUMBER_OF_DEVICES:
                            print("All devices (" + str(NUMBER_OF_DEVICES) + ") active")

                    else:
                        print("Device with the name %s allready in the experiment" % msg[0])
                        # TODO send END command to LGTC with stated reason

                # If device exited the experiment, remove it from the database
                elif msg[2] == "VESNA_ERROR":  
                    md.removeDevice(msg[0])

                    devstate = {"address":msg[0], "state":"OFFLINE"}
                    devstate = str(devstate)
                    frontend.send_multipart([flask_script_id, b"DeviceUpdate", b"-1", devstate.encode()])
                    print("Device %s send VESNA_ERROR message" % msg[0])

                # EXPERIMENT COMMAND response
                else:
                    db.update_dev_state(msg[0], msg[2])
                    print("New state of device %s: %s" % (msg[0], db.get_dev_state(msg[0])))

                    devstate = {"address":msg[0], "state":msg[2]}
                    devstate = str(devstate)
                    frontend.send_multipart([flask_script_id, b"DeviceUpdate", b"-1", devstate.encode()])

            # COMMAND response
            else:
                # Send response back to the server [device, count, data]
                frontend.send_multipart([flask_script_id, address, data_nbr, data])
                logging.info("Received [%s] from device %s: %s" % (msg[1], msg[0], msg[2]))


            print(" ")
        # -------------------------------------------------------------------------------
        # HEARTBEAT
        # -------------------------------------------------------------------------------
        # TODO Heatbeat: Check status of devices and update it in DB
        #else ...

        #print(".")
except KeyboardInterrupt:
    print("Keyboard interrupt...exiting now.")

tx_msg_nbr += 1
print("Sent messages %i" % tx_msg_nbr)

# Inform devices in backend that monitoring is over
msg =b"-1 EXIT"
backend_pub.send(msg)

# Inform the frontend that experiment has stopped
frontend.send_multipart([flask_script_id, b"End", b"0", b"0"])

