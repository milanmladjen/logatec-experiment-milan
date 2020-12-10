import time
import zmq
import logging
import sys
from datetime import datetime as timer
#from timeit import default_timer as timer #TODO test if better


class zmq_client():

    
    ACK_TIMEOUT = 3

    rxCnt = 0
    txCnt = 0

    # Initialize sockets and poller
    def __init__(self, SUBS_HOSTNAME, ROUT_HOSTNAME, deviceID="NoName"):

        context = zmq.Context()

        # Get device address
        device_address = deviceID.encode("ascii")

        # Connect to subscribe socket (--> publish)
        logging.debug("Connecting to publish server...")
        self.subscriber = context.socket(zmq.SUB)
        self.subscriber.connect(SUBS_HOSTNAME)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')  #TODO

        # Connect to dealer socket (--> router)
        logging.debug("Connecting to router server...")
        self.dealer = context.socket(zmq.DEALER)
        self.dealer.identity = device_address
        self.dealer.connect(ROUT_HOSTNAME)

        # Configure poller
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        self.poller.register(self.dealer, zmq.POLLIN)

        # Class variables ... they are storing:
        self.waitingForAck = []             # Buffer - a list with sequence number of messages that must receive an ACK
        self.lastSentInfo = []              # The last sent message
        self.nbrRetries = 0                 # A number of sending retries 
        #self.lastSentTime = timer.now()    # The last time we sent any message (it must be a type: datetime.datetime)
        

    # Poll the sockets for given amount of timeout (0 = return immediately)
    def check_input(self, timeout):
        
        sockets = dict(self.poller.poll(timeout))

        if sockets.get(self.subscriber) == zmq.POLLIN:
            return "SUBSCRIBER"
        elif sockets.get(self.dealer) == zmq.POLLIN:
            return "DEALER"
        else:
            return None

    
    # Read received message...returns list (type_of_msg, nbr_of_msg, msg)
    def receive(self, instance):

        self.rxCnt += 1

        if (instance == "SUBSCRIBER"):
            msg = self.subscriber.recv()

            ms = msg.split()
            nbr = ms[0]
            msg = ms[1]

            logging.info("Received PUB_CMD [%s]: %s" % (nbr, msg))

            return "PUB_CMD", nbr, msg

        elif (instance == "DEALER"):
            msg_type, nbr, msg = self.dealer.recv_multipart()

            return msg_type, nbr, msg

        else:
            loging.error("Unknown instance...check the code")
            return None, None, None


    # Send a message to the server - must be formed as a list: [type, nbr, msg]
    def transmit(self, msg):

        if not isinstance(msg, list):
            logging.error("Incorect format of message")
            return False
        
        logging.debug("Sending data to server...")
        self.dealer.send_multipart(msg)
        
        self.txCnt += 1
        return True


    # Force wait for ACK on given message number - discard all other received messages
    # Timeout is in seconds!!!
    def wait_ack(self, nbr, timeout):

        startTime = timer.now()

        while True:
            if ((timer.now() - startTime).total_seconds() < timeout):
                inp = self.check_input(0)
                if inp:
                    rec = self.receive(inp)
                    # Nbr of transmitted and received msg must be the same
                    if(rec[0] == "ACK" and rec[1] == str(nbr)):
                        return True
                    else:
                        logging.warning("Received " + rec[0] + " message but waiting for ACK")
            else:
                return False
            
    # Receive message and return it...handel ACK without informing the user 
    def receive_async(self, instance):
        # Returns:
        #       True if we received an ACK
        #       False if there is no message/error
        #       (type_of_msg, nbr_of_msg, msg) if we received some data

        self.rxCnt += 1

        # If it is a message from publish socket
        if (instance == "SUBSCRIBER"):
            msg = self.subscriber.recv()

            ms = msg.split()
            nbr = ms[0]
            msg = ms[1]

            logging.info("Received PUB_CMD [%s]: %s" % (nbr, msg))

            return "PUB_CMD", nbr, msg

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

                return True, None, None

            # If we received any unicast command
            elif msg_type == "UNI_CMD":
                logging.info("Received UNI_CMD [%s]: %s" % (nbr ,msg))
                return msg_type, nbr, msg

            elif ms_type == "SYNC":
                print("Received SYNC message...something went wrong")
                sys.exit(1) #TODO

            # If we received unknown type of message
            else:
                loging.warning("Received unknown type of message...discarting.")
                return False, None, None

        # If there is an error in calling the function
        else:
            loging.warning("Unknown instance...check the code")
            return None, None, None


    def transmit_async(self, msg):
        # Send a message to the server - must be formed as a list: [type, nbr, msg]
        self.transmit(msg)
    
        # Server sent another command before sending ACK to our previous message
        if len(self.waitingForAck) != 0:
            logging.warning("New message sent but server didn't ack our previous message!")
            # logging.warning("Old message will be overwritten.. :/")
        
        self.waitingForAck.append(msg[1])
        self.lastSentInfo = msg
        self.lastSentTime = timer.now()

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




    # Send SYNC message to the server, so it knows we are online
    def sync_with_server(self, timeout):

        logging.debug("Send a synchronization request.")

        sync_request = ["SYNC", b"0", b" "]
        self.transmit(sync_request)
        state = self.wait_ack("0", timeout)

        if state is True:
            logging.info("Synced with server!")
            return True
        else:
            logging.error("Could not sync with server!")
            return False







"""  
# Demo usage
if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO
)

    address = u'LGTC-%s' % sys.argv[1]       #TODO

    cliente = zmq_client(address)

    # ------------------------------------------------------------------------------- #
    # First synchronize with the server
    cliente.sync_with_server()

    # ------------------------------------------------------------------------------- #
    # Than start the app


    while True:
        # Check for any incoming messages
        input_message = cliente.check_input(0)
        if input_message:

            # Read them
            msg_type, msg, rxPnbr = cliente.receive(input_message)
            
            # Obtain the info upon received command 
            #info = obtain_info(msg)
            info = "42!"

            # Form reply
            reply = [msg_type, rxPnbr, info] 
            
            # Respond to the server
            cliente.send(reply)

            # Maybe add a just a bit of delay here. Because without it, client won't receive the ACK right
            # away and will go work some other stuff. Which is ok, but it must come here fast enough (rest 
            # of the code shouldn't delay for too long)

            # Or maybe use "continue" to return to poller check on the beginning
            # Beware that then you can stuck here if you got many messages in queue
            continue


        # If we sent one message and there was no response for more than a second, resend it
        if len(cliente.waitingForAck) != 0:
            cliente.send_retry()

        
        # Do some other stuff
        print(".")
        time.sleep(1)
"""


