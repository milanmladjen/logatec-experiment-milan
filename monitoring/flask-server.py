#   TODO
#   Maybe use socketio threads instead of threading library? (example: https://github.com/shanealynn/async_flask/blob/master/application.py)
#

from threading import Thread
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import zmq

# Flask and SocketIO config
app = Flask(__name__)
socketio = SocketIO(app)

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
    #print(cmd)

    # Forward the received command from client browser to the 0MQ broker script
    zmq_socket.send_multipart([cmd["device"].encode(), cmd["count"].encode(), cmd["data"].encode()])

def socketio_send_response(resp):
    socketio.emit("command response", resp, broadcast=True)

def socketio_send_status_update():
    socketio.emit("status update", {"data":"update smth"}, broadcast=True)



# ------------------------------------------------------------------------------- #
# 0MQ communication between 2 processes (IPC transport)
# ------------------------------------------------------------------------------- #
context = zmq.Context()
zmq_socket = context.socket(zmq.DEALER)
zmq_socket.setsockopt(zmq.IDENTITY, b"flask_process")
zmq_socket.connect("ipc:///tmp/zmq_ipc")



# ------------------------------------------------------------------------------- #
# Another thread only for receiving messages from 0MQ broker script
# ------------------------------------------------------------------------------- #
class zmqWorker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.active = True
 
    def run(self):
        poller = zmq.Poller()
        poller.register(zmq_socket, zmq.POLLIN)

        while self.active:
            # Check if there is any message for us in queue (reduce it to 100ms or such)
            socks = dict(poller.poll(1000))

            if socks.get(zmq_socket) == zmq.POLLIN:

                print("Received message from broker!")

                device, count, data = zmq_socket.recv_multipart()

                # From bytes to string [device, count, data]
                msg = [device.decode(), count.decode(), data.decode()]

                if msg[0] == "all":
                    socketio_send_status_update()
                
                else:
                    # Form response in dict
                    response = {
                        "device" : msg[0],
                        "count" : msg[1],
                        "data" : msg[2]
                    }
                    # Forward message to the client over websockets
                    socketio_send_response(response)




if __name__ == '__main__':

    worker = zmqWorker()
    worker.start()

    print("Start the server!")
    socketio.run(app, host='0.0.0.0', debug=True)

