# 
#   Server test - server that talks to the LGTC clients over 0MQ
#   User can input commands in the terminal, which are sent to synced devices
#

import zmq 
import time
import logging

import select, sys # For user input


LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 3

lgtc_addr = []


# ===================================================================================== #
# Configure logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

#if __name__ == '__main__':


context = zmq.Context.instance()

# Socket for publishing commands
publisher = context.socket(zmq.PUB)
publisher.sndhwm = 1100000      # set SNDHWM, so we don't drop messages for slow subscribers
publisher.bind('tcp://*:5561')

# Socket to get responses
router = context.socket(zmq.ROUTER)
router.bind('tcp://*:5562')

# Configure poller
poller = zmq.Poller()
poller.register(router, zmq.POLLIN)


# ------------------------------------------------------------------------------- #
# First wait for synchronization from all subscribers
# ------------------------------------------------------------------------------- #
logging.info("Waiting for LGTC devices ... ")

subscribers = 0
try:
    while subscribers < NUMBER_OF_DEVICES:
        # Wait for synchronization request (
        address, packet_type, nbr, msg = router.recv_multipart()

        if packet_type == "SYNC":
            # Add address to the list of LGTC addr
            if address not in lgtc_addr:
                lgtc_addr.append(address)

            # Send synchronization reply
            router.send_multipart([address, b"ACK", b"0", b" "])

            # Inform user about new device
            subscribers += 1
            logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))
        else:
            logging.warning("Got a message but not sync request...discarting.")

except KeyboardInterrupt:
    print("Keybopard interrupt...continuing application.")


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the app
# ------------------------------------------------------------------------------- #

print("-------------------------------------------------------------------------------")
print("Type in the command. For multicast use prefix m, for unicast use prefix u.")
print("Example: mSTATE, mSTART_APP, u81STATE, ...")
print(" ")
tx_msg_nbr = 0
while True:

    # Wait one second for any user input message
    i, o, e = select.select( [sys.stdin], [], [], 1 )

    # If there is any user input, act upon it
    if (i):
        cmd = sys.stdin.readline().strip()
        #print("User input:" + cmd)
        print (" ")
        tx_msg_nbr += 1

        # PUBLISH COMMAND
        if cmd[0] == "m":

            msg =b"%i %s" % (tx_msg_nbr, cmd[1:])
            publisher.send(msg)
            logging.debug("Sent PUB_CMD [%i]: %s" % (tx_msg_nbr, cmd[1:]))
        
        # UNICAST COMMAND
        if cmd[0] == "u":
            adr = "LGTC" + cmd[1:3]

            print(cmd[3:])

            if adr in lgtc_addr:
                msg = [adr, b"UNI_CMD", str(tx_msg_nbr), cmd[3:]]
                router.send_multipart(msg)
                logging.debug("Sent UNI_CMD [%i] to device %s: %s" % (tx_msg_nbr, adr, cmd[3:]))
            else:
                logging.warning("Incorect address input: %s (possible %s)!" % (adr, lgtc_addr))

        
    
    # Wait just a bit (10ms) to check if there is more incomeing messages
    # If we go ahead too fast, we will miss them and client has to wait for us to come here again
    # LGTC needs aprox 30ms if not even more
    # But if we will go through the rest of the code fast, we don't need this timeout
    # Problem is that now we wait here for 30ms or even more each time we get here..not good
    socks = dict(poller.poll(100))

    # If there is any message in pollin queue
    if socks.get(router) == zmq.POLLIN:
        address, msg_type, msg_nbr, msg = router.recv_multipart()

        # TODO: Add some filtering here? If received SYNC, should we ACK or not?
        router.send_multipart([address, b"ACK", msg_nbr, b" "])

        logging.info("Received %s[%s] from device %s: %s" % (msg_type, msg_nbr, address, msg))
        print(" ")



    #print(".")

tx_msg_nbr += 1
cmd = "END"
msg =b"%i %s" % (tx_msg_nbr, cmd)
# Send stop command
publisher.send(msg)


