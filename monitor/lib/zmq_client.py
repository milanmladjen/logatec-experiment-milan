import time
import zmq
import logging
import sys
from datetime import datetime as timer
#from timeit import default_timer as timer #TODO test if better

LOG_LEVEL = logging.DEBUG

class zmq_client():

    
    ACK_TIMEOUT = 3

    rxCnt = 0
    txCnt = 0

    # ----------------------------------------------------------------------------------------
    # Initialize sockets and poller
    #
    # ----------------------------------------------------------------------------------------
    def __init__(self, SUBS_HOSTNAME, ROUT_HOSTNAME, deviceID="NoName"):

        self.log = logging.getLogger(__name__)
        self.log.setLevel(LOG_LEVEL)

        context = zmq.Context()

        # Get device address
        device_address = deviceID.encode("ascii")

        # Connect to subscribe socket (--> publish)
        self.log.debug("Connecting to publish socket...")
        self.subscriber = context.socket(zmq.SUB)
        self.subscriber.connect(SUBS_HOSTNAME)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')  #TODO

        # Connect to dealer socket (--> router)
        self.log.debug("Connecting to router socket...")
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
            self.log.error("transmit: Incorect format of message")
            return False
    
        # Encode the message from string to bytes
        msg = [msg[0].encode(), msg[1].encode()]
        
        self.log.debug("Sending data to broker...")
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
  
        if not self.transmit(msg):
            return

        # Broker sent another command before sending ACK to our previous message
        if len(self.waitingForAck) > 1:
            self.log.warning("New message sent but broker didn't ack our previous one!")
            # TODO: stop receiveing messages after 3 already in queue?

        self.waitingForAck.append(msg[0]) 
        self.lastSentInfo.append(msg)
        self.lastSentTime = timer.now()

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

            self.log.debug("Subscriber got [%s]: %s" % (nbr, data))

            return nbr, data

        elif (instance == "DEALER"):
            nbr, data = self.dealer.recv_multipart()

            # Decode message from bytes to string
            msg = [nbr.decode(), data.decode()]

            self.log.debug("Dealer got [%s]: %s" % (msg[0], msg[1]))

            return msg
        else:
            self.log.error("receive: Unknown instance...check the code")
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
            sqn = p[0].decode()
            data = p[1].decode()

            self.log.debug("aSubscriber got [%s]: %s" % (sqn, data))

            return sqn, data

        # If it is a message from router socket
        elif (instance == "DEALER"):
            sqn, msg = self.dealer.recv_multipart()

            # Decode the message from bytes to string
            sqn = sqn.decode()
            msg = msg.decode()

            # If we got acknowledge on transmitted data, message stores SQN of acknowledged response
            if sqn == "ACK":
                if msg in self.waitingForAck:
                    self.log.debug("Broker acknowledged our data [" + msg + "]")
                    self.nbrRetries = 0

                    # Delete messages waiting in queue with number in msg
                    self.waitingForAck.remove(msg)
                    i = 0
                    for info in self.lastSentInfo:
                        if info[0] == msg:
                            del self.lastSentInfo[i]
                        i += 1
                else:
                    self.log.warning("Got ACK for msg %s but in queue we have:" % msg)
                    self.log.warning(self.waitingForAck)
                    self.nbrRetries = 0

                return None, True

            # If we received any unicast command
            else:
                self.log.debug("aDealer got [%s]: %s" % (sqn ,msg))
                return sqn, msg

        # If there is an error in calling the function
        else:
            self.log.warning("receive_async: Unknown instance...check the code")
            return None, None


    # ----------------------------------------------------------------------------------------
    # Check how long we waited for ACK on sent package. If ACK_TIMEOUT seconds have passed,
    # send message again. Should be called periodically, whenever LGTC has some spare time.
    # 
    #   @params:    / (everything is stored in class variables)
    # ----------------------------------------------------------------------------------------
    def send_retry(self):

        if ((timer.now() - self.lastSentTime).total_seconds() > self.ACK_TIMEOUT):
            self.log.warning("3 second have passed and no response from broker.. Resending data!")

            # Resend info with lowest number...Example:
            # waitingForAck = [15, 16, 17]
            # lastSentInfo = [[15, START], [16, STOP], [17, START]]

            oldest = self.waitingForAck[0]

            for info in self.lastSentInfo:
                if info[0] == oldest:
                    self.transmit(info)
                    self.lastSentTime = timer.now()
                    break

            self.nbrRetries += 1
            if self.nbrRetries > 1:
                # Server has died ?
                self.waitingForAck = []
                self.lastSentInfo = []
                self.nbrRetries = 0
                self.log.warning("Broker has died :(")
                #TODO clean the resources (zmq.close)
        else:
            return


    # ----------------------------------------------------------------------------------------
    # Force wait for ACK on given message number - it will block the code and discard all 
    # other received messages.
    # 
    #   @params:    sqn     - a message number on which we are waiting for ACK...must be in string!
    #               timeout - time to wait in seconds!
    #   @return:    True when received ACK, False if timeout passes
    # ----------------------------------------------------------------------------------------
    def wait_ack(self, sqn, timeout):

        if not isinstance(sqn, str):
            self.log.error("wait_ack: Input data must be string")
            return False

        startTime = timer.now()

        while True:
            if ((timer.now() - startTime).total_seconds() < timeout):
                inp = self.check_input(0)
                if inp:

                    rec = self.receive(inp)     # rec = ["ACK", sqn]
                    # Nbr of transmitted and received msg must be the same
                    if(rec[0] == "ACK" and rec[1] == sqn):
                        return True
                    else:
                        self.log.warning("Received: " + rec[0] + " message but waiting for ACK")
            else:
                return False






# TODO: Demo usage?
# if __name__ == "__main__":