#   TODO
#   Do I still need that type_of_message param?   
#   Use different names to prevent shadowing and overwritting 

import zmq 
import time
import logging

from lib import mongodb_client

LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 3

# ------------------------------------------------------------------------------- #
# Configuration
# ------------------------------------------------------------------------------- #
# Logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

#if __name__ == '__main__':

mdb = mongodb_client.mongodb_client("active-devices", DATABASE="experiment-monitor")

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
frontend.bind("ipc:///tmp/zmq_ipc")
flask_script_id = b"flask_process"    # defined in flask

# Configure poller
poller = zmq.Poller()
poller.register(backend, zmq.POLLIN)
poller.register(frontend, zmq.POLLIN)


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

            # Inform user about new device in terminal
            subscribers += 1
            logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))
        else:
            logging.warning("Got a message but not sync request (%s) ...discarting." % packet_type)

except KeyboardInterrupt:
    print("Keybopard interrupt...continuing application.")


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the main loop
# ------------------------------------------------------------------------------- #
mdb.printTestbedState()

print("Starting main loop...") #TODO make it multitherad?
tx_msg_nbr = 0

try:
    while True:

        sockets = dict(poller.poll(100))

        # If there is a message in polling queue from the flask server, forward it to LGTC devices
        if sockets.get(frontend) == zmq.POLLIN:

            dummy_flask_script_id, device, count, data = frontend.recv_multipart()

            # From bytes to string for loging output [device, count, data]
            msg = [device.decode(), count.decode(), data.decode()]

            logging.info("Received CMD [%s] from server: %s for: %s" % (msg[1],msg[2], msg[0]))

            tx_msg_nbr += 1

            # PUBLISH COMMAND - if message is for all devices
            if msg[0] == "All":

                cmd ="%s %s" % (msg[1], msg[2])
                backend_pub.send(cmd.encode())
                logging.debug("Published message [%s]: %s" % (msg[1], msg[2]))
            
            # UNICAST COMMAND - if message is only for one device
            else:
                # Addres must be in database, otherwise it is not active
                if mdb.isDeviceActive(device):
                    cmd = [device, count, data]
                    backend.send_multipart(cmd)
                    logging.debug("Router sent message [%s]: %s to device %s" % (msg[1], msg[2], msg[0]))
                else:
                    logging.warning("Device address is not in DB")


        # If there is any message in pollin queue from LGTC devices, forward it to flask_server
        elif sockets.get(backend) == zmq.POLLIN:
            
            address, data_nbr, data = backend.recv_multipart()

            # Send ACK back
            backend.send_multipart([address, data_nbr, b"ACK"])

            # From bytes to string for loging output [address, count, data]
            msg = [address.decode(), data_nbr.decode(), data.decode()]

            # If we received state packet, update the database only
            if msg[1] == "0":
                mdb.updateDeviceState(msg[0], msg[2])
                # TODO inform frontend

            # If device come to experiment later than sync process, add it do database
            else if msg[1] == "-1":
                # Add device to the database
                if not mdb.isDeviceActive(msg[0]):
                    mdb.insertDevice(msg[0], "ONLINE")

            else:
                # Send response back to the server [device, count, data]
                frontend.send_multipart([flask_script_id, address, data_nbr, data])

            logging.info("Received [%s] from device %s: %s" % (msg[1], msg[0], msg[2]))
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
backend_pub.send(msg)


