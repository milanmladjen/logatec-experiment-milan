
import zmq 
import time
import logging
import signal, sys, os

from timeit import default_timer as timer

from lib import testbed_database


# --------------------------------------------------------------------------------------------
# EXPERIMENT DEFINITIONS AND CONFIGURATION
# --------------------------------------------------------------------------------------------

LOG_LEVEL = logging.DEBUG
LOGGING_FILENAME = "ECMS_controller.log"

try:
    NUMBER_OF_DEVICES = int(os.environ["DEVICE_NUM"])
except:
    print("No device number given...going with default: 21")
    NUMBER_OF_DEVICES = 21

try:
    RADIO_TYPE = os.environ["RADIO_TYPE"]
except:
    print("No radio type given...going with default: TEST_TYPE")
    RADIO_TYPE = "TEST_TYPE"





# --------------------------------------------------------------------------------------------
# ZeroMQ class
# --------------------------------------------------------------------------------------------
class zmq_broker():

    # ----------------------------------------------------------------------------------------
    # Initialize sockets and poller
    # ----------------------------------------------------------------------------------------
    def __init__(self):
        self.log = logging.getLogger("zmq_broker")
        self.log.setLevel(LOG_LEVEL)

        context = zmq.Context.instance()

        # Socket for communication with Flask server
        self.frontend = context.socket(zmq.ROUTER)
        #frontend.bind("ipc:///tmp/zmq_ipc")
        self.frontend.bind("tcp://*:5563")
        self.controller_server_id = b"flask_process"      # As defined in controller_server.py

        # Socket for publishing LGTC commands
        self.backend_pub = context.socket(zmq.PUB)
        self.backend_pub.sndhwm = 1100000
        self.backend_pub.bind('tcp://*:5561')

        # Socket to get responses from LGTC
        self.backend = context.socket(zmq.ROUTER)
        self.backend.bind('tcp://*:5562')

        # Configure poller
        self.poller = zmq.Poller()
        self.poller.register(self.backend, zmq.POLLIN)
        self.poller.register(self.frontend, zmq.POLLIN)



    # ----------------------------------------------------------------------------------------
    # Check poller for any incoming message
    #
    #   @params:    timeout - number of ms to wait (0 = return immediately)
    #   @return:    name of the instance that received the message
    # ----------------------------------------------------------------------------------------
    def check_input(self, timeout):
        sockets = dict(self.poller.poll(timeout))

        if sockets.get(self.backend) == zmq.POLLIN:
            return "BACKEND"
        elif sockets.get(self.frontend) == zmq.POLLIN:
            return "FRONTEND"
        else:
            return None



    # ----------------------------------------------------------------------------------------
    # Read received message from backend socket. 
    #
    #   @return:    nbr - number of received message (-1 means SYSTEM message)
    #               adr - name of the device that sent the message
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def backend_receive(self):
        self.log.debug("Received from backend...")

        adr, nbr, data = self.backend.recv_multipart()

        return nbr.decode(), adr.decode(), data.decode()


    # ----------------------------------------------------------------------------------------
    # Send a message to a device in backend.
    #
    #   @params:    nbr - number of sent message (-1 means SYSTEM message)
    #               adr - name of targeted device
    #                     if adr is "All" send message to all devices (publish socket)           
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def backend_send(self, nbr, adr, data):

        if adr == "All":
            self.log.debug("Publish message [%s]: %s" % (nbr, data))

            cmd ="%s %s" % (nbr, data)
            self.backend_pub.send(cmd.encode())

        else:
            self.log.debug("Router send message [%s]: %s to device %s" % (nbr, data, adr))

            self.backend.send_multipart([adr.encode(), nbr.encode(), data.encode()])




    # ----------------------------------------------------------------------------------------
    # Read received message from frontend socket. Used for forwarding commands from F -> B and
    # for sending user commands targeted for broker script (depends on the the adr var)
    #
    #   @return:    nbr - number of received message OR type of message for broker
    #               adr - name of targeted device 
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def frontend_receive(self):
        self.log.debug("Received from frontend...")

        # dummy is the frontend ID
        dummy, nbr, adr, data = self.frontend.recv_multipart()

        return nbr.decode(), adr.decode(), data.decode()

    # ----------------------------------------------------------------------------------------
    # Send message to the frontend socket. Used for forwarding responses B -> F and for 
    # sending some experiment commands for server script
    #
    #   @params:    nbr - number of response OR type (tip) of message for server
    #               adr - name of device that sent response
    #               data - ...
    # ----------------------------------------------------------------------------------------
    def frontend_send(self, nbr, adr, data):
        self.log.debug("Send to frontend: [" + nbr +"|" + adr + "|" + data +"]")

        self.frontend.send_multipart(
            [self.controller_server_id, nbr.encode(), adr.encode(), data.encode()])

    # ----------------------------------------------------------------------------------------
    # Send device state to frontend socket - costum function to inform server about new state.
    #
    #  @params:     device - name of device
    #               state  - new state of device
    # ----------------------------------------------------------------------------------------
    def frontend_deviceUpdate(self, device, state):
        self.log.debug("Send new state of device to frontend...")

        self.frontend.send_multipart(
            [self.controller_server_id, b"DEVICE_UPDATE", device.encode(), state.encode()])

    # ----------------------------------------------------------------------------------------
    # Send some info string to frontend socket - costum function to inform user about smth.
    #
    #  @params:     info - string which will be displayed to the user console
    #               
    # ----------------------------------------------------------------------------------------
    def frontend_info(self, device, info):
        self.log.debug("Send info to frontend: " + info)

        self.frontend.send_multipart(
            [self.controller_server_id, b"INFO", device.encode(), info.encode()])



def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)


# --------------------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------------------
if __name__ == "__main__":

    # For gracefull stop with $docker stop command
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Config logging module format for all scripts. 
    # Log level is defined in each submodule with var LOG_LEVEL.
    logging.basicConfig(format="%(asctime)s [%(levelname)7s]:[%(name)16s > %(funcName)16s() > %(lineno)3s] - %(message)s", level=LOG_LEVEL, filename=LOGGING_FILENAME)
    #logging.basicConfig(format="[%(levelname)5s:%(funcName)16s() > %(module)17s] %(message)s", level=LOG_LEVEL)
    log = logging.getLogger("main")

    log.info("New experiment " + RADIO_TYPE + " with " + str(NUMBER_OF_DEVICES) + " devices available!")
    
    # Init ZMQ 
    broker = zmq_broker()

    # Small delay for zmq init
    time.sleep(1)

    # Init database library
    db = testbed_database.testbed_database("database.db")

    # Inform frontend that experiment began
    broker.frontend_send("EXP_START", "Controller", RADIO_TYPE)
    broker.frontend_info("Controller", "New active experiment in the testbed! \n")

    log.info("Starting main loop...")

    subscribers = 0
    #hb_time = timer()

    # ----------------------------------------------------------------------------------------
    # MAIN LOOP
    try:
        while True:

            inp = broker.check_input(100)

            # ------------------------------------------------------------------------------------
            # FRONTEND --> BACKEND
            if inp == "FRONTEND":
                msg_type, address, arguments = broker.frontend_receive()

                # UPDATE TESTBED STATE - return state of testbed to server
                if msg_type == "TESTBED_UPDATE":
                    log.info("Return testbed state:")
                    log.debug(db.get_tb_state_str)
                    broker.frontend_send(msg_type, "Controller", str(db.get_tb_state_json()))

                # FORWARD COMMAND - to LGTC devices
                else:
                    # Addres must be in database, otherwise it is not active
                    if db.is_dev(address) or (address == "All"):
                        sqn = msg_type
                        broker.backend_send(sqn, address, arguments)
                    else:
                        log.warning("Device address is not in DB")
                        broker.frontend_info("Controller", "Device " + address + " is not active!")
                        broker.frontend_deviceUpdate(address,"OFFLINE")

            # ------------------------------------------------------------------------------------
            # BACKEND --> FRONTEND 
            elif inp == "BACKEND":
                msg_type, device, data = broker.backend_receive()

                # Send ACK back to backend - argument is message to be acknowledged
                broker.backend_send("ACK", device, msg_type)

                # SYSTEM MESSAGES
                if msg_type == "SYNC":

                    # If device come to experiment add it do database
                    if not db.is_dev(device):
                        db.insert_dev(device, "ONLINE")
                        broker.frontend_deviceUpdate(device, "ONLINE")
                        log.info("New device " + device)

                        subscribers += 1
                        if subscribers == NUMBER_OF_DEVICES:
                            log.info("All devices ("+ str(NUMBER_OF_DEVICES) +") active")
                            broker.frontend_info("Controller", "All devices (" + str(NUMBER_OF_DEVICES) +") available!")

                    else:
                        log.warning("Device %s allready in the experiment" % device)
                        # TODO send END command to LGTC with stated reason

                # TODO - tega ne uporablja client nikjer
                elif msg_type == "ERROR":
                    # Device encountered an error and stopped working
                    db.remove_dev(device)
                    broker.frontend_deviceUpdate(device, "OFFLINE")
                    log.warning("Device %s send ERROR message..." % address)

                # DEVICE STATE UPDATE
                elif msg_type == "STATE":
                    db.update_dev_state(device, data)
                    broker.frontend_deviceUpdate(device, data)
                    log.info("New state of device %s: %s" % (device, data))

                    if data == "OFFLINE":
                        subscribers -= 1
                        if subscribers == 0:
                            log.info("All devices offline -> exiting!")
                            break

                # DEVICE INFO
                elif msg_type == "INFO":
                    broker.frontend_info(device, data)
                
                # EXPERIMENT COMMAND RESPONSE
                else:
                    # Forward response back to the server
                    # msg_type is a command SEQUENCE NUMBER 
                    broker.frontend_send(msg_type, device, data)
                    log.debug("Response number [%s] from device %s: %s" % (msg_type, device, data))



            # -----------------------------------------------------------------------------------
            # HEARTBEAT - TODO
            #else:
            # Every 3 seconds send STATE command to all of active devices in the experiment
            # Update database accordingly
            #if((timer() - hb_time) > 3):
            #hb_time = timer()

            #device = TODO: get it from DB
            #cmd = [device, "-1", "STATE"]

    # --------------------------------------------------------------------------------------------
    # END
    except KeyboardInterrupt:
        pass
    
    except Exception as e:
        #logging.error(traceback.format_exc())
        logging.error(e.__doc__)
        logging.error(e.message)
    
    finally:

        # Inform the frontend that experiment has stopped
        broker.frontend_send("EXP_STOP", "", "")
        broker.frontend_info("Controller", "\n Experiment ended! \n -----------------")

        log.info("End of controller main loop...")
