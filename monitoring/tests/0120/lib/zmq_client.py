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

    # ----------------------------------------------------------------------------------------
    # Initialize sockets and poller
    #
    # ----------------------------------------------------------------------------------------
    def __init__(self, SUBS_HOSTNAME, ROUT_HOSTNAME, deviceID="NoName"):

        context = zmq.Context()

        # Get device address
        device_address = deviceID.encode("ascii")

        # Connect to subscribe socket (--> publish)
        logging.debug("Connecting to publish socket...")
        self.subscriber = context.socket(zmq.SUB)
        self.subscriber.connect(SUBS_HOSTNAME)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')  #TODO

        # Connect to dealer socket (--> router)
        logging.debug("Connecting to router socket...")
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


    # ----------------------------------------------------------------------------------------
    # Send a message to the broker via DEALER socket
    # 
    #   @params:    message made with list of strings: [number, data]
    #   @return:    True if success
    # ----------------------------------------------------------------------------------------
    def transmit(self, msg):

        if not isinstance(msg, list):
            logging.error("transmit: Incorect format of message")
            return False
    
        # Encode the message from string to bytes
        msg = [msg[0].encode(), msg[1].encode()]
        
        logging.debug("Sending data to broker...")
        self.dealer.send_multipart(msg)
        
        self.txCnt += 1
        return True


    # ----------------------------------------------------------------------------------------
    # Send a message to the broker via DEALER socket (same as transmit)
    # But also put message number in ack queue
    #
    #   @params:    message made with list of strings: [number, data]
    # ----------------------------------------------------------------------------------------
    def transmit_async(self, msg):
        self.transmit(msg)

        # Broker sent another command before sending ACK to our previous message
        if len(self.waitingForAck) != 0:
            logging.warning("New message sent but broker didn't ack our previous one!")
            # TODO: stop receiveing messages after 3 already in queue

        self.waitingForAck.append(msg[0]) 
        self.lastSentInfo.append(msg)
        self.lastSentTime = timer.now()

        print("Info in queue ")
        print(self.lastSentInfo)

        return


    # ----------------------------------------------------------------------------------------
    # Check if there is any message in the poll queue
    #
    #   @params:    timeout - number of ms to wait (0 = return immediately)
    #   @return:    name of instance that received the message
    # ----------------------------------------------------------------------------------------
    def check_input(self, timeout):
        
        sockets = dict(self.poller.poll(timeout))

        if sockets.get(self.subscriber) == zmq.POLLIN:
            return "SUBSCRIBER"
        elif sockets.get(self.dealer) == zmq.POLLIN:
            return "DEALER"
        else:
            return None


    # ----------------------------------------------------------------------------------------
    # Read received message of given instance (use with func check_input). 
    # 
    #   @params:    instance - which socket has received message 
    #   @return:    [number, data] of received message in format string
    #               [None, None] if instance is unknown
    # ----------------------------------------------------------------------------------------
    def receive(self, instance):

        self.rxCnt += 1

        if (instance == "SUBSCRIBER"):
            packet = self.subscriber.recv()

            # Decode message manually
            p = packet.split()
            nbr = p[0].decode()
            data = p[1].decode()

            logging.debug("Subscriber got [%s]: %s" % (nbr, data))

            return nbr, data

        elif (instance == "DEALER"):
            nbr, data = self.dealer.recv_multipart()

            # Decode message from bytes to string
            msg = [nbr.decode(), data.decode()]

            logging.debug("Dealer got [%s]: %s" % (msg[0], msg[1]))

            return msg
        else:
            loging.error("receive: Unknown instance...check the code")
            return None, None


    # ----------------------------------------------------------------------------------------
    # Read received message of given instance (use with func check_input).
    # Handle received ACK without informing the user.
    # 
    #   @params:    instance - which socket has received message 
    #   @return:    [number, data] of received message in format string
    #               [None, True] if we received ACK
    #               [None, None] if instance is unknown
    # ----------------------------------------------------------------------------------------  
    def receive_async(self, instance):

        self.rxCnt += 1

        # If it is a message from publish socket
        if (instance == "SUBSCRIBER"):
            packet = self.subscriber.recv()

            p = packet.split()
            nbr = p[0].decode()
            data = p[1].decode()

            logging.debug("aSubscriber got [%s]: %s" % (nbr, data))

            return nbr, data

        # If it is a message from router socket
        elif (instance == "DEALER"):
            nbr, msg = self.dealer.recv_multipart()

            # Decode the message from bytes to string
            nbr = nbr.decode()
            msg = msg.decode()

            # If we got acknowledge on transmitted data
            if msg == "ACK":
                if nbr in self.waitingForAck:
                    logging.debug("Broker acknowledged our data [" + nbr + "]")
                    self.nbrRetries = 0

                    # Delete messages waiting in queue with number nbr
                    self.waitingForAck.remove(nbr)
                    i = 0
                    for info in self.lastSentInfo:
                        if info[0] == nbr:
                            del self.lastSentInfo[i]
                        i += 1
                else:
                    logging.warning("Got ACK for msg %s but in queue we have:" % nbr)
                    logging.warning(self.waitingForAck)
                    self.nbrRetries = 0

                return None, True

            # If we received any unicast command
            else:
                logging.debug("aDealer got [%s]: %s" % (nbr ,msg))
                return nbr, msg

        # If there is an error in calling the function
        else:
            loging.warning("receive_async: Unknown instance...check the code")
            return None, None


    # ----------------------------------------------------------------------------------------
    # Check how long we waited for ACK on sent package. If ACK_TIMEOUT seconds have passed,
    # send message again. Should be called periodically, whenever LGTC has some spare time.
    # Try to send the oldest message first. Try it no more than 2 times..
    # 
    #   @params:    / (everything is stored in class variables)
    # ----------------------------------------------------------------------------------------
    def send_retry(self):

        if ((timer.now() - self.lastSentTime).total_seconds() > self.ACK_TIMEOUT):
            logging.warning("3 second have passed and no response from broker.. Resending data!")

            oldest = self.waitingForAck[0]

            print("Sending oldest: " + oldest + "...")
            for info in self.lastSentInfo:
                if info[0] == oldest:
                    print(info)
                    self.transmit(info)
                    self.lastSentTime = timer.now()
                    break

            self.nbrRetries += 1
            if self.nbrRetries > 1:
                # Server has died ?
                self.waitingForAck = []
                self.lastSentInfo = []
                self.nbrRetries = 0
                logging.warning("Broker has died :(")
        else:
            return


    # ----------------------------------------------------------------------------------------
    # Force wait for ACK on given message number - it will block the code and discard all 
    # other received messages.
    # 
    #   @params:    nbr     - a message number on which we are waiting for ACK...must be in string!
    #               timeout - time to wait in seconds!
    #   @return:    True when received ACK, False if timeout passes
    # ----------------------------------------------------------------------------------------
    def wait_ack(self, nbr, timeout):

        if not isinstance(nbr, str):
            logging.error("wait_ack: Input data must be string")
            return False

        startTime = timer.now()

        while True:
            if ((timer.now() - startTime).total_seconds() < timeout):
                inp = self.check_input(0)
                if inp:

                    rec = self.receive(inp)     # rec = [nbr, data]
                    # Nbr of transmitted and received msg must be the same
                    if(rec[0] == nbr and rec[1] == "ACK"):
                        return True
                    else:
                        logging.warning("Received: " + rec[1] + " message but waiting for ACK")
            else:
                return False









"""  
# Demo usage TODO: deprecated
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


