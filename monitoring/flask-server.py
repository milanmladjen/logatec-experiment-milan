#   TODO
#   Maybe use socketio threads instead of threading library? (example: https://github.com/shanealynn/async_flask/blob/master/application.py)
#

from threading import Thread, Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import zmq


# Global variable - command in queue, which needs to be sent to LGTC device
# If array is empty that means that no message needs to be sent. 
# Because it is thread shared variable, use lock before using it 
message_to_send = []
lock = Lock()

# Flask and SocketIO config
app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)

thread = Thread()

# ------------------------------------------------------------------------------- #
# Flask
# ------------------------------------------------------------------------------- #

# Store essential values and use it in case of page reload-TODO MongoDB
templateData ={
    "example_string" : "monitor" 
}

@app.route("/")
def index():
    # Use jinja2 template to render html with app values
    return render_template("index.html", **templateData)



# ------------------------------------------------------------------------------- #
# SocketIO
# ------------------------------------------------------------------------------- #
@socketio.on("connect")
def connect():
    print("Client connected")
    emit("after connect",  {"data":"Hello there!"})

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
    lock.acquire()
    global message_to_send
    message_to_send = [cmd["device"].encode(), cmd["count"].encode(), cmd["data"].encode()] # From dict to byte array
    #print(message_to_send)
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
        
        # print("Thread")

        lock.acquire()
        global message_to_send

        # If there is any message to be sent
        if message_to_send:
            print("Send message to broker!")
            print(message_to_send)
            zmq_soc.send_multipart(message_to_send)
            message_to_send = []
            lock.release()

        else:
            lock.release()

            socks = dict(poller.poll(0))

            if socks.get(zmq_soc) == zmq.POLLIN:

                print("Received message from broker!")

                device, count, data = zmq_soc.recv_multipart()

                # From bytes to string [device, count, data]
                msg = [device.decode(), count.decode(), data.decode()]

                if msg[0] == "All":
                    socketio.emit("status update", {"data":"update smth"}, broadcast=True)
                
                else:
                    # Form response in dict
                    response = {
                        "device" : msg[0],
                        "count" : msg[1],
                        "data" : msg[2]
                    }
                    print("Forwarding it to client...")
                    # Forward message to the client over websockets
                    socketio.emit("command response", response, broadcast=True)
            else:
                socketio.sleep(0.5)




if __name__ == '__main__':

    #worker = zmqWorker()
    #worker.start()

    thread = socketio.start_background_task(zmqThread)


    print("Start the server!")
    socketio.run(app, host='0.0.0.0', debug=False)

