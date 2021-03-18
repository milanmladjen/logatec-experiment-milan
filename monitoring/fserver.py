# -------------------------------------------------------------------------------
# TODO:
# * Display essential values from DB when clients connects to the server
# -------------------------------------------------------------------------------


# import eventlet
# eventlet.monkey_patch()

from threading import Thread, Lock, Event
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import zmq
import ast  # From str to json conversion


# Global variables:
message_to_send = []
update_testbed = False
experiment_started = False

# Thread init
lock = Lock()
thread = Thread()
thread_stop_event = Event()

# Flask and SocketIO config
app = Flask(__name__, static_url_path="", static_folder="static", template_folder="templates")

socketio = SocketIO(app, async_mode="eventlet", path="/socket.io")


# ------------------------------------------------------------------------------- #
# Flask
# ------------------------------------------------------------------------------- #

# Store essential values and use it in case of page reload-TODO from DB
templateData ={
    "example_string" : "monitor" 
}

# Serve templates
@app.route("/")
def index():
    # Use jinja2 template to render html with app values
    return render_template("index.html", **templateData)


# Serve static files - should use Nginx for that
@app.route("/static/js/<path:path>")
def send_js(path):
    return send_from_directory("static/js/", path)

@app.route("/static/css/<path:path>")
def send_css(path):
    return send_from_directory("static/css/", path)

@app.route("/static/img/<path:path>")
def send_img(path):
    return send_from_directory("static/img/", path)



# ------------------------------------------------------------------------------- #
# SocketIO
# ------------------------------------------------------------------------------- #
@socketio.on("connect")
def connect():
    print("Client connected")

    # Start ZMQ background thread if it is not active
    global thread
    if not thread.is_alive():
        print("Start ZMQ thread")
        thread = socketio.start_background_task(zmqThread)

    lock.acquire()
    global experiment_started
    reply = {"data":str(experiment_started)}
    lock.release()

    emit("after connect", reply)

@socketio.on("disconnect")
def disconnect():
    print("Client disconnected.")

    # Stop the ZMQ thread
    #thread_stop_event.set()

@socketio.on("new command")
def received_command(cmd):
    print("Client sent: ")
    print(cmd)

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
# ZeroMQ
# ------------------------------------------------------------------------------- #
def zmqThread():

    active = True
    context = zmq.Context()
    zmq_soc = context.socket(zmq.DEALER)
    zmq_soc.setsockopt(zmq.IDENTITY, b"flask_process")
    #zmq_soc.connect("ipc:///tmp/zmq_ipc")      # local test (on PC)
    #zmq_soc.connect("tcp://192.168.88.239:5563")# local test (Docker)
    zmq_soc.connect("tcp://193.2.205.19:5563") # testbed 

    poller = zmq.Poller()
    poller.register(zmq_soc, zmq.POLLIN)

    print("Initialized 0MQ")

    socketio.sleep(1)
 
    while not thread_stop_event.is_set():
        
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

# Run the ZMQ thread in the beginning
thread = socketio.start_background_task(zmqThread)

if __name__ == '__main__':

    print("Start the server!")
    socketio.run(app, host="localhost", port=8001, debug=False)









# -------------------------------------------------------------------------------
# DEPLOYMENT WITH GUNICORN & EVENTLET
#
# A WSGI server is recommended for Flask app deployment - Gunicorn with eventlet  
# https://flask-socketio.readthedocs.io/en/latest/#deployment
# Run with: gunicorn --bind localhost:8001 --worker-class eventlet -w 1 fserver:app
# 
# Optional: you can deploy Flask app only with eventlet (without Gunicorn)
# Than use monkey patching on the begining of the script
# https://flask-socketio.readthedocs.io/en/latest/#using-multiple-workers
# Run with: python3 fserver.py
# -------------------------------------------------------------------------------
# STATIC FILES
# 
# Recommended way of serving static files is to use Nginx. 
#
# location /controller/static {
#                alias /.../monitoring/static;
# }
#
# But if we don't want it, Flask can also serve static files...
# (https://stackoverflow.com/questions/20646822/how-to-serve-static-files-in-flask)
# -------------------------------------------------------------------------------
# SOCKET MULTIPLEXING
#
# If multiple connections on single websockets are needed, add "namespaces" to 
# the application...
# usecase: if SMS portal will need another WebSocket communication on default URL
# https://socket.io/docs/v3/namespaces/index.html
# https://flask-socketio.readthedocs.io/en/latest/
#-------------------------------------------------------------------------------
# CORS
# 
# For security reasons, CORS is not enabled by default, thus disabling WebSockets
# on different domains names than default server name - problem because of Nginx 
# proxying. WS client (script.js) can now connect to the WS server (fserver.py)
#
# Enableing all domains:
#       cors_allowed_origins="*"
# exposes potential risks (https://flask-socketio.readthedocs.io/en/latest/)
# so solution for now is:
#       cors_allowed_origins="http://localhost"
# 
# Read more on:
# https://socket.io/docs/v3/client-initialization/
# https://flask-socketio.readthedocs.io/en/latest/#cross-origin-controls
#-------------------------------------------------------------------------------
# ZMQ
# 
# Is used to communicate with Controller Docker container (zmq-broker.py) over
# 0MQ TCP sockets. ZMQ is not threadsafe (using zmq context in multiple threads
# is not safe), while SocketIO is. That's why they exchange messages via global 
# variables. Use Lock() before accessing them.
#
# IPC (inter process communication) sockets can be used if this script is 
# running on the same machine as broker script. Otherwise use TCP sockets.
# zmq.connect() must have parametrized address!
# While in Docker container, 127.0.0.1 won't work - use machine IP address  