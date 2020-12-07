import zmq 
import time
import logging

LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 1

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
subscribers = 0
while subscribers < NUMBER_OF_DEVICES:
    # Wait for synchronization request (msg is "Hi")
    #address, msg = router.recv_multipart()
    address, packet_type, nbr, msg = router.recv_multipart()

    # Add address to the list of LGTC addr
    if address not in lgtc_addr:
        lgtc_addr.append(address)

    # Send synchronization reply
    resp = "Hello there!"
    router.send_multipart([address, b"SYNC", b"0", resp])

    # Inform user about new device
    subscribers += 1
    logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the app
# ------------------------------------------------------------------------------- #

# Start pushing commands
tx_msg_nbr = 0
for i in range(60):
    

    # Push command
    if(i%6 == 0):
        tx_msg_nbr += 1

        cmd = "Do-smth"

        msg =b"%i %s" % (tx_msg_nbr, cmd)
        publisher.send(msg)
        logging.debug("Sent PUB_CMD [%i]: %s" % (tx_msg_nbr, cmd))

    if(i%8 == 0):
        adr = lgtc_addr[0]
        router.send_multipart([adr, b"UNI_CMD", b"1", b"STATE"])

    # Check if we got any response from devices
    while True:
        
        # Wait just a bit (10ms) to check if there is more incomeing messages
        # If we go ahead too fast, we will miss them and client has to wait for us to come here again
        # LGTC needs aprox 30ms if not even more
        # But if we will go through the rest of the code fast, we don't need this timeout
        # Problem is that now we wait here for 30ms or even more each time we get here..not good

        socks = dict(poller.poll(100))

        # If there is any message in pollin queue
        if socks.get(router) == zmq.POLLIN:
            address, msg_type, rx_msg_nbr, msg = router.recv_multipart()
            router.send_multipart([address, b"DATA_ACK", rx_msg_nbr, b""])

            logging.debug("%s sent: %s" % (address, msg))

            #tx_msg_nbr += 1
            #router.send_multipart([address, b"UNI_CMD", tx_msg_nbr, b""])

        # No response from devices
        else:
            break

    print(".")
    time.sleep(0.5)

tx_msg_nbr += 1
cmd = "END"
msg =b"%i %s" % (tx_msg_nbr, cmd)
# Send stop command
publisher.send(msg)


