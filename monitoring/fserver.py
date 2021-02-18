#   TODO
#   Maybe use socketio threads instead of threading library? (example: https://github.com/shanealynn/async_flask/blob/master/application.py)
#

from threading import Thread, Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import zmq

import ast  # From str to json conversion


# Global variable - command in queue, which needs to be sent to LGTC device
# If array is empty that means that no message needs to be sent. 
# Because it is thread shared variable, use lock before using it 
message_to_send = []
update_testbed = False
experiment_started = False
lock = Lock()

# Flask and SocketIO config
app = Flask(__name__, static_url_path="", static_folder="static", template_folder="templates")
socketio = SocketIO(app, async_mode=None)

thread = Thread()

# ------------------------------------------------------------------------------- #
# Flask
# ------------------------------------------------------------------------------- #

# Store essential values and use it in case of page reload-TODO MongoDB
templateData ={
    "example_string" : "monitor" 
}

@app.route("/controller")
def index():
    # Use jinja2 template to render html with app values
    return render_template("index.html", **templateData)



# ------------------------------------------------------------------------------- #
# SocketIO
# ------------------------------------------------------------------------------- #
@socketio.on("connect")
def connect():
    print("Client connected")

    lock.acquire()
    global experiment_started
    reply = {"data":str(experiment_started)}
    lock.release()

    emit("after connect", reply)

@socketio.on("disconnect")
def disconnect():
    print("Client disconnected.")

@socketio.on("new command")
def received_command(cmd):
    print("Client sent: ")
    print(cmd)

    # Forward the received command from client browser to the 0MQ broker script
    # Can't send it from here, because 0MQ is in other thread - using 0MQ context
    # in multiple threads may cause problems (it is not thread safe)

    # If messages from client come to quickly, overwrite them TODO maybe inform user?
    lock.acquire()
    global message_to_send
    message_to_send = [cmd["device"].encode(), cmd["count"].encode(), cmd["data"].encode()] # From dict to byte array
    lock.release()

@socketio.on("testbed update")
def get_testbed_state():
    print("Client wants to update testbed state")

    # Same goes here
    lock.acquire()
    global update_testbed 
    update_testbed = True
    lock.release()


def socketio_send_response(resp):
    socketio.emit("command response", resp, broadcast=True)

def socketio_send_status_update():
    socketio.emit("status update", {"data":"update smth"}, broadcast=True)



# ------------------------------------------------------------------------------- #
# Another thread only for receiving messages from 0MQ broker script
# 0MQ communication between 2 processes (IPC transport)
# ------------------------------------------------------------------------------- #
def zmqThread():

    active = True
    context = zmq.Context()
    zmq_soc = context.socket(zmq.DEALER)
    zmq_soc.setsockopt(zmq.IDENTITY, b"flask_process")
    zmq_soc.connect("ipc:///tmp/zmq_ipc")

    poller = zmq.Poller()
    poller.register(zmq_soc, zmq.POLLIN)

    print("Initialized 0MQ")

    socketio.sleep(1)
 
    while active:
        
        global experiment_started
        global message_to_send
        global update_testbed
        lock.acquire()

        # If there is any message to be sent to backend
        if message_to_send:
            print("Send message to broker!")
            print(message_to_send)
            zmq_soc.send_multipart(message_to_send)
            message_to_send = []
            lock.release()
        
        # Or if user wants to update the testbed state manually
        elif update_testbed:
            print("Get testbed state from brokers database.")
            zmq_soc.send_multipart([b"TestbedUpdate", b"", b""])
            update_testbed = False
            lock.release()

        # Else check for incoming messages
        else:
            lock.release()

            socks = dict(poller.poll(0))

            if socks.get(zmq_soc) == zmq.POLLIN:

                device, count, data = zmq_soc.recv_multipart()

                # From bytes to string [device, count, data]
                msg = [device.decode(), count.decode(), data.decode()]

                # Received new device state
                if msg[0] == "DeviceUpdate":
                    print("Received new device state from brokers database!")

                    # From string to dict
                    json = ast.literal_eval(msg[2])

                    update = {
                            "device" : "Update",
                            "count" : msg[1],
                            "data" : json
                        }
                    socketio.emit("device state update", update, broadcast=True)

                # Received whole testbed device state
                elif msg[0] == "TestbedUpdate":
                    print("Received testbed state from brokers database!")

                    # From string to list of dicts
                    json_data = ast.literal_eval(msg[2])

                    state = {
                        "device" : "Update",
                        "count" : msg[1],
                        "data" : json_data
                    }
                    socketio.emit("testbed state update", state, broadcast=True)

                # Sync between broker and flask server in the beginning
                elif msg[0] == "Online":
                    print("Experiment has started")

                    lock.acquire()
                    experiment_started = True
                    lock.release()

                    socketio.emit("experiment started", {}, broadcast=True)

                # When broker exits, inform the user
                elif msg[0] == "End":
                    print("Experiment has stopped")

                    lock.acquire()
                    experiment_started = False
                    lock.release()

                    socketio.emit("experiment stopped", {}, broadcast=True)

                # Received command response
                else:
                    print("Received message from broker!")
     
                    response = {
                        "device" : msg[0],
                        "count" : msg[1],
                        "data" : msg[2]
                    }

                    # Forward message to the client over websockets
                    socketio.emit("command response", response, broadcast=True)
            else:
                socketio.sleep(0.5)


thread = socketio.start_background_task(zmqThread)

if __name__ == '__main__':

    print("Start the server!")
    socketio.run(app, host="localhost", port=8001, debug=False)

