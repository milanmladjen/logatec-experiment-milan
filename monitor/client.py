import time
import zmq
import logging
import sys


LOG_LEVEL = logging.DEBUG
DATA_RESP_RETRIES = 2

def main():

    # Socket for responding to server
    logging.debug("Connecting to router server...")
    device_address = u'LGTC-%d' % 2
    client = context.socket(zmq.REQ)
    client.identity = device_address.encode("ascii")
    client.connect('tcp://192.168.88.253:5562')

    logging.info("Device name: %s" % device_address)

    # First sync with the server, so it knows we are online
    logging.debug("Send a synchronization request")
    client.send(b'')
    #client.send_string(b"%s" % device_address)

    client.recv()
    logging.info("Synced with server!")

    
    # Wait for incoming commands
    nbr = 0
    while True:
        # Argument specifies how many milliseconds to wait... blank or -1 blocks until message received, 0 returns imediatelly and so on
        socks = dict(poller.poll(0))
        
        # If there are any command_messages from the publish server in queue (zmq.POLLIN je int enka)
        if socks.get(subscriber) == zmq.POLLIN:
            # Read them
            cmd = subscriber.recv()
            logging.info("Received: %s" % cmd)
            if cmd == b'END':
                break

            # Respond to the serve
            retries_left = DATA_RESP_RETRIES
            while True:
                logging.debug("Sending data...")
                client.send_string(u"Here is your info: %s" % cmd)

                # 1 second timeout to get the response back
                # To big value will hang the monitor
                if (client.poll(1000) & zmq.POLLIN) != 0:
                    client.recv()
                    logging.debug("Server got it!")
                    break

                retries_left -= 1
                logging.warning("No response from server")
                # Socket is confused. Close and remove it.
                client.setsockopt(zmq.LINGER, 0)
                client.close()
                if retries_left == 0:
                    logging.error("Server seems to be offline, abandoning")
                    sys.exit()

                logging.info("Reconnecting to server...")
                # Create new connection
                client = context.socket(zmq.REQ)
                client.connect('tcp://192.168.88.253:5562')

            
            nbr += 1
        else:
            logging.debug(".")
            time.sleep(5)

    logging.debug("Received %d updates" % nbr)



# ===================================================================================== #
# Configure logging module
logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)


#if __name__ == '__main__':


context = zmq.Context()

# Socket to subscribe to publish server
logging.debug("Connecting to publish server...")
subscriber = context.socket(zmq.SUB)
subscriber.connect('tcp://192.168.88.253:5561')
subscriber.setsockopt(zmq.SUBSCRIBE, b'')



# Configure poller
poller = zmq.Poller()
poller.register(subscriber, zmq.POLLIN)

main()