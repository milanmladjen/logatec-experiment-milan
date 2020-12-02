import zmq 
import time
import logging

LOG_LEVEL = logging.DEBUG
NUMBER_OF_DEVICES = 1

def main():
    
    # First wait for synchronization from all subscribers
    subscribers = 0
    while subscribers < NUMBER_OF_DEVICES:
        # Wait for synchronization request
        address, empty, empty = router.recv_multipart()
        # Send synchronization reply
        resp = b''
        router.send_multipart([address, resp, resp])
        subscribers += 1
        logging.info("Device %s online (%i/%i)" % (address, subscribers, NUMBER_OF_DEVICES))

    

    # Start pushing commands
    user_command = 0
    for i in range(60):

        # Push command
        if(i%6 == 0):
            user_command = user_command + 1
            publisher.send_string(u'%i' % user_command)
            logging.debug("Send command: %i" % user_command)

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
                naslov, empty, msg = router.recv_multipart()
                logging.debug("Device %s sent: %s" % (naslov, msg))
                resp = b''
                router.send_multipart([naslov, resp, resp])

            # No response from devices
            else:
                break

        print(".")
        time.sleep(0.5)
    
    # Send stop command
    publisher.send(b'END')


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

main()