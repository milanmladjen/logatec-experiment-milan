import time
import zmq
import logging
import sys
from datetime import datetime as timer


LOG_LEVEL = logging.DEBUG
DATA_RESP_RETRIES = 2


def obtain_info(cmd):
    # Return the requested info 

    data = "42!"

    if cmd == "END":
        # Exit application
        logging.debug("Got END command...exiting now!")
        sys.exit(1)

    elif cmd == "STATE":
        # Return the current state of the LGTC deivce
        logging.debug("Return the STATE of the device")

    elif cmd == "START_APP":
        # Send start command through serial_monitor.py
        logging.debug("Start the application!")

    elif cmd == "STOP_APP":
        # Send stop command through serial_monitor.py
        logging.debug("Stop the application!")

    else:
        logging.warning("Unknown command: %s" % cmd)

    return data

def main():

    # First sync with the server, so it knows we are online
    logging.debug("Send a synchronization request")

    packet_type = b"SYNC"
    client.send_multipart([packet_type, b"Hi"])

    packet_type, msg = client.recv_multipart()
    if packet_type == "SYNC":
        logging.info("Synced with server (%s)" % msg)
    else:
        logging.error("Could not sync with server!")


# ------------------------------------------------------------------------------- #
# Devices are synchronized - start the app
# ------------------------------------------------------------------------------- #

    waiting_for_ack = False
    last_sent_info = b""
    last_sent_time = 0
    
    rx_msg_nbr = 0
    rx_pub_nbr = 0
    tx_msg_nbr = 0
    retires_nbr = 0

    while True:
        # Check for any incoming messages
        socks = dict(poller.poll(0))
        
        # If there are any command_messages from the publish server
        if socks.get(subscriber) == zmq.POLLIN:

            # Read them
            msg = subscriber.recv()

            msg_s = msg.split()
            rx_pub_nbr = int(msg_s[0])
            msg = msg_s[1]

            logging.info("Received PUB_CMD [%i]: %s" % (rx_pub_nbr, msg))
            
            # Obtain the info upon received command 
            info = obtain_info(msg)

            # Form reply
            reply = ["PUB_DAT", str(rx_pub_nbr), info] 

            # Respond to the server
            logging.debug("Sending data...")
            client.send_multipart(reply)

            # If waiting is still true, that means that server did not hear us until now
            if waiting_for_ack:
                logging.warning("Got new command but server didn't receive our previous message!")
                # logging.warning("Old message will be discarted.. :/")
                # If user needs that message again, he will request for it.. 
            
            waiting_for_ack = rx_pub_nbr
            last_sent_info = reply
            last_sent_time = timer.now()

            # Maybe add a just a bit of delay here. Because without it, client won't receive the ACK right
            # away and will go work some other stuff. Which is ok, but it must come here fast enough (rest 
            # of the code shouldn't delay for too long)

            # Or maybe use "continue" to return to poller check on the beginning
            # Beware that then you can stuck here if you got many messages in queue
            continue

        
        # If we received any direct messages from router server
        if socks.get(client) == zmq.POLLIN:
            # Read them
            msg_type, rx_msg_nbr, msg = client.recv_multipart()

            # If we got acknowledge on transmitted data
            if msg_type == "DATA_ACK":
                if int(rx_msg_nbr) == waiting_for_ack:
                    logging.info("Server acknowledged our data " + rx_msg_nbr)
                    waiting_for_ack = None
                    retires_nbr = 0
                else:
                    # This shouldn't occur to many times - here for possible upgrade
                    # It is rare because if we send new data before we get prev ack, int waiting_for_ack will 
                    # be overwritten...but it still can happen if we overwrite message and receive prev ack right after it
                    logging.warning("Got ACK for msg %s instead of %s.." % (rx_msg_nbr, waiting_for_ack))
                    waiting_for_ack = None
                    retires_nbr = 0

            elif msg_type == "UNI_CMD":
                logging.info("Received UNI_CMD [%s]: %s" % (rx_msg_nbr,msg))

                # Obtain the info upon received command 
                info = obtain_info(msg)

                # Form reply
                reply = ["UNI_DAT", rx_msg_nbr, info]

                # Respond to the server
                logging.debug("Sending data...")
                client.send_multipart(reply)

                # If waiting is still true, that means that server did not hear us until now
                if waiting_for_ack:
                    logging.warning("Got new command but server didn't ack our previous message!")
                    # logging.warning("Old message will be discarted.. :/")
                    # If user needs that message again, he will request for it.. 
                
                waiting_for_ack = rx_pub_nbr
                last_sent_info = reply
                last_sent_time = timer.now()

            else:
                loging.warning("Received unknown type of message...discarting.")


        # If we sent one message and there was no response for more than a second, resend it
        if waiting_for_ack > 0:
            # Check how long we waited for ACK - if second passed
            time_now = timer.now()
            if ((time_now - last_sent_time).total_seconds() > 1):
                logging.warning("Second has passed and no response from server.. Resending data!")
                # Resend info
                client.send_multipart(last_sent_info)
                waiting_for_ack = last_sent_info[1] # tx_msg_nbr
                last_sent_time = timer.now()

                retires_nbr += 1
                if retires_nbr > 2:
                    # Server has died ?
                    waiting_for_ack = None
                    retires_nbr = 0
                    logging.warning("Server has died :(")

        
        # Do some other stuff
        print(".")
        #logging.debug(".")
        time.sleep(0.1)




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

# Socket for responding to server
logging.debug("Connecting to router server...")
device_address = u'LGTC-%s' % sys.argv[1]
client = context.socket(zmq.DEALER)
client.identity = device_address.encode("ascii")
client_ident = client.identity
client.connect('tcp://192.168.88.253:5562')

logging.info("Device name: %s" % device_address)

# Configure poller
poller = zmq.Poller()
poller.register(subscriber, zmq.POLLIN)
poller.register(client, zmq.POLLIN)

main()