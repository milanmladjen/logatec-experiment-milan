# 
#   Broker test script - zmq server that talks to the LGTC clients
#   User can input commands in the terminal, which are sent to synced devices
#   MongoDB is also used
#   There is no connection with the flask server
#


import zmq 
import time
import logging

from lib import mongodb_client

import select, sys # For user input

LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 3

# ------------------------------------------------------------------------------- #
# Configuration
# ------------------------------------------------------------------------------- #
# Logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

#if __name__ == '__main__':

print("Don't forget tu turn on mongod service")

mdb = mongodb_client.mongodb_client("active-devices", DATABASE="experiment-monitor")

context = zmq.Context.instance()

# Socket for publishing commands
backend_pub = context.socket(zmq.PUB)
backend_pub.sndhwm = 1100000
backend_pub.bind('tcp://*:5561')

# Socket to get responses
backend = context.socket(zmq.ROUTER)
backend.bind('tcp://*:5562')

# Configure poller
poller = zmq.Poller()
poller.register(backend, zmq.POLLIN)


# ------------------------------------------------------------------------------- #
# First wait for synchronization from all subscribers
# ------------------------------------------------------------------------------- #
logging.info("Waiting for %i LGTC devices ... interrupt it with Ctrl+C" % NUMBER_OF_DEVICES)

subscribers = 0
try:
    while subscribers < NUMBER_OF_DEVICES:
        # Wait for synchronization request (
        address, nbr, msg = backend.recv_multipart()

        if nbr == b"-1":

            # Send synchronization reply
            backend.send_multipart([address, b"-1", b"ACK"])
            
            # Add device to the database
            if not mdb.isDeviceActive(address.decode()):
                mdb.insertDevice(address.decode(), "ONLINE")
            else:
                continue #TODO

            # Inform user about new device in terminal
            subscribers += 1
            logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))
        else:
            logging.warning("Got a message but not sync request...discarting." )

except KeyboardInterrupt:
    print("Keybopard interrupt...continuing application.")


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the main loop
# ------------------------------------------------------------------------------- #
mdb.printTestbedState()

print("-------------------------------------------------------------------------------")
print("Type in the command. For multicast use prefix m, for unicast use prefix u.")
print("Example: mSTATE, mSTART_APP, u81STATE, ...")
print(" ")
print("To check the database enter command d")
print(" ")

tx_msg_nbr = 0

try:
    while True:

        # Wait one second for any user input message
        i, o, e = select.select( [sys.stdin], [], [], 1 )

        # If there is any user input in terminal, act upon it
        if (i):
            
            msg = sys.stdin.readline().strip()
            #print("User input:" + cmd)
            print (" ")

            tx_msg_nbr += 1

            # PUBLISH COMMAND (mSTART_APP)
            if msg[0] == "m":

                # Manually check if message number should be 0
                if msg[1:] == "STATE":
                    cmd ="0 STATE"
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


        sockets = dict(poller.poll(100))

        # If there is any message in pollin queue from LGTC devices
        if sockets.get(backend) == zmq.POLLIN:
            
            address, data_nbr, data = backend.recv_multipart()

            # Send ACK back
            backend.send_multipart([address, data_nbr, b"ACK"])

            # From bytes to string for loging output [address, count, data]
            msg = [address.decode(), data_nbr.decode(), data.decode()]

            # STATE
            if msg[1] == "0":
                mdb.updateDeviceState(msg[0], msg[2])
                print("New state of device %s: %s" % (msg[0] ,mdb.getDeviceState(msg[0])))
            
            #SYS
            elif msg[1] == "-1":

                # If device come to experiment later than sync process, add it do database
                if msg[2] == "SYNC":
                    # Add device to the database
                    if not mdb.isDeviceActive(msg[0]):
                        mdb.insertDevice(msg[0], "ONLINE")
                    print("Device %s send SYNC message" % msg[0])
                
                if msg[2] == "SOFT_EXIT":
                    # Remove device from the database
                    md.removeDevice(msg[0])
                    print("Device %s send SOFT_EXIT message" % msg[0])
                
            # DATA
            else:
                # Send response back to the server [device, count, data]
                print("Received [%s] from device %s: %s" % (msg[1], msg[0], msg[2]))
                
            print(" ")

        # TODO Heatbeat: Check status of devices and update it in DB
        #else ...

        #print(".")
except KeyboardInterrupt:
    print("Keyboard interrupt...exiting now.")

tx_msg_nbr += 1
print("Sent messages %i" % tx_msg_nbr)

msg =b"-1 END"
# Send stop command
#backend_pub.send(msg)


