import time
import zmq
import logging
import sys
from datetime import datetime as timer
#from timeit import default_timer as timer #TODO test if better


LOG_LEVEL = logging.DEBUG


class zmq_client():

    ROUTER_HOSTNAME = "tcp://192.168.88.253:5562"
    SUBSCR_HOSTNAME = "tcp://192.168.88.253:5561"
    ACK_TIMEOUT = 3

    rxCnt = 0
    txCnt = 0


    def __init__(self, deviceID):
        # Initialize sockets and poller 

        # Get device address
        device_address = deviceID.encode("ascii")
        logging.info("Device name: %s" % device_address)

        context = zmq.Context()

        # Connect to subscribe socket (--> publish)
        logging.debug("Connecting to publish server...")
        self.subscriber = context.socket(zmq.SUB)
        self.subscriber.connect(self.SUBSCR_HOSTNAME)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')  #TODO

        # Connect to dealer socket (--> router)
        logging.debug("Connecting to router server...")
        self.dealer = context.socket(zmq.DEALER)
        self.dealer.identity = device_address
        self.dealer.connect(self.ROUTER_HOSTNAME)

        # Configure poller
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        self.poller.register(self.dealer, zmq.POLLIN)

        # Class variables ... they are storing:
        self.waitingForAck = []             # Buffer - a list with sequence number of messages that must receive an ACK
        self.lastSentInfo = []              # The last sent message
        self.nbrRetries = 0                 # A number of sending retries 
        #self.lastSentTime = timer.now()    # The last time we sent any message (it must be a type: datetime.datetime)
        



    def sync_with_server(self):
        # Send SYNC message to the server, so it knows we are online

        logging.debug("Send a synchronization request.")

        msgType = b"SYNC"
        self.dealer.send_multipart([msgType, b"0", b"Hi"])

        msgType, nbr, msg = self.dealer.recv_multipart()
        if msgType == "SYNC":
            logging.info("Synced with server (%s)" % msg)
        else:
            logging.error("Could not sync with server!")


    def receive(self, instance):
        # Read received message

        self.rxCnt += 1

        # If it is a message from publish socket
        if (instance == "SUBSCRIBER"):
            msg = self.subscriber.recv()

            ms = msg.split()
            nbr = ms[0]
            msg = ms[1]

            logging.info("Received PUB_CMD [%s]: %s" % (nbr, msg))

            return msg, nbr

        # If it is a message from router socket
        elif (instance == "DEALER"):
            msg_type, nbr, msg = self.dealer.recv_multipart()

            # If we got acknowledge on transmitted data
            if msg_type == "ACK":
                if nbr in self.waitingForAck:
                    logging.info("Server acknowledged our data [" + nbr + "]")
                    self.waitingForAck.remove(nbr)
                    self.nbrRetries = 0
                else:
                    logging.warning("Got ACK for msg %s...in queue %s:" % (nbr, self.waitingForAck))
                    self.nbrRetries = 0

                return None, None

            # If we received any unicast command
            elif msg_type == "UNI_CMD":
                logging.info("Received UNI_CMD [%s]: %s" % (nbr ,msg))
                return msg, nbr

            elif ms_type == "SYNC":
                print("Received SYNC message...something went wrong")
                sys.exit(1) #TODO

            # If we received unknown type of message
            else:
                loging.warning("Received unknown type of message...discarting.")
                return None, None

        # If there is an error in calling the function
        else:
            loging.warning("Unknown instance...check the code")
            return None, None


    def send(self, reply):
        # Send a message to the server - must be formed as a list: [type, nbr, msg]

        logging.debug("Sending data to server...")
        self.dealer.send_multipart(reply)

        # Server sent another command before sending ACK to our previous message
        if len(self.waitingForAck) != 0:
            logging.warning("New message sent but server didn't ack our previous message!")
            # logging.warning("Old message will be overwritten.. :/")
        
        self.waitingForAck.append(reply[1])
        self.lastSentInfo = reply
        self.lastSentTime = timer.now()
        
        self.txCnt += 1

        return


    def send_retry(self):
        # Check how long we waited for ACK - if 3 seconds have passed, send message again
 
        if ((timer.now() - self.lastSentTime).total_seconds() > self.ACK_TIMEOUT):
            logging.warning("3 second have passed and no response from server.. Resending data!")
            # Resend info
            self.dealer.send_multipart(self.lastSentInfo)
            self.lastSentTime = timer.now()

            self.nbrRetries += 1
            if self.nbrRetries > 1:
                # Server has died ?
                self.waitingForAck = []
                self.nbrRetries = 0
                logging.warning("Server has died :(")   #TODO
        else:
            return


    
# Demo usage
if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)

    address = u'LGTC-%s' % sys.argv[1]       #TODO

    cliente = zmq_client(address)

    # ------------------------------------------------------------------------------- #
    # First synchronize with the server
    cliente.sync_with_server()

    # ------------------------------------------------------------------------------- #
    # Than start the app


    while True:
        # Check for any incoming messages
        socks = dict(cliente.poller.poll(0))
        
        # If there are any command_messages from the publish server
        if socks.get(cliente.subscriber) == 1:

            # Read them
            msg, rxPnbr = cliente.receive("SUBSCRIBER")
            
            # Obtain the info upon received command 
            #info = obtain_info(msg)
            info = "42!"

            # Form reply
            reply = ["PUB_DAT", rxPnbr, info] 
            
            # Respond to the server
            cliente.send(reply)

            # Maybe add a just a bit of delay here. Because without it, client won't receive the ACK right
            # away and will go work some other stuff. Which is ok, but it must come here fast enough (rest 
            # of the code shouldn't delay for too long)

            # Or maybe use "continue" to return to poller check on the beginning
            # Beware that then you can stuck here if you got many messages in queue
            continue

        
        # If we received any direct messages from router server
        if socks.get(cliente.dealer) == 1:

            # Read them
            msg, rxDnbr = cliente.receive("DEALER")

            # If there is a message for us
            if msg != None:
                # Obtain the info upon received command 
                #info = obtain_info(msg)
                info = "41!"

                # Form reply
                reply = ["UNI_DAT", rxDnbr, info]

                # Respond to the server
                cliente.send(reply)


        # If we sent one message and there was no response for more than a second, resend it
        if len(cliente.waitingForAck) != 0:
            cliente.send_retry()

        
        # Do some other stuff
        print(".")
        time.sleep(1)




