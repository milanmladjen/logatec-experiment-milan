#   TODO
#   Do I still need that type_of_message param?   
#   Use different names to prevent shadowing and overwritting 

import zmq 
import time
import logging

import select, sys # For user input


LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 3

lgtc_addr = []


# ------------------------------------------------------------------------------- #
# Configuration
# ------------------------------------------------------------------------------- #
# Logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

#if __name__ == '__main__':


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
        address, packet_type, nbr, msg = backend.recv_multipart()

        if packet_type == b"SYNC":
            # Add address to the list of LGTC addr
            if address not in lgtc_addr:
                lgtc_addr.append(address)

            # Send synchronization reply
            backend.send_multipart([address, b"ACK", b"0", b" "])

            # Inform user about new device (TODO store it to DB)
            subscribers += 1
            logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))
        else:
            logging.warning("Got a message but not sync request (%s) ...discarting." % packet_type)

except KeyboardInterrupt:
    print("Keybopard interrupt...continuing application.")


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the main loop
# ------------------------------------------------------------------------------- #

print("Starting main loop") #TODO make it multitherad?
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
                logging.debug("Sent PUB_CMD [%s]: %s" % (msg[1], msg[2]))
            
            # UNICAST COMMAND - if message is only for one device
            else:
                # Addres must be in list of available devices
                if device in lgtc_addr:
                    cmd = [device, b"UNI_CMD", count, data]
                    backend.send_multipart(cmd)
                    logging.debug("Sent UNI_CMD [%s]: %s to device %s" % (msg[1], msg[2], msg[0]))
                else:
                    logging.warning("Incorect address input: %s (possible %s)!" % (device, lgtc_addr))


        # If there is any message in pollin queue from LGTC devices, forward it to flask_server
        elif sockets.get(backend) == zmq.POLLIN:
            
            address, data_type, data_nbr, data = backend.recv_multipart()

            # TODO: Add some filtering here? If received SYNC, should we ACK or not?
            backend.send_multipart([address, b"ACK", data_nbr, b" "])

            # From bytes to string for loging output [device, count, data]
            msg = [address.decode(), data_nbr.decode(), data.decode(), data_type.decode()]

            logging.info("Received %s[%s] from device %s: %s" % (msg[3], msg[1], msg[0], msg[2]))
            print(" ")

            # Send response back to the server [device, count, data]
            frontend.send_multipart([flask_script_id, address, data_nbr, data])

        # Check status of devices and update it in DB
        #else ...

        #print(".")
except KeyboardInterrupt:
    Print("Keyboard interrupt...exiting now.")

tx_msg_nbr += 1
cmd = "END"
msg =b"%i %s" % (tx_msg_nbr, cmd)
# Send stop command
backend_pub.send(msg)


